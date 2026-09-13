import ast
import unittest
from pathlib import Path

source=ast.parse(Path(__file__).with_name('operacao_local_json.py').read_text(encoding='utf-8-sig'))
scope={'Any':object,'FalhaOperacao':ValueError}
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='chave_prioridade'],type_ignores=[]),'prioridade-real','exec'),scope)
key=scope['chave_prioridade']

def row(card,group,overall,budget=20):
    return dict(card_id=card,linha_id=int(card),funcao_id=8,posicao_id=11,
                prioridade_grupo=group,overall_prioridade=overall,nivel_maximo=budget//2+1,
                orcamento_real=budget,captura_id='prova',prioridade_ordenacao='novos_orcamento_overall_desc_v2')

class PrioridadeNovos(unittest.TestCase):
    def test_tres_grupos_e_overall_decrescente(self):
        data=[row('1',1,110),row('2',0,75,0),row('3',2,120,0),row('4',0,100),row('5',1,80)]
        self.assertEqual([x['card_id'] for x in sorted(data,key=key)],['4','2','1','5','3'])
    def test_overall_ausente_fica_apos_conhecidos(self):
        self.assertLess(key(row('2',0,40)),key(row('1',0,None)))
    def test_novo_exige_marcador_da_regra(self):
        r=row('1',0,90);r.pop('prioridade_ordenacao')
        with self.assertRaises(ValueError):key(r)
    def test_prova_continua_obrigatoria(self):
        r=row('1',0,90);r['captura_id']=None
        with self.assertRaises(ValueError):key(r)
    def test_historico_preservado(self):
        a=row('1',1,None);b=row('2',1,90)
        a.pop('prioridade_ordenacao');b.pop('prioridade_ordenacao')
        self.assertLess(key(a),key(b))

if __name__=='__main__':unittest.main()
