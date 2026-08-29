"""Validação read-only, integral e com proveniência dos Ímpetos.

V4.6: a lógica permanece a mesma, mas endereço físico não é duplicado neste
módulo. Tamanho, bit, largura, arquivo e proveniência vêm das próprias tabelas
canônicas de clube_novo.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Iterable

CONTRACT = "clubef-impetos-physical-v1"


def _rows(cursor: Any, query: str) -> list[dict[str, Any]]:
    cursor.execute(query)
    names = [description.name for description in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _order_key(row: tuple[Any, ...]) -> str:
    return json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=str)


def _sha256(rows: Iterable[tuple[Any, ...]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=_order_key):
        digest.update(_order_key(row).encode("utf-8")); digest.update(b"\n")
    return digest.hexdigest()


def _compare(source: set[tuple[Any, ...]], database: set[tuple[Any, ...]]) -> dict[str, Any]:
    missing = sorted(source - database, key=_order_key)
    extra = sorted(database - source, key=_order_key)
    return {
        "source": len(source), "database": len(database),
        "missing_in_database": len(missing), "extra_in_database": len(extra),
        "source_sha256": _sha256(source), "database_sha256": _sha256(database),
        "samples": {"missing": missing[:10], "extra": extra[:10]},
        "exact": not missing and not extra,
    }


def _detail(record: dict[str, Any], role: str) -> dict[str, Any]:
    details = (record.get("source_details") or {}).get(role) or []
    return details[0] if details else {}


def _need(mapping: dict[Any, dict[str, Any]], key: Any, label: str) -> dict[str, Any]:
    row = mapping.get(key)
    if row is None:
        raise ValueError(f"{label} sem referência canônica no clube_novo: {key}")
    return row


def validate_impetos(snapshot: dict[str, Any], connection: Any) -> dict[str, Any]:
    if snapshot.get("contract") != CONTRACT:
        raise ValueError("contrato físico de Ímpetos inválido")
    union = snapshot.get("records") or []
    if len(union) != 440 or len({str(record.get("id")) for record in union}) != 440:
        raise ValueError("a união física de Ímpetos não contém 440 códigos únicos")
    current = [r for r in union if r.get("preferred_source") == "dt870_updated" and r.get("tipo_condicao_status") == "coletado"]
    if len(current) != 407:
        raise ValueError(f"a fonte atual contém {len(current)} condições reais; esperado 407")

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação de Ímpetos não ficou protegida como somente leitura")
        database_union_rows = _rows(cursor, "select codigo_jogo,tamanho_registro,bit_codigo,largura_codigo,registro_dt200,registro_dt870_steam,registro_dt870_atualizacao,presente_dt200,presente_dt870_steam,presente_dt870_atualizacao from clube_novo.impeto_jogo")
        database_effect_rows = _rows(cursor, "select codigo_impeto,codigo_atributo,delta,bit_delta,largura_delta,registro_origem,arquivo_origem,fonte_origem from clube_novo.impeto_atributo_jogo")
        database_condition_rows = _rows(cursor, "select codigo_impeto,criterio_codigo,tipo_raw,arquivo_origem,tamanho_registro,indice_registro,registro_sha256,bit_tipo,largura_tipo,bit_tipo_espelho,largura_tipo_espelho from clube_novo.impeto_condicao_jogo")
        database_range_rows = _rows(cursor, "select codigo_impeto,ordem,quantidade_minima,quantidade_maxima,delta from clube_novo.impeto_condicao_faixa_jogo")
        database_parameter_rows = _rows(cursor, "select codigo_impeto,corte_raw,bit_corte,largura_corte,efeito_maximo,bit_efeito_maximo,largura_efeito_maximo,registro_sha256 from clube_novo.impeto_condicao_parametro_faixa_jogo")
        database_nationality_rows = _rows(cursor, "select codigo_impeto,codigo_nacionalidade,arquivo_origem,tamanho_registro,indice_registro,bit_alvo,largura_alvo,registro_sha256 from clube_novo.impeto_condicao_nacionalidade_jogo")
        database_league_rows = _rows(cursor, "select codigo_impeto,codigo_liga_categoria,arquivo_origem,tamanho_registro,indice_registro,bit_alvo,largura_alvo,registro_sha256 from clube_novo.impeto_condicao_liga_jogo")
        database_club_rows = _rows(cursor, "select codigo_impeto,codigo_clube from clube_novo.impeto_condicao_clube_jogo")
        database_class_rows = _rows(cursor, "select codigo_impeto,classe_dono,bit_classe_dono,largura_classe_dono,bit_classe_candidato,largura_classe_candidato from clube_novo.impeto_condicao_classe_jogo")
        database_member_rows = _rows(cursor, "select codigo_impeto,codigo_liga_membro,ordem_fisica,codigo_liga_alvo_base,papel_fisico,arquivo_origem,tamanho_registro,indice_registro,bit_inicial,largura,registro_sha256 from clube_novo.impeto_condicao_liga_membro_jogo")
        slots = _rows(cursor, "select count(*)::int as total,count(*) filter (where codigo_impeto is not null)::int as preenchidos,count(*) filter (where vaga)::int as vagas from clube_novo.carta_impeto_jogo")[0]
        consumer = _rows(cursor, "select count(*) filter (where pode_rodar)::int as condicoes_aptas,count(*) filter (where not pode_rodar)::int as condicoes_bloqueadas from clube_novo.impeto_condicao_jogo")[0]
        provenance = _rows(cursor, "select (select count(*) from clube_novo.impeto_atributo_jogo where endereco_origem is not null and bit_delta is not null and registro_origem is not null)::int as efeitos_com_endereco,(select count(*) from clube_novo.impeto_condicao_jogo where registro_sha256 is not null and indice_registro is not null)::int as condicoes_com_registro,(select count(*) from clube_novo.impeto_condicao_liga_membro_jogo where registro_sha256 is not null and indice_registro is not null)::int as membros_com_registro")[0]
        preserved = _rows(cursor, "select (select count(*) from clube_novo.texto_do_jogo)::int as textos,(select count(*) from clube_novo.tecnico_jogo where fonte_autoritativa='dt870_updated')::int as tecnicos,(select count(*) from clube_novo.carta_jogo)::int as cartas")[0]

    union_ref = {int(r["codigo_jogo"]): r for r in database_union_rows}
    effect_ref = {(int(r["codigo_impeto"]), str(r["codigo_atributo"])): r for r in database_effect_rows}
    condition_ref = {int(r["codigo_impeto"]): r for r in database_condition_rows}
    parameter_ref = {int(r["codigo_impeto"]): r for r in database_parameter_rows}
    nationality_ref = {int(r["codigo_impeto"]): r for r in database_nationality_rows}
    league_ref = {int(r["codigo_impeto"]): r for r in database_league_rows}
    class_ref = {int(r["codigo_impeto"]): r for r in database_class_rows}
    member_ref = {(int(r["codigo_impeto"]), int(r["codigo_liga_membro"]), int(r["ordem_fisica"])): r for r in database_member_rows}

    source_union = set()
    for record in union:
        code = int(record["id"]); ref = _need(union_ref, code, "ímpeto")
        source_union.add((code, int(ref["tamanho_registro"]), int(ref["bit_codigo"]), int(ref["largura_codigo"]),
            _detail(record,"dt200").get("record_index"), _detail(record,"dt870_original").get("record_index"), _detail(record,"dt870_updated").get("record_index"),
            bool((record.get("source_details") or {}).get("dt200")), bool((record.get("source_details") or {}).get("dt870_original")), bool((record.get("source_details") or {}).get("dt870_updated"))))

    source_effects = set()
    for record in current:
        for effect in record.get("efeitos") or []:
            key=(int(record["id"]), str(effect["codigo_atributo"])); ref=_need(effect_ref,key,"efeito de ímpeto")
            source_effects.add((key[0],key[1],int(effect["delta"]),int(ref["bit_delta"]),int(ref["largura_delta"]),int(_detail(record,"dt870_updated")["record_index"]),ref["arquivo_origem"],ref["fonte_origem"]))

    source_conditions=set(); source_parameters=set(); source_nationality_targets=set(); source_league_targets=set(); source_classes=set()
    for record in current:
        code=int(record["id"]); cref=_need(condition_ref,code,"condição de ímpeto"); detail=_detail(record,"dt870_updated")
        source_conditions.add((code,record.get("criterio_codigo"),int(record["tipo_condicao_raw"]),cref["arquivo_origem"],int(cref["tamanho_registro"]),int(detail["record_index"]),detail.get("record_sha256"),int(cref["bit_tipo"]),int(cref["largura_tipo"]),int(cref["bit_tipo_espelho"]),int(cref["largura_tipo_espelho"])))
        if int(record["tipo_condicao_raw"]) == 2:
            ref=_need(parameter_ref,code,"parâmetro de faixa"); source_parameters.add((code,int(record["corte_raw"]),int(ref["bit_corte"]),int(ref["largura_corte"]),int(record["efeito_maximo"]),int(ref["bit_efeito_maximo"]),int(ref["largura_efeito_maximo"]),detail.get("record_sha256")))
        if record.get("alvo_tipo") == "nacionalidade_regiao":
            ref=_need(nationality_ref,code,"alvo nacionalidade"); source_nationality_targets.add((code,int(record["alvo_codigo"]),ref["arquivo_origem"],int(ref["tamanho_registro"]),int(detail["record_index"]),int(ref["bit_alvo"]),int(ref["largura_alvo"]),detail.get("record_sha256")))
        if record.get("alvo_tipo") == "liga_categoria":
            ref=_need(league_ref,code,"alvo liga"); source_league_targets.add((code,int(record["alvo_codigo"]),ref["arquivo_origem"],int(ref["tamanho_registro"]),int(detail["record_index"]),int(ref["bit_alvo"]),int(ref["largura_alvo"]),detail.get("record_sha256")))
        if int(record.get("classe_dono") or 0) > 0:
            ref=_need(class_ref,code,"classe de ímpeto"); source_classes.add((code,int(record["classe_dono"]),int(ref["bit_classe_dono"]),int(ref["largura_classe_dono"]),int(ref["bit_classe_candidato"]),int(ref["largura_classe_candidato"])))

    source_ranges={(int(r["id"]),order,int(item["quantidade_minima"]),int(item["quantidade_maxima"]),int(item["delta"])) for r in current for order,item in enumerate(r.get("faixas") or [],start=1)}
    source_club_targets={(int(r["id"]),int(r["alvo_codigo"])) for r in current if r.get("alvo_tipo")=="clube_equipe"}
    league_targets={int(r["id"]):int(r["alvo_codigo"]) for r in current if r.get("alvo_tipo")=="liga_categoria"}
    current_by_code={int(r["id"]):r for r in current}; source_members=set()
    for code,target in league_targets.items():
        for member in snapshot.get("liga_membros") or []:
            if int(member["codigo_liga_alvo_base"]) != target: continue
            key=(code,int(member["codigo_liga_membro"]),int(member["ordem_fisica"])); ref=_need(member_ref,key,"membro de liga")
            source_members.add((code,key[1],key[2],int(member["codigo_liga_alvo_base"]),member["papel_fisico"],ref["arquivo_origem"],int(ref["tamanho_registro"]),int(ref["indice_registro"]),int(ref["bit_inicial"]),int(ref["largura"]),ref["registro_sha256"]))

    database_union={(int(r["codigo_jogo"]),int(r["tamanho_registro"]),int(r["bit_codigo"]),int(r["largura_codigo"]),r["registro_dt200"],r["registro_dt870_steam"],r["registro_dt870_atualizacao"],bool(r["presente_dt200"]),bool(r["presente_dt870_steam"]),bool(r["presente_dt870_atualizacao"])) for r in database_union_rows}
    database_effects={(int(r["codigo_impeto"]),r["codigo_atributo"],int(r["delta"]),int(r["bit_delta"]),int(r["largura_delta"]),int(r["registro_origem"]),r["arquivo_origem"],r["fonte_origem"]) for r in database_effect_rows}
    database_conditions={(int(r["codigo_impeto"]),r["criterio_codigo"],int(r["tipo_raw"]),r["arquivo_origem"],int(r["tamanho_registro"]),int(r["indice_registro"]),r["registro_sha256"],int(r["bit_tipo"]),int(r["largura_tipo"]),int(r["bit_tipo_espelho"]),int(r["largura_tipo_espelho"])) for r in database_condition_rows}
    database_ranges={(int(r["codigo_impeto"]),int(r["ordem"]),int(r["quantidade_minima"]),int(r["quantidade_maxima"]),int(r["delta"])) for r in database_range_rows}
    database_parameters={(int(r["codigo_impeto"]),int(r["corte_raw"]),int(r["bit_corte"]),int(r["largura_corte"]),int(r["efeito_maximo"]),int(r["bit_efeito_maximo"]),int(r["largura_efeito_maximo"]),r["registro_sha256"]) for r in database_parameter_rows}
    database_nationality_targets={(int(r["codigo_impeto"]),int(r["codigo_nacionalidade"]),r["arquivo_origem"],int(r["tamanho_registro"]),int(r["indice_registro"]),int(r["bit_alvo"]),int(r["largura_alvo"]),r["registro_sha256"]) for r in database_nationality_rows}
    database_league_targets={(int(r["codigo_impeto"]),int(r["codigo_liga_categoria"]),r["arquivo_origem"],int(r["tamanho_registro"]),int(r["indice_registro"]),int(r["bit_alvo"]),int(r["largura_alvo"]),r["registro_sha256"]) for r in database_league_rows}
    database_club_targets={(int(r["codigo_impeto"]),int(r["codigo_clube"])) for r in database_club_rows}
    database_classes={(int(r["codigo_impeto"]),int(r["classe_dono"]),int(r["bit_classe_dono"]),int(r["largura_classe_dono"]),int(r["bit_classe_candidato"]),int(r["largura_classe_candidato"])) for r in database_class_rows}
    database_members={(int(r["codigo_impeto"]),int(r["codigo_liga_membro"]),int(r["ordem_fisica"]),int(r["codigo_liga_alvo_base"]),r["papel_fisico"],r["arquivo_origem"],int(r["tamanho_registro"]),int(r["indice_registro"]),int(r["bit_inicial"]),int(r["largura"]),r["registro_sha256"]) for r in database_member_rows}

    source_type_counts=dict(sorted(Counter(int(r["tipo_condicao_raw"]) for r in current).items())); database_type_counts=dict(sorted(Counter(int(r["tipo_raw"]) for r in database_condition_rows).items()))
    comparisons={"union_catalog":_compare(source_union,database_union),"effects":_compare(source_effects,database_effects),"conditions":_compare(source_conditions,database_conditions),"ranges":_compare(source_ranges,database_ranges),"range_parameters":_compare(source_parameters,database_parameters),"nationality_targets":_compare(source_nationality_targets,database_nationality_targets),"league_targets":_compare(source_league_targets,database_league_targets),"club_targets":_compare(source_club_targets,database_club_targets),"classes":_compare(source_classes,database_classes),"competition_unit_members":_compare(source_members,database_members)}
    expected_types={0:131,1:30,2:232,3:8,5:6}
    counts_ok=(len(source_effects)==2072 and len(source_conditions)==407 and len(source_ranges)==696 and len(source_nationality_targets)==203 and len(source_league_targets)==19 and len(source_classes)==10 and len(source_members)==35 and not source_club_targets and source_type_counts==expected_types and database_type_counts==expected_types and slots=={"total":3748,"preenchidos":2381,"vagas":1367} and provenance=={"efeitos_com_endereco":2072,"condicoes_com_registro":407,"membros_com_registro":35} and preserved=={"textos":11679,"tecnicos":1478,"cartas":43072})
    passed=all(item["exact"] for item in comparisons.values()) and counts_ok and consumer["condicoes_aptas"]==0
    return {"contract":CONTRACT,"transaction_read_only":True,"database_write":False,"preserved_schema":"clube","checks":{**comparisons,"type_counts":{"source":source_type_counts,"database":database_type_counts,"exact":source_type_counts==database_type_counts},"slots":slots,"address_and_provenance":provenance,"consumer_readiness":consumer,"preserved_fronts":preserved},"passed":passed,"result":"aprovado" if passed else "reabrir_frente"}
