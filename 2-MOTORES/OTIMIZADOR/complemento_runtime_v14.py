"""Extensao do adaptador: busca oficial, complemento e formatacao oficial.

Usar apenas em processo de calculo exclusivo. A formula da busca permanece
selada separadamente do contexto e da versao do complemento.
"""
from complemento_contexto_v14 import por_funcao
from complemento_solucao_v14 import aplicar


def ativar(runner, contexto):
    original = getattr(runner, '_trabalha_sem_complemento_v14', runner.trabalha)
    runner._trabalha_sem_complemento_v14 = original

    def trabalha(job):
        opcoes = por_funcao(contexto, job['funcao_id'])
        busca = runner._executa_busca_contando_builds
        metadados = {}

        def buscar(motor, carta, tecnicos, incidencia):
            b, n = busca(motor,carta,tecnicos,incidencia)
            if b is None: return b,n
            novo = aplicar(motor,carta,b,funcao_id=job['funcao_id'],**opcoes)
            metadados.update(complemento_contexto_fingerprint=contexto['fingerprint'],
                habilidades_complementares=novo['habilidades_complementares'],
                complemento_habilidades=novo['complemento_habilidades'])
            return novo,n

        runner._executa_busca_contando_builds = buscar
        try: resultado = original(job)
        finally: runner._executa_busca_contando_builds = busca
        if isinstance(resultado,dict) and not resultado.get('ERRO'):
            resultado.update(metadados)
        return resultado

    runner.trabalha = trabalha
