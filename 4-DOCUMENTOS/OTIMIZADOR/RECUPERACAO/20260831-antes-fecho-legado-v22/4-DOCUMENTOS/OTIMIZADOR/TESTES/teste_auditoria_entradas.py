# -*- coding: utf-8 -*-
"""Testes sem rede da auditoria que deve existir antes de cada troca."""

import importlib.util
import os
import unittest


RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CAMINHO = os.path.join(RAIZ, '2-MOTORES', 'OTIMIZADOR', 'auditar_entradas_v1.py')
SPEC = importlib.util.spec_from_file_location('auditar_entradas_v1', CAMINHO)
AUD = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(AUD)


def carta_nova(card_id='1', atributo=80, gate=True):
    compat = {
        'overall': 90, 'posicao': 'CA', 'atributos': [atributo] * 26,
        'altura': 180, 'peso': 75, 'idade': 30, 'pe': 'Direito',
        'pe_ruim_uso': 2, 'pe_ruim_precisao': 2, 'resistencia_lesao': 'Normal',
        'forma': 2, 'corpo': list(range(12)), 'level_cap': 20, 'orcamento': 40,
        'cap_estimado': False, 'habilidades_bits': [621],
        'aptidoes': {'CA': 2}, 'slot1_id': 4, 'slot2_id': 0,
        'vaga_s1': False, 'vaga_s2': False, 'box': None, 'tipo': 'Normal'}
    return {
        'card_id': card_id,
        'apresentacao': {'nome': 'Teste', 'posicao': 'Centroavante'},
        'escalares': {'overall': 90, 'altura': 180, 'peso': 75, 'idade': 30,
                      'level_cap': 20, 'orcamento': 40, 'cap_estimado': False},
        'dimensoes': {'nacionalidade_id': 1, 'clube_id': 2, 'liga_id': 3,
                      'tipo_carta_id': '1/0'},
        'posicao_principal_id': 12,
        'atributos': [{'indice_otimizador': i, 'codigo': 'A%d' % i,
                       'bit': i, 'valor': atributo} for i in range(26)],
        'corpo': [{'pos': i, 'codigo': 'C%d' % i, 'valor': i} for i in range(12)],
        'posicoes': [{'posicao_id': i, 'nivel_aptidao': 2} for i in range(12)],
        'habilidades': [{'skill_id': 3, 'ordem': 0, 'bit_na_carta': 621,
                         'tipo': 'comum', 'fabricavel': True, 'vetada': False,
                         'nome_apresentacao': 'Habilidade A'}],
        'estilos_ia': [{'bit_estilo_ia': 10, 'nome_apresentacao': 'IA A'}],
        'pes': [{'campo': 'pe_dominante', 'valor': 0, 'codigo': 'PD0',
                 'nome_apresentacao': 'Direito'},
                {'campo': 'pe_ruim_uso', 'valor': 2, 'codigo': 'PU2'},
                {'campo': 'pe_ruim_precisao', 'valor': 2, 'codigo': 'PP2'}],
        'playstyles': [{'slot_fisico': 1, 'playstyle_id': 260,
                        'nome_apresentacao': 'Estilo A'},
                       {'slot_fisico': 2, 'playstyle_id': 256,
                        'nome_apresentacao': 'Estilo B'}],
        'impetos': [],
        'gate': {'pode_rodar': gate, 'motivos': [] if gate else ['bloqueado']},
        'cardinalidades': {'atributos': 26, 'corpo': 12, 'posicoes': 12,
                            'posicao_principal': 1, 'pes': 3, 'playstyles': 2},
        'compatibilidade_legado': compat}


def carta_antiga(nova):
    x = dict(nova['compatibilidade_legado'])
    x.update({'card_id': nova['card_id'], 'roda_motor': True, 'nome': 'Teste'})
    return x


class AuditoriaEntradasTest(unittest.TestCase):
    def test_igual_aprova(self):
        n = carta_nova(); r = AUD.compara([carta_antiga(n)], [n])
        self.assertTrue(r['aprovado_para_troca'])

    def test_divergencia_diz_fontes_campo_e_valores(self):
        n = carta_nova(atributo=81); a = carta_antiga(n); a['atributos'] = [80] * 26
        r = AUD.compara([a], [n])
        d = next(x for x in r['diferencas'] if x['campo'] == 'atributos')
        self.assertEqual(d['origem_antiga'], AUD.FONTE_ANTIGA)
        self.assertEqual(d['origem_nova'], AUD.FONTE_NOVA)
        self.assertFalse(r['aprovado_para_troca'])

    def test_ausente_no_novo_nao_cai_para_antigo(self):
        n = carta_nova(); r = AUD.compara([carta_antiga(n)], [])
        self.assertFalse(r['aprovado_para_troca'])
        self.assertEqual(r['diferencas'][0]['status'], 'ausente_no_novo')

    def test_gate_fechado_fica_visivel_sem_fingir_fallback(self):
        n = carta_nova(gate=False); r = AUD.compara([carta_antiga(n)], [n])
        self.assertTrue(any(x['status'] == 'bloqueado_gate_novo' for x in r['diferencas']))

    def test_cardinalidade_invalida_reprova(self):
        n = carta_nova(); n['cardinalidades']['atributos'] = 25
        r = AUD.compara([carta_antiga(n)], [n])
        self.assertFalse(r['aprovado_para_troca'])

    def test_renomear_rotulos_nao_muda_assinatura(self):
        self.assertTrue(AUD.prova_renomeacao(carta_nova()))

    def test_mudar_skill_id_muda_assinatura(self):
        a, b = carta_nova(), carta_nova(); b['habilidades'][0]['skill_id'] = 99
        self.assertNotEqual(AUD.fingerprint(AUD.assinatura_calculo(a)),
                            AUD.fingerprint(AUD.assinatura_calculo(b)))

    def test_null_do_legado_nao_impede_classificar_carta_somente_nova(self):
        n = carta_nova(); r = AUD.compara([None], [n])
        self.assertEqual(r['diferencas'][0]['status'], 'somente_novo')
        self.assertEqual(r['quantidades']['antigos'], 0)


if __name__ == '__main__':
    unittest.main()
