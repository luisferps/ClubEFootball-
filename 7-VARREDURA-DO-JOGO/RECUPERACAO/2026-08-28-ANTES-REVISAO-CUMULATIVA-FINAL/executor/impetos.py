"""Validação read-only da releitura física dos ímpetos contra clube_novo."""
from __future__ import annotations
from typing import Any

CONTRACT='clubef-impetos-physical-v1'

def _rows(cur,query,params=()):
    cur.execute(query,params); names=[d.name for d in cur.description]
    return [dict(zip(names,row,strict=True)) for row in cur.fetchall()]

def validate_impetos(snapshot:dict[str,Any],connection:Any)->dict[str,Any]:
    if snapshot.get('contract')!=CONTRACT: raise ValueError('contrato físico de ímpetos inválido')
    current=[r for r in snapshot.get('records',[]) if r.get('preferred_source')=='dt870_updated' and not r.get('vaga_de_slot')]
    source_effects={(int(r['id']),e['codigo_atributo']):int(e['delta']) for r in current for e in r.get('efeitos',[])}
    source_conditions={int(r['id']):r for r in current}
    with connection.cursor() as cur:
        db_effects={(int(r['codigo_impeto']),r['codigo_atributo']):int(r['delta']) for r in _rows(cur,'select codigo_impeto,codigo_atributo,delta from clube_novo.impeto_atributo_jogo')}
        db_conditions=_rows(cur,'select codigo_impeto,criterio_codigo from clube_novo.impeto_condicao_jogo')
        db_ranges=_rows(cur,'select codigo_impeto,quantidade_minima,quantidade_maxima,delta from clube_novo.impeto_condicao_faixa_jogo')
        db_members=_rows(cur,'select codigo_impeto,codigo_liga_membro,ordem_fisica from clube_novo.impeto_condicao_liga_membro_jogo')
        slots=_rows(cur,'select count(*)::int total,count(*) filter(where codigo_impeto is not null)::int preenchidos,count(*) filter(where vaga)::int vagas from clube_novo.carta_impeto_jogo') [0]
        apt=_rows(cur,'select count(*) filter(where pode_rodar)::int aptos from clube_novo.impeto_condicao_jogo')[0]['aptos']
    missing=sorted(set(source_effects)-set(db_effects)); extra=sorted(set(db_effects)-set(source_effects)); changed=sorted(k for k in set(source_effects)&set(db_effects) if source_effects[k]!=db_effects[k])
    expected_ranges={(int(r['id']),x['quantidade_minima'],x['quantidade_maxima'],x['delta']) for r in current for x in r.get('faixas',[])}
    actual_ranges={(r['codigo_impeto'],r['quantidade_minima'],r['quantidade_maxima'],r['delta']) for r in db_ranges}
    league_targets={int(r['id']):int(r['alvo_codigo']) for r in current if r.get('criterio_codigo')=='quantidade_jogadores_liga_categoria'}
    source_members={(code,m['codigo_liga_membro'],m['ordem_fisica']) for code,target in league_targets.items() for m in snapshot.get('liga_membros',[]) if m['codigo_liga_alvo_base']==target}
    actual_members={(r['codigo_impeto'],r['codigo_liga_membro'],r['ordem_fisica']) for r in db_members}
    condition_map={r['codigo_impeto']:r['criterio_codigo'] for r in db_conditions}
    condition_changed=sorted(code for code,r in source_conditions.items() if condition_map.get(code)!=r.get('criterio_codigo'))
    checks={
      'effects':{'source':len(source_effects),'database':len(db_effects),'missing_in_database':len(missing),'extra_in_database':len(extra),'changed':len(changed),'samples':{'missing':missing[:20],'extra':extra[:20],'changed':changed[:20]}},
      'conditions':{'source':len(source_conditions),'database':len(condition_map),'changed':len(condition_changed),'samples':condition_changed[:20]},
      'ranges':{'source':len(expected_ranges),'database':len(actual_ranges),'symmetric_difference':len(expected_ranges^actual_ranges)},
      'league_members':{'source':len(source_members),'database':len(actual_members),'symmetric_difference':len(source_members^actual_members)},
      'slots':slots,'consumer_apt':apt,
    }
    passed=all([not missing,not extra,not changed,not condition_changed,expected_ranges==actual_ranges,source_members==actual_members,apt==0])
    return {'contract':CONTRACT,'transaction_read_only':True,'database_write':False,'preserved_schema':'clube','checks':checks,'passed':passed,'result':'aprovado' if passed else 'reabrir_frente'}
