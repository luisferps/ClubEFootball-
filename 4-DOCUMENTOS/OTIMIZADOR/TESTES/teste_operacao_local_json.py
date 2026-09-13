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
from unittest.mock import patch


RAIZ = Path(__file__).resolve().parents[3]
FONTE = RAIZ / "2-MOTORES" / "OTIMIZADOR" / "OPERACAO-LOCAL-JSON" / "programas" / "operacao_local_json.py"
MIGRACAO = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3" / "MIGRACAO-OPERACAO-LOCAL-JSON-V65.sql"
MIGRACAO_V67 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "MIGRACAO-OPERACAO-LOCAL-JSON-V67-SELO-POR-LINHA.sql"
)
ROLLBACK_V67 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "ROLLBACK-OPERACAO-LOCAL-JSON-V67-SELO-POR-LINHA.sql"
)
VALIDACAO_V67 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "VALIDAR-OPERACAO-LOCAL-JSON-V67-SELO-POR-LINHA.sql"
)
MIGRACAO_V68 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "MIGRACAO-OPERACAO-LOCAL-JSON-V68-SELO-CANONICO-POR-LINHA.sql"
)
ROLLBACK_V68 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "ROLLBACK-OPERACAO-LOCAL-JSON-V68-SELO-CANONICO-POR-LINHA.sql"
)
VALIDACAO_V68 = (
    RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "FILA-PRODUCAO-V3"
    / "VALIDAR-OPERACAO-LOCAL-JSON-V68-SELO-CANONICO-POR-LINHA.sql"
)

ESPEC = importlib.util.spec_from_file_location("operacao_local_json", FONTE)
assert ESPEC and ESPEC.loader
MODULO = importlib.util.module_from_spec(ESPEC)
ESPEC.loader.exec_module(MODULO)


def item(linha_id: int) -> dict:
    return {
        "linha_id": linha_id,
        "calculado_em_utc": "2026-09-02T00:00:00Z",
        "resultado": {"b1": 1, "barras": {}, "tecnico_id": 1, "habilidades": [], "builds_comparadas": 1, "builds_possiveis": 1,
                      "formula_fingerprint": "formula-atual", "contrato_fingerprint": "contrato-atual", "motor_versao": "v12"},
    }


def pacote_teste(lote_id: str, linhas: list[int]):
    itens = [{"linha_id": linha_id} for linha_id in linhas]
    return SimpleNamespace(
        lote_id=lote_id,
        manifesto={"formula_fingerprint": "formula-atual", "contrato_fingerprint": "contrato-atual", "motor_versao": "v12"},
        validar_integridade=lambda: None,
        iter_linhas=lambda: iter(itens),
    )


class OperacaoLocalJsonTest(unittest.TestCase):
    def test_envio_preserva_formula_antiga_e_envia_atual_da_mesma_linha(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp)/'OTIMIZADOR';op=raiz/MODULO.NOME_PASTA
            pasta=op/'RESULTADOS-JSON/lote/PENDENTES';pasta.mkdir(parents=True)
            antigo=item(10);antigo['resultado']['formula_fingerprint']='formula-v11'
            arquivos=[]
            for n,it in enumerate([antigo,item(10)],1):
                arq=pasta/f'resultado-{n:06d}.json'
                MODULO.gravar_json_atomico(arq,{'contrato':MODULO.CONTRATO_RESULTADO,'versao':1,'lote_id':'lote','itens':[it]})
                arquivos.append(arq)
            antes=arquivos[0].read_bytes()
            resposta={'contrato':MODULO.CONTRATO_IMPORTACAO,'linha_id':10,'enviado_em_utc':'2026-09-09T09:00:00Z',
                      'build_otimizador_id':123,'resultado_fingerprint':'teste','idempotente':False}
            with patch.object(MODULO,'_mortar_pacote',return_value=pacote_teste('lote',[10])),\
                 patch.object(MODULO,'_ler_config',return_value=('https://teste.invalid','teste',{})),\
                 patch.object(MODULO,'chamar_importacao',return_value=resposta) as enviar,redirect_stdout(io.StringIO()):
                self.assertEqual(MODULO.enviar(raiz,'lote',None),0)
                enviar.assert_called_once()
                self.assertEqual(enviar.call_args.args[3]['resultado']['formula_fingerprint'],'formula-atual')
            self.assertEqual(arquivos[0].read_bytes(),antes)
            self.assertFalse(arquivos[1].exists())

    def test_envio_so_antigo_nao_consulta_banco_nem_configuracao(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp);op=raiz/MODULO.NOME_PASTA;pasta=op/'RESULTADOS-JSON/lote/PENDENTES';pasta.mkdir(parents=True)
            antigo=item(10);antigo['resultado']['motor_versao']='v11'
            arq=pasta/'resultado-000001.json'
            MODULO.gravar_json_atomico(arq,{'contrato':MODULO.CONTRATO_RESULTADO,'versao':1,'lote_id':'lote','itens':[antigo]})
            antes=arq.read_bytes()
            with patch.object(MODULO,'_mortar_pacote',return_value=pacote_teste('lote',[10])),\
                 patch.object(MODULO,'_ler_config') as config,patch.object(MODULO,'chamar_importacao') as enviar,redirect_stdout(io.StringIO()):
                self.assertEqual(MODULO.enviar(raiz,'lote',None),0)
                config.assert_not_called();enviar.assert_not_called()
            self.assertEqual(arq.read_bytes(),antes)

    def test_envio_nao_rejeita_so_por_mudanca_do_agregado_do_lote(self):
        with tempfile.TemporaryDirectory() as tmp:
            arq=Path(tmp)/'resultado-000001.json';entrada=item(10)
            entrada['resultado']['lote_fingerprint']='agregado-anterior'
            MODULO.gravar_json_atomico(arq,{'contrato':MODULO.CONTRATO_RESULTADO,'versao':1,'lote_id':'lote','itens':[entrada]})
            pacote=pacote_teste('lote',[10]);pacote.manifesto['lote_fingerprint']='agregado-atual'
            self.assertEqual(MODULO._arquivos_da_formula_atual([arq],pacote),[arq])

    def test_envio_recusa_mistura_ou_ausencia_de_selos_sem_alterar_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            arq=Path(tmp)/'resultado-000001.json';antigo=item(11)
            antigo['resultado']['motor_versao']='v11'
            for itens in ([item(10),antigo],[{'linha_id':10,'calculado_em_utc':'2026-09-09T00:00:00Z','resultado':{}}]):
                MODULO.gravar_json_atomico(arq,{'contrato':MODULO.CONTRATO_RESULTADO,'versao':1,'lote_id':'lote','itens':itens})
                antes=arq.read_bytes()
                with self.assertRaises(MODULO.FalhaOperacao):
                    MODULO._arquivos_da_formula_atual([arq],pacote_teste('lote',[10]))
                self.assertEqual(arq.read_bytes(),antes)

    def test_envio_global_pula_encerrados_preserva_historico_e_continua_em_ordem(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp)/'OTIMIZADOR';op=raiz/MODULO.NOME_PASTA;op.mkdir(parents=True)
            selecao={'contrato':'prioridade_orcamento_v1',
                'lotes':['correcao1','correcao2','encerrado1','encerrado2','restante1','restante2'],
                'lotes_prioritarios':['correcao1','correcao2','encerrado1','encerrado2'],
                'lotes_sem_pendentes':['encerrado1','encerrado2']}
            fila=op/'FILA-ATIVA.json';fila.write_text(json.dumps(selecao));antes=fila.read_bytes()
            antigos=[]
            for lote,n in [('encerrado1',90),('encerrado2',91),('restante1',10),('restante2',11)]:
                pasta=op/'RESULTADOS-JSON'/lote/'PENDENTES';pasta.mkdir(parents=True)
                arq=pasta/'resultado-000001.json'
                MODULO.gravar_json_atomico(arq,{'contrato':MODULO.CONTRATO_RESULTADO,'versao':1,'lote_id':lote,'itens':[item(n)]})
                if lote.startswith('encerrado'):antigos.append((arq,arq.read_bytes()))
            (op/'config.txt').write_text('SUPABASE_URL=https://teste.invalid\nSUPABASE_KEY=teste\n')
            montados=[];enviados=[]
            def montar(_raiz,_op,lote):
                montados.append(lote)
                self.assertIn(lote,['restante1','restante2'])
                return pacote_teste(lote,[10 if lote=='restante1' else 11])
            def confirmar(_url,_chave,lote,entrada):
                enviados.append((lote,entrada['linha_id']))
                return {'contrato':MODULO.CONTRATO_IMPORTACAO,'linha_id':entrada['linha_id'],
                    'enviado_em_utc':'2026-09-09T09:00:00Z','build_otimizador_id':123,
                    'resultado_fingerprint':'teste','idempotente':False}
            with patch.object(MODULO,'_mortar_pacote',side_effect=montar),patch.object(MODULO,'chamar_importacao',side_effect=confirmar),redirect_stdout(io.StringIO()):
                self.assertEqual(MODULO.enviar(raiz,None,None),0)
            self.assertEqual(montados,['restante1','restante2'])
            self.assertEqual(enviados,[('restante1',10),('restante2',11)])
            self.assertEqual(fila.read_bytes(),antes)
            for arq,original in antigos:self.assertEqual(arq.read_bytes(),original)
            for lote in ['restante1','restante2']:
                recibos=list((op/'RESULTADOS-JSON'/lote/'ENVIADOS').glob('*.recibos.jsonl'))
                self.assertEqual(len(recibos),1)

    def test_envio_vazio_nao_exige_pacote_nem_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp);(raiz/MODULO.NOME_PASTA).mkdir()
            with patch.object(MODULO,'_mortar_pacote') as montar,patch.object(MODULO,'_ler_config') as config,redirect_stdout(io.StringIO()):
                self.assertEqual(MODULO.enviar(raiz,'lote',None),0)
                montar.assert_not_called();config.assert_not_called()

    def test_envio_recusa_pacote_ativo_invalido_sem_tocar_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz=Path(tmp);op=raiz/MODULO.NOME_PASTA
            p=op/'RESULTADOS-JSON/ativo/PENDENTES';p.mkdir(parents=True)
            arq=p/'resultado-000001.json';arq.write_text('{"preservar":true}')
            original=arq.read_bytes()
            with patch.object(MODULO,'_mortar_pacote',side_effect=MODULO.FalhaOperacao('selo invalido')),patch.object(MODULO,'chamar_importacao') as gravar:
                with self.assertRaisesRegex(MODULO.FalhaOperacao,'selo invalido'):MODULO.enviar(raiz,'ativo',None)
                gravar.assert_not_called()
            self.assertEqual(arq.read_bytes(),original)

    def test_envio_global_recusa_encerrados_fora_da_selecao(self):
        for encerrados in (['fora'],['ativo','ativo'],'ativo',[None]):
            with self.subTest(encerrados=encerrados),tempfile.TemporaryDirectory() as tmp:
                raiz=Path(tmp);op=raiz/MODULO.NOME_PASTA;op.mkdir()
                (op/'FILA-ATIVA.json').write_text(json.dumps({'contrato':'prioridade_orcamento_v1','lotes':['ativo'],'lotes_sem_pendentes':encerrados}))
                with patch.object(MODULO,'_mortar_pacote') as montar,self.assertRaises(MODULO.FalhaOperacao):MODULO.enviar(raiz,None,None)
                montar.assert_not_called()

    def test_painel_nao_chama_toda_decisao_terminal_de_confirmacao(self) -> None:
        saida = io.StringIO()
        pacote = SimpleNamespace(manifesto={"linhas_total": 10, "cartas_total": 2})
        with redirect_stdout(saida):
            MODULO._mostrar_processamento(pacote, 7, 2, 5, 1)
        texto = saida.getvalue()
        self.assertIn("Cartas neste pacote: 2", texto)
        self.assertIn("Linhas com cálculo local salvo: 7", texto)
        self.assertIn("Resultados locais aguardando envio: 2", texto)
        self.assertIn("Linhas com envio já encerrado: 5", texto)
        self.assertIn("Linhas ainda sem cálculo local: 3", texto)
        self.assertIn("Falhas de cálculo registradas: 1", texto)
        self.assertNotIn("Enviadas e confirmadas pelo banco", texto)

    def test_painel_ignora_resultados_que_sairam_do_pacote_renovado(self) -> None:
        calculadas, prontas, enviadas = MODULO.contagens_painel_pacote(
            ids_pacote={2, 3, 4},
            concluidas={1, 2, 3},
            ids_jornal={4, 99},
            pendentes_unicos={2, 3, 90},
            enviados_unicos={1, 2, 91},
        )
        self.assertEqual(3, calculadas)
        self.assertEqual(1, prontas)
        self.assertEqual(1, enviadas)

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

    def test_v67_confere_e_persiste_selos_imutaveis_da_linha(self) -> None:
        texto = MIGRACAO_V67.read_text(encoding="utf-8").lower()
        self.assertIn(
            "p_resultado->>'formula_fingerprint' is distinct from "
            "v_l.otimizador_formula_fingerprint_esperado",
            texto,
        )
        self.assertIn(
            "p_resultado->>'contrato_fingerprint' is distinct from "
            "v_l.otimizador_contrato_fingerprint_esperado",
            texto,
        )
        self.assertIn(
            "p_resultado->>'motor_versao' is distinct from "
            "v_l.otimizador_motor_versao_esperada",
            texto,
        )
        self.assertIn("v_l.otimizador_contrato_fingerprint_esperado,", texto)
        self.assertIn("v_l.otimizador_formula_fingerprint_esperado,", texto)
        self.assertIn("v_l.otimizador_motor_versao_esperada,", texto)

    def test_v67_nao_invalida_linha_quando_agregado_do_lote_muda(self) -> None:
        texto = MIGRACAO_V67.read_text(encoding="utf-8").lower()
        self.assertNotIn(
            "p_resultado->>'lote_fingerprint' <> v_lote.fingerprint",
            texto,
        )
        self.assertIn("v_lote_fingerprint_recebido !~ '^[0-9a-f]{64}$'", texto)
        self.assertIn("e.evento = 'preparo_integral_concluido'", texto)
        self.assertIn(
            "e.detalhe->>'fingerprint' = v_lote_fingerprint_recebido",
            texto,
        )
        self.assertIn("'lote_fingerprint_recebido', v_lote_fingerprint_recebido", texto)
        self.assertIn(
            "p_resultado->>'carta_entrada_fingerprint' is distinct from "
            "v_q.entrada_fingerprint",
            texto,
        )

    def test_v67_preserva_limites_da_porta_privada_e_tem_rollback(self) -> None:
        texto = MIGRACAO_V67.read_text(encoding="utf-8").lower()
        rollback = ROLLBACK_V67.read_text(encoding="utf-8").lower()
        validacao = VALIDACAO_V67.read_text(encoding="utf-8").lower()
        self.assertIn("security definer", texto)
        self.assertIn("set search_path to ''", texto)
        self.assertIn("from public, anon, authenticated", texto)
        self.assertIn("to service_role", texto)
        self.assertIn("pode_publicar is not false", texto)
        self.assertIn("v_lote.estado <> 'pausado'", texto)
        self.assertIn("p_resultado->>'lote_fingerprint' <> v_lote.fingerprint", rollback)
        self.assertNotIn("v_lote_fingerprint_recebido", rollback)
        self.assertNotIn("insert into", validacao)
        self.assertNotIn("update ", validacao)
        self.assertNotIn("delete from", validacao)
        self.assertNotIn(
            "select public.otimizador_producao_importar_json_local_v1(",
            validacao,
        )

    def test_v68_usa_somente_selos_canonicos_da_linha(self) -> None:
        texto = MIGRACAO_V68.read_text(encoding="utf-8").lower()
        self.assertIn(
            "p_resultado->>'formula_fingerprint' is distinct from "
            "v_l.otimizador_formula_fingerprint_esperado",
            texto,
        )
        self.assertIn(
            "p_resultado->>'contrato_fingerprint' is distinct from "
            "v_l.otimizador_contrato_fingerprint_esperado",
            texto,
        )
        self.assertIn(
            "p_resultado->>'motor_versao' is distinct from "
            "v_l.otimizador_motor_versao_esperada",
            texto,
        )
        self.assertIn(
            "p_resultado->>'carta_entrada_fingerprint' is distinct from "
            "v_q.entrada_fingerprint",
            texto,
        )
        self.assertNotIn("e.evento = 'preparo_integral_concluido'", texto)
        self.assertNotIn(
            "p_resultado->>'lote_fingerprint' <> v_lote.fingerprint",
            texto,
        )
        self.assertIn("v_lote_fingerprint_recebido !~ '^[0-9a-f]{64}$'", texto)
        self.assertIn("'lote_fingerprint_recebido', v_lote_fingerprint_recebido", texto)

    def test_v68_preserva_porta_privada_e_rollback_da_v67(self) -> None:
        texto = MIGRACAO_V68.read_text(encoding="utf-8").lower()
        rollback = ROLLBACK_V68.read_text(encoding="utf-8").lower()
        validacao = VALIDACAO_V68.read_text(encoding="utf-8").lower()
        self.assertIn("security definer", texto)
        self.assertIn("set search_path to ''", texto)
        self.assertIn("from public, anon, authenticated", texto)
        self.assertIn("to service_role", texto)
        self.assertIn("pode_publicar is not false", texto)
        self.assertIn("v_lote.estado <> 'pausado'", texto)
        self.assertIn("e.evento = 'preparo_integral_concluido'", rollback)
        self.assertNotIn("insert into", validacao)
        self.assertNotIn("update ", validacao)
        self.assertNotIn("delete from", validacao)
        self.assertNotIn(
            "select public.otimizador_producao_importar_json_local_v1(",
            validacao,
        )

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

    def test_linha_retirada_da_fila_no_banco_e_classificada(self) -> None:
        original_urlopen = MODULO.urllib.request.urlopen

        def recusar(*_args, **_kwargs):
            raise HTTPError(
                "https://exemplo.test/rpc",
                400,
                "Bad Request",
                {},
                io.BytesIO(json.dumps({
                    "code": "P0001",
                    "details": None,
                    "hint": None,
                    "message": "importação JSON recusada: lote ou linha não pertence à fila integral",
                }).encode("utf-8")),
            )

        MODULO.urllib.request.urlopen = recusar
        try:
            with self.assertRaises(MODULO.LinhaForaFilaNoBanco):
                MODULO.chamar_importacao("https://exemplo.test", "chave-teste", "lote", item(380352))
        finally:
            MODULO.urllib.request.urlopen = original_urlopen

    def test_lock_timeout_55p03_e_classificado_como_banco_ocupado(self) -> None:
        original_urlopen = MODULO.urllib.request.urlopen

        def banco_ocupado(*_args, **_kwargs):
            raise HTTPError(
                "https://exemplo.test/rpc",
                500,
                "Internal Server Error",
                {},
                io.BytesIO(
                    json.dumps({
                        "code": "55P03",
                        "details": None,
                        "hint": None,
                        "message": "canceling statement due to lock timeout",
                    }).encode("utf-8")
                ),
            )

        MODULO.urllib.request.urlopen = banco_ocupado
        try:
            with self.assertRaises(MODULO.BancoOcupado):
                MODULO.chamar_importacao("https://exemplo.test", "chave-teste", "lote", item(10))
        finally:
            MODULO.urllib.request.urlopen = original_urlopen

        self.assertEqual([5, 10, 20, 30, 30], [
            MODULO._segundos_banco_ocupado(tentativa)
            for tentativa in range(1, 6)
        ])

    def test_enviador_repete_mesma_linha_apos_55p03_e_so_entao_grava_recibo(self) -> None:
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
                "itens": [item(10)],
            })
            original_chamada = MODULO.chamar_importacao
            original_espera = MODULO._aguardar_banco_ocupado
            original_pacote = MODULO._mortar_pacote
            chamadas: list[int] = []
            esperas: list[tuple[int, int]] = []

            def ocupar_e_confirmar(_url, _chave, _lote, entrada):
                chamadas.append(int(entrada["linha_id"]))
                if len(chamadas) == 1:
                    raise MODULO.BancoOcupado("lock timeout")
                return {
                    "contrato": MODULO.CONTRATO_IMPORTACAO,
                    "linha_id": int(entrada["linha_id"]),
                    "enviado_em_utc": "2026-09-05T02:40:00Z",
                    "build_otimizador_id": 456,
                    "resultado_fingerprint": "teste",
                    "idempotente": False,
                }

            def espera_sem_dormir(entrada, tentativa):
                esperas.append((int(entrada["linha_id"]), int(tentativa)))

            MODULO.chamar_importacao = ocupar_e_confirmar
            MODULO._aguardar_banco_ocupado = espera_sem_dormir
            MODULO._mortar_pacote = lambda *_args: pacote_teste(lote, [10])
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(0, MODULO.enviar(raiz, lote, None))
            finally:
                MODULO.chamar_importacao = original_chamada
                MODULO._aguardar_banco_ocupado = original_espera
                MODULO._mortar_pacote = original_pacote

            self.assertEqual([10, 10], chamadas)
            self.assertEqual([(10, 1)], esperas)
            enviados = operacao / "RESULTADOS-JSON" / lote / "ENVIADOS"
            recibos = list(enviados.glob("*.recibos.jsonl"))
            self.assertEqual(1, len(recibos))
            self.assertEqual([10], [x["linha_id"] for x in MODULO.ler_jsonl(recibos[0])])
            self.assertEqual([], list((operacao / "RESULTADOS-JSON" / lote / "FALHAS-ENVIO").glob("*.json")))

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
            original_pacote = MODULO._mortar_pacote

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
            MODULO._mortar_pacote = lambda *_args: pacote_teste(lote, [10, 11])
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(0, MODULO.enviar(raiz, lote, None))
            finally:
                MODULO.chamar_importacao = original_chamada
                MODULO._mortar_pacote = original_pacote

            arquivo_final = operacao / "RESULTADOS-JSON" / lote / "ENVIADOS" / "resultado-000001.json"
            self.assertTrue(arquivo_final.is_file())
            self.assertFalse((pendentes / "resultado-000001.json").exists())
            resumo = json.loads((arquivo_final.parent / "resultado-000001.resumo.json").read_text(encoding="utf-8"))
            self.assertEqual(1, resumo["total_confirmado"])
            self.assertEqual(1, resumo["total_ignorado_por_banco"])

    def test_enviador_arquiva_linha_retirada_no_banco_e_continua(self) -> None:
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
                "itens": [item(380352), item(380353)],
            })
            original_chamada = MODULO.chamar_importacao
            original_pacote = MODULO._mortar_pacote
            chamadas: list[int] = []

            def retirar_ou_confirmar(_url, _chave, _lote, entrada):
                linha_id = int(entrada["linha_id"])
                chamadas.append(linha_id)
                if linha_id == 380352:
                    raise MODULO.LinhaForaFilaNoBanco("a linha 380352 foi retirada da fila integral no banco")
                return {
                    "contrato": MODULO.CONTRATO_IMPORTACAO,
                    "linha_id": linha_id,
                    "enviado_em_utc": "2026-09-07T08:00:00Z",
                    "build_otimizador_id": 999,
                    "resultado_fingerprint": "teste",
                    "idempotente": False,
                }

            MODULO.chamar_importacao = retirar_ou_confirmar
            MODULO._mortar_pacote = lambda *_args: pacote_teste(lote, [380352, 380353])
            try:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(0, MODULO.enviar(raiz, lote, None))
            finally:
                MODULO.chamar_importacao = original_chamada
                MODULO._mortar_pacote = original_pacote

            self.assertEqual([380352, 380353], chamadas)
            enviados = operacao / "RESULTADOS-JSON" / lote / "ENVIADOS"
            recibos = list(enviados.glob("*.recibos.jsonl"))
            self.assertEqual(1, len(recibos))
            decisoes = MODULO.ler_jsonl(recibos[0])
            self.assertEqual("linha_retirada_da_fila_integral_no_banco", decisoes[0]["motivo_codigo"])
            self.assertTrue(decisoes[1]["confirmado"])


if __name__ == "__main__":
    unittest.main()
