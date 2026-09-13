# -*- coding: utf-8 -*-
"""Casos manuais da prioridade global; não usa banco nem inicia o motor."""
import importlib.util
import json
import tempfile
import unittest
import shutil
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[3]
FONTE = RAIZ / "2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON/programas/operacao_local_json.py"
spec = importlib.util.spec_from_file_location("operacao_prioridade_test", FONTE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def linha(ident, grupo=1, nivel=34, overall=90, card=None, funcao=1, posicao=1, cond=None):
    return {"linha_id":ident, "card_id":str(card or ident), "funcao_id":funcao, "posicao_id":posicao,
            "ordem_fila":ident, "prioridade_grupo":grupo, "nivel_maximo":nivel,
            "orcamento_real":2*(nivel-1), "overall_prioridade":overall, "captura_id":"prova",
            "impeto_condicional_codigo":82 if cond else None, "impeto_condicional_nivel":cond}


def pacote(lote, linhas):
    return SimpleNamespace(
        lote_id=lote, manifesto={"prioridade_contrato":"prioridade_orcamento_v1",
            "formula_fingerprint":"a"*64,"contrato_fingerprint":"b"*64,"lote_fingerprint":"c"*64},
        iter_linhas=lambda: iter(linhas), validar_integridade=lambda: None,
        carta_da_linha=lambda l: {"carta":{"escalares":{"orcamento":l["orcamento_real"]}}},
    )


class PrioridadeTest(unittest.TestCase):
    def test_erro_de_calculo_grava_falha_e_retorna_codigo_dois(self):
        original=Path.cwd()
        runner=SimpleNamespace(_gd=SimpleNamespace(LIGADO=True),prepara_lote_producao_v3=lambda regua:None)
        modules={"fila_local_v1":SimpleNamespace(FalhaPacoteLocal=RuntimeError),
                 "fila_producao_v3":SimpleNamespace(FORMULA_APROVADA="formula",formula_fingerprint=lambda:"formula"),
                 "roda_lote_v6":runner,
                 "complemento_contexto_v14":SimpleNamespace(carregar_atual=lambda raiz:{}),
                 "complemento_runtime_v14":SimpleNamespace(ativar=lambda *args:None)}
        try:
            with tempfile.TemporaryDirectory() as temp:
                raiz=Path(temp); op=raiz/mod.NOME_PASTA; op.mkdir()
                foto=pacote("principal",[linha(1)]);foto.manifesto["regua"]={}
                try:
                    with patch.dict("sys.modules",modules),patch.object(mod,"calcular_linha",side_effect=RuntimeError("falha controlada")):
                        self.assertEqual(mod.processar(raiz,"principal",None,pacote_override=foto),2)
                    falhas=list(op.rglob("linha-1.json"))
                    self.assertEqual(len(falhas),1)
                    self.assertEqual(json.loads(falhas[0].read_text())["erro"],"falha controlada")
                    estado=json.loads(next(op.rglob("ESTADO-PROCESSAMENTO.json")).read_text())
                    self.assertEqual(estado["codigo_saida"],2)
                    self.assertEqual(estado["estado"],"com_falhas")
                finally:
                    os.chdir(original)
        finally:
            os.chdir(original)

    def test_falha_de_trecho_nao_e_apagada_pelo_fechamento_dos_journals(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz=Path(temp); op=raiz/mod.NOME_PASTA; op.mkdir()
            (op/"FILA-ATIVA.json").write_text(json.dumps({"contrato":"prioridade_orcamento_v1","lotes":["principal"]}))
            foto=pacote("principal",[linha(1)])
            with patch.object(mod,"_mortar_pacote",return_value=foto), patch.object(mod,"processar",side_effect=[2,0]) as processar:
                self.assertEqual(mod.processar_global(raiz,None),2)
                self.assertEqual(processar.call_count,2)
            estado=json.loads((op/"ESTADO-PROCESSAMENTO-GLOBAL.json").read_text())
            self.assertEqual(estado["estado"],"com_falhas")
            self.assertEqual(estado["codigo_saida"],2)

    def test_processador_aceita_prioritarios_encerrados_preservando_cauda(self):
        selecao={"contrato":"prioridade_orcamento_v1",
            "lotes":["nova1","nova2","encerrado1","encerrado2","antigo1","antigo2"],
            "lotes_prioritarios":["nova1","nova2","encerrado1","encerrado2"],
            "lotes_sem_pendentes":["encerrado1","encerrado2"]}
        fotos=[pacote("nova1",[linha(5,overall=60)]),pacote("nova2",[linha(6,overall=100)]),
               pacote("antigo1",[linha(1,overall=99),linha(2,overall=80)]),
               pacote("antigo2",[linha(3,overall=90),linha(4,overall=70)])]
        with tempfile.TemporaryDirectory() as temp:
            raiz=Path(temp); op=raiz/mod.NOME_PASTA; op.mkdir()
            f=op/"FILA-ATIVA.json";f.write_text(json.dumps(selecao))
            antes=f.read_bytes()
            with patch.object(mod,"_mortar_pacote",side_effect=fotos) as montar, patch.object(mod,"processar",return_value=0) as processar:
                self.assertEqual(mod.processar_global(raiz,None),0)
                self.assertEqual([c.args[2] for c in montar.call_args_list],["nova1","nova2","antigo1","antigo2"])
                ids=[l['linha_id'] for c in processar.call_args_list for l in c.kwargs['linhas_override']]
                self.assertEqual(ids,[5,6,1,3,2,4])
            self.assertEqual(f.read_bytes(),antes)

    def test_processador_fila_toda_concluida_nao_monta_pacotes(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz=Path(temp);op=raiz/mod.NOME_PASTA;op.mkdir()
            (op/"FILA-ATIVA.json").write_text(json.dumps({"contrato":"prioridade_orcamento_v1",
                "lotes":["concluido"],"lotes_prioritarios":["concluido"],"lotes_sem_pendentes":["concluido"]}))
            with patch.object(mod,"_mortar_pacote") as montar,patch.object(mod,"processar") as processar:
                self.assertEqual(mod.processar_global(raiz,None),0)
                montar.assert_not_called();processar.assert_not_called()

    def test_processador_recusa_prioritarios_invalidos_antes_de_tocar_resultados(self):
        for prioridades in (["fora"],["concluido","concluido"],"concluido",[None],False):
            with self.subTest(prioridades=prioridades),tempfile.TemporaryDirectory() as temp:
                raiz=Path(temp);op=raiz/mod.NOME_PASTA;op.mkdir()
                (op/"FILA-ATIVA.json").write_text(json.dumps({"contrato":"prioridade_orcamento_v1",
                    "lotes":["concluido"],"lotes_prioritarios":prioridades,"lotes_sem_pendentes":["concluido"]}))
                with patch.object(mod,"_mortar_pacote") as montar,self.assertRaises(mod.FalhaOperacao):
                    mod.processar_global(raiz,None)
                montar.assert_not_called()

    def test_renovacao_sem_pendentes_preserva_ordem_e_prioridade(self):
        fonte = RAIZ / '2-MOTORES/OTIMIZADOR/renovar_pacotes_prioridade_v1.py'
        spec_r = importlib.util.spec_from_file_location('renovacao_ordem_test', fonte)
        renovacao = importlib.util.module_from_spec(spec_r); spec_r.loader.exec_module(renovacao)
        lotes=['7581b184-dccb-4a4b-9ad9-c767d4f4947c','1833e4d0-1707-4ea2-8ba3-3733b5101310']
        gateway=SimpleNamespace(rpc=lambda *args: {'prioridade_contrato':'prioridade_orcamento_v1',
            'prioridade_fingerprint':'selo','linhas_total':0})
        with tempfile.TemporaryDirectory() as temp:
            raiz=Path(temp); op=raiz/mod.NOME_PASTA; op.mkdir()
            f=op/'FILA-ATIVA.json'
            f.write_text(json.dumps({'contrato':'prioridade_orcamento_v1','lotes':lotes,'lotes_prioritarios':[lotes[1]]}))
            with patch.dict('sys.modules',{'fila_local_v1':SimpleNamespace(PacoteLocalV1=object),
                'empacotar_fila_integral_portatil_v1':SimpleNamespace(empacotar=lambda *args: None)}):
                renovacao.renovar(raiz,lotes,mod,gateway,preservar_ordem=True)
            atual=json.loads(f.read_text())
            self.assertEqual(lotes,atual['lotes'])
            self.assertEqual([lotes[1]],atual['lotes_prioritarios'])
            self.assertEqual(lotes,atual['lotes_sem_pendentes'])
            self.assertFalse(atual['worker_iniciado'])

    def test_ordem_manual_global_carta_nova_na_frente_de_cada_bloco(self):
        # Valores esperados definidos pelo contrato: primeiro evolutivos
        # especiais, depois 1/1 especiais, por último toda carta base.
        a = pacote("principal", [linha(1,3,52,99), linha(2,2,1,99), linha(3,1,34,None)])
        b = pacote("corretiva", [linha(4,1,32,88), linha(5,1,34,91), linha(6,3,1,100)])
        ids = [l["linha_id"] for _,l in mod.ordenar_fila_global([a,b],{})]
        self.assertEqual(ids, [3,5,4,2,6,1])

    def test_desempates_condicao_e_linha_estaveis(self):
        linhas = [linha(4,card="100",cond=3),linha(3,card="100",cond=2),
                  linha(2,card="100",cond=1),linha(1,card="100")]
        self.assertEqual([l["linha_id"] for _,l in mod.ordenar_fila_global([pacote("a",linhas)],{})], [1,2,3,4])

    def test_resultados_calculados_nao_voltam(self):
        a=pacote("a",[linha(1),linha(2)])
        self.assertEqual([l["linha_id"] for _,l in mod.ordenar_fila_global([a],{"a":{1}})], [2])

    def test_nivel_desconhecido_ou_grupo_incompativel_recusado(self):
        for mudanca in ({"nivel_maximo":None},{"captura_id":None},{"prioridade_grupo":2},
                        {"orcamento_real":64},{"overall_prioridade":"90"}):
            l=linha(1); l.update(mudanca)
            with self.subTest(mudanca=mudanca), self.assertRaises(mod.FalhaOperacao):
                mod.chave_prioridade(l)

    def test_pacote_antigo_id_duplicado_e_orcamento_errado_recusados(self):
        a=pacote("a",[linha(1)])
        velho=pacote("v",[linha(2)]); velho.manifesto={}
        with self.assertRaises(mod.FalhaOperacao): mod.ordenar_fila_global([velho],{})
        with self.assertRaises(mod.FalhaOperacao): mod.ordenar_fila_global([a,pacote("b",[linha(1)])],{})
        a.carta_da_linha=lambda l: {"carta":{"escalares":{"orcamento":64}}}
        with self.assertRaises(mod.FalhaOperacao): mod.ordenar_fila_global([a],{})

    def test_consumidor_intercala_lotes_mantendo_destinos(self):
        a=pacote("principal",[linha(1,overall=94),linha(3,grupo=2,nivel=1,overall=99)])
        b=pacote("corretiva",[linha(2,overall=90)])
        with tempfile.TemporaryDirectory() as temp:
            raiz=Path(temp); op=raiz/mod.NOME_PASTA; op.mkdir()
            (op/"FILA-ATIVA.json").write_text(json.dumps({"contrato":"prioridade_orcamento_v1","lotes":["principal","corretiva"]}))
            with patch.object(mod,"_mortar_pacote",side_effect=[a,b]), patch.object(mod,"processar",return_value=0) as processar:
                self.assertEqual(mod.processar_global(raiz,None),0)
                trechos=[(call.args[1],[l["linha_id"] for l in call.kwargs["linhas_override"]])
                         for call in processar.call_args_list if call.kwargs["linhas_override"]]
                self.assertEqual(trechos,[("principal",[1]),("corretiva",[2]),("principal",[3])])
                self.assertFalse((op/"PROCESSADOR-GLOBAL.lock").exists())

    def test_antepor_mantem_lotes_encerrados_fora_do_processamento(self):
        fonte = RAIZ / '2-MOTORES/OTIMIZADOR/renovar_pacotes_prioridade_v1.py'
        spec = importlib.util.spec_from_file_location('renovacao_prefixo_test', fonte)
        renovacao = importlib.util.module_from_spec(spec); spec.loader.exec_module(renovacao)
        novo='00000000-0000-0000-0000-000000000001'
        encerrado='00000000-0000-0000-0000-000000000002'
        pendente='00000000-0000-0000-0000-000000000003'
        manifesto={'prioridade_contrato':'prioridade_orcamento_v1','prioridade_fingerprint':'selo',
                   'linhas_total':1,'cartas_total':1,'lote_id':novo}
        class Foto:
            def __init__(self,pasta):self.manifesto=dict(manifesto);self.lote_id=novo
            def validar_integridade(self):pass
            def iter_linhas(self):return iter([linha(1)])
            def carta_da_linha(self,l):return {'carta':{'escalares':{'orcamento':66}}}
            @classmethod
            def criar_do_contrato(cls,gateway,lote,staging):
                pasta=staging/'foto';pasta.mkdir();(pasta/'nova.json').write_text('nova');return cls(pasta)
        with tempfile.TemporaryDirectory() as temp:
            raiz=Path(temp);op=raiz/mod.NOME_PASTA;op.mkdir()
            mod.gravar_json_atomico(op/'FILA-ATIVA.json',{'contrato':'prioridade_orcamento_v1',
                'lotes':[encerrado,pendente],'lotes_prioritarios':[encerrado],'lotes_sem_pendentes':[encerrado]})
            with patch.dict('sys.modules',{
                'fila_local_v1':SimpleNamespace(PacoteLocalV1=Foto),
                'empacotar_fila_integral_portatil_v1':SimpleNamespace(empacotar=lambda staging,lote:staging/'foto')}):
                renovacao.renovar(raiz,[novo],mod,SimpleNamespace(rpc=lambda *a:dict(manifesto)),antepor=True)
            atual=json.loads((op/'FILA-ATIVA.json').read_text())
            self.assertEqual(atual['lotes'],[novo,encerrado,pendente])
            self.assertEqual(atual['lotes_prioritarios'],[novo,encerrado])
            self.assertEqual(atual['lotes_sem_pendentes'],[encerrado])

    def test_renovacao_preserva_pacotes_anteriores_e_resultados(self):
        fonte = RAIZ / "2-MOTORES/OTIMIZADOR/renovar_pacotes_prioridade_v1.py"
        spec_r = importlib.util.spec_from_file_location("renovacao_test", fonte)
        renovacao = importlib.util.module_from_spec(spec_r); spec_r.loader.exec_module(renovacao)
        lote = "7581b184-dccb-4a4b-9ad9-c767d4f4947c"
        manifesto = {"prioridade_contrato":"prioridade_orcamento_v1","prioridade_fingerprint":"selo",
                     "linhas_total":1,"cartas_total":1,"lote_id":lote}

        class Foto:
            def __init__(self, pasta):
                self.manifesto=dict(manifesto); self.lote_id=lote
            def validar_integridade(self): pass
            def iter_linhas(self): return iter([linha(1)])
            def carta_da_linha(self,l): return {"carta":{"escalares":{"orcamento":66}}}
            @classmethod
            def criar_do_contrato(cls,gateway,lote,staging):
                pasta=staging/"runtime/fila-local"/lote; pasta.mkdir(parents=True)
                (pasta/"nova.json").write_text("fotografia nova")
                return cls(pasta)

        def empacotar(staging,lote):
            destino=staging/"PACOTE-FILA-INTEGRAL"/lote
            shutil.copytree(staging/"runtime/fila-local"/lote,destino)
            return destino

        gateway=SimpleNamespace(rpc=lambda *args: dict(manifesto))
        with tempfile.TemporaryDirectory() as temp:
            raiz=Path(temp); op=raiz/mod.NOME_PASTA; op.mkdir()
            recibo=op/"RESULTADOS-JSON"/lote/"RECIBOS/recibo.json"
            recibo.parent.mkdir(parents=True); recibo.write_text("resultado preservado")
            for base in (raiz,op):
                antigo=base/"PACOTE-FILA-INTEGRAL"/lote; antigo.mkdir(parents=True)
                (antigo/"antiga.json").write_text("fotografia anterior")
            with patch.dict("sys.modules", {
                "fila_local_v1":SimpleNamespace(PacoteLocalV1=Foto),
                "empacotar_fila_integral_portatil_v1":SimpleNamespace(empacotar=empacotar),
            }):
                self.assertEqual(renovacao.renovar(raiz,[lote],mod,gateway),0)
            self.assertEqual(recibo.read_text(),"resultado preservado")
            self.assertEqual(len(list((op/"RENOVACOES").rglob("antiga.json"))),2)
            self.assertTrue((op/"PACOTE-FILA-INTEGRAL"/lote/"nova.json").is_file())
            self.assertTrue((raiz/"PACOTE-FILA-INTEGRAL"/lote/"nova.json").is_file())
            self.assertEqual(json.loads((op/"FILA-ATIVA.json").read_text())["lotes"],[lote])


if __name__ == "__main__":
    unittest.main()
