"""Recomposicao completa de uma solucao existente, sem executar nova busca.

Uso em processo exclusivo e com snapshots ja conferidos. Nao acessa escrita
no banco. Reusa o formatador oficial de roda_lote_v6.trabalha: etapas, universo
de builds, sugestoes e metadados sao reconstruidos, nao copiados da saida antiga.
O importador normal deve gravar o resultado e refazer a finalizacao/publicacao.
"""
from __future__ import annotations
import copy


def preparar(regua):
    import fonte_unica
    fonte_unica.carrega_tudo_do_snapshot_v3(regua)
    import roda_lote_v6 as runner
    runner.prepara_lote_producao_v3(regua)
    return runner


def _recompor(runner, snapshot_carta, linha, anterior, habilidades, complementares):
    import fonte_unica as fonte
    M = runner._W['M']
    fid = int(linha['funcao_id']); card_id = str(linha['card_id'])
    c0 = runner.carrega_carta_snapshot_producao_v3(snapshot_carta)
    c = fonte.aplica_impetos_da_linha(c0, linha.get('impeto_condicional_codigo'),
                                    linha.get('impeto_condicional_nivel'))
    c['arows'] = copy.deepcopy(runner._W['MOLDE'][fid])
    if [r[:3] for r in c['arows']] != [r[:3] for r in anterior['arows_snapshot']]:
        raise ValueError('Molde mudou: encaminhar para busca integral')
    permitidas = set(runner._pool_de(c, card_id, fid))
    permitidas.update(complementares)
    vetadas = {int(h) for h, v in M.HAB.items() if v.get('vetada')} - set(complementares)
    if len(habilidades)>5 or len(set(habilidades))!=len(habilidades) or set(habilidades)-permitidas or set(habilidades)&vetadas:
        raise ValueError('Adicionais fora do pool atual')
    if not c.get('orc') and habilidades:
        raise ValueError('Carta sem evolucao nao recebe adicionais')
    t = next(t for t in runner._W['TECS'] if int(t['id'])==int(anterior['tecnico_id']))
    barras = dict(anterior['barras'])
    cd = M.Card(c, m=t['m'])
    if any(int(barras.get(b,0))<0 or int(barras.get(b,0))>cd.nmax_barra[b] for b in M.MBK) or cd.gasto(barras)>cd.orc:
        raise ValueError('Distribuicao nao cabe no orcamento atual')
    impeto = anterior.get('impeto_adicional_codigo')
    imp = list(cd.nm)
    if impeto is None and (cd.L or cd.Rr):
        raise ValueError('Ha vaga livre de impeto: encaminhar para busca integral')
    if impeto is not None:
        adicionais = [x for x in M._cands_impeto(cd) if x[1]==impeto]
        if not adicionais:
            raise ValueError('Impeto anterior fora do catalogo permitido')
        extra = adicionais[0][0]
        imp = [a+b for a,b in zip(imp,extra)]
    boost = [0]*26
    for i in t['boost']:boost[i]+=1
    fixas = list(c.get('fab') or [])+list(c.get('raras') or [])
    bf = M.buff_de(fixas+list(habilidades))
    interno = M.Card(c,m=t['m'],bf=bf)
    bb = cd.base_barras(barras); tela = cd.aplicar(barras,imp,boost)
    vals = interno.vals_finais(barras,imp,boost)
    nota = M.notaDe(vals,c['arows'])
    # Complemento pode aumentar a nota: nao descartar seus efeitos.
    if nota < float(anterior['pontuacao']) - 1e-7:
        raise ValueError('Complemento reduziu a pontuacao anterior')
    # Mesmo quando peso=0, o valor e recalculado e vai para o contrato final.
    if any(tela[r[0]]!=anterior['atributos_finais'][r[0]] for r in c['arows'] if r[1]):
        raise ValueError('Cadeia fisica ponderada mudou: encaminhar para busca integral')
    solucao = {'nota':nota,'lvl':barras,'m':t['m'],'tecnico_id':t['id'],'tecnico':t['nome'],
      'habilidades':list(habilidades),'buff':bf,'vals_carta':bb,'vals_tela':tela,'vals':vals,
      'fab':[] if impeto is None else [impeto], 'boost':list(t['boost']),
      'impeto_add':imp,'boost_add':boost,'add':[a+b for a,b in zip(imp,boost)],
      'sobra':cd.orc-cd.gasto(barras),'politica_habilidades':M.POLITICA_HABILIDADES,
      'habilidades_sem_ganho_removidas':[h for h in anterior['habilidades_adicionais'] if h not in habilidades]}
    original = runner._executa_busca_contando_builds
    def solucao_conferida(motor, carta, tecnicos, incidencia):
        if carta['base']!=c['base'] or carta['arows']!=c['arows']:
            raise ValueError('Formatacao recebeu outra entrada')
        return copy.deepcopy(solucao), 1
    try:
        # Unico ponto substituido: a busca. Todo o restante e o caminho oficial.
        runner._executa_busca_contando_builds = solucao_conferida
        result = runner.trabalha({'n':linha['linha_id'],'card_id':card_id,'funcao_id':fid,
          'impeto_condicional_codigo':linha.get('impeto_condicional_codigo'),
          'impeto_condicional_nivel':linha.get('impeto_condicional_nivel'),
          'origem':'complemento_recomposicao_v14'})
    finally:
        runner._executa_busca_contando_builds = original
    if not isinstance(result,dict) or result.get('ERRO'):
        raise ValueError(str(result))
    if result['vals']!=vals or result['vals_tela']!=tela or result['vals_carta']!=bb or len(result['cadeia'])!=26:
        raise ValueError('Formatador nao preservou os 26 atributos')
    for i,etapa in enumerate(result['cadeia']):
        if etapa['attr']!=i or etapa['base']!=c['base'][i] or etapa['com_barras']!=bb[i] or etapa['na_tela']!=tela[i] or etapa['final']!=vals[i]:
            raise ValueError('Etapa inconsistente')
    result['etapas_atributos']={'base':c['base'],'com_barras':bb,
      'proficiencia':[M._mult(bb[i],t['m']) for i in range(26)],
      'boost_tecnico':boost,'impetos':imp,'fisicos_atuais':tela,'internos_atuais':vals}
    result['correcao_pontual']={'contrato':'complemento_habilidades_sem_nova_busca_v14',
      'build_anterior':anterior['id'],'resultado_anterior_fingerprint':anterior['resultado_fingerprint'],
      'motor_busca_anterior':anterior['motor_versao'],'habilidades_antes':anterior['habilidades_adicionais'],
      'habilidades_depois':list(habilidades),'pontuacao_anterior':anterior['pontuacao'],
      'builds_comparadas_anteriores':anterior['builds_comparadas'],
      'builds_possiveis_anteriores':anterior['builds_possiveis'],
      'nova_busca_integral':False,'solucoes_recompostas':1,'formatador_oficial':True}
    return result


def recompor(runner, snapshot_carta, linha, anterior, *, nativas,
             aceita_adicionais, catalogo, ranking, bloqueios, pesos_por_codigo):
    """Entrada publica: toda inclusao deve passar pela politica aprovada.

    Contexto deve pertencer ao snapshot selado do executor; nao consulta banco.
    """
    from complemento_habilidades_v14 import selecionar
    selecao = selecionar(funcao_id=linha['funcao_id'], nativas=nativas,
        adicionais=anterior['habilidades_adicionais'],
        aceita_adicionais=aceita_adicionais, catalogo=catalogo,
        ranking=ranking, bloqueios=bloqueios, pesos_por_codigo=pesos_por_codigo)
    if not selecao['complementares']:
        return None
    result = _recompor(runner, snapshot_carta, linha, anterior,
                      selecao['habilidades'], selecao['complementares'])
    result['habilidades_complementares'] = selecao['complementares']
    result['complemento_habilidades'] = selecao
    return result
