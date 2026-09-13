import os
import time
import unittest
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from calculo_paralelo import distribuir


def trabalho(linha):
    inicio = time.monotonic()
    time.sleep(0.35 if linha['id'] % 2 else 0.1)
    if linha.get('falhar'):
        raise ValueError('falha de teste')
    return linha['id'], os.getpid(), inicio, time.monotonic()


class ParaleloTest(unittest.TestCase):
    def test_spawn_quatro_ordem_e_barreira(self):
        linhas = [{'id': i, 'prioridade_grupo': i // 4} for i in range(8)]
        with ProcessPoolExecutor(max_workers=4, mp_context=multiprocessing.get_context('spawn')) as pool:
            resultados = [f.result() for _, f in distribuir(pool, linhas, 4, trabalho)]
        self.assertEqual([r[0] for r in resultados], list(range(8)))
        self.assertEqual(len({r[1] for r in resultados[:4]}), 4)
        self.assertGreaterEqual(min(r[2] for r in resultados[4:]), max(r[3] for r in resultados[:4]))

    def test_falha_nao_duplica_nem_perde_demais(self):
        linhas = [{'id': i, 'prioridade_grupo': 0, 'falhar': i == 2} for i in range(5)]
        ids, falhas = [], []
        with ProcessPoolExecutor(max_workers=4, mp_context=multiprocessing.get_context('spawn')) as pool:
            for linha, futuro in distribuir(pool, linhas, 4, trabalho):
                try:
                    ids.append(futuro.result()[0])
                except ValueError:
                    falhas.append(linha['id'])
        self.assertEqual(ids, [0, 1, 3, 4])
        self.assertEqual(falhas, [2])


if __name__ == '__main__':
    multiprocessing.freeze_support()
    unittest.main()
