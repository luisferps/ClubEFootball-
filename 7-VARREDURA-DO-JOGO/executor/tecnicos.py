"""Validação integral e somente leitura de Técnicos contra clube_novo.

Regra V4.6: endereço físico não é autoridade deste módulo. Bits/larguras são
recebidos na fotografia produzida pelo contrato ativo e comparados ao banco.
"""
from __future__ import annotations
import hashlib, json
from typing import Any, Iterable

CONTRACT = "clubef-tecnicos-carga-v4-sobreposicao"

def _rows(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(query, params); names=[d.name for d in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]

def _sha256(rows: Iterable[tuple[Any,...]]) -> str:
    digest=hashlib.sha256()
    for row in rows:
        digest.update(json.dumps(row,ensure_ascii=False,separators=(",",":"),default=str).encode()); digest.update(b"\n")
    return digest.hexdigest()

def _compare(source:set[tuple[Any,...]], database:set[tuple[Any,...]]) -> dict[str,Any]:
    key=lambda row: json.dumps(row,ensure_ascii=False,separators=(",",":"),default=str)
    missing=sorted(source-database,key=key); extra=sorted(database-source,key=key)
    return {"source":len(source),"database":len(database),"missing_in_database":len(missing),"extra_in_database":len(extra),"source_sha256":_sha256(sorted(source,key=key)),"database_sha256":_sha256(sorted(database,key=key)),"samples":{"missing":missing[:10],"extra":extra[:10]},"exact":not missing and not extra}

def _physical(row:dict[str,Any], label:str) -> tuple[int,int]:
    bit=row.get("bit"); width=row.get("largura")
    if not isinstance(bit,int) or not isinstance(width,int) or bit < 0 or width <= 0:
        raise ValueError(f"{label} sem endereço/largura fornecidos pelo contrato")
    return bit,width

def validate_tecnicos(snapshot:dict[str,Any], connection:Any)->dict[str,Any]:
    if snapshot.get("contract") != CONTRACT: raise ValueError("contrato físico de Técnicos incompatível")
    records=snapshot.get("records") or []; nationalities=snapshot.get("nationalities") or []; affinities=snapshot.get("affinities") or []
    if len(records)!=1478 or len({str(r.get('id')) for r in records})!=1478: raise ValueError("a fotografia física não contém 1.478 técnicos únicos")
    if len(nationalities)!=214 or len(affinities)!=8: raise ValueError("catálogos compartilhados de nacionalidade/afinidade incompletos")
    source_technicians={(int(r['id']),r.get('nome_en') or None,r.get('nome_jp') or None,r.get('nome_cn') or None,int(r['idade']),int(r['nacionalidade_codigo']),int(r['afinidade_codigo']),int(r['record_index']),str(r['source_file_sha256'])) for r in records}
    source_nationalities={(int(r['codigo_jogo']),r.get('nome_pt_br'),r.get('sigla'),int(r['record_index']),int(r['record_size']),int(r['codigo_bit']),int(r['codigo_largura']),int(r['nome_offset']),int(r['nome_largura']),int(r['sigla_offset']),int(r['sigla_largura']),str(r['source_file_sha256'])) for r in nationalities}
    source_affinities={(int(r['codigo_jogo']),r.get('nome_pt'),r.get('nome_tela'),bool(r.get('ausencia_legitima')),bool(r.get('rotulo_confirmado')),int(r['bit']),int(r['largura']),str(r['source_file_sha256']),bool(r.get('pode_rodar')),r.get('falta_o_que')) for r in affinities}
    source_styles=set(); pending=[]
    for r in records:
        for code,value in (r.get('proficiencias') or {}).items():
            evidence=(r.get('proficiencias_fisico') or {}).get(code) or {}
            bit,width=_physical(evidence,f"proficiencia {code}")
            source_styles.add((int(r['id']),code,int(value),'Coach.bin',int(r['record_index']),bit,width,str(r['source_file_sha256']),True))
        for boost in r.get('boosts') or []:
            bit,width=_physical(boost,'boost de técnico')
            pending.append((int(r['id']),int(boost['ordem']),int(boost['atributo_idx_canonico']),int(boost['delta']),'Coach.bin',int(r['record_index']),bit,width,str(r['source_file_sha256']),True))
    with connection.cursor() as cursor:
        cursor.execute('show transaction_read_only')
        if cursor.fetchone()[0] != 'on': raise RuntimeError('a validação de Técnicos não ficou protegida como somente leitura')
        attrs=_rows(cursor,"select indice_otimizador,codigo_atributo codigo from clube_novo.atributo_ordem_otimizador where indice_otimizador between 0 and 25")
        attr_codes={int(r['indice_otimizador']):str(r['codigo']) for r in attrs}
        tech=_rows(cursor,"select id,nome_en,nome_jp,nome_cn,idade,codigo_nacionalidade,codigo_afinidade,registro_campos_apresentacao,hash_campos_apresentacao from clube_novo.tecnico_jogo where fonte_autoritativa='dt870_updated' and presente_dt870_atualizacao is true")
        nat=_rows(cursor,"select codigo_jogo,nome_pt_br,sigla,registro,tamanho_registro,bit_codigo,largura_codigo,offset_nome_pt_br,largura_nome_pt_br,offset_sigla,largura_sigla,hash_country_bin from clube_novo.nacionalidade_jogo")
        aff=_rows(cursor,"select codigo_jogo,nome_pt,nome_tela,ausencia_legitima,rotulo_confirmado,bit,largura,hash_coach_bin,pode_rodar,falta_o_que from clube_novo.afinidade_tecnico_jogo")
        styles=_rows(cursor,"select r.tecnico_id,r.codigo_estilo,r.proficiencia,r.arquivo,r.registro,r.bit,r.largura,r.hash_coach_bin,r.confirmado from clube_novo.tecnico_estilo_jogo r join clube_novo.tecnico_jogo t on t.id=r.tecnico_id where t.fonte_autoritativa='dt870_updated' and t.presente_dt870_atualizacao is true")
        boosts=_rows(cursor,"select r.tecnico_id,r.ordem,r.codigo_atributo,r.delta,r.arquivo,r.registro,r.bit,r.largura,r.hash_coach_bin,r.confirmado from clube_novo.tecnico_atributo_jogo r join clube_novo.tecnico_jogo t on t.id=r.tecnico_id where t.fonte_autoritativa='dt870_updated' and t.presente_dt870_atualizacao is true")
        orphans=_rows(cursor,"select (select count(*) from clube_novo.tecnico_jogo t left join clube_novo.nacionalidade_jogo n on n.codigo_jogo=t.codigo_nacionalidade where t.fonte_autoritativa='dt870_updated' and n.codigo_jogo is null)::int nacionalidade,(select count(*) from clube_novo.tecnico_jogo t left join clube_novo.afinidade_tecnico_jogo a on a.codigo_jogo=t.codigo_afinidade where t.fonte_autoritativa='dt870_updated' and a.codigo_jogo is null)::int afinidade,(select count(*) from clube_novo.tecnico_estilo_jogo r left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id where t.id is null)::int estilo_tecnico,(select count(*) from clube_novo.tecnico_atributo_jogo r left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id where t.id is null)::int boost_tecnico")[0]
    unresolved=sorted({r[2] for r in pending}-set(attr_codes))
    if unresolved: raise ValueError(f"boost de Técnico sem atributo canônico: {unresolved[0]}")
    source_boosts={(r[0],r[1],attr_codes[r[2]],*r[3:]) for r in pending}
    dbtech={(int(r['id']),r['nome_en'],r['nome_jp'],r['nome_cn'],int(r['idade']),int(r['codigo_nacionalidade']),int(r['codigo_afinidade']),int(r['registro_campos_apresentacao']),str(r['hash_campos_apresentacao'])) for r in tech}
    dbnat={(int(r['codigo_jogo']),r['nome_pt_br'],r['sigla'],int(r['registro']),int(r['tamanho_registro']),int(r['bit_codigo']),int(r['largura_codigo']),int(r['offset_nome_pt_br']),int(r['largura_nome_pt_br']),int(r['offset_sigla']),int(r['largura_sigla']),str(r['hash_country_bin'])) for r in nat}
    dbaff={(int(r['codigo_jogo']),r['nome_pt'],r['nome_tela'],bool(r['ausencia_legitima']),bool(r['rotulo_confirmado']),int(r['bit']),int(r['largura']),str(r['hash_coach_bin']),bool(r['pode_rodar']),r['falta_o_que']) for r in aff}
    dbstyles={(int(r['tecnico_id']),r['codigo_estilo'],int(r['proficiencia']),r['arquivo'],int(r['registro']),int(r['bit']),int(r['largura']),str(r['hash_coach_bin']),bool(r['confirmado'])) for r in styles}
    dbboosts={(int(r['tecnico_id']),int(r['ordem']),r['codigo_atributo'],int(r['delta']),r['arquivo'],int(r['registro']),int(r['bit']),int(r['largura']),str(r['hash_coach_bin']),bool(r['confirmado'])) for r in boosts}
    checks={'technicians':_compare(source_technicians,dbtech),'nationalities':_compare(source_nationalities,dbnat),'affinities':_compare(source_affinities,dbaff),'proficiencies_and_overload':_compare(source_styles,dbstyles),'boosts':_compare(source_boosts,dbboosts),'foreign_key_orphans':orphans}
    exact=all(checks[n]['exact'] for n in ('technicians','nationalities','affinities','proficiencies_and_overload','boosts'))
    passed=exact and not any(orphans.values())
    return {'contract':CONTRACT,'transaction_read_only':True,'database_write':False,'preserved_schema':'clube','checks':checks,'passed':passed,'result':'aprovado' if passed else 'reabrir_frente'}
