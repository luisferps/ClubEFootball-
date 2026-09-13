"""Complementa a solucao vencedora sem executar outra busca.

O formatador oficial deve consumir o retorno, inclusive vals e buff atualizados.
O contexto de incidencia precisa fazer parte do pacote selado do chamador.
"""
from copy import deepcopy
from complemento_habilidades_v14 import selecionar


def aplicar(motor, carta, solucao, *, funcao_id, catalogo, ranking,
            bloqueios, pesos_por_codigo):
    selecionadas = selecionar(
        funcao_id=funcao_id,
        nativas=list(carta.get('fab') or []) + list(carta.get('raras') or []),
        adicionais=solucao['habilidades'],
        aceita_adicionais=(bool(carta.get('orc')) and
            (carta.get('dimensoes_ids') or {}).get('tipo_fisico') in (0, 1, 5, 6)),
        catalogo=catalogo, ranking=ranking, bloqueios=bloqueios,
        pesos_por_codigo=pesos_por_codigo)
    saida = deepcopy(solucao)
    saida['complemento_habilidades'] = selecionadas
    saida['habilidades_complementares'] = selecionadas['complementares']
    if not selecionadas['complementares']:
        return saida
    fixas = list(carta.get('fab') or []) + list(carta.get('raras') or [])
    buff = motor.buff_de(fixas + selecionadas['habilidades'])
    card = motor.Card(carta, m=solucao['m'], bf=buff)
    valores = card.vals_finais(solucao['lvl'], solucao['impeto_add'], solucao['boost_add'])
    if len(valores) != 26:
        raise ValueError('Complemento exige 26 atributos')
    nota = motor.notaDe(valores, carta['arows'])
    if nota < solucao['nota'] - 1e-7:
        raise ValueError('Complemento reduziu a pontuacao vencedora')
    saida.update(habilidades=selecionadas['habilidades'], buff=buff,
                 vals=valores, nota=nota)
    return saida
