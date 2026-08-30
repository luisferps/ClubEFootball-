from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executor" / "impetos_v4610.py"
RESULT_PATH = Path(__file__).with_name("teste-reconciliacao-historica-failclosed.json")


class Description:
    def __init__(self, name: str) -> None:
        self.name = name


class Cursor:
    def __init__(self) -> None:
        self.description: list[Description] = []
        self.values: list[tuple[object, ...]] = []

    def __enter__(self) -> "Cursor":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, query: str) -> None:
        normalized = " ".join(query.split()).lower()
        if normalized == "show transaction_read_only":
            self.description = [Description("transaction_read_only")]
            self.values = [("on",)]
            return
        if "from clube_novo.impeto_jogo" in normalized:
            names = [
                "codigo_jogo", "tamanho_registro", "bit_codigo", "largura_codigo",
                "registro_dt200", "registro_dt870_steam", "registro_dt870_atualizacao",
                "presente_dt200", "presente_dt870_steam", "presente_dt870_atualizacao",
            ]
            self.description = [Description(name) for name in names]
            self.values = [
                (38, 40, 112, 10, None, None, 10, False, False, True),
                (204, 40, 112, 10, None, 81, None, False, True, False),
            ]
            return
        if "from clube_novo.impeto_condicao_jogo order by" in normalized:
            self.description = [Description(name) for name in ("codigo_impeto", "tipo_raw", "indice_registro", "registro_sha256")]
            self.values = []
            return
        if "as union_catalog" in normalized:
            names = [
                "union_catalog", "effects", "conditions", "ranges", "range_parameters",
                "nationality_targets", "league_targets", "club_targets", "classes",
                "competition_unit_members",
            ]
            self.description = [Description(name) for name in names]
            self.values = [(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)]
            return
        if "as condicoes_aptas" in normalized:
            self.description = [Description("condicoes_aptas"), Description("condicoes_bloqueadas")]
            self.values = [(0, 0)]
            return
        raise AssertionError(f"consulta inesperada: {query}")

    def fetchone(self) -> tuple[object, ...]:
        return self.values[0]

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.values


class Connection:
    def cursor(self) -> Cursor:
        return Cursor()


spec = importlib.util.spec_from_file_location("impetos_v4610", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

snapshot = {
    "contract": "clubef-impetos-physical-v1",
    "record_size": 40,
    "field_contract": {"codigo": {"bit": 112, "largura": 10}},
    "records": [
        {
            "id": "38",
            "preferred_source": "dt870_updated",
            "tipo_condicao_status": "registro_nao_impeto_raw4",
            "source_details": {
                "dt870_updated": [{
                    "record_index": 10,
                    "record_sha256": "updated-record-sha",
                    "source_file_sha256": "updated-file-sha",
                }],
            },
            "efeitos": [],
            "faixas": [],
        }
    ],
    "historical_source": {
        "semantic_status": "layout_legado_sem_decodificador_comprovado",
        "canonical_merge_enabled": False,
        "records": [{
            "record_index": 80,
            "record_number": 81,
            "raw_code": 203,
            "record_sha256": "historical-record-sha",
            "source_file_sha256": "historical-file-sha",
            "source_role": "dt870_original",
        }],
    },
    "liga_membros": [],
}
contract = {
    "familias": [{
        "chave_familia": "impetos",
        "papeis_fonte": ["dt200", "dt870_original", "dt870_updated"],
    }]
}

result = module.validate_impetos_v4610(snapshot, Connection(), contract)
assert result["classification"]["removed"] == []
assert result["classification"]["new"] == []
assert result["classification"]["altered"] == []
assert len(result["classification"]["historical_unresolved"]) == 1
item = result["classification"]["historical_unresolved"][0]
assert item["chave_canonica"] == {"codigo_impeto": 204}
assert item["codigo_bruto_observado"] == 203
assert item["reconciliado"] is False
assert result["review"]["required"] is True
assert result["technical_integrity"] is True

RESULT_PATH.write_text(
    json.dumps(
        {
            "test": "reconciliacao_historica_fail_closed",
            "passed": True,
            "database_write": False,
            "domain_write": False,
            "assertions": {
                "historical_not_new": True,
                "historical_not_removed": True,
                "historical_not_altered": True,
                "historical_not_reconciled": True,
                "historical_review_alert": True,
            },
            "classification": result["classification"],
            "result": result["result"],
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(RESULT_PATH)
