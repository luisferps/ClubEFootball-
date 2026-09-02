# -*- coding: utf-8 -*-
"""Testes sem banco para o protocolo de arquivos da operação local JSON."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
