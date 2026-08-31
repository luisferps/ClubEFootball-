from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[3]
SQL = Path(__file__).resolve().parent
APPLY = SQL / "APLICAR-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1.sql"
ROLLBACK = SQL / "ROLLBACK-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1.sql"
VALIDATE = SQL / "VALIDAR-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1.sql"
APPLY_COMPOSABLE = SQL / "APLICAR-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1-COMPOSAVEL.sql"
ROLLBACK_COMPOSABLE = SQL / "ROLLBACK-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1-COMPOSAVEL.sql"
CONTRACT = SQL / "CONTRATO-ESCRITOR-TRANSACIONAL-BONIFICADOR-V1.md"
LEGACY = ROOT / "2-MOTORES" / "BONIFICADOR" / "motor_bonus.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def strip_sql(text: str) -> str:
    text = re.sub(r"--[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return text


def static_parse(text: str, name: str, require_transaction: bool = True) -> None:
    """Parser estrutural offline: blocos dollar-quote e parenteses balanceados."""
    clean = strip_sql(text)
    tags = re.findall(r"\$[A-Za-z_][A-Za-z_0-9]*\$|\$\$", clean)
    stack: list[str] = []
    for tag in tags:
        if stack and stack[-1] == tag:
            stack.pop()
        else:
            stack.append(tag)
    require(not stack, f"{name}: dollar-quote sem fechamento: {stack}")

    outside = clean
    for tag in sorted(set(tags), key=len, reverse=True):
        outside = re.sub(re.escape(tag) + r".*?" + re.escape(tag), "", outside, flags=re.S)
    depth = 0
    in_string = False
    i = 0
    while i < len(outside):
        char = outside[i]
        if char == "'":
            if in_string and i + 1 < len(outside) and outside[i + 1] == "'":
                i += 2
                continue
            in_string = not in_string
        elif not in_string and char == "(":
            depth += 1
        elif not in_string and char == ")":
            depth -= 1
            require(depth >= 0, f"{name}: parenteses fechou antes de abrir")
        i += 1
    require(not in_string, f"{name}: string SQL sem fechamento")
    require(depth == 0, f"{name}: parenteses desbalanceados: {depth}")
    if require_transaction:
        require(re.search(r"\bbegin(?:\s+transaction(?:\s+read\s+only)?)?\s*;", clean, re.I),
                f"{name}: sem transacao")
        require(re.search(r"\b(commit|rollback)\s*;", clean, re.I), f"{name}: sem fechamento")


def without_outer_transaction(text: str) -> str:
    result = re.sub(r"(?im)^begin;\s*\n", "", text, count=1)
    result = re.sub(r"(?im)\n(?:commit|rollback);\s*$", "\n", result, count=1)
    return result


def main() -> None:
    for path in (APPLY, ROLLBACK, VALIDATE, APPLY_COMPOSABLE,
                 ROLLBACK_COMPOSABLE, CONTRACT, LEGACY):
        require(path.exists(), f"arquivo ausente: {path}")

    apply = APPLY.read_text(encoding="utf-8")
    rollback = ROLLBACK.read_text(encoding="utf-8")
    validate = VALIDATE.read_text(encoding="utf-8")
    apply_composable = APPLY_COMPOSABLE.read_text(encoding="utf-8")
    rollback_composable = ROLLBACK_COMPOSABLE.read_text(encoding="utf-8")
    legacy_before = subprocess.check_output(
        ["git", "hash-object", str(LEGACY)], cwd=ROOT, text=True
    ).strip()

    for name, text in (("apply", apply), ("rollback", rollback), ("validate", validate)):
        static_parse(text, name)
    static_parse(apply_composable, "apply_composable", require_transaction=False)
    static_parse(rollback_composable, "rollback_composable", require_transaction=False)
    apply_header = (
        "-- CORPO COMPOSAVEL: executar somente dentro de uma transacao externa explicita.\n"
        "-- O conteudo e verificado contra o APPLY standalone pelo teste offline.\n"
    )
    rollback_header = (
        "-- CORPO COMPOSAVEL: executar somente dentro de uma transacao externa explicita.\n"
        "-- O conteudo e verificado contra o ROLLBACK standalone pelo teste offline.\n"
    )
    require(apply_composable.rstrip() ==
            (apply_header + without_outer_transaction(apply)).rstrip(),
            "APPLY composavel diverge do standalone")
    require(rollback_composable.rstrip() ==
            (rollback_header + without_outer_transaction(rollback)).rstrip(),
            "ROLLBACK composavel diverge do standalone")
    require(not re.search(r"(?im)^(begin|commit|rollback)(?:\s+transaction.*?)?;\s*$",
                          strip_sql(apply_composable)),
            "APPLY composavel contem controle transacional")
    require(not re.search(r"(?im)^(begin|commit|rollback)(?:\s+transaction.*?)?;\s*$",
                          strip_sql(rollback_composable)),
            "ROLLBACK composavel contem controle transacional")

    lower = apply.lower()
    body = lower.split(
        "create function public.gravar_build_bonificador_v1(p_resultado jsonb)", 1
    )[1]
    body = body.split("$function$;", 1)[0]
    require("security definer" in body, "writer nao e SECURITY DEFINER")
    require("set search_path = ''" in body, "writer sem search_path fechado")
    require("for update" in body and "for share" in body, "locks de concorrencia ausentes")
    require("carta_completude_motor_versao" in body, "gate de completude ausente")
    require("vigente and apto_motor" in body, "vigencia/apto nao exigidos")
    require("public.bonificador_carta_v1" in body, "segunda conferencia do gate ausente")
    require("public.bonificador_regua_v1" in body, "regua atual nao e reconferida")
    require("extensions.digest" in body, "fingerprint nao e derivado no banco")
    require("selos do contrato/formula ficaram obsoletos" in body,
            "writer aceita selos de contrato/formula enviados sem readback")
    require("bonus_outros ainda nao possui contrato de soma" in body,
            "bonus_outros sem semantica foi aceito")
    require("soma do detalhe fisico diverge de bonus_fisico_total" in body,
            "detalhe fisico incoerente foi aceito")
    require("('build_linha_card','build_otimizador_id')" in lower,
            "preflight omite build_linha_card.build_otimizador_id")
    require("('carta_completude_motor_versao','versao_id')" in lower,
            "preflight omite carta_completude_motor_versao.versao_id")
    require("resultado_fingerprint" in body, "idempotencia por fingerprint ausente")
    require("build_bonificador_id" in body, "ligacao build_linha_card ausente")
    require("readback transacional falhou" in body, "readback transacional ausente")
    require("grant execute" in lower and "to service_role" in lower, "grant service_role ausente")
    for role in ("public", "anon", "authenticated"):
        require(role in lower, f"revogacao de {role} ausente")
    require("owner to postgres" in lower, "owner do writer nao foi fixado em postgres")
    require("create function public.bonificador_contexto_escrita_v2" in lower,
            "contexto privado de identidade/selos ausente")
    context = lower.split(
        "create function public.bonificador_contexto_escrita_v2", 1
    )[1].split("$function$;", 1)[0]
    require("from public.bonificador_pares_v1(p_limit,p_offset)" not in context,
            "contexto pagina antes de filtrar as linhas pendentes")
    require("from clube_novo.bonificador_par" in context
            and "join clube_novo.build_linha_card" in context,
            "contexto nao consulta diretamente a fila canonica e a linha")
    require(context.index("where l.estado='pendente'") < context.index("limit least("),
            "LIMIT aparece antes do filtro das linhas pendentes")
    require("create function clube_novo.gravar_build_bonificador_v1" not in lower
            and "create function clube_novo.bonificador_contexto_escrita" not in lower,
            "RPC ficou no schema privado nao exposto")
    require("build_linha_card_id" in lower and "formula_fingerprint" in lower,
            "contexto nao entrega identidade e selos completos")
    require("insert into clube.build" not in body, "writer toca clube.build")
    require("update clube.build" not in body, "writer toca clube.build")
    require("insert into clube.fila" not in body, "writer toca clube.fila")
    require("update clube.fila" not in body, "writer toca clube.fila")
    require("delete from clube.fila" not in body, "writer toca clube.fila")
    require("publicacao" not in body, "writer acoplou publicacao ao motor")
    require("grant select" not in lower and "grant insert" not in lower
            and "grant update" not in lower and "grant usage" not in lower,
            "pacote ampliou ACL direta das tabelas/sequence")

    require("drop function public.gravar_build_bonificador_v1(jsonb)" in rollback.lower(),
            "rollback nao remove a porta")
    require("drop function public.bonificador_contexto_escrita_v2(integer,integer)"
            in rollback.lower(), "rollback nao remove o contexto")
    require("delete from clube_novo.build_bonificador" not in rollback.lower(),
            "rollback nao pode apagar resultados")
    require("begin transaction read only" in validate.lower(), "validacao nao e read-only")
    require("<cole_o_resultado_fingerprint_aqui>" in validate.lower(),
            "readback independente por fingerprint ausente")
    require("d.soma_detalhe is distinct from b.bonus_fisico_total" in validate.lower(),
            "validacao independente do detalhe fisico ausente")
    require("where n.nspname='public'" in validate.lower(),
            "validacao ainda procura as RPCs no schema privado")
    contract = CONTRACT.read_text(encoding="utf-8").lower()
    require("pgrst106" in contract and "sem `content-profile`" in contract,
            "contrato REST nao registra o schema publico e o bloqueio real")

    legacy_after = subprocess.check_output(
        ["git", "hash-object", str(LEGACY)], cwd=ROOT, text=True
    ).strip()
    require(legacy_before == legacy_after, "motor_bonus.py foi alterado durante o teste")
    print("OK: parser estrutural, writer fail-closed, idempotencia, rollback e readback offline")
    print(f"motor_bonus.py preservado: {legacy_after}")


if __name__ == "__main__":
    main()
