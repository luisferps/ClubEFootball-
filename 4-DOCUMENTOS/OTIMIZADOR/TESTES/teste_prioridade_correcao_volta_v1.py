"""A correção é prefixo; a ordem relativa da fila existente é preservada."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

raiz = Path(__file__).resolve().parents[3] / '2-MOTORES/OTIMIZADOR'
sys.path.insert(0, str(raiz / 'OPERACAO-LOCAL-JSON/programas'))
import operacao_local_json as api


def pacote(lote, ids):
    linhas = [dict(linha_id=i, card_id=str(i), funcao_id=1, posicao_id=1,
                   prioridade_grupo=1, overall_prioridade=overall, nivel_maximo=30,
                   orcamento_real=58, captura_id='fisico') for i, overall in ids]
    return SimpleNamespace(lote_id=lote, manifesto={'prioridade_contrato': 'prioridade_orcamento_v1'},
                           iter_linhas=lambda: iter(linhas),
                           carta_da_linha=lambda l: {'carta': {'escalares': {'orcamento': 58}}})


class OrdemCorrecao(unittest.TestCase):
    def test_prefixo_preserva_fila_intercalada_e_ignora_calculadas(self):
        antigos = [pacote('a', [(1,99),(2,80)]), pacote('b', [(3,90),(4,70)])]
        base = api.ordenar_fila_global(antigos, {'a':{2}})
        novos = [pacote('c', [(5,60)]), pacote('d', [(6,100)])]
        resultado = api.ordenar_fila_global(novos+antigos, {'a':{2}}, ['c','d'])
        self.assertEqual([l['linha_id'] for _,l in resultado], [5,6,1,3,4])
        self.assertEqual(resultado[2:], base)

    def test_sem_prioridade_mantem_comportamento(self):
        antigos = [pacote('a', [(1,99),(2,80)]), pacote('b', [(3,90)])]
        self.assertEqual([l['linha_id'] for _,l in api.ordenar_fila_global(antigos,{})], [1,3,2])

    def test_recusa_prioridade_desconhecida_ou_repetida(self):
        for prioridades in (['ausente'], ['a','a'], 'a'):
            with self.subTest(prioridades=prioridades), self.assertRaises(api.FalhaOperacao):
                api.ordenar_fila_global([pacote('a',[(1,80)])],{},prioridades)


if __name__ == '__main__':
    unittest.main()
