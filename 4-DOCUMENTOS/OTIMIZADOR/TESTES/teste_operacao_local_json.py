# -*- coding: utf-8 -*-
"""Testes sem banco para o protocolo de arquivos da operação local JSON."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from urllib.error import HTTPError
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


RAIZ = Path(__file__).resolve().parents[3]
FONTE = RAIZ / "2-MOTORES" / "OTIMIZADOR" / "OPERACAO-LOCAL-JSON" / "programas" / "operacao_local_json.py"
MIGRACAO = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "MIGRACAO-OPERACAO-LOCAL-JSON-V65.sql"

ESPEC = importlib.util.spec_from_file_location("operacao_local_json", FONTE)
assert ESPEC and ESPEC.loader
MODULO = importlib.util.module_from_spec(ESPEC)
ESPEC.loader.exec_module(MODULO)


def item(linha_id: int) -> dict:
    return {
        "linha_id": linha_id,
        "calculado_em_utc": "2026-09-02T00:00:00Z",
        "resultado": {"b1": 1, "barras": {}, "tecnico_id": 1, "habilidades": [], "builds_comparadas": 1, "builds_possiveis": 1},
    }


class OperacaoLocalJsonTest(unittest.TestCase):
    def test_jornal_duravel_e_leitura(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            arquivo = Path(temporario) / "resultado-000001.jsonl"
            MODULO.acrescentar_jsonl_duravel(arquivo, item(10))
            MODULO.acrescentar_jsonl_duravel(arquivo, item(11))
            self.assertEqual([10, 11], [x["linha_id"] for x in MODULO.ler_jsonl(arquivo)])

    def test_jornal_parcial_vira_resultado_pronto_no_encerramento(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            estrutura = MODULO.garantir_estrutura(Path(temporario) / "saida")
            pacote = SimpleNamespace(lote_id="lote-teste", manifesto={
                "lote_fingerprint": "lote", "contrato_fingerprint": "contrato",
                "formula_fingerprint": "formula", "motor_versao": "motor",
            })
            jornal = estrutura["trabalho"] / "resultado-000001.jsonl"
            MODULO.acrescentar_jsonl_duravel(jornal, item(10))
            final = MODULO.finalizar_jornal(estrutura, pacote, 1, jornal, MODULO.ler_jsonl(jornal))
            self.assertFalse(jornal.exists())
            self.assertTrue(final.is_file())
            self.assertEqual([10], [x["linha_id"] for x in MODULO._ler_envelope(final)["itens"]])

    def test_recibo_nao_perde_hora_confirmada(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            arquivo = Path(temporario) / "recibos.jsonl"
            recibo = {
                "contrato": MODULO.CONTRATO_RECIBO,
                "confirmado": True,
                "linha_id": 10,
                "enviado_em_utc": "2026-09-02T00:01:00Z",
            }
            MODULO.acrescentar_jsonl_duravel(arquivo, recibo)
            self.assertEqual("2026-09-02T00:01:00Z", MODULO._recibos_confirmados(arquivo)[10]["enviado_em_utc"])

    def test_migracao_exige_lote_pausado_e_grava_os_dois_tempos(self) -> None:
        texto = MIGRACAO.read_text(encoding="utf-8").lower()
        self.assertIn("v_lote.estado <> 'pausado'", texto)
        self.assertIn("p_calculado_em_utc", texto)
        self.assertIn("otimizador_finalizado_em = v_enviado_em", texto)
        self.assertIn("'enviado_em_utc', v_enviado_em", texto)
        self.assertIn("'idempotente', true", texto)
        self.assertIn("revoke all on function", texto)

    def test_resultado_compacto_nao_vaza_chave(self) -> None:
        envelope = {"contrato": MODULO.CONTRATO_RESULTADO, "versao": 1, "itens": [item(10)]}
        texto = MODULO.texto_json(envelope)
        self.assertNotIn("SUPABASE_KEY", texto)
        self.assertEqual(envelope, json.loads(texto))

    def test_painel_mostra_id_no_contexto_do_nome_da_carta(self) -> None:
        painel = io.StringIO()
        pacote = SimpleNamespace(manifesto={"linhas_total": 100, "cartas_total": 10})
        linha = {
            "linha_id": 42,
            "card_id": "55068728",
            "carta_nome": "Carta de teste",
            "funcao_rotulo": "Meia ofensivo",
            "posicao_rotulo": "Meia atacante",
        }
        with redirect_stdout(painel):
            MODULO._mostrar_processamento(pacote, 1, 0, 0, 0, linha, 0.0)
        texto = painel.getvalue()
        self.assertIn("Linha da fila: 42", texto)
        self.assertIn("Carta: Carta de teste (ID da carta: 55068728)", texto)
        self.assertIn("Função: Meia ofensivo", texto)
        self.assertIn("Posição: Meia atacante", texto)

    def test_repeticao_igual_conta_uma_linha_e_divergencia_para(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            pasta = Path(temporario)
            primeiro = pasta / "resultado-000001.json"
            segundo = pasta / "resultado-000002.json"
            envelope = {"contrato": MODULO.CONTRATO_RESULTADO, "versao": 1, "itens": [item(10)]}
            MODULO.gravar_json_atomico(primeiro, envelope)
            MODULO.gravar_json_atomico(segundo, envelope)
            unicos, total, repetidos = MODULO._inventariar_resultados([primeiro, segundo])
            self.assertEqual({10}, set(unicos))
            self.assertEqual(2, total)
            self.assertEqual(1, repetidos)

            divergente = item(10)
            divergente["resultado"] = {**divergente["resultado"], "b1": 2}
            MODULO.gravar_json_atomico(segundo, {**envelope, "itens": [divergente]})
            with self.assertRaises(MODULO.FalhaOperacao):
                MODULO._inventariar_resultados([primeiro, segundo])

    def test_resumo_de_envio_nao_e_resultado_e_nao_para_processamento(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            pasta = Path(temporario)
            resultado = pasta / "resultado-000008.json"
            resumo = pasta / "resultado-000008.resumo.json"
            MODULO.gravar_json_atomico(resultado, {
                "contrato": MODULO.CONTRATO_RESULTADO,
                "versao": 1,
                "itens": [item(10)],
            })
            MODULO.gravar_json_atomico(resumo, {
                "contrato": "otimizador_resumo_envio_local_json_v1",
                "total_confirmado": 1,
            })
            self.assertEqual([resultado], MODULO._arquivos_resultado(pasta))
            self.assertEqual(1, MODULO.contar_resultados(pasta))

    def test_linha_ja_concluida_e_decisao_terminal_nao_sao_retentadas(self) -> None:
        original_urlopen = MODULO.urllib.request.urlopen

        def recusar(*_args, **_kwargs):
            raise HTTPError(
                "https://exemplo.test/rpc",
                400,
                "Bad Request",
                {},
                io.BytesIO('{"message":"importação JSON recusada: linha concluída com resultado diferente"}'.encode("utf-8")),
            )

        MODULO.urllib.request.urlopen = recusar
        try:
            with self.assertRaises(MODULO.LinhaJaConcluidaNoBanco):
                MODULO.chamar_importacao("https://exemplo.test", "chave-teste", "lote", item(10))
        finally:
            MODULO.urllib.request.urlopen = original_urlopen

        with tempfile.TemporaryDirectory() as temporario:
            recibo = Path(temporario) / "resultado-000001.recibos.jsonl"
            decisao = {
                "contrato": MODULO.CONTRATO_RECIBO,
                "confirmado": False,
                "ignorado_por_banco": True,
                "linha_id": 10,
                "motivo": "já existia",
            }
            MODULO.acrescentar_jsonl_duravel(recibo, decisao)
            self.assertEqual({10}, set(MODULO._recibos_terminais(recibo)))
            self.assertEqual({}, MODULO._recibos_confirmados(recibo))

    def test_enviador_arquiva_conflito_e_continua_a_proxima_linha(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario) / "OTIMIZADOR"
            operacao = raiz / MODULO.NOME_PASTA
            lote = "lote-teste"
            pendentes = operacao / "RESULTADOS-JSON" / lote / "PENDENTES"
            pendentes.mkdir(parents=True)
            (operacao / "config.txt").write_text(
                "SUPABASE_URL=https://exemplo.test\nSUPABASE_KEY=chave-teste\n",
                encoding="utf-8",
            )
            MODULO.gravar_json_atomico(pendentes / "resultado-000001.json", {
                "contrato": MODULO.CONTRATO_RESULTADO,
                "versao": 1,
                "lote_id": lote,
                "itens": [item(10), item(11)],
            })
            original_chamada = MODULO.chamar_importacao

            def confirmar_ou_conflitar(_url, _chave, _lote, entrada):
                if int(entrada["linha_id"]) == 10:
                    raise MODULO.LinhaJaConcluidaNoBanco("a linha 10 já foi concluída no banco com outro resultado")
                return {
                    "contrato": MODULO.CONTRATO_IMPORTACAO,
                    "linha_id": int(entrada["linha_id"]),
                    "enviado_em_utc": "2026-09-02T00:02:00Z",
                    "build_otimizador_id": 123,
                    "resultado_fingerprint": "teste",
                    "idempotente": False,
                }

            MODULO.chamar_importacao = confirmar_ou_conflitar
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(0, MODULO.enviar(raiz, lote, None))
            finally:
                MODULO.chamar_importacao = original_chamada

            arquivo_final = operacao / "RESULTADOS-JSON" / lote / "ARQUIVADOS-COM-CONFLITO" / "resultado-000001.json"
            self.assertTrue(arquivo_final.is_file())
            self.assertFalse((pendentes / "resultado-000001.json").exists())
            resumo = json.loads((arquivo_final.parent / "resultado-000001.resumo.json").read_text(encoding="utf-8"))
            self.assertEqual(1, resumo["total_confirmado"])
            self.assertEqual(1, resumo["total_ignorado_por_banco"])


if __name__ == "__main__":
    unittest.main()
