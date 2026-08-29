from __future__ import annotations

import hashlib
import json
import shutil
import csv
from datetime import datetime, timezone
from pathlib import Path


TASK = Path(__file__).resolve().parents[1]
PROJECT = Path(r"C:\Users\Luis Fernando\Downloads\Clubefootball V4")
REFERENCE_ROOT = PROJECT / "7-VARREDURA-DO-JOGO" / "artefatos" / "referencias-metadados"
POINTER = REFERENCE_ROOT / "referencia-vigente.json"
PHYSICAL = TASK / "work" / "auditoria-coach-fisico.json"
MANIFEST_V2 = TASK / "outputs" / "02-carga-atual" / "tecnicos-2026-08-27" / "canonico-v2" / "manifesto-tecnicos-v2.json"
DISPLAY_ROOT = TASK / "outputs" / "02-carga-atual" / "tecnicos-2026-08-28" / "campos-apresentacao-v1"
DISPLAY_TECHNICIANS = DISPLAY_ROOT / "tecnico-apresentacao-fisico.csv"
DISPLAY_NATIONALITIES = DISPLAY_ROOT / "nacionalidade_jogo.csv"
DISPLAY_AFFINITIES = DISPLAY_ROOT / "afinidade_tecnico_jogo.csv"
DISPLAY_MANIFEST = DISPLAY_ROOT / "manifesto-tecnico-apresentacao.json"
READBACK = DISPLAY_ROOT / "READBACK-IDEMPOTENCIA-CAMPOS-TECNICO.json"

STYLES = [
    ("possessionGame", 206),
    ("longBallCounter", 238),
    ("quickCounter", 224),
    ("longBall", 199),
    ("outWide", 213),
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def bits(raw: bytes, bit: int, width: int) -> int:
    value = 0
    for index in range(width):
        absolute = bit + index
        value |= ((raw[absolute >> 3] >> (absolute & 7)) & 1) << index
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def coach_record(row: dict, display: dict, nationality: dict, coach_hash: str) -> dict:
    raw = bytes.fromhex(row["header_hex"])
    boosts = []
    for order, bit in enumerate((160, 148), start=1):
        encoded = bits(raw, bit, 5)
        if encoded:
            boosts.append({
                "ordem": order,
                "atributo_idx_canonico": encoded - 1,
                "delta": 1,
                "bit": bit,
                "largura": 5,
            })
    age_raw = int(display["idade_valor_fisico"])
    record = {
        "id": str(row["id"]),
        "nome_jp": row["nome_jp"],
        "nome_en": row["nome_en"],
        "nome_cn": row["nome_cn"],
        "proficiencias": {code: bits(raw, bit, 7) for code, bit in STYLES},
        "boosts": boosts,
        "idade": age_raw + 14,
        "idade_valor_fisico": age_raw,
        "nacionalidade_codigo": int(display["nacionalidade_codigo"]),
        "nacionalidade_nome_pt_br": nationality["nome_pt_br"],
        "nacionalidade_sigla": nationality["sigla"],
        "afinidade_codigo": int(display["afinidade_codigo"]),
        "source_role": "dt870_updated",
        "arquivo": "Coach.bin",
        "record_index": int(row["record_index"]),
        "record_size": 176,
        "source_file_sha256": coach_hash,
        "field_contract": {
            "idade": {"bit": 231, "largura": 7, "transformacao": "valor_fisico + 14"},
            "nacionalidade": {"bit": 170, "largura": 8, "resolve_em": "Country.bin.codigo bit 10 largura 9"},
            "afinidade": {"bit": 187, "largura": 3, "zero": "ausencia_legitima"},
        },
        "ativo": True,
    }
    return {**record, "fingerprint": stable(record)}


def nationality_record(row: dict) -> dict:
    record = {
        "id": row["codigo"],
        "codigo_jogo": int(row["codigo"]),
        "nome_pt_br": row["nome_pt_br"],
        "sigla": row["sigla"],
        "source_role": "dt870_updated",
        "arquivo": "Country.bin",
        "record_index": int(row["registro"]),
        "record_size": int(row["tamanho_registro"]),
        "codigo_bit": int(row["bit_codigo"]),
        "codigo_largura": int(row["largura_codigo"]),
        "nome_offset": int(row["offset_nome_pt_br"]),
        "nome_largura": int(row["largura_nome_pt_br"]),
        "nome_codificacao": row["codificacao_nome_pt_br"],
        "sigla_offset": 708,
        "sigla_largura": 10,
        "source_file_sha256": row["hash_country_bin"],
        "presente_dt200": row["presente_dt200"].lower() == "true",
        "presente_dt870_original": row["presente_dt870_steam"].lower() == "true",
        "presente_dt870_atualizacao": row["presente_dt870_atualizacao"].lower() == "true",
        "ativo": True,
    }
    return {**record, "fingerprint": stable(record)}


def affinity_record(row: dict, coach_hash: str) -> dict:
    code = int(row["codigo_jogo"])
    proven = row["rotulo_confirmado"].lower() == "true"
    legitimate_absence = row["ausencia_legitima"].lower() == "true"
    record = {
        "id": str(code),
        "codigo_jogo": code,
        "nome_pt": row["nome_pt"] or None,
        "nome_tela": row["nome_tela"] or None,
        "ausencia_legitima": legitimate_absence,
        "rotulo_confirmado": proven,
        "source_role": "dt870_updated",
        "arquivo": "Coach.bin",
        "bit": int(row["bit"]),
        "largura": int(row["largura"]),
        "source_file_sha256": coach_hash,
        "texto_source_role": "dt261_bra" if proven else None,
        "texto_arquivo": "all.str" if proven else None,
        "texto_secao": row["secao_texto"] or None,
        "texto_id": int(row["id_texto"]) if row["id_texto"] else None,
        "pode_rodar": row["pode_rodar"].lower() == "true",
        "falta_o_que": row["falta_o_que"] or None,
        "ativo": True,
    }
    return {**record, "fingerprint": stable(record)}


def main() -> None:
    pointer = json.loads(POINTER.read_text(encoding="utf-8-sig"))
    previous_id = pointer["reference_id"]
    previous_dir = REFERENCE_ROOT / "versoes" / previous_id
    previous_manifest = json.loads((previous_dir / "manifesto.json").read_text(encoding="utf-8-sig"))
    snapshot = json.loads((previous_dir / "snapshot.json").read_text(encoding="utf-8-sig"))
    physical = json.loads(PHYSICAL.read_text(encoding="utf-8-sig"))
    technical_manifest = json.loads(MANIFEST_V2.read_text(encoding="utf-8-sig"))
    display_manifest = json.loads(DISPLAY_MANIFEST.read_text(encoding="utf-8-sig"))
    readback = json.loads(READBACK.read_text(encoding="utf-8-sig"))
    if not readback["passed"] or not readback["idempotent"]:
        raise SystemExit("readback/idempotência dos campos de apresentação não passou")
    display_rows = read_csv(DISPLAY_TECHNICIANS)
    display_by_id = {row["tecnico_id"]: row for row in display_rows}
    nationality_rows = read_csv(DISPLAY_NATIONALITIES)
    nationality_by_code = {row["codigo"]: row for row in nationality_rows}
    affinity_rows = read_csv(DISPLAY_AFFINITIES)
    coach_hash = display_manifest["coach_bin_sha256"]

    rows = [
        coach_record(
            row,
            display_by_id[str(row["id"])],
            nationality_by_code[display_by_id[str(row["id"])]["nacionalidade_codigo"]],
            coach_hash,
        )
        for row in physical["sources"]["dt870_updated"]["rows"]
    ]
    ids = [row["id"] for row in rows]
    if len(rows) != 1478 or len(ids) != len(set(ids)):
        raise SystemExit("Coach.bin atual não passou em contagem/unicidade")
    capello = next(row for row in rows if row["id"] == "17601312850052")
    if capello["proficiencias"] != {
        "possessionGame": 46,
        "longBallCounter": 89,
        "quickCounter": 57,
        "longBall": 89,
        "outWide": 64,
    } or [(item["atributo_idx_canonico"], item["delta"]) for item in capello["boosts"]] != [(6, 1), (10, 1)]:
        raise SystemExit("amostra Capello divergiu do contrato aprovado")

    snapshot["generated_at"] = datetime.now(timezone.utc).isoformat()
    nationalities = [nationality_record(row) for row in nationality_rows]
    affinities = [affinity_record(row, coach_hash) for row in affinity_rows]
    snapshot["catalogs"]["tecnicos"] = {
        "source_table": "clube_novo.tecnico_jogo + tecnico_estilo_jogo + tecnico_atributo_jogo",
        "comparavel": True,
        "records": rows,
        "contract": "clubef-tecnicos-carga-v3-apresentacao",
        "migration_sha256": technical_manifest["files"]["MIGRACAO-TECNICOS-CANONICA.sql"]["sha256"],
        "blocked_fields": {
            "sobreposicao": "catálogo confirmado; campo de proficiência ainda não localizado no Coach.bin",
            "link_up": "CoachLink.bin localizado; sem semântica/cardinalidade integralmente comprovadas",
        },
    }
    snapshot["catalogs"]["nacionalidades"] = {
        "source_table": "clube_novo.nacionalidade_jogo",
        "comparavel": True,
        "records": nationalities,
        "contract": "clubef-nacionalidades-v1",
    }
    snapshot["catalogs"]["afinidades_tecnico"] = {
        "source_table": "clube_novo.afinidade_tecnico_jogo",
        "comparavel": True,
        "records": affinities,
        "contract": "clubef-afinidades-tecnico-v1",
        "blocked_labels": [1, 2, 3, 4, 6, 7],
    }
    snapshot_bytes = (json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    snapshot_sha = sha_bytes(snapshot_bytes)
    reference_id = f"meta-ref-{previous_manifest['source_identity_sha256'][:12]}-{snapshot_sha[:12]}"
    final_dir = REFERENCE_ROOT / "versoes" / reference_id
    staging = REFERENCE_ROOT / "versoes" / f".{reference_id}.tmp"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    (staging / "snapshot.json").write_bytes(snapshot_bytes)

    summary = dict(previous_manifest["summary"])
    summary["tecnicos"] = {
        "status": "comparado",
        "reason": None,
        "current": 1478,
        "baseline_active": 1478,
        "new": 0,
        "changed": 0,
        "absent": 0,
        "without_previous_fingerprint": 0,
        "duplicate_ids": 0,
        "source_roles": ["dt870_updated"],
        "contract": "identidade + idade + nacionalidade + afinidade física + cinco proficiências + até dois boosts; Link-up/Sobreposição bloqueados",
    }
    summary["nacionalidades"] = {
        "status": "comparado", "reason": None, "current": 214,
        "baseline_active": 214, "new": 0, "changed": 0, "absent": 0,
        "without_previous_fingerprint": 0, "duplicate_ids": 0,
        "source_roles": ["dt870_updated"], "contract": "Country.bin físico com 214 códigos",
    }
    summary["afinidades_tecnico"] = {
        "status": "comparado", "reason": None, "current": 8,
        "baseline_active": 8, "new": 0, "changed": 0, "absent": 0,
        "without_previous_fingerprint": 0, "duplicate_ids": 0,
        "source_roles": ["dt870_updated", "dt261_bra"],
        "contract": "códigos 0..7; somente código 5 possui rótulo comprovado",
    }
    manifest = {
        "contract": "clubef-metadata-reference-v1",
        "reference_id": reference_id,
        "previous_reference_id": previous_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_identity": previous_manifest["source_identity"],
        "source_identity_sha256": previous_manifest["source_identity_sha256"],
        "snapshot": {"file": "snapshot.json", "bytes": len(snapshot_bytes), "sha256": snapshot_sha},
        "summary": summary,
        "source_policy": previous_manifest["source_policy"],
        "database_write": False,
        "technical_database_readback": {
            "tecnico_jogo": 1594,
            "tecnicos_aptos": 1478,
            "tecnico_estilo_jogo": 7390,
            "tecnico_atributo_jogo": 104,
            "nacionalidade_jogo": 214,
            "afinidade_tecnico_jogo": 8,
            "campos_apresentacao_completos": 1478,
            "historicos_sem_preenchimento": 116,
            "semantic_fingerprints": readback["semantic_state_after"]["fingerprints"],
        },
    }
    manifest["manifest_sha256"] = sha_bytes(stable(manifest).encode("utf-8"))
    (staging / "manifesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if final_dir.exists():
        shutil.rmtree(staging)
    else:
        staging.rename(final_dir)
    new_pointer = {
        "contract": "clubef-metadata-reference-pointer-v1",
        "reference_id": reference_id,
        "manifest_sha256": manifest["manifest_sha256"],
        "updated_at": manifest["created_at"],
    }
    POINTER.write_text(json.dumps(new_pointer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "reference_id": reference_id,
        "previous_reference_id": previous_id,
        "records": len(rows),
        "snapshot_sha256": snapshot_sha,
        "manifest_sha256": manifest["manifest_sha256"],
        "capello": {"proficiencias": capello["proficiencias"], "boosts": capello["boosts"]},
        "database_write": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
