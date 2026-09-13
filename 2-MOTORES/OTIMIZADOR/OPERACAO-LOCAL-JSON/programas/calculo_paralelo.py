"""Workers somente de cálculo; o processo principal é o único escritor."""
from concurrent.futures import ProcessPoolExecutor
from itertools import groupby, islice
from pathlib import Path
import multiprocessing
import os
import sys

_pacote = _runner = _operacao = None


def inicializar(raiz_texto, lote_id, complemento):
    global _pacote, _runner, _operacao
    for variavel in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[variavel] = '1'
    raiz = Path(raiz_texto)
    sys.path.insert(0, str(raiz))
    import operacao_local_json as operacao
    import roda_lote_v6 as runner
    from complemento_runtime_v14 import ativar
    os.chdir(operacao.pasta_operacao(raiz))
    pacote = operacao._mortar_pacote(raiz, operacao.pasta_operacao(raiz), lote_id)
    pacote.validar_integridade()
    runner._gd.LIGADO = False
    runner.prepara_lote_producao_v3(pacote.manifesto['regua'])
    ativar(runner, complemento)
    _pacote, _runner, _operacao = pacote, runner, operacao


def calcular(linha):
    return _operacao.calcular_linha(_pacote, _runner, linha)


def distribuir(executor, linhas, processos, tarefa):
    # Barreira entre grupos: nenhuma carta do grupo seguinte começa antes
    # de terminar o atual. Resultados são consumidos na ordem da fila.
    for _, grupo in groupby(linhas, key=lambda l: l.get('prioridade_grupo')):
        while bloco := list(islice(grupo, processos)):
            futuros = [executor.submit(tarefa, linha) for linha in bloco]
            for linha, futuro in zip(bloco, futuros):
                yield linha, futuro


def iter_calculos(raiz, lote_id, linhas, processos, complemento):
    if processos == 1:
        for linha in linhas:
            yield linha, None
        return
    with ProcessPoolExecutor(max_workers=processos,
                             mp_context=multiprocessing.get_context('spawn'),
                             initializer=inicializar,
                             initargs=(str(raiz), lote_id, complemento)) as executor:
        yield from distribuir(executor, linhas, processos, calcular)
