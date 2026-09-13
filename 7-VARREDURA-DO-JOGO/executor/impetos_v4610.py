"""Validador V4.6.10 de Ímpetos orientado pelo pedido do banco.

A cardinalidade e os códigos esperados são lidos de clube_novo em cada
execução. Ausências, novidades, alterações e duplicidades são relatadas sem
interromper as outras famílias do Extrator.
"""
from __future__ import annotations

from collections import Counter
import json
import os
import re
from typing import Any

CONTRACT = "clubef-impetos-physical-v1"


def _rows(cursor: Any, query: str) -> list[dict[str, Any]]:
    cursor.execute(query)
    names = [column.name for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _first_detail(record: dict[str, Any], role: str) -> dict[str, Any]:
    items = (record.get("source_details") or {}).get(role) or []
    return items[0] if items else {}


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _provenance(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None
    preferred = record.get("preferred_source")
    detail = _first_detail(record, str(preferred)) if isinstance(preferred, str) else {}
    sources = record.get("source_details") or {}
    return {
        "papel_fonte": preferred,
        "registro": _int_or_none(detail.get("record_index")),
        "registro_sha256": detail.get("record_sha256"),
        "fontes_presentes": sorted(str(role) for role, values in sources.items() if values),
    }


def _source_is_proven(record: dict[str, Any], allowed_roles: set[str]) -> bool:
    provenance = _provenance(record)
    return bool(
        provenance
        and provenance["papel_fonte"] in allowed_roles
        and provenance["registro"] is not None
        and isinstance(provenance["registro_sha256"], str)
        and provenance["registro_sha256"]
    )


def _catalog_link(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    return {
        "codigo_jogo": _int_or_none(row.get("codigo_jogo")),
        "registro_dt200": _int_or_none(row.get("registro_dt200")),
        "registro_dt870_steam": _int_or_none(row.get("registro_dt870_steam")),
        "registro_dt870_atualizacao": _int_or_none(row.get("registro_dt870_atualizacao")),
    }


_COLUNAS_DO_CATALOGO = (
    "tamanho_registro", "bit_codigo", "largura_codigo",
    "registro_dt200", "registro_dt870_atualizacao",
    "presente_dt200", "presente_dt870_atualizacao",
)


def _catalogo_fisico(code: int, record: dict[str, Any] | None, tamanho: Any, bit: Any, largura: Any,
                     types: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """O que o arquivo do jogo diz deste impeto, com o nome da coluna do banco.

    Ordem do Luis (04/09/2026): o comparador entregava so a chave, e com um nome
    que a tabela nao usa (codigo_impeto em vez de codigo_jogo). Sem destino e sem
    valores, nenhum impeto do catalogo achava onde ser gravado e os 416 saiam como
    "destino ausente ou ambiguo". Aqui ele entrega chave, destino e valores.
    """
    if not isinstance(record, dict):
        return None
    detalhes = record.get("source_details") or {}
    dt200 = _first_detail(record, "dt200")
    atualizado = _first_detail(record, "dt870_updated")
    result = {
        "codigo_jogo": code,
        "tamanho_registro": _int_or_none(tamanho),
        "bit_codigo": _int_or_none(bit),
        "largura_codigo": _int_or_none(largura),
        "registro_dt200": _int_or_none(dt200.get("record_index")),
        "registro_dt870_atualizacao": _int_or_none(atualizado.get("record_index")),
        "presente_dt200": bool(detalhes.get("dt200")),
        "presente_dt870_atualizacao": bool(detalhes.get("dt870_updated")),
    }
    if atualizado and record.get("tipo_condicao_status") == "coletado":
        raw = record.get("tipo_condicao_raw")
        candidates = [item for item in types or [] if item.get("codigo_raw") == raw]
        if len(candidates) != 1 or not isinstance(candidates[0].get("condicional_confirmado"), bool):
            raise ValueError(f"ímpeto {code}: tipo ou comportamento sem referência canônica")
        result.update({
            "tipo_condicao_raw": raw, "condicional": candidates[0]["condicional_confirmado"],
            "condicao_estado": "tipo_e_comportamento_comprovados",
            "bit_condicao": _int_or_none(atualizado.get("tipo_bit")),
            "largura_condicao": _int_or_none(atualizado.get("tipo_largura")),
            "registro_condicao": _int_or_none(atualizado.get("record_index")),
            "fonte_condicao": "dt870_atualizacao:PlayerBooster.bin",
        })
    return result


def _catalogo_banco(database: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(database, dict):
        return None
    saida: dict[str, Any] = {"codigo_jogo": _int_or_none(database.get("codigo_jogo"))}
    for coluna in _COLUNAS_DO_CATALOGO:
        valor = database.get(coluna)
        saida[coluna] = bool(valor) if coluna.startswith("presente_") else _int_or_none(valor)
    for coluna in ("tipo_condicao_raw", "condicional", "condicao_estado", "bit_condicao",
                   "largura_condicao", "registro_condicao", "fonte_condicao"):
        saida[coluna] = database.get(coluna)
    return saida


_REGRA_CONDICAO = (
    "alvo_origem", "campo_alvo", "avaliacao_minima", "avaliacao_maxima",
    "status_validacao", "falta_o_que", "chave_texto_hex", "rotina_condicao_va",
    "transformacao_regra", "texto_regra_secao", "texto_regra_id", "texto_regra_offset",
)


def _regra_condicao(record: dict[str, Any], references: list[dict[str, Any]]) -> dict[str, Any]:
    """Reutiliza a regra canônica comprovada, nunca a origem física de outro registro."""
    candidates = [
        {key: row.get(key) for key in _REGRA_CONDICAO}
        for row in references
        if row.get("tipo_raw") == record.get("tipo_condicao_raw")
        and row.get("criterio_codigo") == record.get("criterio_codigo")
    ]
    signatures = {json.dumps(row, sort_keys=True, ensure_ascii=False) for row in candidates}
    if len(signatures) != 1:
        raise ValueError(f"condição {record.get('id')}: regra canônica ausente ou ambígua")
    rule = candidates[0]
    required = ("alvo_origem", "status_validacao", "falta_o_que", "chave_texto_hex",
                "rotina_condicao_va", "transformacao_regra")
    if any(not isinstance(rule[key], str) or not rule[key].strip() for key in required):
        raise ValueError(f"condição {record.get('id')}: regra canônica incompleta")
    return rule


def _origem_pacote(contract: dict[str, Any]) -> dict[str, str]:
    sources = {(row.get("template_caminho"), row.get("sha256_cpk"))
               for row in contract.get("localizadores_fontes", [])
               if row.get("papel_fonte") == "dt870_updated"}
    if len(sources) != 1:
        raise ValueError("origem DT870 atual ausente ou ambígua no contrato")
    path, sha = sources.pop()
    if not isinstance(path, str) or not path.strip() or not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
        raise ValueError("origem DT870 atual incompleta no contrato")
    return {"pacote_origem": os.path.expandvars(path), "hash_pacote": sha}


def _condicao_fisica(code: int, record: dict[str, Any] | None, tamanho: Any,
                    references: list[dict[str, Any]] | None = None,
                    contract: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """A condicao do impeto lida do jogo, com o nome das colunas da tabela.

    Decisao do Luis em 04/09/2026: a lista de condicoes e dado do jogo, entao o
    Extrator grava. Sem destino declarado, a chave codigo_impeto servia para seis
    tabelas e os 208 sempre saiam como "destino ambiguo".
    """
    if not isinstance(record, dict):
        return None
    detalhe = _first_detail(record, "dt870_updated")
    return {
        **_regra_condicao(record, references or []),
        **_origem_pacote(contract or {}),
        "codigo_impeto": code,
        "tipo_raw": _int_or_none(record.get("tipo_condicao_raw")),
        "criterio_codigo": record.get("criterio_codigo"),
        "bit_tipo": _int_or_none(detalhe.get("tipo_bit")),
        "largura_tipo": _int_or_none(detalhe.get("tipo_largura")),
        "bit_tipo_espelho": _int_or_none(detalhe.get("tipo_espelho_bit")),
        "largura_tipo_espelho": _int_or_none(detalhe.get("tipo_espelho_largura")),
        "indice_registro": _int_or_none(detalhe.get("record_index")),
        "registro_sha256": detalhe.get("record_sha256"),
        "arquivo_origem": "PlayerBooster.bin",
        "tamanho_registro": _int_or_none(tamanho),
    }


def _condicao_banco(database: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(database, dict):
        return None
    colunas = ("codigo_impeto", "tipo_raw", "criterio_codigo", "bit_tipo", "largura_tipo",
               "bit_tipo_espelho", "largura_tipo_espelho", "indice_registro",
               "registro_sha256", "arquivo_origem", "tamanho_registro")
    return {coluna: database.get(coluna) for coluna in colunas}


def _efeitos_classificados(snapshot: dict[str, Any], database: list[dict[str, Any]]) -> dict[str, list]:
    """Compara efeitos por identidade; a contagem total não prova equivalência."""
    result = {key: [] for key in ("new", "altered", "removed")}
    stored = {(int(row["codigo_impeto"]), row["codigo_atributo"]): row for row in database}
    seen = set()
    for record in snapshot.get("records", []):
        if record.get("preferred_source") != "dt870_updated" or record.get("tipo_condicao_status") != "coletado":
            continue
        code = int(record["id"])
        detail = _first_detail(record, "dt870_updated")
        used = {int(row["ordem"]) for key, row in stored.items() if key[0] == code}
        for effect in record.get("efeitos", []):
            key = (code, effect["codigo_atributo"])
            if key in seen:
                raise ValueError(f"efeito duplicado na fotografia: {key}")
            seen.add(key)
            before = stored.get(key)
            order = int(before["ordem"]) if before else next(n for n in range(1, 100) if n not in used)
            used.add(order)
            index, bit, width = int(detail["record_index"]), int(effect["bit_delta"]), int(effect["largura_delta"])
            physical = {"codigo_impeto": code, "codigo_atributo": key[1], "ordem": order,
                        "delta": int(effect["delta"]), "bit_delta": bit, "largura_delta": width,
                        "arquivo_origem": effect["arquivo_origem"], "fonte_origem": effect["fonte_origem"],
                        "status_validacao": "comprovado_biblioteca_dt870",
                        "registro_origem": index,
                        "endereco_origem": f"registro {index} de {snapshot['record_size']} bytes; bit {bit}; largura {width}"}
            kind = "new" if before is None else "altered"
            if before is not None and all(before.get(k) == v for k, v in physical.items()):
                continue
            result[kind].append({"classificacao": "novo" if before is None else "alterado", "escopo": "efeitos",
                "destino_tabela": "impeto_atributo_jogo", "chave_canonica": {"codigo_impeto": code, "codigo_atributo": key[1]},
                "valor_fisico": physical, "valor_banco": before, "fonte_fisica": _provenance(record),
                "fonte_fisica_comprovada": True})
    for key, before in stored.items():
        if key not in seen:
            result["removed"].append({"classificacao": "removido", "escopo": "efeitos", "destino_tabela": "impeto_atributo_jogo",
                "chave_canonica": {"codigo_impeto": key[0], "codigo_atributo": key[1]}, "valor_banco": before})
    return result


def _classified_item(
    status: str,
    code: int,
    record: dict[str, Any] | None,
    database: dict[str, Any] | None,
    scope: str,
    allowed_roles: set[str],
    fisico: dict[str, Any] | None = None,
    banco: dict[str, Any] | None = None,
) -> dict[str, Any]:
    do_catalogo = scope == "catalogo"
    da_condicao = scope == "condicoes"
    item: dict[str, Any] = {
        "classificacao": status,
        "escopo": scope,
        "chave_canonica": {"codigo_jogo": code} if do_catalogo else {"codigo_impeto": code},
        "procedencia_fisica": _provenance(record),
        "vinculo_banco": _catalog_link(database),
        "fonte_fisica_comprovada": _source_is_proven(record, allowed_roles) if record else False,
    }
    if do_catalogo:
        item["destino_tabela"] = "impeto_jogo"
        item["valor_fisico"] = fisico
        item["valor_banco"] = banco
        # O aplicador procura a procedencia em "fonte_fisica". Entregar so em
        # "procedencia_fisica" fazia os 207 impetos do catalogo cairem em
        # "mudanca sem procedencia fisica persistida". Mesmo conteudo, o nome que ele le.
        item["fonte_fisica"] = item["procedencia_fisica"]
    if da_condicao:
        item["destino_tabela"] = "impeto_condicao_jogo"
        item["valor_fisico"] = fisico
        item["valor_banco"] = banco
        item["fonte_fisica"] = item["procedencia_fisica"]
    return item


def validate_impetos_v4610(snapshot: dict[str, Any], connection: Any, reading_contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or snapshot.get("contract") != CONTRACT:
        raise ValueError("contrato físico de Ímpetos inválido")

    physical_records = snapshot.get("records")
    if not isinstance(physical_records, list):
        raise ValueError("a fotografia física de Ímpetos não contém registros")
    family = next(
        (
            item for item in reading_contract.get("familias", [])
            if isinstance(item, dict) and item.get("chave_familia") == "impetos"
        ),
        None,
    )
    if not isinstance(family, dict):
        raise ValueError("pedido canônico não solicitou a família Ímpetos")
    allowed_roles = {str(role) for role in family.get("papeis_fonte", []) if isinstance(role, str) and role}
    if not allowed_roles:
        raise ValueError("pedido canônico de Ímpetos não declarou fontes permitidas")
    types = [row for catalog in reading_contract.get("catalogos", [])
             if catalog.get("schema") == "clube_novo" and catalog.get("table") == "tipo_impeto_jogo"
             for row in catalog.get("rows", [])]

    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a validação de Ímpetos não ficou protegida como somente leitura")

        expected_catalog = _rows(
            cursor,
            "select codigo_jogo,tamanho_registro,bit_codigo,largura_codigo,"
            "registro_dt200,registro_dt870_steam,registro_dt870_atualizacao,"
            "presente_dt200,presente_dt870_steam,presente_dt870_atualizacao,"
            "tipo_condicao_raw,condicional,condicao_estado,bit_condicao,largura_condicao,registro_condicao,fonte_condicao "
            "from clube_novo.impeto_jogo order by codigo_jogo",
        )
        expected_conditions = _rows(
            cursor,
            "select * "
            "from clube_novo.impeto_condicao_jogo order by codigo_impeto",
        )
        expected_effects = _rows(cursor, "select * from clube_novo.impeto_atributo_jogo")
        requested_counts = _rows(
            cursor,
            "select "
            "(select count(*) from clube_novo.impeto_jogo)::int as union_catalog,"
            "(select count(*) from clube_novo.impeto_atributo_jogo)::int as effects,"
            "(select count(*) from clube_novo.impeto_condicao_jogo)::int as conditions,"
            "(select count(*) from clube_novo.impeto_condicao_faixa_jogo)::int as ranges,"
            "(select count(*) from clube_novo.impeto_condicao_parametro_faixa_jogo)::int as range_parameters,"
            "(select count(*) from clube_novo.impeto_condicao_nacionalidade_jogo)::int as nationality_targets,"
            "(select count(*) from clube_novo.impeto_condicao_liga_jogo)::int as league_targets,"
            "(select count(*) from clube_novo.impeto_condicao_clube_jogo)::int as club_targets,"
            "(select count(*) from clube_novo.impeto_condicao_classe_jogo)::int as classes,"
            "(select count(*) from clube_novo.impeto_condicao_liga_membro_jogo)::int as competition_unit_members",
        )[0]
        consumer = _rows(
            cursor,
            "select count(*) filter (where pode_rodar)::int as condicoes_aptas,"
            "count(*) filter (where not pode_rodar)::int as condicoes_bloqueadas "
            "from clube_novo.impeto_condicao_jogo",
        )[0]

    ids: list[int] = []
    invalid_records: list[dict[str, Any]] = []
    by_code: dict[int, dict[str, Any]] = {}
    for index, record in enumerate(physical_records):
        if not isinstance(record, dict):
            invalid_records.append({"index": index, "reason": "registro não é objeto"})
            continue
        code = _int_or_none(record.get("id"))
        if code is None:
            invalid_records.append({"index": index, "reason": "id ausente ou inválido"})
            continue
        ids.append(code)
        by_code.setdefault(code, record)

    duplicate_codes = sorted(code for code, total in Counter(ids).items() if total > 1)
    found_codes = set(by_code)
    expected_by_code = {int(row["codigo_jogo"]): row for row in expected_catalog}
    expected_codes = set(expected_by_code)

    historical_source = snapshot.get("historical_source") or {}
    historical_records = historical_source.get("records") or []
    historical_by_record_number = {
        int(record["record_number"]): record
        for record in historical_records
        if isinstance(record, dict) and _int_or_none(record.get("record_number")) is not None
    }
    historical_unresolved: list[dict[str, Any]] = []
    historical_codes: set[int] = set()
    for code, database in sorted(expected_by_code.items()):
        record_number = _int_or_none(database.get("registro_dt870_steam"))
        historical = historical_by_record_number.get(record_number) if record_number is not None else None
        if not historical:
            continue
        raw_code = _int_or_none(historical.get("raw_code"))
        if raw_code == code:
            continue
        historical_codes.add(code)
        historical_unresolved.append({
            "classificacao": "historico_deslocado_sem_prova_semantica",
            "escopo": "catalogo_historico",
            "chave_canonica": {"codigo_impeto": code},
            "codigo_bruto_observado": raw_code,
            "vinculo_banco": _catalog_link(database),
            "procedencia_fisica": {
                "papel_fonte": historical.get("source_role"),
                "registro": _int_or_none(historical.get("record_index")),
                "numero_registro": record_number,
                "registro_sha256": historical.get("record_sha256"),
                "arquivo_sha256": historical.get("source_file_sha256"),
            },
            "fonte_fisica_comprovada": bool(
                historical.get("record_sha256") and historical.get("source_file_sha256")
            ),
            "reconciliado": False,
            "motivo": (
                "o registro e o código bruto foram comprovados, mas o layout legado não possui "
                "decodificador validado para condição, alvos, efeitos e faixas"
            ),
        })

    missing_codes = sorted((expected_codes - found_codes) - historical_codes)
    extra_codes = sorted(found_codes - expected_codes)
    changed_codes: list[int] = []

    record_size = _int_or_none(snapshot.get("record_size"))
    code_field = (snapshot.get("field_contract") or {}).get("codigo") or {}
    code_bit = _int_or_none(code_field.get("bit"))
    code_width = _int_or_none(code_field.get("largura"))

    for code in sorted(expected_codes & found_codes):
        expected = expected_by_code[code]
        record = by_code[code]
        details = record.get("source_details") or {}
        dt200 = _first_detail(record, "dt200")
        updated = _first_detail(record, "dt870_updated")
        source_signature = (
            record_size,
            code_bit,
            code_width,
            _int_or_none(dt200.get("record_index")),
            _int_or_none(updated.get("record_index")),
            bool(details.get("dt200")),
            bool(details.get("dt870_updated")),
        )
        expected_signature = (
            _int_or_none(expected.get("tamanho_registro")),
            _int_or_none(expected.get("bit_codigo")),
            _int_or_none(expected.get("largura_codigo")),
            _int_or_none(expected.get("registro_dt200")),
            _int_or_none(expected.get("registro_dt870_atualizacao")),
            bool(expected.get("presente_dt200")),
            bool(expected.get("presente_dt870_atualizacao")),
        )
        physical_catalog = _catalogo_fisico(code, record, record_size, code_bit, code_width, types)
        if source_signature != expected_signature or any(
            expected.get(field) != value for field, value in physical_catalog.items()
        ):
            changed_codes.append(code)

    current_records = {
        code: record
        for code, record in by_code.items()
        if record.get("preferred_source") == "dt870_updated"
        and record.get("tipo_condicao_status") == "coletado"
    }
    expected_condition_by_code = {
        int(row["codigo_impeto"]): row for row in expected_conditions
    }
    expected_condition_codes = set(expected_condition_by_code)
    found_condition_codes = set(current_records)

    missing_conditions = sorted(expected_condition_codes - found_condition_codes)
    extra_conditions = sorted(found_condition_codes - expected_condition_codes)
    changed_conditions: list[int] = []
    for code in sorted(expected_condition_codes & found_condition_codes):
        expected = expected_condition_by_code[code]
        record = current_records[code]
        detail = _first_detail(record, "dt870_updated")
        source_signature = (
            _int_or_none(record.get("tipo_condicao_raw")),
            _int_or_none(detail.get("record_index")),
            detail.get("record_sha256"),
        )
        expected_signature = (
            _int_or_none(expected.get("tipo_raw")),
            _int_or_none(expected.get("indice_registro")),
            expected.get("registro_sha256"),
        )
        if source_signature != expected_signature:
            changed_conditions.append(code)

    extracted_counts = {
        "raw_records": len(physical_records),
        "valid_records": len(ids),
        "unique_codes": len(found_codes),
        "union_catalog": len(found_codes),
        "effects": sum(len(record.get("efeitos") or []) for record in current_records.values()),
        "conditions": len(current_records),
        "ranges": sum(len(record.get("faixas") or []) for record in current_records.values()),
        "range_parameters": sum(
            1
            for record in current_records.values()
            if _int_or_none(record.get("tipo_condicao_raw")) == 2
        ),
        "nationality_targets": sum(
            1 for record in current_records.values()
            if record.get("alvo_tipo") == "nacionalidade_regiao"
        ),
        "league_targets": sum(
            1 for record in current_records.values()
            if record.get("alvo_tipo") == "liga_categoria"
        ),
        "club_targets": sum(
            1 for record in current_records.values()
            if record.get("alvo_tipo") == "clube_equipe"
            and record.get("alvo_codigo") is not None
        ),
        "classes": sum(
            1 for record in current_records.values()
            if (_int_or_none(record.get("classe_dono")) or 0) > 0
        ),
        "competition_unit_members": len(snapshot.get("liga_membros") or []),
    }

    count_differences = {
        key: {
            "requested": int(requested_counts.get(key) or 0),
            "found": int(extracted_counts.get(key) or 0),
        }
        for key in requested_counts
        if int(requested_counts.get(key) or 0) != int(extracted_counts.get(key) or 0)
    }

    classification = {
        "new": [
            _classified_item("novo", code, by_code[code], None, "catalogo", allowed_roles,
                             _catalogo_fisico(code, by_code[code], record_size, code_bit, code_width, types), None)
            for code in extra_codes
        ],
        "removed": [_classified_item("removido", code, None, expected_by_code[code], "catalogo", allowed_roles,
                                     None, _catalogo_banco(expected_by_code[code])) for code in missing_codes],
        "altered": [
            _classified_item("alterado", code, by_code[code], expected_by_code[code], "catalogo", allowed_roles,
                             _catalogo_fisico(code, by_code[code], record_size, code_bit, code_width, types),
                             _catalogo_banco(expected_by_code[code]))
            for code in changed_codes
        ],
        "repeated": [
            {
                **_classified_item("repetido", code, by_code[code], expected_by_code.get(code), "catalogo", allowed_roles),
                "ocorrencias": [
                    {"indice_fotografia": index, "procedencia_fisica": _provenance(record)}
                    for index, record in enumerate(physical_records)
                    if isinstance(record, dict) and _int_or_none(record.get("id")) == code
                ],
            }
            for code in duplicate_codes
        ],
        "invalid": [
            {
                "classificacao": "invalido",
                "escopo": "catalogo",
                "chave_canonica": None,
                "procedencia_fisica": None,
                "vinculo_banco": None,
                **item,
            }
            for item in invalid_records
        ],
        "conditions": {
            "new": [
                _classified_item("novo", code, current_records[code], None, "condicoes", allowed_roles,
                                 _condicao_fisica(code, current_records[code], record_size, expected_conditions, reading_contract), None)
                for code in extra_conditions
            ],
            "removed": [
                _classified_item("removido", code, None, expected_condition_by_code[code], "condicoes", allowed_roles,
                                 None, _condicao_banco(expected_condition_by_code[code]))
                for code in missing_conditions
            ],
            "altered": [
                _classified_item("alterado", code, current_records[code], expected_condition_by_code[code], "condicoes", allowed_roles,
                                 _condicao_fisica(code, current_records[code], record_size, expected_conditions, reading_contract),
                                 _condicao_banco(expected_condition_by_code[code]))
                for code in changed_conditions
            ],
        },
        "historical_unresolved": historical_unresolved,
        "effects": _efeitos_classificados(snapshot, expected_effects),
    }
    improper_sources = [
        _classified_item("invalido", code, record, expected_by_code.get(code), "catalogo", allowed_roles)
        for code, record in by_code.items()
        if not _source_is_proven(record, allowed_roles)
    ]
    if improper_sources:
        classification["invalid"].extend({**item, "reason": "procedência física incompleta ou fonte indevida"} for item in improper_sources)

    review_changes = (
        classification["new"]
        + classification["removed"]
        + classification["altered"]
        + classification["conditions"]["new"]
        + classification["conditions"]["removed"]
        + classification["conditions"]["altered"]
        + classification["historical_unresolved"]
        + classification["effects"]["new"]
        + classification["effects"]["altered"]
        + classification["effects"]["removed"]
    )
    technical_failures = classification["repeated"] + classification["invalid"]
    snapshot_candidates = [
        item for item in classification["new"] + classification["conditions"]["new"]
        if item.get("fonte_fisica_comprovada")
    ]
    return {
        "contract": CONTRACT,
        "authority": "clube_novo",
        "transaction_read_only": True,
        "database_write": False,
        "preserved_schema": "clube",
        "continue_pipeline": True,
        "classification_complete": True,
        "technical_integrity": not bool(technical_failures),
        "requested_by_database": {key: int(value or 0) for key, value in requested_counts.items()},
        "extracted": extracted_counts,
        "code_report": {
            "requested": len(expected_codes),
            "found_unique": len(found_codes),
            "missing": missing_codes,
            "extra": extra_codes,
            "changed": changed_codes,
            "duplicates": duplicate_codes,
            "conditions_requested": len(expected_condition_codes),
            "conditions_found": len(found_condition_codes),
            "conditions_missing": missing_conditions,
            "conditions_extra": extra_conditions,
            "conditions_changed": changed_conditions,
            "historical_unresolved": [
                int(item["chave_canonica"]["codigo_impeto"])
                for item in historical_unresolved
            ],
        },
        "classification": classification,
        "count_observations": count_differences,
        "review": {
            "required": bool(review_changes),
            "changes": review_changes,
            "candidate_items": snapshot_candidates,
            "promotion": "somente candidata; decisão pertence exclusivamente à política de revisão devolvida no pedido canônico",
        },
        "technical_failures": technical_failures,
        "checks": {
            "consumer_readiness": consumer,
            "count_differences": count_differences,
        },
        "exact_match": not technical_failures and not review_changes,
        "result": "violacao_tecnica" if technical_failures else "divergencias_diagnosticadas" if review_changes else "sem_divergencias_observadas",
    }
