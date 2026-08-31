"""Validador V4.6.10 de Técnicos orientado pelo conteúdo atual do banco.

Não fixa quantidades de técnicos, nacionalidades ou afinidades no código.
Divergências são devolvidas como relatório e não interrompem outras famílias.
"""
from __future__ import annotations

from typing import Any

import tecnicos as legacy


CONTRACT = "clubef-tecnicos-carga-v4-sobreposicao"


def _classify(scope: str, target_table: str, columns: tuple[str, ...], source: set[tuple[Any, ...]], database: set[tuple[Any, ...]], key_size: int) -> dict[str, list[dict[str, Any]]]:
    """Compara por identidade estável; valores restantes são conteúdo."""
    result: dict[str, list[dict[str, Any]]] = {kind: [] for kind in ("new", "removed", "altered", "repeated", "invalid")}
    def index(rows: set[tuple[Any, ...]], origin: str) -> dict[tuple[Any, ...], tuple[Any, ...]]:
        indexed: dict[tuple[Any, ...], tuple[Any, ...]] = {}
        for row in rows:
            key = row[:key_size]
            if key in indexed and indexed[key] != row:
                result["repeated"].append({"classificacao": "repetido", "escopo": scope, "destino_tabela": target_table, "chave_canonica": dict(zip(columns[:key_size], key, strict=True)), "origem": origin})
            else:
                indexed[key] = row
        return indexed
    left, right = index(source, "fisica"), index(database, "banco")
    for key in sorted(set(left) | set(right), key=str):
        physical, stored = left.get(key), right.get(key)
        physical_row = dict(zip(columns, physical, strict=True)) if physical is not None else None
        provenance = None if physical_row is None else {
            field: physical_row.get(field)
            for field in ("arquivo", "registro", "record_index", "hash_coach_bin", "hash_campos_apresentacao", "hash_country_bin")
            if physical_row.get(field) is not None
        }
        base = {
            "escopo": scope,
            "destino_tabela": target_table,
            "colunas_fisicas": list(columns),
            "chave_canonica": dict(zip(columns[:key_size], key, strict=True)),
            "fonte_fisica": provenance,
            "vinculo_banco": None if stored is None else dict(zip(columns[:key_size], key, strict=True)),
            "valor_fisico": physical,
            "valor_banco": stored,
        }
        if stored is None: result["new"].append({"classificacao": "novo", **base})
        elif physical is None: result["removed"].append({"classificacao": "removido", **base})
        elif physical != stored: result["altered"].append({"classificacao": "alterado", **base})
    return result


def validate_tecnicos_v4610(snapshot: dict[str, Any], connection: Any, reading_contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ValueError("fotografia física de Técnicos incompatível")

    family = next((item for item in reading_contract.get("familias", []) if isinstance(item, dict) and item.get("chave_familia") == "tecnicos"), None)
    roles = family.get("precedencia_fontes") if isinstance(family, dict) else None
    if not isinstance(roles, list) or not roles or not isinstance(roles[0], str):
        raise ValueError("pedido canônico não declara a fonte prioritária de Técnicos")
    source_role = roles[0]
    records = snapshot.get("records") or []
    nationalities = snapshot.get("nationalities") or []
    affinities = snapshot.get("affinities") or []
    if not isinstance(records, list) or not isinstance(nationalities, list) or not isinstance(affinities, list):
        raise ValueError("fotografia física de Técnicos possui catálogos inválidos")

    source_technicians = {
        (
            int(row["id"]),
            row.get("nome_en") or None,
            row.get("nome_jp") or None,
            row.get("nome_cn") or None,
            int(row["idade"]),
            int(row["nacionalidade_codigo"]),
            int(row["afinidade_codigo"]),
            int(row["record_index"]),
            str(row["source_file_sha256"]),
        )
        for row in records
    }
    source_nationalities = {
        (
            int(row["codigo_jogo"]),
            row.get("nome_pt_br"),
            row.get("sigla"),
            int(row["record_index"]),
            int(row["record_size"]),
            int(row["codigo_bit"]),
            int(row["codigo_largura"]),
            int(row["nome_offset"]),
            int(row["nome_largura"]),
            int(row["sigla_offset"]),
            int(row["sigla_largura"]),
            str(row["source_file_sha256"]),
        )
        for row in nationalities
    }
    source_affinities = {
        (
            int(row["codigo_jogo"]),
            row.get("nome_pt"),
            row.get("nome_tela"),
            bool(row.get("ausencia_legitima")),
            bool(row.get("rotulo_confirmado")),
            int(row["bit"]),
            int(row["largura"]),
            str(row["source_file_sha256"]),
            bool(row.get("pode_rodar")),
            row.get("falta_o_que"),
        )
        for row in affinities
    }

    source_styles: set[tuple[Any, ...]] = set()
    pending_boosts: list[tuple[Any, ...]] = []
    for row in records:
        record_file = legacy._source_file(row, f"técnico {row.get('id')}")
        for code, value in (row.get("proficiencias") or {}).items():
            evidence = (row.get("proficiencias_fisico") or {}).get(code) or {}
            bit, width = legacy._physical(evidence, f"proficiência {code}")
            source_styles.add(
                (
                    int(row["id"]),
                    code,
                    int(value),
                    str(evidence.get("arquivo") or record_file),
                    int(row["record_index"]),
                    bit,
                    width,
                    str(row["source_file_sha256"]),
                    True,
                )
            )
        for boost in row.get("boosts") or []:
            bit, width = legacy._physical(boost, "boost de técnico")
            pending_boosts.append(
                (
                    int(row["id"]),
                    int(boost["ordem"]),
                    int(boost["atributo_idx_canonico"]),
                    int(boost["delta"]),
                    str(boost.get("arquivo") or record_file),
                    int(row["record_index"]),
                    bit,
                    width,
                    str(row["source_file_sha256"]),
                    True,
                )
            )

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação de Técnicos não ficou protegida como somente leitura")

        attrs = legacy._rows(
            cursor,
            "select indice_otimizador,codigo_atributo codigo "
            "from clube_novo.atributo_ordem_otimizador "
            "where indice_otimizador between 0 and 25",
        )
        tech = legacy._rows(
            cursor,
            "select id,nome_en,nome_jp,nome_cn,idade,codigo_nacionalidade,"
            "codigo_afinidade,registro_campos_apresentacao,hash_campos_apresentacao "
            "from clube_novo.tecnico_jogo "
            "where fonte_autoritativa=%s and presente_dt870_atualizacao is true", (source_role,),
        )
        nat = legacy._rows(
            cursor,
            "select codigo_jogo,nome_pt_br,sigla,registro,tamanho_registro,"
            "bit_codigo,largura_codigo,offset_nome_pt_br,largura_nome_pt_br,"
            "offset_sigla,largura_sigla,hash_country_bin "
            "from clube_novo.nacionalidade_jogo",
        )
        aff = legacy._rows(
            cursor,
            "select codigo_jogo,nome_pt,nome_tela,ausencia_legitima,"
            "rotulo_confirmado,bit,largura,hash_coach_bin,pode_rodar,falta_o_que "
            "from clube_novo.afinidade_tecnico_jogo",
        )
        styles = legacy._rows(
            cursor,
            "select relation.tecnico_id,relation.codigo_estilo,relation.proficiencia,"
            "relation.arquivo,relation.registro,relation.bit,relation.largura,"
            "relation.hash_coach_bin,relation.confirmado "
            "from clube_novo.tecnico_estilo_jogo relation "
            "join clube_novo.tecnico_jogo tecnico on tecnico.id=relation.tecnico_id "
            "where tecnico.fonte_autoritativa=%s and tecnico.presente_dt870_atualizacao is true", (source_role,),
        )
        boosts = legacy._rows(
            cursor,
            "select relation.tecnico_id,relation.ordem,relation.codigo_atributo,"
            "relation.delta,relation.arquivo,relation.registro,relation.bit,"
            "relation.largura,relation.hash_coach_bin,relation.confirmado "
            "from clube_novo.tecnico_atributo_jogo relation "
            "join clube_novo.tecnico_jogo tecnico on tecnico.id=relation.tecnico_id "
            "where tecnico.fonte_autoritativa=%s and tecnico.presente_dt870_atualizacao is true", (source_role,),
        )
        orphans = legacy._rows(
            cursor,
            "select "
            "(select count(*) from clube_novo.tecnico_jogo t "
            " left join clube_novo.nacionalidade_jogo n "
            " on n.codigo_jogo=t.codigo_nacionalidade "
            " where t.fonte_autoritativa='dt870_updated' and n.codigo_jogo is null)::int nacionalidade,"
            "(select count(*) from clube_novo.tecnico_jogo t "
            " left join clube_novo.afinidade_tecnico_jogo a "
            " on a.codigo_jogo=t.codigo_afinidade "
            " where t.fonte_autoritativa='dt870_updated' and a.codigo_jogo is null)::int afinidade,"
            "(select count(*) from clube_novo.tecnico_estilo_jogo r "
            " left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id "
            " where t.id is null)::int estilo_tecnico,"
            "(select count(*) from clube_novo.tecnico_atributo_jogo r "
            " left join clube_novo.tecnico_jogo t on t.id=r.tecnico_id "
            " where t.id is null)::int boost_tecnico",
        )[0]

    attr_codes = {int(row["indice_otimizador"]): str(row["codigo"]) for row in attrs}
    unresolved = sorted({row[2] for row in pending_boosts} - set(attr_codes))
    if unresolved:
        raise ValueError(f"boost de Técnico sem atributo canônico: {unresolved[0]}")
    source_boosts = {
        (row[0], row[1], attr_codes[row[2]], *row[3:]) for row in pending_boosts
    }

    database_technicians = {
        (
            int(row["id"]), row["nome_en"], row["nome_jp"], row["nome_cn"],
            int(row["idade"]), int(row["codigo_nacionalidade"]),
            int(row["codigo_afinidade"]), int(row["registro_campos_apresentacao"]),
            str(row["hash_campos_apresentacao"]),
        )
        for row in tech
    }
    database_nationalities = {
        (
            int(row["codigo_jogo"]), row["nome_pt_br"], row["sigla"],
            int(row["registro"]), int(row["tamanho_registro"]),
            int(row["bit_codigo"]), int(row["largura_codigo"]),
            int(row["offset_nome_pt_br"]), int(row["largura_nome_pt_br"]),
            int(row["offset_sigla"]), int(row["largura_sigla"]),
            str(row["hash_country_bin"]),
        )
        for row in nat
    }
    database_affinities = {
        (
            int(row["codigo_jogo"]), row["nome_pt"], row["nome_tela"],
            bool(row["ausencia_legitima"]), bool(row["rotulo_confirmado"]),
            int(row["bit"]), int(row["largura"]), str(row["hash_coach_bin"]),
            bool(row["pode_rodar"]), row["falta_o_que"],
        )
        for row in aff
    }
    database_styles = {
        (
            int(row["tecnico_id"]), row["codigo_estilo"], int(row["proficiencia"]),
            row["arquivo"], int(row["registro"]), int(row["bit"]),
            int(row["largura"]), str(row["hash_coach_bin"]), bool(row["confirmado"]),
        )
        for row in styles
    }
    database_boosts = {
        (
            int(row["tecnico_id"]), int(row["ordem"]), row["codigo_atributo"],
            int(row["delta"]), row["arquivo"], int(row["registro"]),
            int(row["bit"]), int(row["largura"]), str(row["hash_coach_bin"]),
            bool(row["confirmado"]),
        )
        for row in boosts
    }

    checks = {"foreign_key_orphans": orphans}
    classifications = {
        "technicians": _classify("tecnicos", "tecnico_jogo", ("id", "nome_en", "nome_jp", "nome_cn", "idade", "codigo_nacionalidade", "codigo_afinidade", "registro_campos_apresentacao", "hash_campos_apresentacao"), source_technicians, database_technicians, 1),
        "nationalities": _classify("nacionalidades", "nacionalidade_jogo", ("codigo_jogo", "nome_pt_br", "sigla", "registro", "tamanho_registro", "bit_codigo", "largura_codigo", "offset_nome_pt_br", "largura_nome_pt_br", "offset_sigla", "largura_sigla", "hash_country_bin"), source_nationalities, database_nationalities, 1),
        "affinities": _classify("afinidades", "afinidade_tecnico_jogo", ("codigo_jogo", "nome_pt", "nome_tela", "ausencia_legitima", "rotulo_confirmado", "bit", "largura", "hash_coach_bin", "pode_rodar", "falta_o_que"), source_affinities, database_affinities, 1),
        "proficiencies_and_overload": _classify("proficiencias_tecnico", "tecnico_estilo_jogo", ("tecnico_id", "codigo_estilo", "proficiencia", "arquivo", "registro", "bit", "largura", "hash_coach_bin", "confirmado"), source_styles, database_styles, 2),
        "boosts": _classify("boosts_tecnico", "tecnico_atributo_jogo", ("tecnico_id", "ordem", "codigo_atributo", "delta", "arquivo", "registro", "bit", "largura", "hash_coach_bin", "confirmado"), source_boosts, database_boosts, 2),
    }
    classification = {kind: [] for kind in ("new", "removed", "altered", "repeated", "invalid")}
    for items in classifications.values():
        for kind, entries in items.items(): classification[kind].extend(entries)
    technical_integrity = not classification["repeated"] and not classification["invalid"] and not any(int(value or 0) for value in orphans.values())
    return {
        "contract": CONTRACT,
        "authority": "clube_novo",
        "transaction_read_only": True,
        "database_write": False,
        "preserved_schema": "clube",
        "continue_pipeline": True,
        "requested_by_database": {
            "technicians": len(database_technicians),
            "nationalities": len(database_nationalities),
            "affinities": len(database_affinities),
            "proficiencies_and_overload": len(database_styles),
            "boosts": len(database_boosts),
        },
        "extracted": {
            "technicians": len(source_technicians),
            "nationalities": len(source_nationalities),
            "affinities": len(source_affinities),
            "proficiencies_and_overload": len(source_styles),
            "boosts": len(source_boosts),
        },
        "checks": checks,
        "classification_complete": True,
        "technical_integrity": technical_integrity,
        "exact_match": not any(classification[kind] for kind in classification),
        "classification": classification,
        "result": "violacao_tecnica" if not technical_integrity else "divergencias_diagnosticadas" if any(classification[kind] for kind in ("new", "removed", "altered")) else "sem_divergencias_observadas",
    }
