"""Casos manuais aprovados e consumidor Python real, sem iniciar pipeline."""
import ast
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'2-MOTORES/BONIFICADOR'
FIX=json.loads(Path(__file__).with_name('fixture_estilos_v12.json').read_text(encoding='utf-8'))
tree=ast.parse((BASE/'motor_bonus.py').read_text(encoding='utf-8'))
FUNCS={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in
    {'_por_id','bonus_do_estilo','bonus_do_estilo_componentes'}],type_ignores=[]),'motor_bonus.py','exec'),FUNCS)
sql=(ROOT/'4-DOCUMENTOS/BONIFICADOR/SQL/VALIDAR-POLITICA-ESTILOS-0909-V1.sql').read_text(encoding='utf-8')
manual=sql.split('for c in select * from (values',1)[1].split(') as t(',1)[0]
CASES=ast.literal_eval('['+manual+']')

class Gateway:
    def rpc(self,nome,corpo=None):
        if nome=='bonificador_regua_v4':return FIX['regua']
        if nome=='bonificador_carta_v3':return next(c['v3'] for c in FIX['cartas'] if c['card_id']==corpo['p_card_id'])
        raise AssertionError('RPC fora do ensaio: '+nome)

class EstilosV12(unittest.TestCase):
    def test_25_casos_manuais(self):
        for nome,func,pos,a,d,ba,bd in CASES:
            with self.subTest(nome=nome):
                self.assertEqual(FUNCS['bonus_do_estilo_componentes'](FIX['regua'],a,d,func,pos),(ba+bd,ba,bd))

    def test_quatro_sem_definicao_nao_recebem_zero_falso(self):
        for estilo in (87,95,96,34):
            with self.subTest(estilo=estilo),self.assertRaisesRegex(RuntimeError,'aguarda definicao'):
                FUNCS['bonus_do_estilo_componentes'](FIX['regua'],34 if estilo==34 else 256,256 if estilo==34 else estilo,4 if estilo==34 else 17,0 if estilo==34 else 4)

    def test_corpo_pe_ia_e_fingerprint_fisico_preservados(self):
        for c in FIX['cartas']:
            for chave in ('corpo','pe_ruim_uso','pe_ruim_precisao','estilos_ia','carta_fingerprint','carta_versao'):
                with self.subTest(card=c['card_id'],campo=chave):self.assertEqual(c['v2'][chave],c['v3'][chave])

    def test_projecao_dos_cinco_cards(self):
        esperado={'88044145348029':(392,392),'89138288270047':(256,329),'88045755964138':(257,344),'88045755964130':(256,347),'88045755829367':(256,337)}
        for c in FIX['cartas']:
            self.assertEqual((c['v3']['slot1_id_jogo'],c['v3']['slot2_id_jogo']),esperado[c['card_id']])
            self.assertTrue(c['v3']['pode_rodar'])

    def test_interface_carrega_toda_dependencia_e_usa_posicao_escolhida(self):
        spec=importlib.util.spec_from_file_location('interface_teste_v12',BASE/'interface/servidor.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        service=module.ServicoBonificador(Gateway())
        ca=service.simular('88045755964138',1,12)
        sa=service.simular('88045755964138',3,11)
        self.assertEqual(ca['bonus']['estilo'],1.5)
        self.assertEqual(sa['bonus']['estilo'],0.5)
        self.assertEqual(sa['regra_estilo']['posicao_escolhida_id'],11)
        self.assertTrue(sa['regra_estilo']['principal_depende_da_funcao'])
        self.assertEqual(service.simular('88044145348029',17,4)['bonus']['estilo'],1.5)

    def test_pipeline_usa_posicao_da_linha(self):
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('bonus_do_estilo','bonus_do_estilo_componentes') and len(n.args)==5 and isinstance(n.args[0],ast.Name) and n.args[0].id=='rb']
        calls=[n for n in calls if isinstance(n.args[3],ast.Name) and n.args[3].id=='fun_id']
        self.assertEqual(len(calls),2)
        self.assertTrue(all(isinstance(n.args[4],ast.Name) and n.args[4].id=='linha_posicao_id' for n in calls))

if __name__=='__main__':unittest.main(verbosity=2)
