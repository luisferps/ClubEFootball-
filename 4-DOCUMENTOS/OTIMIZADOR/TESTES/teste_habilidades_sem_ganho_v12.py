"""Casos manuais de ganho marginal, usando equacao, regua e motor reais offline."""
from pathlib import Path
import sys, types, unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '2-MOTORES' / 'OTIMIZADOR'))
fonte = types.ModuleType('fonte_unica')
fonte.tabela_multiplicador = lambda: {0: 1.0, 99: 1.0}
fonte.catalogo_fabricaveis = lambda: []
fonte.catalogo_habilidades = lambda: {
    1000: {'fabricavel': True, 'efeito': {'0': {'pct': 2}}},
    1001: {'fabricavel': True, 'efeito': {'0': {'pct': 2}}},
    1002: {'fabricavel': True, 'efeito': {'1': {'pct': 10}}},
}
sys.modules['fonte_unica'] = fonte
import equacao, regua, motor


class HabilidadesSemGanho(unittest.TestCase):
    def test_goleiro_430_nao_completa_vagas(self):
        self.assertEqual([], motor.habilidades_minimas([1000,1001], lambda hs: 430.0))

    def test_ganho_de_uma_habilidade_permanece(self):
        self.assertEqual([1000], motor.habilidades_minimas([1000,1002],
                         lambda hs: 430.0 + (2 if 1000 in hs else 0)))

    def test_duas_redundantes_nao_podem_sair_juntas(self):
        # Qualquer uma preserva 431; nenhuma volta a 430. Preferencia por incidencia.
        self.assertEqual([1001], motor.habilidades_minimas([1000,1001],
                         lambda hs: 431.0 if hs else 430.0, {1001: 9}))

    def test_duas_com_ganho_cumulativo_ficam(self):
        self.assertEqual([1000,1001], motor.habilidades_minimas([1000,1001],
                         lambda hs: 430.0 + len(hs)))

    def test_teto_real_do_motor(self):
        # Alvo 80, peso 12: os nove degraus somam 4,68*12 = 56,16 -> 56,2.
        self.assertEqual(56.2, regua.notaDe([99], [(0,12,80)]))
        self.assertEqual([], motor.habilidades_minimas([1000],
                         lambda hs: regua.notaDe([99 + (2 if hs else 0)], [(0,12,80)])))

    def test_ceil_real_duas_gemeas_so_precisam_de_uma(self):
        # Referencia 1: ceil(2%) e ceil(3%) valem 1. Nao remove as duas.
        def pontuar(hs):
            pct, flat = equacao.buff_de(hs).get(0, (0,0))
            return regua.notaDe([equacao.aplica_buff(80,pct,flat,ref=1)],[(0,12,80)])
        self.assertEqual(12.0,pontuar([1000,1001]))
        self.assertEqual([1000],motor.habilidades_minimas([1001,1000],pontuar))

    def test_motor_integrado_remove_filler_e_preserva_nativas(self):
        c={'base':[99]*26,'orc':0,'arows':[(0,12,80)],'sl':[0,0],
           'nm':[],'fab':[1000],'raras':[], 'falta':[1001,1002]}
        b=motor.build_completo2(c, [{'id':1,'nome':'Teste','m':1.0,'boost':[]}])
        self.assertEqual(56.2,b['nota'])
        self.assertEqual([],b['habilidades'])
        self.assertEqual([1000],c['fab'])
        self.assertEqual(101,b['vals'][0])
        self.assertEqual(99,b['vals_tela'][0])
        self.assertEqual(motor.POLITICA_HABILIDADES,b['politica_habilidades'])

    def test_rejeita_entrada_invalida(self):
        with self.assertRaises(ValueError):
            motor.habilidades_minimas([1,1], lambda hs: 0)
        with self.assertRaises(ValueError):
            motor.habilidades_minimas([1], lambda hs: float('nan'))


if __name__=='__main__':
    unittest.main()
