"""Testes estáticos offline do pacote de completude dos motores V1.

Não abre jogo, não acessa Supabase e não aplica SQL.
"""

from __future__ import annotations

import re
from pathlib import Path


BASE = Path(__file__).resolve().parent
FILES = {
    "apply": BASE / "APLICAR-COMPLETUDE-MOTORES-CARTA-V1.sql",
    "apply_composable": BASE / "APLICAR-COMPLETUDE-MOTORES-CARTA-V1-COMPOSAVEL.sql",
    "rollback": BASE / "ROLLBACK-COMPLETUDE-MOTORES-CARTA-V1.sql",
    "validate": BASE / "VALIDAR-COMPLETUDE-MOTORES-CARTA-V1.sql",
    "contract": BASE / "CONTRATO-MATERIALIZACAO-COMPLETUDE-MOTORES-V1.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def balanced_dollar_tags(sql: str, label: str) -> None:
    tags = re.findall(r"\$[a-zA-Z_][a-zA-Z0-9_]*\$", sql)
    for tag in sorted(set(tags)):
        require(tags.count(tag) % 2 == 0, f"{label}: delimitador {tag} sem par")


def main() -> None:
    for label, path in FILES.items():
        require(path.is_file(), f"arquivo ausente: {label}: {path}")

    apply = FILES["apply"].read_text(encoding="utf-8")
    apply_composable = FILES["apply_composable"].read_text(encoding="utf-8")
    rollback = FILES["rollback"].read_text(encoding="utf-8")
    validate = FILES["validate"].read_text(encoding="utf-8")
    contract = FILES["contract"].read_text(encoding="utf-8")
    lower_apply = apply.lower()

    require(re.search(r"^begin;", apply, re.MULTILINE), "migração sem BEGIN")
    require(re.search(r"^commit;\s*$", apply, re.MULTILINE), "migração sem COMMIT")
    expected_composable = apply.replace("\nbegin;\n\n", "\n", 1)
    require(expected_composable.endswith("\n\ncommit;\n"),
            "migração oficial não termina no COMMIT externo esperado")
    expected_composable = expected_composable[:-len("\n\ncommit;\n")] + "\n"
    require(apply_composable == expected_composable,
            "variante composável diverge do corpo oficial além de BEGIN/COMMIT")
    require(not re.search(r"^(?:begin|commit|rollback);\s*$", apply_composable,
                          re.MULTILINE | re.IGNORECASE),
            "variante composável contém controle transacional externo")
    require(re.search(r"^begin;", rollback, re.MULTILINE), "rollback sem BEGIN")
    require(re.search(r"^commit;\s*$", rollback, re.MULTILINE), "rollback sem COMMIT")
    require("begin transaction isolation level repeatable read read only;" in validate.lower(),
            "validação não é READ ONLY")
    require(re.search(r"^rollback;\s*$", validate, re.MULTILINE),
            "validação não encerra com ROLLBACK")
    balanced_dollar_tags(apply, "apply")
    balanced_dollar_tags(apply_composable, "apply_composable")
    balanced_dollar_tags(rollback, "rollback")
    balanced_dollar_tags(validate, "validate")

    for state in (
        "conferido_com_valor",
        "conferido_sem_valor",
        "nao_conferido",
        "leitura_com_problema",
    ):
        require(state in apply, f"estado de coleta ausente: {state}")
    for state in (
        "resolvido",
        "pendencia_conhecida",
        "nao_resolvido",
        "nao_aplicavel",
        "orfao_catalogo_atual",
    ):
        require(state in apply, f"estado de resolução ausente: {state}")

    for column in (
        "estado_coleta",
        "estado_resolucao",
        "apto_motor",
        "missing_inputs",
        "pendencias_resolucao",
        "motivos_bloqueio_motor",
        "input_fingerprint_sha256",
        "cobertura_fingerprint_sha256",
        "completude_fingerprint_sha256",
        "fingerprint_entrada_legado_sha256",
    ):
        require(column in apply, f"coluna/contrato ausente: {column}")

    components = (
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
    registration = apply.split("create function clube_novo.registrar_completude_motor_v1", 1)[1]
    registration = registration.split("revoke all on function clube_novo.registrar_completude_motor_v1", 1)[0]
    for component in components:
        require(f"'{component}'" in registration, f"registrador sem componente {component}")
    require("from jsonb_array_elements(p_componentes) x\n    where x->>'estado_coleta' not in" in registration,
            "missing_inputs não deriva exclusivamente do estado de coleta")
    require("v_qty is distinct from 0" in registration and "sem valor exige zero explícito" in registration,
            "vazio conferido não está modelado explicitamente")

    require("carta_completude_motor_decisao" in apply,
            "decisão manual não foi separada da coleta")
    require("evidencia.decisao_motor" in apply,
            "pendência não bloqueante não exige decisão auditável")
    require("v_orphan_current" in apply and "'clube_bloqueado','liga_bloqueada'" in apply,
            "órfão de catálogo atual não tem tratamento não bloqueante explícito")

    require("planejar_completude_motor_v1" in apply,
            "planejamento incremental ausente")
    for action in ("materializar", "revisao_manual", "nenhuma"):
        require(f"'{action}'" in apply, f"planejador sem ação {action}")
    require("prepared_not_enabled" in contract,
            "contrato não mantém worker desabilitado antes da migração/seed")
    require("Seed inicial" in contract and "Rodadas seguintes" in contract,
            "contrato não explica seed único e incremento diário")

    require("from clube.fila" not in lower_apply and "join clube.fila" not in lower_apply,
            "migração reativou a fila histórica clube.fila")
    require("fila v1 desativada" in lower_apply,
            "dependência da fila V1 não falha fechada")
    require("migracao_gravar_bonus_grant_snapshot_v1" in apply,
            "grants atuais de gravar_bonus não são fotografados")
    require("aclexplode(coalesce(p.proacl,acldefault('f',p.proowner)))" in apply,
            "snapshot de gravar_bonus não cobre ACL padrão/proprietário")
    require("rename to gravar_bonus_sem_completude_v1" in lower_apply,
            "implementação legada gravar_bonus não foi preservada")
    require("gravar_bonus bloqueada:" in lower_apply and "nenhuma linha foi gravada" in lower_apply,
            "nome gravar_bonus não falha fechado com mensagem explícita")
    require("revoke all privileges on function public.gravar_bonus(jsonb) from service_role" in lower_apply,
            "service_role ainda pode receber EXECUTE em gravar_bonus")
    blocker = apply.split("create function public.gravar_bonus(p_linhas jsonb)", 1)[1]
    blocker = blocker.split("$blocked$", 2)[1]
    require("gravar_bonus_sem_completude_v1" not in blocker,
            "bloqueador redireciona silenciosamente à implementação legada")
    require("cm.vigente and cm.apto_motor" in apply,
            "fila do Bonificador não filtra completude vigente/apta")
    require("'contrato_versao','bonificador-regua-v1+bonificador-carta-v1'" in apply,
            "contrato da carta não expõe a mesma versão usada pelo writer do Bonificador")
    require("create trigger build_linha_completude_motor_v1" in apply,
            "gate universal de build_linha_card ausente")
    require("new.build_otimizador_id is not null" in apply,
            "conclusão do Otimizador sem segundo gate")
    require("new.build_bonificador_id is not null" in apply,
            "conclusão do Bonificador sem segundo gate")

    invalidation_triggers = re.findall(
        r"create trigger (carta_[a-z_]+_invalidar_completude_motor_v1)", apply
    )
    require(len(set(invalidation_triggers)) == 10,
            f"esperados 10 triggers de insumo; encontrados {len(set(invalidation_triggers))}")
    require("after insert or delete or update of" in lower_apply,
            "trigger da carta não é AFTER")
    require("before insert or delete or update of" not in lower_apply,
            "inserção de carta seria bloqueada")

    forbidden_dml = re.findall(
        r"\b(?:insert\s+into|update|delete\s+from)\s+"
        r"(?:clube_novo\.)?(?:carta_jogo|box|carta_box|home|publicacao_carta)\b",
        lower_apply,
    )
    require(not forbidden_dml, f"DML indevido de publicação/carta: {forbidden_dml}")
    require("não controla inserção, home, box nem publicação" in lower_apply,
            "independência da publicação não está declarada")

    for function in (
        "otimizador_carta_v2",
        "otimizador_proxima_fila_v1",
        "bonificador_carta_v1",
        "bonificador_pares_v1",
    ):
        require(f"rename to {function}" in rollback,
                f"rollback não restaura {function}")
    require("rollback recusado" in rollback and "mudaram" in rollback,
            "rollback não se recusa a sobrescrever trabalho posterior")
    require("restaurar_grants_gravar_bonus" in rollback,
            "rollback não restaura grants de gravar_bonus")
    require("grant %s on function public.gravar_bonus(jsonb)" in rollback,
            "rollback não recompõe grants capturados")
    require(rollback.count("except") >= 2 and
            "grants de gravar_bonus não voltaram exatamente" in rollback,
            "rollback não compara readback bidirecional dos grants")

    require("NÃO HABILITAR MOTORES" in validate,
            "validação não possui gate operacional explícito")
    require("q.n<>11" in validate,
            "validação não confere todos os componentes")
    require("input_fingerprint_sha256 is distinct from" in validate,
            "validação não refaz o fingerprint do input")
    require("NÃO HABILITAR BONIFICADOR" in validate,
            "validação não prova fechamento do bypass gravar_bonus")
    require("has_function_privilege('service_role','public.gravar_bonus(jsonb)','EXECUTE')" in validate,
            "validação não testa EXECUTE de service_role")
    require("Fechamento do escritor legado do Bonificador" in contract,
            "contrato não explica o bloqueio sem redirecionamento")

    print("OK: pacote V1 consistente em testes estáticos offline")
    print("OK: coleta, resolução e aptidão permanecem separadas")
    print("OK: fila/conclusão protegidas; publicação da carta independente")
    print("OK: gravar_bonus legado sem EXECUTE, sem redirecionamento e com rollback de grants")
    print("OK: seed incremental, decisão manual, rollback e readback presentes")


if __name__ == "__main__":
    main()
