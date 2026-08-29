# -*- coding: utf-8 -*-
import importlib.util
import os
import unittest


RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
P = os.path.join(RAIZ, '2-MOTORES', 'OTIMIZADOR', 'auditar_moldes_v1.py')
SPEC = importlib.util.spec_from_file_location('auditar_moldes_v1', P)
MOD = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)


def fixtures():
    antigo = {'versao_molde': 5, 'molde': {}}
    novo = {'versao_molde': 5, 'funcoes': [], 'molde': []}
    for fid in range(1, 20):
        codigo = 'f%d' % fid
        antigo['molde'][codigo] = {str(i): [80 + i / 10.0, i % 3] for i in range(26)}
        novo['funcoes'].append({'funcao_id': fid, 'codigo_compatibilidade': codigo,
                                'rotulo_apresentacao': 'Função %d' % fid})
        for i in range(26):
            novo['molde'].append({'funcao_id': fid, 'indice_otimizador': i,
                                  'alvo': 80 + i / 10.0, 'peso': i % 3})
    return antigo, novo


class MoldesTest(unittest.TestCase):
    def test_19_x_26_identicos(self):
        a, n = fixtures(); self.assertTrue(MOD.compara(a, n)['aprovado'])

    def test_alvo_diferente_reprova_e_localiza(self):
        a, n = fixtures(); n['molde'][7]['alvo'] += 1
        r = MOD.compara(a, n)
        self.assertFalse(r['aprovado']); self.assertEqual(r['divergencias'][0]['funcao_id'], 1)
        self.assertEqual(r['divergencias'][0]['indice_otimizador'], 7)

    def test_codigo_sem_id_bloqueia_so_a_ponte(self):
        a, n = fixtures(); n['funcoes'] = n['funcoes'][1:]
        r = MOD.compara(a, n)
        self.assertFalse(r['aprovado']); self.assertEqual(r['faltas_na_ponte'][0]['codigo_compatibilidade'], 'f1')

    def test_renomear_rotulo_nao_troca_molde(self):
        a, n = fixtures(); self.assertTrue(MOD.prova_renomeacao(a, n))


if __name__ == '__main__': unittest.main()
