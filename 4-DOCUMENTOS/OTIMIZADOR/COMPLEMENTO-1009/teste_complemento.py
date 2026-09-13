import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'2-MOTORES'/'OTIMIZADOR'))
from complemento_habilidades_v14 import selecionar

def hab(code,vetada=False,tipo='comum'):
    return dict(fabricavel=tipo=='comum',pode_rodar=True,vetada=vetada,
                tipo=tipo,efeito_por_codigo={code:{'pct':1}})

class Complemento(unittest.TestCase):
    def base(self,**kw):
        args=dict(funcao_id=1,nativas=[],adicionais=[],aceita_adicionais=True,
                  catalogo={1:hab('drible'),2:hab('drible'),3:hab('passe'),
                            69:hab('ofensivo',True),48:hab('penalti',True)},
                  ranking=[dict(funcao_id=1,skill_id=1,cartas_com=10,cartas_total=100),
                           dict(funcao_id=1,skill_id=2,cartas_com=20,cartas_total=100),
                           dict(funcao_id=1,skill_id=3,cartas_com=9,cartas_total=100)],
                  bloqueios=set(),pesos_por_codigo={})
        args.update(kw);return selecionar(**args)
    def test_corte_e_gemeas(self):
        self.assertEqual(self.base()['habilidades'],[2,1])
    def test_bloqueio(self):
        self.assertEqual(self.base(bloqueios={2})['habilidades'],[1])
    def test_nao_evolui(self):
        self.assertEqual(self.base(aceita_adicionais=False)['habilidades'],[])
    def test_preserva_escolhida(self):
        self.assertEqual(self.base(adicionais=[1])['habilidades'],[1,2])
    def test_nativa_nao_exclui_gemea(self):
        self.assertEqual(self.base(nativas=[1])['habilidades'],[2])
    def test_finalizacao_desejavel(self):
        self.assertEqual(self.base(pesos_por_codigo={'PB:530:6':7,'PB:498:6':3})['habilidades'],[2,1,48])
    def test_duas_excecoes(self):
        self.assertEqual(self.base(pesos_por_codigo={'PB:530:6':12,'PB:498:6':12})['habilidades'],[2,1,69,48])
    def test_penalti_nao_usa_bola_parada(self):
        self.assertEqual(self.base(pesos_por_codigo={'PB:368:6':12})['habilidades'],[2,1])
    def test_ranking_invalido(self):
        with self.assertRaises(ValueError):
            self.base(ranking=[dict(funcao_id=1,skill_id=1,cartas_com=101,cartas_total=100)])

if __name__=='__main__':unittest.main()
