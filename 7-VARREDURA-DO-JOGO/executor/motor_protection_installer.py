"""Instalador explícito e transacional da proteção dos motores.

Este módulo não é chamado pela varredura normal nem pelo botão APLICAR PACOTE.
A prévia abre somente leitura. A instalação produtiva exige simultaneamente o
botão dedicado da interface e ``CLUBEF_ENABLE_REAL_WRITE=1`` no processo filho.
Credenciais chegam apenas pelo ambiente do processo e nunca entram nos
artefatos, argumentos ou mensagens produzidos aqui.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import executor_local as runtime


MANIFEST_SCHEMA = "clubef-completude-motores-seed-v1"
ENVELOPE_SCHEMA = "clubef-completude-motores-seed-envelope-v1"
RULE_VERSION = "completude-motores-carta-v1"
REQUIRED_COMPONENTS = (
    "dados_basicos",
    "dimensoes",
    "atributos",
    "corpo",
    "posicoes",
    "posicao_principal",
    "habilidades",
    "estilos_ia",
    "pes",
    "playstyles",
    "impetos",
)
PROTECTION_TRIGGERS = (
    "build_linha_completude_motor_v1",
    "carta_jogo_invalidar_completude_motor_v1",
    "carta_atributo_invalidar_completude_motor_v1",
    "carta_corpo_invalidar_completude_motor_v1",
    "carta_habilidade_invalidar_completude_motor_v1",
    "carta_estilo_ia_invalidar_completude_motor_v1",
    "carta_posicao_invalidar_completude_motor_v1",
    "carta_posicao_principal_invalidar_completude_motor_v1",
    "carta_pe_invalidar_completude_motor_v1",
    "carta_playstyle_invalidar_completude_motor_v1",
    "carta_impeto_invalidar_completude_motor_v1",
)
COMPLETENESS_SQL = (
    "4-DOCUMENTOS/EXTRATOR/SQL/"
    "APLICAR-COMPLETUDE-MOTORES-CARTA-V1-COMPOSAVEL.sql"
)
BONUS_WRITER_SQL = (
    "4-DOCUMENTOS/BONIFICADOR/SQL/"
    "APLICAR-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1-COMPOSAVEL.sql"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_TOP_LEVEL = {
    "begin;",
    "begin transaction;",
    "commit;",
    "rollback;",
}


class MotorProtectionError(RuntimeError):
    """Recusa segura antes de qualquer confirmação produtiva."""


class MotorProtectionCommitStatusError(MotorProtectionError):
    """Falha que carrega o estado comprovável depois de um COMMIT incerto."""

    def __init__(self, message: str, *, commit_status: str, database_write: bool):
        super().__init__(message)
        self.commit_status = commit_status
        self.database_write = database_write


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _ordinary_file(path: Path, *, maximum_bytes: int | None = None) -> None:
    if not path.is_file() or path.is_symlink():
        raise MotorProtectionError(f"arquivo obrigatório ausente ou não local: {path.name}")
    size = path.stat().st_size
    if size <= 0 or (maximum_bytes is not None and size > maximum_bytes):
        raise MotorProtectionError(f"arquivo obrigatório com tamanho inválido: {path.name}")


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".novo")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _load_object(path: Path) -> dict[str, Any]:
    _ordinary_file(path, maximum_bytes=8 * 1024 * 1024)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise MotorProtectionError(f"{path.name}: objeto JSON esperado")
    return value


@dataclass(frozen=True)
class CardEvidence:
    all_components_eligible: bool
    orphan_current_club: bool
    semantic_coverage_sha256: str
    local_input_sha256: str


@dataclass
class ValidatedPackage:
    manifest_path: Path
    seed_path: Path
    manifest: dict[str, Any]
    card_ids: set[str]
    card_evidence: dict[str, CardEvidence]

    @property
    def count(self) -> int:
        return len(self.card_ids)

    @property
    def package_sha256(self) -> str:
        return str(self.manifest["seed"]["sha256"])


def _semantic_component_payload(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cobertura estável: preserva decisão/evidência e ignora caminho/hash do arquivo local."""
    normalized: list[dict[str, Any]] = []
    for component in components:
        value = {
            "componente": component.get("componente"),
            "estado_coleta": component.get("estado_coleta"),
            "estado_resolucao": component.get("estado_resolucao"),
            "apto_motor": component.get("apto_motor"),
            "evidencia": component.get("evidencia") or {},
        }
        if component.get("quantidade_valores") is not None:
            value["quantidade_valores"] = component.get("quantidade_valores")
        if component.get("problema") is not None:
            value["problema"] = component.get("problema")
        normalized.append(value)
    return sorted(normalized, key=lambda item: str(item["componente"]))


def _validate_component_list(card_id: str, components: Any) -> CardEvidence:
    if not isinstance(components, list) or len(components) != len(REQUIRED_COMPONENTS):
        raise MotorProtectionError(f"{card_id}: o seed não contém exatamente os 11 componentes")
    names: list[str] = []
    eligible = True
    orphan = False
    for component in components:
        if not isinstance(component, dict):
            raise MotorProtectionError(f"{card_id}: componente do seed não é um objeto")
        name = component.get("componente")
        if not isinstance(name, str):
            raise MotorProtectionError(f"{card_id}: componente sem nome")
        names.append(name)
        if not isinstance(component.get("apto_motor"), bool):
            raise MotorProtectionError(f"{card_id}/{name}: decisão de uso no motor não é booleana")
        if not isinstance(component.get("proveniencia"), dict) or not component["proveniencia"]:
            raise MotorProtectionError(f"{card_id}/{name}: proveniência física ausente")
        if not isinstance(component.get("evidencia"), dict):
            raise MotorProtectionError(f"{card_id}/{name}: evidência inválida")
        eligible = eligible and component["apto_motor"]
        orphan = orphan or (
            name == "dimensoes"
            and component.get("estado_resolucao") == "orfao_catalogo_atual"
            and component["apto_motor"]
        )
    if tuple(sorted(names)) != tuple(sorted(REQUIRED_COMPONENTS)) or len(set(names)) != len(names):
        raise MotorProtectionError(f"{card_id}: nomes obrigatórios dos componentes divergem")
    return CardEvidence(
        eligible,
        orphan,
        _sha256_value(_semantic_component_payload(components)),
        "",
    )


def _validate_envelope(value: Any) -> tuple[str, CardEvidence]:
    if not isinstance(value, dict) or value.get("schema") != ENVELOPE_SCHEMA:
        raise MotorProtectionError("linha do seed não usa o envelope esperado")
    if value.get("regra_versao") != RULE_VERSION or value.get("database_write") is not False:
        raise MotorProtectionError("linha do seed tem regra ou declaração de escrita divergente")
    if value.get("application_id") is not None:
        raise MotorProtectionError("o seed não pode trazer application_id pronto")
    if value.get("aplicacao_id_binding") != "aplicacao_id_criado_pelo_instalador_na_mesma_transacao_do_seed":
        raise MotorProtectionError("o seed não exige o application_id criado nesta transação")
    if value.get("rpc") != "clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)":
        raise MotorProtectionError("o destino declarado pelo seed é inesperado")
    card_id = value.get("card_id")
    if not isinstance(card_id, str) or not card_id.strip():
        raise MotorProtectionError("linha do seed sem card_id")
    local_fp = value.get("input_fingerprint_local_sha256")
    component_fp = value.get("componentes_fingerprint_sha256")
    if not isinstance(local_fp, str) or not _SHA256.fullmatch(local_fp):
        raise MotorProtectionError(f"{card_id}: fingerprint local inválido")
    components = value.get("componentes")
    evidence = _validate_component_list(card_id, components)
    if not isinstance(component_fp, str) or component_fp != _sha256_value(components):
        raise MotorProtectionError(f"{card_id}: hash dos 11 componentes diverge")
    return card_id, CardEvidence(
        evidence.all_components_eligible,
        evidence.orphan_current_club,
        evidence.semantic_coverage_sha256,
        local_fp,
    )


def _iter_seed(path: Path) -> Iterator[tuple[bytes, dict[str, Any]]]:
    with path.open("rb") as stream:
        for ordinal, raw in enumerate(stream, start=1):
            if not raw.strip():
                raise MotorProtectionError(f"seed contém linha vazia no registro {ordinal}")
            try:
                value = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise MotorProtectionError(f"seed contém JSON inválido no registro {ordinal}") from error
            if not isinstance(value, dict):
                raise MotorProtectionError(f"seed contém linha não-objeto no registro {ordinal}")
            yield raw, value


def validate_package(
    root: Path,
    run_dir: Path,
    manifest_path: Path,
    *,
    expected_card_count: int | None = None,
) -> ValidatedPackage:
    """Valida manifesto, NDJSON e todos os artefatos selados sem abrir banco."""
    root = root.resolve()
    run_dir = run_dir.resolve()
    manifest_path = manifest_path.resolve()
    expected_manifest = (run_dir / "protecao-motores" / "manifest-seed-completude-motores.json").resolve()
    if manifest_path != expected_manifest:
        raise MotorProtectionError("o manifesto deve pertencer à execução concluída mostrada na janela")
    manifest = _load_object(manifest_path)
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("versao") != 1:
        raise MotorProtectionError("manifesto de proteção incompatível")
    if manifest.get("database_write") is not False or manifest.get("publicacao_independente") is not True:
        raise MotorProtectionError("manifesto não preserva o modo local e a publicação independente")
    if manifest.get("componentes_obrigatorios") != list(REQUIRED_COMPONENTS):
        raise MotorProtectionError("manifesto não declara os 11 componentes na ordem contratada")
    declared_payload_hash = manifest.get("manifest_payload_sha256")
    payload_without_hash = dict(manifest)
    payload_without_hash.pop("manifest_payload_sha256", None)
    if not isinstance(declared_payload_hash, str) or declared_payload_hash != _sha256_value(payload_without_hash):
        raise MotorProtectionError("hash interno do manifesto diverge")

    seed_info = manifest.get("seed")
    if not isinstance(seed_info, dict):
        raise MotorProtectionError("manifesto sem identificação do NDJSON")
    seed_path = (manifest_path.parent / "seed-completude-motores.ndjson").resolve()
    if Path(str(seed_info.get("arquivo") or "")).resolve() != seed_path:
        raise MotorProtectionError("manifesto aponta para outro arquivo de seed")
    _ordinary_file(seed_path)
    if seed_info.get("bytes") != seed_path.stat().st_size:
        raise MotorProtectionError("tamanho do NDJSON diverge do manifesto")
    declared_seed_hash = seed_info.get("sha256")
    if not isinstance(declared_seed_hash, str) or not _SHA256.fullmatch(declared_seed_hash):
        raise MotorProtectionError("manifesto contém hash inválido para o NDJSON")

    source_entries = manifest.get("fontes")
    if not isinstance(source_entries, dict):
        raise MotorProtectionError("manifesto não preserva os artefatos usados no seed")
    expected_sources = {
        "resultado.json",
        "prontidao-motores.json",
        "cartas-fisicas-canonicas.json",
        "dimensoes-fisicas.json",
        "metadados-fisicos.json",
    }
    if set(source_entries) != expected_sources:
        raise MotorProtectionError("conjunto de artefatos do seed diverge")
    for name in sorted(expected_sources):
        entry = source_entries[name]
        expected_path = (run_dir / name).resolve()
        if not isinstance(entry, dict) or Path(str(entry.get("arquivo") or "")).resolve() != expected_path:
            raise MotorProtectionError(f"{name}: caminho selado diverge da execução")
        _ordinary_file(expected_path)
        if entry.get("sha256") != _sha256_file(expected_path):
            raise MotorProtectionError(f"{name}: conteúdo mudou depois da preparação do seed")

    source_result = _load_object((run_dir / "resultado.json").resolve())
    application_status = source_result.get("application_status")
    if (
        source_result.get("state") != "completed"
        or source_result.get("database_write") is not False
        or not isinstance(application_status, dict)
        or application_status.get("state") != "no_changes"
        or application_status.get("selection_available") is not False
    ):
        raise MotorProtectionError(
            "a execução precisa ter terminado com sucesso e sem dados novos ou alterados para enviar"
        )

    producer = manifest.get("gerador")
    producer_path = (root / "executor" / "motor_protection_seed.py").resolve()
    if not isinstance(producer, dict) or Path(str(producer.get("arquivo") or "")).resolve() != producer_path:
        raise MotorProtectionError("gerador declarado pelo seed não é o gerador operacional")
    if producer.get("sha256") != _sha256_file(producer_path):
        raise MotorProtectionError("o gerador do seed mudou; prepare novamente pela execução atual")

    digest = hashlib.sha256()
    card_ids: set[str] = set()
    evidence: dict[str, CardEvidence] = {}
    for raw, envelope in _iter_seed(seed_path):
        digest.update(raw)
        card_id, card_evidence = _validate_envelope(envelope)
        if card_id in card_ids:
            raise MotorProtectionError(f"card_id repetido no seed: {card_id}")
        card_ids.add(card_id)
        evidence[card_id] = card_evidence
    if digest.hexdigest() != declared_seed_hash:
        raise MotorProtectionError("hash físico do NDJSON diverge do manifesto")
    declared_count = (manifest.get("contagens") or {}).get("envelopes")
    if declared_count != len(card_ids):
        raise MotorProtectionError("o total de cartas do manifesto diverge do NDJSON")
    if expected_card_count is not None and len(card_ids) != expected_card_count:
        raise MotorProtectionError(f"o teste esperava {expected_card_count} cartas e encontrou {len(card_ids)}")
    if (manifest.get("contagens") or {}).get("componentes") != len(card_ids) * len(REQUIRED_COMPONENTS):
        raise MotorProtectionError("total de componentes do manifesto diverge de 11 por carta")
    binding = manifest.get("aplicacao_id")
    if not isinstance(binding, dict) or binding.get("valor_no_seed") is not None:
        raise MotorProtectionError("manifesto tentou antecipar um application_id")
    return ValidatedPackage(manifest_path, seed_path, manifest, card_ids, evidence)


def assert_current_contract(package: ValidatedPackage, current_contract: dict[str, Any]) -> None:
    expected = package.manifest.get("contract_seal")
    if not isinstance(expected, dict):
        raise MotorProtectionError("manifesto sem selo do contrato de leitura")
    keys = (
        "contrato_id",
        "versao_jogo",
        "versao_contrato",
        "fingerprint_contrato_sha256",
        "fingerprint_fontes_sha256",
        "fingerprint_catalogos_sha256",
    )
    if any(not isinstance(expected.get(key), str) or expected.get(key) != current_contract.get(key) for key in keys):
        raise MotorProtectionError("o contrato atual mudou; faça uma nova varredura antes de instalar")


def _read_composable_script(repo_root: Path, relative: str) -> tuple[str, str]:
    path = (repo_root / Path(relative)).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError as error:
        raise MotorProtectionError("script de proteção saiu da pasta operacional") from error
    _ordinary_file(path, maximum_bytes=4 * 1024 * 1024)
    text = path.read_text(encoding="utf-8-sig")
    for line in text.splitlines():
        if line.strip().lower() in _FORBIDDEN_TOP_LEVEL:
            raise MotorProtectionError(f"{path.name}: controle transacional interno proibido")
    return text, _sha256_file(path)


def load_install_scripts(root: Path) -> dict[str, dict[str, str]]:
    repo_root = root.resolve().parent
    completeness, completeness_hash = _read_composable_script(repo_root, COMPLETENESS_SQL)
    writer, writer_hash = _read_composable_script(repo_root, BONUS_WRITER_SQL)
    return {
        "completude": {"path": str((repo_root / COMPLETENESS_SQL).resolve()), "sha256": completeness_hash, "sql": completeness},
        "writer_bonificador": {"path": str((repo_root / BONUS_WRITER_SQL).resolve()), "sha256": writer_hash, "sql": writer},
    }


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    return {}


def _will_remain_historical(row: tuple[Any, ...], evidence: CardEvidence) -> bool:
    (
        _line_id,
        _card_id,
        state,
        _card_version,
        line_fingerprint,
        optimizer_id,
        bonus_id,
        legacy_fingerprint,
        optimizer_payload,
        bonus_payload,
        optimizer_fingerprint,
        bonus_fingerprint,
    ) = row
    optimizer = _json_object(optimizer_payload)
    bonus = _json_object(bonus_payload)
    optimizer_reasons = ((optimizer.get("gate") or {}).get("motivos") or [])
    if not isinstance(optimizer_reasons, list):
        optimizer_reasons = ["gate_otimizador_invalido"]
    ignored_for_orphan = {
        "carta.roda_motor=false",
        "carta.pode_rodar_vinculos=false",
        "clube_bloqueado",
        "liga_bloqueada",
    }
    effective_optimizer = [
        str(reason)
        for reason in optimizer_reasons
        if not (evidence.orphan_current_club and str(reason) in ignored_for_orphan)
    ]
    bonus_missing = bonus.get("falta_o_que") or []
    if not isinstance(bonus_missing, list):
        bonus_missing = ["gate_bonificador_invalido"]
    eligible_after_seed = evidence.all_components_eligible and not effective_optimizer and not bonus_missing
    return bool(
        eligible_after_seed
        and state in ("pronta", "publicada")
        and line_fingerprint == legacy_fingerprint
        and optimizer_id is not None
        and bonus_id is not None
        and optimizer_fingerprint == legacy_fingerprint
        and bonus_fingerprint == legacy_fingerprint
    )


class PostgresBackend:
    """Acesso real isolado para permitir testes offline com backend falso."""

    def __init__(self, dsn: str):
        psycopg, sql, jsonb = runtime.import_psycopg()
        self.psycopg = psycopg
        self.sql = sql
        self.Jsonb = jsonb
        self.dsn = dsn

    def open(self, *, read_only: bool):
        connection = self.psycopg.connect(self.dsn, connect_timeout=20)
        connection.read_only = read_only
        return connection

    @staticmethod
    def _essential_signatures() -> tuple[str, ...]:
        return (
            "clube_novo.carta_input_motor_canonico_v1(text)",
            "clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)",
            "clube_novo.planejar_completude_motor_v1(text[])",
            "clube_novo.validar_build_linha_completude_motor_v1()",
            "clube_novo.invalidar_completude_motor_por_insumo_v1()",
            "public.otimizador_carta_v2(text)",
            "public.otimizador_proxima_fila_v1(integer)",
            "public.bonificador_carta_v1(text)",
            "public.bonificador_pares_v1(integer,integer)",
            "public.bonificador_contexto_escrita_v2(integer,integer)",
            "public.gravar_build_bonificador_v1(jsonb)",
        )

    def _protection_state(self, connection: Any) -> tuple[str, dict[str, Any]]:
        object_row = connection.execute(
            """select
                 to_regclass('clube_novo.carta_completude_motor_versao'),
                 to_regclass('clube_novo.carta_completude_motor_componente'),
                 to_regclass('clube_novo.carta_completude_motor_decisao'),
                 to_regclass('clube_novo.carta_completude_motor_atual'),
                 to_regclass('clube_novo.migracao_completude_motor_build_snapshot_v1'),
                 to_regclass('clube_novo.migracao_gravar_bonus_grant_snapshot_v1'),
                 to_regprocedure('clube_novo.carta_input_motor_canonico_v1(text)'),
                 to_regprocedure('clube_novo.registrar_completude_motor_v1(text,bigint,jsonb)'),
                 to_regprocedure('clube_novo.planejar_completude_motor_v1(text[])'),
                 to_regprocedure('clube_novo.validar_build_linha_completude_motor_v1()'),
                 to_regprocedure('clube_novo.invalidar_completude_motor_por_insumo_v1()'),
                 to_regprocedure('public.otimizador_carta_v2(text)'),
                 to_regprocedure('public.otimizador_proxima_fila_v1(integer)'),
                 to_regprocedure('public.bonificador_carta_v1(text)'),
                 to_regprocedure('public.bonificador_pares_v1(integer,integer)'),
                 to_regprocedure('public.bonificador_contexto_escrita_v2(integer,integer)'),
                 to_regprocedure('public.gravar_build_bonificador_v1(jsonb)'),
                 to_regprocedure('public.otimizador_carta_sem_completude_v2(text)'),
                 to_regprocedure('public.otimizador_proxima_fila_sem_completude_v1(integer)'),
                 to_regprocedure('public.bonificador_carta_sem_completude_v1(text)'),
                 to_regprocedure('public.bonificador_pares_sem_completude_v1(integer,integer)'),
                 to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)')"""
        ).fetchone()
        objects = list(object_row or ())
        # Os quatro contratos públicos (índices 11..14) já existem antes da
        # instalação e são renomeados/substituídos pelo SQL. Só os demais são
        # marcadores inequívocos da proteção V1.
        marker_values = objects[:11] + objects[15:]
        present = sum(value is not None for value in marker_values)
        detail: dict[str, Any] = {
            "protection_markers_present": present,
            "protection_markers_expected": len(marker_values),
            "essential_objects_present": sum(value is not None for value in objects),
            "essential_objects_expected": len(objects),
        }
        if present == 0:
            return "ausente", detail
        if present != len(marker_values) or any(value is None for value in objects):
            return "parcial_divergente", detail

        trigger_row = connection.execute(
            """select count(*),coalesce(bool_and(t.tgenabled<>'D'),false)
               from pg_trigger t
               join pg_class c on c.oid=t.tgrelid
               join pg_namespace n on n.oid=c.relnamespace
               where n.nspname='clube_novo' and not t.tgisinternal
                 and t.tgname=any(%s)""",
            (list(PROTECTION_TRIGGERS),),
        ).fetchone()
        triggers_ok = bool(
            trigger_row
            and int(trigger_row[0]) == len(PROTECTION_TRIGGERS)
            and bool(trigger_row[1])
        )

        signatures = self._essential_signatures()
        functions_row = connection.execute(
            """with expected(signature) as (select unnest(%s::text[])), f as (
                 select e.signature,p.oid,p.prosecdef,p.proconfig,
                        pg_get_userbyid(p.proowner) owner,
                        pg_get_functiondef(p.oid) definition
                 from expected e join pg_proc p on p.oid=to_regprocedure(e.signature)
               )
               select count(*),
                      coalesce(bool_and(owner='postgres' and prosecdef
                        and coalesce(proconfig::text,'') ilike '%%search_path%%'),false),
                      coalesce(bool_and(has_function_privilege('service_role',signature,'EXECUTE')
                        and not has_function_privilege('anon',signature,'EXECUTE')
                        and not has_function_privilege('authenticated',signature,'EXECUTE')),false)
               from f""",
            (list(signatures),),
        ).fetchone()
        functions_ok = bool(
            functions_row
            and int(functions_row[0]) == len(signatures)
            and bool(functions_row[1])
            and bool(functions_row[2])
        )

        bypass_row = connection.execute(
            """select
                 to_regprocedure('public.gravar_bonus(jsonb)') is not null,
                 to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)') is not null,
                 coalesce(pg_get_functiondef(to_regprocedure('public.gravar_bonus(jsonb)'))
                          ilike '%%gravar_bonus bloqueada:%%nenhuma linha foi gravada%%',false),
                 not has_function_privilege('service_role','public.gravar_bonus(jsonb)','EXECUTE'),
                 not has_function_privilege('service_role','public.gravar_bonus_sem_completude_v1(jsonb)','EXECUTE'),
                 not has_function_privilege('anon','public.gravar_bonus(jsonb)','EXECUTE'),
                 not has_function_privilege('authenticated','public.gravar_bonus(jsonb)','EXECUTE'),
                 (select count(*)=0 from pg_proc p
                   cross join lateral aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
                   where p.oid in (to_regprocedure('public.gravar_bonus(jsonb)'),
                                   to_regprocedure('public.gravar_bonus_sem_completude_v1(jsonb)'))
                     and a.privilege_type='EXECUTE'),
                 not has_function_privilege('service_role','public.otimizador_carta_sem_completude_v2(text)','EXECUTE'),
                 not has_function_privilege('service_role','public.otimizador_proxima_fila_sem_completude_v1(integer)','EXECUTE'),
                 not has_function_privilege('service_role','public.bonificador_carta_sem_completude_v1(text)','EXECUTE'),
                 not has_function_privilege('service_role','public.bonificador_pares_sem_completude_v1(integer,integer)','EXECUTE')"""
        ).fetchone()
        bypass_ok = bool(bypass_row and all(bool(value) for value in bypass_row))

        definitions_row = connection.execute(
            """select
                 pg_get_functiondef('public.gravar_build_bonificador_v1(jsonb)'::regprocedure)
                   not ilike '%%clube.build%%'
                   and pg_get_functiondef('public.gravar_build_bonificador_v1(jsonb)'::regprocedure)
                   not ilike '%%clube.fila%%',
                 pg_get_functiondef('public.otimizador_proxima_fila_v1(integer)'::regprocedure)
                   not ilike '%%from clube.fila%%'
                   and pg_get_functiondef('public.otimizador_proxima_fila_v1(integer)'::regprocedure)
                   not ilike '%%join clube.fila%%'
                   and pg_get_functiondef('public.otimizador_proxima_fila_v1(integer)'::regprocedure)
                   ilike '%%raise exception%%'
                   and pg_get_functiondef('public.otimizador_proxima_fila_v1(integer)'::regprocedure)
                   ilike '%%fila V1 desativada:%%',
                 pg_get_functiondef('public.otimizador_carta_v2(text)'::regprocedure)
                   ilike '%%carta_completude_motor_versao%%',
                 pg_get_functiondef('public.bonificador_carta_v1(text)'::regprocedure)
                   ilike '%%carta_completude_motor_versao%%'"""
        ).fetchone()
        definitions_ok = bool(definitions_row and all(bool(value) for value in definitions_row))
        access_row = connection.execute(
            """select
                 has_table_privilege('service_role','clube_novo.carta_completude_motor_atual','SELECT'),
                 not has_table_privilege('anon','clube_novo.carta_completude_motor_atual','SELECT'),
                 not has_table_privilege('authenticated','clube_novo.carta_completude_motor_atual','SELECT'),
                 (select bool_and(c.relrowsecurity)
                  from pg_class c join pg_namespace n on n.oid=c.relnamespace
                  where n.nspname='clube_novo' and c.relname in (
                    'carta_completude_motor_versao','carta_completude_motor_componente',
                    'carta_completude_motor_decisao','migracao_completude_motor_build_snapshot_v1',
                    'migracao_gravar_bonus_grant_snapshot_v1'))"""
        ).fetchone()
        access_ok = bool(access_row and all(bool(value) for value in access_row))
        detail.update(
            triggers_ok=triggers_ok,
            functions_ok=functions_ok,
            bypass_ok=bypass_ok,
            definitions_ok=definitions_ok,
            access_ok=access_ok,
        )
        return (
            "ja_instalada"
            if triggers_ok and functions_ok and bypass_ok and definitions_ok and access_ok
            else "parcial_divergente",
            detail,
        )

    @staticmethod
    def _input_state_query(*, installed: bool) -> str:
        otim = "public.otimizador_carta_sem_completude_v2" if installed else "public.otimizador_carta_v2"
        bonus = "public.bonificador_carta_sem_completude_v1" if installed else "public.bonificador_carta_v1"
        return f"""select c.card_id,
          encode(extensions.digest(jsonb_build_object(
            'card_id',c.card_id,
            'dados_basicos',jsonb_build_object(
              'overall',c.overall,'altura',c.altura,'peso',c.peso,'idade',c.idade,
              'level_cap',c.level_cap,'orcamento',c.orcamento,'cap_estimado',c.cap_estimado,
              'grupo_id',c.grupo_id,'forma',c.forma,'roda_motor',c.roda_motor,
              'pode_rodar_vinculos',c.pode_rodar_vinculos),
            'dimensoes',jsonb_build_object(
              'codigo_nacionalidade',c.codigo_nacionalidade,'codigo_clube',c.codigo_clube,
              'codigo_liga',c.codigo_liga,'tipo_carta_id',c.tipo_carta_id,
              'codigo_tipo_carta_fisico',c.codigo_tipo_carta_fisico,
              'marcador_subtipo_tipo_carta',c.marcador_subtipo_tipo_carta),
            'atributos',coalesce((select jsonb_agg(jsonb_build_object('codigo_atributo',x.codigo_atributo,'valor',x.valor) order by x.codigo_atributo) from clube_novo.carta_atributo_jogo x where x.card_id=c.card_id),'[]'::jsonb),
            'corpo',coalesce((select jsonb_agg(jsonb_build_object('codigo_corpo',x.codigo_corpo,'valor',x.valor) order by x.codigo_corpo) from clube_novo.carta_corpo_jogo x where x.card_id=c.card_id),'[]'::jsonb),
            'posicoes',coalesce((select jsonb_agg(jsonb_build_object('posicao_id',x.posicao_id,'nivel_aptidao',x.nivel_aptidao) order by x.posicao_id) from clube_novo.carta_posicao_jogo x where x.card_id=c.card_id),'[]'::jsonb),
            'posicao_principal',(select jsonb_build_object('posicao_id',x.posicao_id) from clube_novo.carta_posicao_principal_jogo x where x.card_id=c.card_id),
            'habilidades',coalesce((select jsonb_agg(jsonb_build_object('skill_id',x.skill_id,'ordem',x.ordem) order by x.skill_id) from clube_novo.carta_habilidade_jogo x where x.card_id=c.card_id),'[]'::jsonb),
            'estilos_ia',coalesce((select jsonb_agg(jsonb_build_object('bit_estilo_ia',x.bit_estilo_ia) order by x.bit_estilo_ia) from clube_novo.carta_estilo_ia_jogo x where x.card_id=c.card_id),'[]'::jsonb),
            'pes',coalesce((select jsonb_agg(jsonb_build_object('campo',x.campo,'valor',x.valor) order by x.campo) from clube_novo.carta_pe_jogo x where x.card_id=c.card_id),'[]'::jsonb),
            'playstyles',coalesce((select jsonb_agg(jsonb_build_object('slot_fisico',x.slot_fisico,'playstyle_id',x.playstyle_id,'valor_raw',x.valor_raw) order by x.slot_fisico) from clube_novo.carta_playstyle_jogo x where x.card_id=c.card_id),'[]'::jsonb),
            'impetos',coalesce((select jsonb_agg(jsonb_build_object('slot',x.slot,'codigo_impeto',x.codigo_impeto,'vaga',x.vaga,'condicional',x.condicional) order by x.slot) from clube_novo.carta_impeto_jogo x where x.card_id=c.card_id),'[]'::jsonb)
          )::text,'sha256'),'hex') input_fp,
          encode(extensions.digest(coalesce({otim}(c.card_id),'null'::jsonb)::text,'sha256'),'hex') otim_fp,
          encode(extensions.digest(coalesce({bonus}(c.card_id),'null'::jsonb)::text,'sha256'),'hex') bonus_fp
        from clube_novo.carta_jogo c order by c.card_id"""

    def _database_state_seal(self, connection: Any, *, installed: bool) -> tuple[str, int]:
        digest = hashlib.sha256()
        count = 0
        cursor = connection.execute(self._input_state_query(installed=installed))
        while True:
            rows = cursor.fetchmany(500)
            if not rows:
                break
            for row in rows:
                digest.update((_canonical(list(row)) + "\n").encode("utf-8"))
                count += 1
        return digest.hexdigest(), count

    @staticmethod
    def _db_components(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, str):
            value = json.loads(value)
        return value if isinstance(value, list) else []

    def _installed_versions(self, connection: Any) -> dict[str, tuple[Any, ...]]:
        rows = connection.execute(
            """select j.card_id,v.versao_id,v.regra_versao,v.contrato_id,
                      v.input_fingerprint_sha256,
                      encode(extensions.digest(clube_novo.carta_input_motor_canonico_v1(j.card_id)::text,'sha256'),'hex') current_input_fp,
                      coalesce(jsonb_agg(jsonb_strip_nulls(jsonb_build_object(
                        'componente',c.componente,'estado_coleta',c.estado_coleta,
                        'estado_resolucao',c.estado_resolucao,'apto_motor',c.apto_motor,
                        'quantidade_valores',c.quantidade_valores,'evidencia',c.evidencia,
                        'problema',c.problema)) order by c.componente)
                        filter (where c.componente is not null),'[]'::jsonb) components
               from clube_novo.carta_jogo j
               left join clube_novo.carta_completude_motor_versao v
                 on v.card_id=j.card_id and v.vigente
               left join clube_novo.carta_completude_motor_componente c
                 on c.versao_id=v.versao_id
               group by j.card_id,v.versao_id,v.regra_versao,v.contrato_id,
                        v.input_fingerprint_sha256
               order by j.card_id"""
        ).fetchall()
        return {str(row[0]): tuple(row) for row in rows}

    def preview(self, connection: Any, package: ValidatedPackage, *, require_read_only: bool) -> dict[str, Any]:
        mode = connection.execute("show transaction_read_only").fetchone()
        observed_read_only = bool(mode and str(mode[0]).lower() == "on")
        if require_read_only and not observed_read_only:
            raise MotorProtectionError("a prévia não ficou protegida como somente leitura")
        operator = connection.execute("select current_user").fetchone()
        if not operator or str(operator[0]) != "postgres":
            raise MotorProtectionError(
                "a proteção exige a conexão proprietária postgres; outra função foi recusada"
            )
        state, objects = self._protection_state(connection)
        if state == "parcial_divergente":
            raise MotorProtectionError(
                "a proteção existe de forma parcial ou divergente; instalar/atualizar foi bloqueado para não encobrir o problema"
            )

        seal = package.manifest["contract_seal"]
        contract = connection.execute(
            """select versao_jogo,versao_contrato,fingerprint_contrato_sha256,
                      fingerprint_fontes_sha256,estado,cobertura_total
               from clube_novo.contrato_leitura_jogo where contrato_id=%s""",
            (seal["contrato_id"],),
        ).fetchone()
        expected_contract = (
            seal["versao_jogo"],
            seal["versao_contrato"],
            seal["fingerprint_contrato_sha256"],
            seal["fingerprint_fontes_sha256"],
            "ativo",
            True,
        )
        if contract != expected_contract:
            raise MotorProtectionError("o contrato ativo do banco não corresponde ao seed")

        database_ids = {str(row[0]) for row in connection.execute(
            "select card_id from clube_novo.carta_jogo order by card_id"
        ).fetchall()}
        if database_ids != package.card_ids:
            only_database = len(database_ids - package.card_ids)
            only_seed = len(package.card_ids - database_ids)
            raise MotorProtectionError(
                "cartas do banco e do seed divergem "
                f"(somente no banco={only_database}; somente no seed={only_seed})"
            )

        database_state_sha256, state_card_count = self._database_state_seal(
            connection, installed=state == "ja_instalada"
        )
        if state_card_count != package.count:
            raise MotorProtectionError("o selo atual dos insumos não cobriu todas as cartas do seed")

        seal_contract_id = str(seal["contrato_id"])
        if state == "ausente":
            changed_ids = sorted(package.card_ids)
            operation_mode = "initial_install"
        else:
            versions = self._installed_versions(connection)
            if set(versions) != package.card_ids:
                raise MotorProtectionError("as versões vigentes não cobrem exatamente as cartas atuais")
            changed_ids = []
            for card_id in sorted(package.card_ids):
                row = versions[card_id]
                components = self._db_components(row[6])
                semantic_fp = _sha256_value(_semantic_component_payload(components))
                expected_evidence = package.card_evidence[card_id]
                if (
                    row[1] is None
                    or row[2] != RULE_VERSION
                    or str(row[3]) != seal_contract_id
                    or row[4] != row[5]
                    or semantic_fp != expected_evidence.semantic_coverage_sha256
                ):
                    changed_ids.append(card_id)
            operation_mode = "already_up_to_date" if not changed_ids else "incremental_update"

        installed = state == "ja_instalada"
        optimizer_function = (
            "public.otimizador_carta_sem_completude_v2"
            if installed
            else "public.otimizador_carta_v2"
        )
        bonus_function = (
            "public.bonificador_carta_sem_completude_v1"
            if installed
            else "public.bonificador_carta_v1"
        )
        rows = connection.execute(
            f"""select l.id,l.card_id,l.estado,l.carta_versao,l.carta_fingerprint,
                       l.build_otimizador_id,l.build_bonificador_id,
                       encode(extensions.digest(coalesce(q.otim,'null'::jsonb)::text,'sha256'),'hex') legacy_fp,
                       q.otim,q.bonus,o.carta_fingerprint,b.carta_fingerprint
                from clube_novo.build_linha_card l
                cross join lateral (
                  select {optimizer_function}(l.card_id) otim,
                         {bonus_function}(l.card_id) bonus
                ) q
               left join clube_novo.build_otimizador o on o.id=l.build_otimizador_id
               left join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
               where l.estado<>'invalida'
               order by l.id"""
        ).fetchall()
        invalidated_ids: list[int] = []
        preserved_ids: list[int] = []
        unaffected_ids: list[int] = []
        active_snapshot: list[list[Any]] = []
        changed_set = set(changed_ids)
        for row in rows:
            card_id = str(row[1])
            active_snapshot.append(list(row))
            card_evidence = package.card_evidence.get(card_id)
            if card_evidence is None:
                raise MotorProtectionError(f"resultado atual aponta para card ausente do seed: {card_id}")
            if card_id not in changed_set:
                unaffected_ids.append(int(row[0]))
                continue
            target = preserved_ids if _will_remain_historical(row, card_evidence) else invalidated_ids
            target.append(int(row[0]))
        invalidated_digest = _sha256_value(sorted(invalidated_ids))
        preview = {
            "transaction_read_only": observed_read_only,
            "protection_state": state,
            "protection_objects": objects,
            "operation_mode": operation_mode,
            "database_card_count": len(database_ids),
            "cards_to_register": len(changed_ids),
            "changed_card_ids": changed_ids,
            "changed_card_ids_sha256": _sha256_value(changed_ids),
            "local_inputs_sha256": _sha256_value([
                [card_id, package.card_evidence[card_id].local_input_sha256]
                for card_id in sorted(package.card_ids)
            ]),
            "database_state_sha256": database_state_sha256,
            "active_result_count": len(rows),
            "results_to_invalidate": len(invalidated_ids),
            "results_preserved_as_identical_history": len(preserved_ids),
            "results_unaffected": len(unaffected_ids),
            "invalidated_ids_sha256": invalidated_digest,
            "preserved_ids_sha256": _sha256_value(sorted(preserved_ids)),
            "unaffected_ids_sha256": _sha256_value(sorted(unaffected_ids)),
            "active_rows_sha256": _sha256_value(active_snapshot),
            "invalidated_ids": invalidated_ids,
            "preserved_ids": preserved_ids,
            "unaffected_ids": unaffected_ids,
            "active_rows_snapshot": active_snapshot,
        }
        preview["confirmation_sha256"] = _sha256_value({
            "manifest_payload_sha256": package.manifest["manifest_payload_sha256"],
            "seed_sha256": package.package_sha256,
            "operation_mode": operation_mode,
            "database_card_count": preview["database_card_count"],
            "cards_to_register": preview["cards_to_register"],
            "changed_card_ids_sha256": preview["changed_card_ids_sha256"],
            "database_state_sha256": database_state_sha256,
            "active_result_count": preview["active_result_count"],
            "results_to_invalidate": preview["results_to_invalidate"],
            "invalidated_ids_sha256": invalidated_digest,
            "preserved_ids_sha256": preview["preserved_ids_sha256"],
            "unaffected_ids_sha256": preview["unaffected_ids_sha256"],
            "active_rows_sha256": preview["active_rows_sha256"],
        })
        return preview

    def _freeze_clube_novo(self, connection: Any) -> int:
        tables = connection.execute(
            """select n.nspname,c.relname
               from pg_class c join pg_namespace n on n.oid=c.relnamespace
               where n.nspname='clube_novo' and c.relkind in ('r','p')
               order by c.oid"""
        ).fetchall()
        if not tables:
            raise MotorProtectionError("não há tabelas clube_novo para congelar durante a confirmação")
        for schema_name, table_name in tables:
            connection.execute(
                self.sql.SQL("lock table {}.{} in share mode").format(
                    self.sql.Identifier(str(schema_name)), self.sql.Identifier(str(table_name))
                )
            )
        return len(tables)

    @staticmethod
    def _verify_result_transition(
        connection: Any,
        preview: dict[str, Any],
        *,
        stage: str,
    ) -> set[int]:
        """Confere toda a partição de resultados antes e depois do COMMIT."""
        original = {int(row[0]): row for row in preview["active_rows_snapshot"]}
        observed_rows: list[tuple[Any, ...]] = []
        if original:
            observed_rows = connection.execute(
                """select l.id,l.card_id,l.estado,l.carta_versao,l.carta_fingerprint,
                          l.build_otimizador_id,l.build_bonificador_id,
                          encode(extensions.digest(coalesce(q.otim,'null'::jsonb)::text,'sha256'),'hex'),
                          q.otim,q.bonus,o.carta_fingerprint,b.carta_fingerprint
                   from clube_novo.build_linha_card l
                   cross join lateral (
                     select public.otimizador_carta_sem_completude_v2(l.card_id) otim,
                            public.bonificador_carta_sem_completude_v1(l.card_id) bonus
                   ) q
                   left join clube_novo.build_otimizador o on o.id=l.build_otimizador_id
                   left join clube_novo.build_bonificador b on b.id=l.build_bonificador_id
                   where l.id=any(%s::bigint[]) order by l.id""",
                (sorted(original),),
            ).fetchall()
        observed = {int(row[0]): list(row) for row in observed_rows}
        if set(observed) != set(original):
            raise MotorProtectionError(f"{stage}: o conjunto de resultados existentes mudou")
        invalidated = set(preview["invalidated_ids"])
        preserved = set(preview["preserved_ids"])
        unaffected = set(preview["unaffected_ids"])
        if invalidated | preserved | unaffected != set(original) or (
            invalidated & preserved or invalidated & unaffected or preserved & unaffected
        ):
            raise MotorProtectionError(f"{stage}: a partição dos resultados da prévia é inválida")
        for result_id in invalidated:
            if observed[result_id][2] != "invalida":
                raise MotorProtectionError(f"{stage}: um resultado previsto para refazer continuou ativo")
        for result_id in preserved | unaffected:
            if observed[result_id] != original[result_id]:
                raise MotorProtectionError(f"{stage}: um resultado que deveria permanecer igual foi alterado")
        active_after = {
            int(row[0])
            for row in connection.execute(
                "select id from clube_novo.build_linha_card where estado<>'invalida' order by id"
            ).fetchall()
        }
        if active_after != (set(original) - invalidated):
            raise MotorProtectionError(f"{stage}: o conjunto ativo não é o confirmado na prévia")
        return active_after

    def install(
        self,
        connection: Any,
        package: ValidatedPackage,
        preview: dict[str, Any],
        scripts: dict[str, dict[str, str]],
    ) -> dict[str, Any]:
        connection.execute("set local lock_timeout='20s'")
        connection.execute("set local statement_timeout='45min'")
        connection.execute(
            "select pg_advisory_xact_lock(hashtextextended('clubef-protecao-motores-v1',0))"
        )
        locked_tables = self._freeze_clube_novo(connection)
        current = self.preview(connection, package, require_read_only=False)
        if current.get("confirmation_sha256") != preview.get("confirmation_sha256"):
            raise MotorProtectionError(
                "o banco mudou depois da prévia mostrada; nada foi aplicado e uma nova confirmação é obrigatória"
            )
        operation_mode = str(preview["operation_mode"])
        if operation_mode == "initial_install":
            if set(scripts) != {"completude", "writer_bonificador"}:
                raise MotorProtectionError("os dois scripts composáveis pinados são obrigatórios na instalação inicial")
            connection.execute(scripts["completude"]["sql"])
            connection.execute(scripts["writer_bonificador"]["sql"])
        elif operation_mode == "incremental_update":
            if scripts:
                raise MotorProtectionError("uma atualização incremental não pode repetir DDL de instalação")
        else:
            raise MotorProtectionError("não há cartas alteradas para registrar nesta transação")

        seal = package.manifest["contract_seal"]
        source_manifest = {
            "schema": "clubef-fontes-seed-protecao-motores-v1",
            "fontes": {
                name: {"sha256": item["sha256"]}
                for name, item in package.manifest["fontes"].items()
            },
            "arquivos_fisicos_sha256": package.manifest.get("arquivos_fisicos_sha256") or {},
        }
        binding = package.manifest.get("vinculo_instalador") or {}
        key_hash = binding.get("idempotency_key_sha256")
        if not isinstance(key_hash, str) or not _SHA256.fullmatch(key_hash):
            raise MotorProtectionError("manifesto sem chave idempotente válida")
        idempotency_key = "motor-protection-seed:" + key_hash
        staged = connection.execute(
            """select execucao_id,estado
               from clube_novo.estagiar_execucao_leitura_contrato(
                 %s,%s,%s,%s,%s,%s,%s::jsonb)""",
            (
                idempotency_key,
                seal["contrato_id"],
                seal["versao_jogo"],
                seal["fingerprint_contrato_sha256"],
                seal["fingerprint_fontes_sha256"],
                package.package_sha256,
                json.dumps(source_manifest, ensure_ascii=False),
            ),
        ).fetchone()
        if not staged or staged[0] is None or staged[1] != "aceito":
            raise MotorProtectionError("o banco não criou a execução aceita para o seed")
        execution_id = int(staged[0])
        coverage = {
            "regra": RULE_VERSION,
            "componentes_obrigatorios": list(REQUIRED_COMPONENTS),
            "cartas": package.count,
            "publicacao_independente": True,
        }
        audit = {
            "schema": "clubef-auditoria-instalacao-protecao-motores-v1",
            "manifest_payload_sha256": package.manifest["manifest_payload_sha256"],
            "seed_sha256": package.package_sha256,
            "scripts": {
                name: {"path": item["path"], "sha256": item["sha256"]}
                for name, item in scripts.items()
            },
            "operation_mode": operation_mode,
            "locked_clube_novo_tables": locked_tables,
            "preview": {
                "confirmation_sha256": preview["confirmation_sha256"],
                "database_state_sha256": preview["database_state_sha256"],
                "changed_card_ids_sha256": preview["changed_card_ids_sha256"],
                "results_to_invalidate": preview["results_to_invalidate"],
                "invalidated_ids_sha256": preview["invalidated_ids_sha256"],
            },
        }
        application = connection.execute(
            """insert into clube_novo.aplicacao_pacote_revisao_extrator
               (idempotency_key,execucao_id,contrato_id,pacote_sha256,selo_contrato,
                manifesto_fontes,cobertura_familias,auditoria_familias,estado)
               values (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,'aplicado')
               returning aplicacao_id""",
            (
                idempotency_key,
                execution_id,
                seal["contrato_id"],
                package.package_sha256,
                json.dumps(seal, ensure_ascii=False),
                json.dumps(source_manifest, ensure_ascii=False),
                json.dumps(coverage, ensure_ascii=False),
                json.dumps(audit, ensure_ascii=False),
            ),
        ).fetchone()
        if not application or application[0] is None:
            raise MotorProtectionError("o banco não retornou o application_id auditado")
        application_id = int(application[0])

        connection.execute(
            """create temporary table clubef_seed_completude_motor (
                 ordinal bigint primary key,
                 card_id text not null unique,
                 componentes jsonb not null
               ) on commit drop"""
        )
        digest = hashlib.sha256()
        copied = 0
        stream_ordinal = 0
        changed_set = set(preview["changed_card_ids"])
        with connection.cursor() as cursor:
            with cursor.copy(
                "copy pg_temp.clubef_seed_completude_motor (ordinal,card_id,componentes) from stdin"
            ) as copy:
                for stream_ordinal, (raw, envelope) in enumerate(_iter_seed(package.seed_path), start=1):
                    digest.update(raw)
                    card_id, _evidence = _validate_envelope(envelope)
                    if card_id in changed_set:
                        copied += 1
                        copy.write_row((stream_ordinal, card_id, self.Jsonb(envelope["componentes"])))
        if stream_ordinal != package.count or copied != preview["cards_to_register"] or digest.hexdigest() != package.package_sha256:
            raise MotorProtectionError("o NDJSON mudou durante a carga; toda a transação será desfeita")
        copied_readback = connection.execute(
            """select count(*),count(distinct card_id)
               from pg_temp.clubef_seed_completude_motor"""
        ).fetchone()
        if copied_readback != (preview["cards_to_register"], preview["cards_to_register"]):
            raise MotorProtectionError("readback da tabela temporária do seed diverge")

        registered = connection.execute(
            """select count(clube_novo.registrar_completude_motor_v1(
                 card_id,%s,componentes))
               from pg_temp.clubef_seed_completude_motor""",
            (application_id,),
        ).fetchone()
        if not registered or int(registered[0]) != preview["cards_to_register"]:
            raise MotorProtectionError("nem todas as cartas foram registradas pela função protegida")

        counts = connection.execute(
            """select
                 (select count(*) from clube_novo.carta_completude_motor_versao where vigente),
                 (select count(*) from clube_novo.carta_completude_motor_componente c
                    join clube_novo.carta_completude_motor_versao v using(versao_id) where v.vigente),
                 (select count(*) from clube_novo.carta_jogo j left join clube_novo.carta_completude_motor_versao v
                    on v.card_id=j.card_id and v.vigente where v.versao_id is null),
                 (select count(*) from clube_novo.carta_completude_motor_versao v
                    left join clube_novo.carta_completude_motor_componente c using(versao_id)
                    where v.vigente group by v.versao_id having count(c.*)<>11 limit 1),
                 (select count(*) from clube_novo.build_linha_card where id=any(%s) and estado='invalida'),
                 (select pacote_sha256 from clube_novo.aplicacao_pacote_revisao_extrator where aplicacao_id=%s),
                 (select to_regprocedure('public.gravar_build_bonificador_v1(jsonb)') is not null),
                 (select count(*) from clube_novo.carta_completude_motor_versao v
                    where v.vigente and v.input_fingerprint_sha256 is distinct from
                      encode(extensions.digest(clube_novo.carta_input_motor_canonico_v1(v.card_id)::text,'sha256'),'hex'))""",
            (preview["invalidated_ids"], application_id),
        ).fetchone()
        expected_counts = (
            package.count,
            package.count * len(REQUIRED_COMPONENTS),
            0,
            None,
            preview["results_to_invalidate"],
            package.package_sha256,
            True,
            0,
        )
        if counts != expected_counts:
            raise MotorProtectionError("readback anterior ao commit divergiu; toda a transação será desfeita")
        state_after, state_detail = self._protection_state(connection)
        if state_after != "ja_instalada":
            raise MotorProtectionError("os objetos instalados não passaram o readback integral antes do commit")
        active_after = self._verify_result_transition(
            connection,
            preview,
            stage="readback anterior ao COMMIT",
        )
        return {
            "execution_id": execution_id,
            "application_id": application_id,
            "idempotency_key": idempotency_key,
            "operation_mode": operation_mode,
            "cards_registered": preview["cards_to_register"],
            "database_cards": package.count,
            "components": package.count * len(REQUIRED_COMPONENTS),
            "results_invalidated": preview["results_to_invalidate"],
            "results_preserved_as_identical_history": preview["results_preserved_as_identical_history"],
            "seed_sha256": package.package_sha256,
            "scripts": audit["scripts"],
            "protection_state_readback": state_detail,
            "precommit_result_readback": True,
            "precommit_active_result_ids_sha256": _sha256_value(sorted(active_after)),
        }

    def independent_readback(
        self,
        connection: Any,
        package: ValidatedPackage,
        installed: dict[str, Any],
        preview: dict[str, Any],
    ) -> dict[str, Any]:
        mode = connection.execute("show transaction_read_only").fetchone()
        if not mode or str(mode[0]).lower() != "on":
            raise MotorProtectionError("a conferência por nova conexão não ficou somente leitura")
        state, state_detail = self._protection_state(connection)
        if state != "ja_instalada":
            raise MotorProtectionError("a leitura independente encontrou proteção parcial ou divergente")
        versions = self._installed_versions(connection)
        if set(versions) != package.card_ids:
            raise MotorProtectionError("o conjunto vigente de cartas divergiu do seed")
        seal_contract_id = str(package.manifest["contract_seal"]["contrato_id"])
        for card_id in sorted(package.card_ids):
            row = versions[card_id]
            components = self._db_components(row[6])
            if (
                row[1] is None
                or row[2] != RULE_VERSION
                or str(row[3]) != seal_contract_id
                or row[4] != row[5]
                or len(components) != len(REQUIRED_COMPONENTS)
                or _sha256_value(_semantic_component_payload(components))
                    != package.card_evidence[card_id].semantic_coverage_sha256
            ):
                raise MotorProtectionError(f"readback de completude divergiu para a carta {card_id}")

        application = connection.execute(
            """select a.execucao_id,a.contrato_id,a.pacote_sha256,a.selo_contrato,
                      a.manifesto_fontes,a.cobertura_familias,a.auditoria_familias,a.estado,e.estado
               from clube_novo.aplicacao_pacote_revisao_extrator a
               join clube_novo.execucao_leitura_contrato e using(execucao_id)
               where a.aplicacao_id=%s and a.idempotency_key=%s""",
            (installed["application_id"], installed["idempotency_key"]),
        ).fetchone()
        if not application or (
            int(application[0]) != installed["execution_id"]
            or str(application[1]) != seal_contract_id
            or application[2] != package.package_sha256
            or application[7] != "aplicado"
            or application[8] != "aceito"
        ):
            raise MotorProtectionError("a auditoria da execução/aplicação não confere")
        expected_sources = {
            "schema": "clubef-fontes-seed-protecao-motores-v1",
            "fontes": {
                name: {"sha256": item["sha256"]}
                for name, item in package.manifest["fontes"].items()
            },
            "arquivos_fisicos_sha256": package.manifest.get("arquivos_fisicos_sha256") or {},
        }
        expected_coverage = {
            "regra": RULE_VERSION,
            "componentes_obrigatorios": list(REQUIRED_COMPONENTS),
            "cartas": package.count,
            "publicacao_independente": True,
        }
        if (
            _json_object(application[3]) != package.manifest["contract_seal"]
            or _json_object(application[4]) != expected_sources
            or _json_object(application[5]) != expected_coverage
        ):
            raise MotorProtectionError("selo, fontes ou cobertura auditada divergiram")
        audit = _json_object(application[6])
        if (
            audit.get("manifest_payload_sha256") != package.manifest["manifest_payload_sha256"]
            or audit.get("seed_sha256") != package.package_sha256
            or
            audit.get("operation_mode") != installed["operation_mode"]
            or (audit.get("preview") or {}).get("confirmation_sha256") != preview["confirmation_sha256"]
            or (audit.get("scripts") or {}) != installed["scripts"]
        ):
            raise MotorProtectionError("hashes pinados ou prévia auditada divergiram")

        active_after = self._verify_result_transition(
            connection,
            preview,
            stage="readback independente depois do COMMIT",
        )
        invalidated = set(preview["invalidated_ids"])
        preserved = set(preview["preserved_ids"])
        unaffected = set(preview["unaffected_ids"])
        return {
            "transaction_read_only": True,
            "new_connection": True,
            "application_id": installed["application_id"],
            "cards": package.count,
            "components": package.count * len(REQUIRED_COMPONENTS),
            "results_invalidated": len(invalidated),
            "results_preserved": len(preserved),
            "results_unaffected": len(unaffected),
            "active_result_ids_sha256": _sha256_value(sorted(active_after)),
            "package_sha256": package.package_sha256,
            "application_state": "aplicado",
            "execution_state": "aceito",
            "protection_state": state_detail,
        }

    def recover_commit_status(self, connection: Any, installed: dict[str, Any]) -> str:
        connection.execute("set local lock_timeout='30s'")
        connection.execute(
            "select pg_advisory_xact_lock(hashtextextended('clubef-protecao-motores-v1',0))"
        )
        row = connection.execute(
            """select aplicacao_id,execucao_id,estado
               from clube_novo.aplicacao_pacote_revisao_extrator
               where idempotency_key=%s""",
            (installed["idempotency_key"],),
        ).fetchone()
        if row is None:
            return "rolled_back_confirmed"
        if (
            int(row[0]) == installed["application_id"]
            and int(row[1]) == installed["execution_id"]
            and row[2] == "aplicado"
        ):
            return "committed_candidate"
        return "commit_status_unknown"


def _public_preview(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in preview.items()
        if key not in {
            "invalidated_ids",
            "preserved_ids",
            "unaffected_ids",
            "changed_card_ids",
            "active_rows_snapshot",
            "protection_objects",
        }
    }


def preview_motor_protection(
    root: Path,
    run_dir: Path,
    manifest_path: Path,
    current_contract: dict[str, Any],
    dsn: str,
    *,
    backend: Any | None = None,
    expected_card_count: int | None = None,
) -> dict[str, Any]:
    package = validate_package(
        root, run_dir, manifest_path, expected_card_count=expected_card_count
    )
    assert_current_contract(package, current_contract)
    active_backend = backend or PostgresBackend(dsn)
    connection = active_backend.open(read_only=True)
    try:
        preview = active_backend.preview(connection, package, require_read_only=True)
        connection.rollback()
    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        connection.close()
    public_preview = _public_preview(preview)
    already_current = public_preview["operation_mode"] == "already_up_to_date"
    report = {
        "schema": "clubef-previa-instalacao-protecao-motores-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": "already_up_to_date" if already_current else "ready_for_explicit_install_or_update",
        "database_write": False,
        "transaction_read_only": True,
        "automatic_install": False,
        "publication_blocked": False,
        "what_it_means": "As cartas foram conferidas para proteger somente o Otimizador e o Bonificador.",
        "what_happens_to_today_data": (
            f"{public_preview['results_to_invalidate']} resultado(s) atual(is) de teste serão marcados como inválidos para refazer."
        ),
        "what_operator_should_do": (
            "Nada: a proteção já corresponde a todas as cartas conferidas e nenhuma escrita é necessária."
            if already_current
            else "Confirme instalar/atualizar somente se quiser registrar agora esta proteção; publicar cartas continua independente."
        ),
        "manifest": str(package.manifest_path),
        "seed_sha256": package.package_sha256,
        "cards": package.count,
        "confirmation_sha256": preview["confirmation_sha256"],
        "preview": public_preview,
    }
    report_path = run_dir / "previa-protecao-motores.json"
    _atomic_json(report_path, report)
    report["report_path"] = str(report_path)
    return report


def install_motor_protection(
    root: Path,
    run_dir: Path,
    manifest_path: Path,
    current_contract: dict[str, Any],
    dsn: str,
    *,
    confirmed_preview_sha256: str,
    backend: Any | None = None,
    expected_card_count: int | None = None,
    write_enabled: bool | None = None,
) -> dict[str, Any]:
    enabled = os.environ.get("CLUBEF_ENABLE_REAL_WRITE") == "1" if write_enabled is None else write_enabled
    if not enabled:
        raise MotorProtectionError(
            "instalação/atualização produtiva bloqueada: use somente o botão dedicado"
        )
    if not isinstance(confirmed_preview_sha256, str) or not _SHA256.fullmatch(confirmed_preview_sha256):
        raise MotorProtectionError("a confirmação exibida ao operador não foi vinculada à instalação")
    package = validate_package(
        root, run_dir, manifest_path, expected_card_count=expected_card_count
    )
    assert_current_contract(package, current_contract)
    active_backend = backend or PostgresBackend(dsn)

    preview_connection = active_backend.open(read_only=True)
    try:
        preview = active_backend.preview(preview_connection, package, require_read_only=True)
        preview_connection.rollback()
    except Exception:
        try:
            preview_connection.rollback()
        except Exception:
            pass
        raise
    finally:
        preview_connection.close()

    if preview["confirmation_sha256"] != confirmed_preview_sha256:
        raise MotorProtectionError(
            "o banco ou o seed mudou desde a tela de confirmação; faça uma nova prévia"
        )
    if preview["operation_mode"] == "already_up_to_date":
        report = {
            "schema": "clubef-instalacao-protecao-motores-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "state": "already_up_to_date",
            "database_write": False,
            "automatic_install": False,
            "publication_blocked": False,
            "confirmation_sha256": confirmed_preview_sha256,
            "preview": _public_preview(preview),
        }
        report_path = run_dir / "instalacao-protecao-motores.json"
        _atomic_json(report_path, report)
        report["report_path"] = str(report_path)
        return report

    scripts = load_install_scripts(root) if preview["operation_mode"] == "initial_install" else {}

    write_connection = active_backend.open(read_only=False)
    try:
        installed = active_backend.install(write_connection, package, preview, scripts)
    except Exception:
        try:
            write_connection.rollback()
        finally:
            write_connection.close()
        raise
    commit_status = "committed"
    try:
        write_connection.commit()
    except Exception as commit_error:
        commit_status = "commit_status_unknown"
        try:
            write_connection.close()
        except Exception:
            pass
        try:
            recovery_connection = active_backend.open(read_only=False)
            try:
                commit_status = active_backend.recover_commit_status(recovery_connection, installed)
                recovery_connection.rollback()
            finally:
                recovery_connection.close()
        except Exception:
            commit_status = "commit_status_unknown"
        if commit_status == "rolled_back_confirmed":
            failure = {
                "schema": "clubef-instalacao-protecao-motores-v1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "state": "rolled_back_confirmed_after_commit_error",
                "database_write": False,
                "publication_blocked": False,
                "confirmation_sha256": confirmed_preview_sha256,
                "message": "A confirmação do banco falhou, mas uma nova conexão comprovou o rollback integral."
            }
            _atomic_json(run_dir / "instalacao-protecao-motores.json", failure)
            raise MotorProtectionCommitStatusError(
                "o banco confirmou que nada foi gravado; faça uma nova prévia antes de tentar novamente",
                commit_status="rolled_back_confirmed",
                database_write=False,
            ) from commit_error
        if commit_status != "committed_candidate":
            failure = {
                "schema": "clubef-instalacao-protecao-motores-v1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "state": "commit_status_unknown",
                "database_write_confirmed": None,
                "may_have_written": True,
                "publication_blocked": False,
                "confirmation_sha256": confirmed_preview_sha256,
                "application_id": installed.get("application_id"),
                "message": "Não foi possível provar se o COMMIT confirmou. Não tente novamente sem auditoria."
            }
            _atomic_json(run_dir / "instalacao-protecao-motores.json", failure)
            raise MotorProtectionCommitStatusError(
                failure["message"], commit_status="commit_status_unknown", database_write=True
            ) from commit_error
    else:
        write_connection.close()

    verify_connection = active_backend.open(read_only=True)
    try:
        independent = active_backend.independent_readback(
            verify_connection, package, installed, preview
        )
        verify_connection.rollback()
    except Exception as readback_error:
        try:
            verify_connection.rollback()
        except Exception:
            pass
        state = (
            "commit_status_unknown"
            if commit_status == "committed_candidate"
            else "committed_readback_failed"
        )
        failure = {
            "schema": "clubef-instalacao-protecao-motores-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "state": state,
            "database_write": True,
            "may_have_written": True,
            "publication_blocked": False,
            "seed_sha256": package.package_sha256,
            "application_id": installed.get("application_id"),
            "message": (
                "A aplicação foi encontrada depois de uma resposta incerta do COMMIT, mas o readback integral falhou. Não tente novamente sem auditoria."
                if commit_status == "committed_candidate"
                else "A transação confirmou, mas a nova conexão não confirmou o readback integral. Não tente novamente sem auditoria."
            ),
        }
        _atomic_json(run_dir / "instalacao-protecao-motores.json", failure)
        raise MotorProtectionCommitStatusError(
            failure["message"], commit_status=state, database_write=True
        ) from readback_error
    finally:
        verify_connection.close()

    recovered_commit = commit_status == "committed_candidate"
    report = {
        "schema": "clubef-instalacao-protecao-motores-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": (
            "committed_verified_after_uncertain_commit"
            if recovered_commit
            else "installed_or_updated_and_independently_verified"
        ),
        "database_write": True,
        "automatic_install": False,
        "separate_from_data_package_apply": True,
        "single_transaction": True,
        "rollback_on_precommit_failure": True,
        "publication_blocked": False,
        "confirmation_sha256": confirmed_preview_sha256,
        "commit_status": "committed_verified" if recovered_commit else "committed",
        "installed": installed,
        "independent_readback": independent,
    }
    report_path = run_dir / "instalacao-protecao-motores.json"
    _atomic_json(report_path, report)
    report["report_path"] = str(report_path)
    return report
