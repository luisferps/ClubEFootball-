"""Confere se cada insumo lido do jogo já está pronto para entrar no sistema.

Ordem do Luis (04/09/2026): insumo que sobe incompleto estraga duas coisas
diferentes, e as duas custam caro depois.

  Sem pontuação -> o motor calcula tratando o insumo como zero, quando na
  verdade ele apenas nunca foi avaliado. A nota sai errada e ninguém percebe.
  Sem nome      -> a tela mostra o código cru ("Ímpeto 262") no lugar da
  etiqueta. A ficha do card fica ilegível.

Ordem do Luis (04/09/2026, segunda rodada): quando o jogo tem um insumo que o
banco ainda não conhece, não basta dizer "ausente". É preciso abrir o registro
físico e dizer se o jogo entrega o insumo completo ou se o próprio jogo já vem
sem o dado. São dois problemas diferentes: o primeiro sobe e acaba; o segundo
sobe e continua sendo apontado em toda varredura até o jogo publicar o que
falta.

Esta conferência roda dentro da varredura, somente leitura, e aponta as duas
antes de qualquer envio ao banco. Ela não veta nada: quem decide é o dono.

Cinco situações, nunca misturadas:
  ausente_do_banco           -> o jogo tem o insumo e o banco nem o conhece.
  ausente_incompleto_no_jogo -> ausente e o próprio registro físico já vem sem
                                nome ou sem pontuação; sobe assim e continua
                                pendente na varredura seguinte.
  sem_valoracao              -> o banco conhece, mas não há pontuação/efeito.
  sem_nome                   -> não há nome de exibição em português.
  sem_etiqueta_do_jogo       -> não há a chave de texto oficial (all.str).

O relatório também devolve o que já está protegido em clube_novo.valor_do_dono:
o valor manual registrado prevalece mesmo em campos lidos do jogo. Outros
campos do mesmo registro podem ser enviados sem sobrescrever a correção.
"""
from __future__ import annotations

from typing import Any

CONTRACT = "clubef-insumos-motores-v3"

def _impeto_adicionavel_no_jogo(record: dict[str, Any]) -> bool:
    """Mesma regra da regua: nao condicional, com efeito, e todo delta igual a 1.

    O criterio vale sobre o registro fisico porque o insumo novo ainda nao tem
    linha no banco para consultar. Conferido em 04/09/2026 contra
    public.otimizador_regua_v2(): os dois lados devolvem os mesmos 29 codigos.
    """
    if record.get("criterio_codigo") != "sempre_ativo":
        return False
    efeitos = record.get("efeitos")
    if not isinstance(efeitos, list) or not efeitos:
        return False
    return all(isinstance(e, dict) and e.get("delta") == 1 for e in efeitos)


def _tecnico_forca_no_jogo(record: dict[str, Any]) -> dict[str, int]:
    """Forca do tecnico e a proficiencia dele em cada estilo tatico."""
    prof = record.get("proficiencias")
    if not isinstance(prof, dict):
        return {}
    return {str(k): int(v) for k, v in prof.items() if isinstance(v, int)}


def _tecnico_adicionavel_no_jogo(record: dict[str, Any]) -> bool:
    """Todo tecnico do catalogo entra no pool: o otimizador escolhe qualquer um."""
    return True


# Cada insumo declara: catálogo físico de origem, tabela canônica, chave, as
# consultas que definem o que já está pronto no banco, e quais campos do
# registro físico carregam nome e pontuação. Campo não publicado pelo catálogo
# é declarado None: nada é inferido no código.
INPUTS = (
    {
        "chave": "habilidades",
        "rotulo": "Habilidade",
        "catalogo_fisico": "habilidades",
        "tabela": "habilidade_jogo",
        "coluna_chave": "skill_id",
        "criterio_valoracao": "efeito por atributo definido e habilitada para os motores",
        "sql_conhecidas": "select skill_id::text from {schema}.habilidade_jogo",
        "sql_valoradas": "select skill_id::text from {schema}.habilidade_jogo where pode_rodar and efeito_por_codigo is not null and efeito_por_codigo <> '{{}}'::jsonb",
        # nome_pt repetindo o japones do PlayerSkill.bin nao e nome traduzido.
        "sql_nomeadas": "select skill_id::text from {schema}.habilidade_jogo where btrim(coalesce(nome_pt,'')) <> '' and btrim(coalesce(nome_pt,'')) <> btrim(coalesce(nome_jp,''))",
        "sql_etiquetadas": "select skill_id::text from {schema}.habilidade_jogo where id_texto is not null and btrim(coalesce(secao_texto,'')) <> ''",
        "sql_uso_nas_cartas": "select skill_id::text, count(*)::text from {schema}.carta_habilidade_jogo group by 1",
        # PlayerSkill.bin é publicado como bloco cru: não expõe nome nem efeito.
        "fisico_nome": None,
        "fisico_valoracao": None,
        "pool_rotulo": "habilidade que o jogador pode adicionar na carta",
        "pool_certeza": "a_confirmar",
        "pool_porque": "o arquivo do jogo não declara se a habilidade é fabricável; quem marca fabricável é o banco",
        "pool_regra_fisica": None,
        "pool_forca_rotulo": None,
        "pool_forca_fisica": None,
        "pool_forca_sql": None,
    },
    {
        "chave": "impetos",
        "rotulo": "Ímpeto",
        "catalogo_fisico": "impetos",
        "tabela": "impeto_jogo",
        "coluna_chave": "codigo_jogo",
        "criterio_valoracao": "pelo menos um efeito de atributo registrado",
        "sql_conhecidas": "select codigo_jogo::text from {schema}.impeto_jogo",
        "sql_valoradas": "select i.codigo_jogo::text from {schema}.impeto_jogo i where exists (select 1 from {schema}.impeto_atributo_jogo a where a.codigo_impeto=i.codigo_jogo)",
        "sql_nomeadas": "select codigo_jogo::text from {schema}.impeto_jogo where btrim(coalesce(nome_pt,'')) <> ''",
        "sql_etiquetadas": "select codigo_jogo::text from {schema}.impeto_jogo where id_texto is not null and btrim(coalesce(secao_texto,'')) <> ''",
        "sql_uso_nas_cartas": "select codigo_impeto::text, count(*)::text from {schema}.carta_impeto_jogo group by 1",
        # PlayerBooster.bin publica os efeitos; o nome não existe no arquivo.
        "fisico_nome": None,
        "fisico_valoracao": "efeitos",
        "pool_rotulo": "ímpeto adicionável, do tipo que o jogador compra e põe na carta",
        "pool_certeza": "certo",
        "pool_porque": "não condicional, com efeito, e todo delta igual a 1 — a mesma regra de impetos_adicionais da régua",
        "pool_regra_fisica": _impeto_adicionavel_no_jogo,
        "pool_forca_rotulo": None,
        "pool_forca_fisica": None,
        "pool_forca_sql": None,
    },
    {
        "chave": "playstyles",
        "rotulo": "Playstyle",
        "catalogo_fisico": "playstyles",
        "tabela": "playstyle",
        "coluna_chave": "id_jogo",
        "criterio_valoracao": "presente no catálogo canônico",
        "sql_conhecidas": "select id_jogo::text from {schema}.playstyle",
        "sql_valoradas": "select id_jogo::text from {schema}.playstyle",
        "sql_nomeadas": "select id_jogo::text from {schema}.playstyle where btrim(coalesce(nome_pt,'')) <> ''",
        "sql_etiquetadas": "select id_jogo::text from {schema}.playstyle where id_texto is not null and btrim(coalesce(secao_texto,'')) <> ''",
        "sql_uso_nas_cartas": None,
        # Playstyle.bin é publicado como bloco cru.
        "fisico_nome": None,
        "fisico_valoracao": None,
        "pool_rotulo": None,
        "pool_certeza": None,
        "pool_porque": None,
        "pool_regra_fisica": None,
        "pool_forca_rotulo": None,
        "pool_forca_fisica": None,
        "pool_forca_sql": None,
    },
    {
        "chave": "tecnicos",
        "rotulo": "Técnico",
        "catalogo_fisico": "tecnicos",
        "tabela": "tecnico_jogo",
        "coluna_chave": "id",
        "criterio_valoracao": "habilitado para os motores e com proficiência de estilo registrada",
        "sql_conhecidas": "select id::text from {schema}.tecnico_jogo",
        "sql_valoradas": "select t.id::text from {schema}.tecnico_jogo t where t.pode_rodar and exists (select 1 from {schema}.tecnico_estilo_jogo e where e.tecnico_id=t.id)",
        "sql_nomeadas": "select id::text from {schema}.tecnico_jogo where btrim(coalesce(nome_en,'')) <> ''",
        # O nome do técnico é lido direto do Coach.bin; não existe chave de texto.
        "sql_etiquetadas": None,
        "sql_uso_nas_cartas": None,
        "fisico_nome": "nome_en",
        "fisico_valoracao": "proficiencias",
        "pool_rotulo": "técnico novo, e qualquer carta pode receber qualquer técnico",
        "pool_certeza": "certo",
        "pool_porque": "o otimizador escolhe o técnico livremente entre todos os que rodam",
        "pool_regra_fisica": _tecnico_adicionavel_no_jogo,
        "pool_forca_rotulo": "proficiência no estilo",
        "pool_forca_fisica": _tecnico_forca_no_jogo,
        "pool_forca_sql": "select codigo_estilo, max(proficiencia) from {schema}.tecnico_estilo_jogo group by 1",
    },
)

EXAMPLE_LIMIT = 40


def _physical_records(metadata: dict[str, Any], catalog_key: str) -> tuple[dict[str, dict[str, Any]], bool]:
    catalogs = metadata.get("catalogs") if isinstance(metadata, dict) else None
    catalog = catalogs.get(catalog_key) if isinstance(catalogs, dict) else None
    if not isinstance(catalog, dict) or catalog.get("supported") is not True:
        return {}, False
    records = catalog.get("records")
    if not isinstance(records, list):
        return {}, False
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("id") is None:
            raise ValueError(f"catálogo físico {catalog_key} trouxe registro sem id")
        by_id[str(record["id"])] = record
    return by_id, True


def _preenchido(record: dict[str, Any], campo: str | None) -> bool:
    if campo is None:
        return True
    valor = record.get(campo)
    if valor is None:
        return False
    if isinstance(valor, str):
        return bool(valor.strip())
    if isinstance(valor, (list, dict, tuple, set)):
        return bool(valor)
    return True


def _column(connection: Any, query: str) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(query)
        return {str(row[0]) for row in cursor.fetchall()}


def _owner_values(connection: Any, schema: str) -> list[dict[str, Any]]:
    """Lê o que o dono preencheu à mão e que nenhuma carga pode sobrescrever."""
    with connection.cursor() as cursor:
        cursor.execute(
            "select destino_tabela, chave, coluna, porque from {}.valor_do_dono order by destino_tabela, coluna".format(schema)
        )
        return [
            {"tabela": str(row[0]), "chave": row[1], "coluna": str(row[2]), "porque": str(row[3])}
            for row in cursor.fetchall()
        ]


def _pool_strength(spec: dict[str, Any], afeta: list[dict[str, Any]], physical: dict[str, dict[str, Any]],
                   connection: Any, schema: str) -> dict[str, Any] | None:
    """Compara a forca do insumo novo com o melhor que o banco ja tem.

    Ordem do Luis (04/09/2026): tecnico novo com proficiencia 64 nao vence
    nenhuma build montada com tecnico de 96, entao nao ha nota para refazer. O
    relatorio decide isso sozinho onde a forca e medivel, em vez de obrigar a
    perguntar.
    """
    if not afeta or spec["pool_forca_sql"] is None:
        return None
    with connection.cursor() as cursor:
        cursor.execute(spec["pool_forca_sql"].format(schema=schema))
        atual = {str(linha[0]): int(linha[1]) for linha in cursor.fetchall() if linha[1] is not None}
    medir = spec["pool_forca_fisica"]
    superam: list[dict[str, Any]] = []
    melhor_novo = None
    for item in afeta:
        for dimensao, valor in (medir(physical[item["id"]]) or {}).items():
            if melhor_novo is None or valor > melhor_novo:
                melhor_novo = valor
            teto = atual.get(dimensao)
            if teto is None or valor > teto:
                superam.append({"id": item["id"], "nome_no_jogo": item.get("nome_no_jogo"),
                                "dimensao": dimensao, "valor": valor, "teto_atual": teto})
    return {
        "rotulo": spec["pool_forca_rotulo"],
        "melhor_novo": melhor_novo,
        "teto_atual": max(atual.values()) if atual else None,
        "superam_o_teto": superam[:EXAMPLE_LIMIT],
        "superam_o_teto_total": len(superam),
        "muda_nota": bool(superam),
    }


def _cards_already_scored(connection: Any, schema: str) -> dict[str, Any]:
    """Quantas cartas ja tem nota calculada com o pool anterior."""
    with connection.cursor() as cursor:
        cursor.execute(
            "select count(distinct card_id), count(*) filter (where finalizada_em is not null), max(finalizada_em)"
            " from {}.otimizador_lote_producao_linha_v3".format(schema)
        )
        cartas, linhas, ultima = cursor.fetchone()
    return {"cartas": int(cartas or 0), "linhas_finalizadas": int(linhas or 0),
            "ultima_em": ultima.isoformat() if ultima is not None else None}


def _estado_das_cartas_no_motor(connection: Any, schema: str) -> dict[str, Any]:
    """Onde cada carta esta em relacao ao motor: ja rodou, esta na fila, ou nunca rodou.

    Ordem do Luis (04/09/2026): "se elas ja foram otimizadas eu rodo um lote so com
    elas; se ainda estao na fila, preciso esperar, senao a fila passa por cima". Sem
    isso o relatorio manda rodar sem dizer se da para rodar agora.
    """
    with connection.cursor() as cursor:
        cursor.execute("select distinct card_id::text from {}.build_pontuacao_final_v2".format(schema))
        publicadas = {linha[0] for linha in cursor.fetchall()}
        cursor.execute(
            "select distinct c.card_id::text, l.id::text, l.estado"
            " from {0}.otimizador_lote_producao_carta_v3 c"
            " join {0}.otimizador_lote_producao_v3 l on l.id = c.lote_id"
            " where l.estado not in ('concluido','finalizado','publicado')".format(schema)
        )
        em_fila: dict[str, dict[str, str]] = {}
        for card_id, lote_id, estado in cursor.fetchall():
            em_fila[str(card_id)] = {"lote": str(lote_id)[:8], "estado_do_lote": str(estado)}
    return {
        "contrato": "clubef-estado-das-cartas-no-motor-v1",
        "ja_rodaram": sorted(publicadas),
        "ja_rodaram_total": len(publicadas),
        "na_fila": em_fila,
        "na_fila_total": len(em_fila),
        "ja_rodaram_e_estao_na_fila_total": len(publicadas & set(em_fila)),
        "significado": {
            "ja_rodou": "tem nota publicada; se o dado de nota mudou, da para rodar um lote avulso agora",
            "na_fila": "esta dentro de um lote que ainda nao terminou; lote avulso agora seria sobrescrito quando a fila voltar",
            "nunca_rodou": "nao tem nota nem esta em lote; entra na primeira rodada",
        },
    }


def evaluate_engine_inputs(metadata: dict[str, Any], connection: Any, schema: str) -> dict[str, Any]:
    if schema != "clube_novo":
        raise ValueError("conferência de insumos bloqueada fora de clube_novo")
    with connection.cursor() as cursor:
        cursor.execute("show transaction_read_only")
        if cursor.fetchone()[0] != "on":
            raise RuntimeError("a conferência de insumos não ficou protegida por READ ONLY")

    situacoes = ("ausente_do_banco", "ausente_incompleto_no_jogo", "sem_valoracao", "sem_nome", "sem_etiqueta_do_jogo")
    totais_extra = ("afeta_nota_de_cards_ja_rodados",)
    groups: list[dict[str, Any]] = []
    totals = {situacao: 0 for situacao in situacoes + totais_extra}
    for spec in INPUTS:
        physical, supported = _physical_records(metadata, spec["catalogo_fisico"])
        confere_nome_no_jogo = spec["fisico_nome"] is not None
        confere_valoracao_no_jogo = spec["fisico_valoracao"] is not None
        group: dict[str, Any] = {
            "chave": spec["chave"],
            "rotulo": spec["rotulo"],
            "tabela": f"{schema}.{spec['tabela']}",
            "coluna_chave": spec["coluna_chave"],
            "criterio_valoracao": spec["criterio_valoracao"],
            "confere_etiqueta": spec["sql_etiquetadas"] is not None,
            "confere_ausente_no_jogo": confere_nome_no_jogo or confere_valoracao_no_jogo,
            "campo_fisico_nome": spec["fisico_nome"],
            "campo_fisico_valoracao": spec["fisico_valoracao"],
        }
        if not supported:
            group.update({
                "conferido": False,
                "motivo_nao_conferido": "o jogo não expõe uma lista completa deste insumo nesta leitura",
                "lidos_do_jogo": 0,
                "ausente_completo_no_jogo_total": 0,
                "rotulos_do_jogo": {},
                "cartas_que_usam": {},
                "pool_rotulo": spec["pool_rotulo"],
                "forca": None,
            })
            for situacao in situacoes + totais_extra:
                group[situacao] = []
                group[situacao + "_total"] = 0
            groups.append(group)
            continue

        known = _column(connection, spec["sql_conhecidas"].format(schema=schema))
        valoradas = _column(connection, spec["sql_valoradas"].format(schema=schema))
        nomeadas = _column(connection, spec["sql_nomeadas"].format(schema=schema))
        etiquetadas = (
            None if spec["sql_etiquetadas"] is None
            else _column(connection, spec["sql_etiquetadas"].format(schema=schema))
        )

        ausentes = sorted(item for item in physical if item not in known)
        incompletos: list[dict[str, Any]] = []
        completos = 0
        for item in ausentes:
            record = physical[item]
            falta = []
            if not _preenchido(record, spec["fisico_nome"]):
                falta.append("nome")
            if not _preenchido(record, spec["fisico_valoracao"]):
                falta.append("pontuação")
            if falta:
                incompletos.append({"id": item, "falta": falta})
            elif group["confere_ausente_no_jogo"]:
                completos += 1

        found = {
            "ausente_do_banco": ausentes,
            "ausente_incompleto_no_jogo": incompletos,
            "sem_valoracao": sorted(item for item in physical if item in known and item not in valoradas),
            "sem_nome": sorted(item for item in physical if item in known and item not in nomeadas),
            "sem_etiqueta_do_jogo": [] if etiquetadas is None else sorted(
                item for item in physical if item in known and item not in etiquetadas
            ),
        }
        group.update({
            "conferido": True,
            "lidos_do_jogo": len(physical),
            "conhecidos_no_banco": len(known),
            "ausente_completo_no_jogo_total": completos,
        })
        for situacao, items in found.items():
            totals[situacao] += len(items)
            group[situacao] = items[:EXAMPLE_LIMIT]
            group[situacao + "_total"] = len(items)
        # O relatorio precisa falar em nome, nao so em codigo. Quando o catalogo
        # fisico publica o nome, ele viaja junto para o insumo que ainda nao
        # existe no banco e portanto nao tem rotulo canonico para consultar.
        rotulos: dict[str, str] = {}
        if spec["fisico_nome"] is not None:
            listados = {str(item) for item in found["ausente_do_banco"][:EXAMPLE_LIMIT]}
            listados.update(str(item["id"]) for item in found["ausente_incompleto_no_jogo"][:EXAMPLE_LIMIT])
            for item in listados:
                nome = physical.get(item, {}).get(spec["fisico_nome"])
                if isinstance(nome, str) and nome.strip():
                    rotulos[item] = nome.strip()
        group["rotulos_do_jogo"] = rotulos
        # Pergunta que o dono faz sempre: "existe card usando isso hoje?".
        # Insumo pendente que nenhuma carta usa nao atrapalha ninguem.
        uso: dict[str, int] = {}
        if spec["sql_uso_nas_cartas"] is not None:
            interessa = {str(i) for i in ausentes}
            for situacao in ("sem_valoracao", "sem_nome", "sem_etiqueta_do_jogo"):
                interessa.update(str(i) for i in found[situacao][:EXAMPLE_LIMIT])
            with connection.cursor() as cursor:
                cursor.execute(spec["sql_uso_nas_cartas"].format(schema=schema))
                for chave, quantos in cursor.fetchall():
                    if str(chave) in interessa:
                        uso[str(chave)] = int(quantos)
        group["cartas_que_usam"] = uso
        # Insumo NOVO que entra no pool do otimizador muda o teto das cartas que
        # ja foram rodadas antes dele existir. O Extrator so avisa; quem manda
        # recalcular e o dono.
        afeta: list[dict[str, Any]] = []
        if spec["pool_rotulo"] is not None:
            regra = spec["pool_regra_fisica"]
            for item in ausentes:
                if regra is not None and not regra(physical[item]):
                    continue
                afeta.append({
                    "id": item,
                    "nome_no_jogo": rotulos.get(item),
                    "certeza": spec["pool_certeza"],
                    "porque": spec["pool_porque"],
                })
        # Insumo novo so muda nota se for melhor do que o que ja existe. Onde a
        # forca e medivel, o relatorio compara em vez de deixar a pergunta aberta.
        group["forca"] = _pool_strength(spec, afeta, physical, connection, schema)
        group["pool_rotulo"] = spec["pool_rotulo"]
        group["afeta_nota_de_cards_ja_rodados"] = afeta[:EXAMPLE_LIMIT]
        group["afeta_nota_de_cards_ja_rodados_total"] = len(afeta)
        totals["afeta_nota_de_cards_ja_rodados"] += len(afeta)
        groups.append(group)

    owner_values = _owner_values(connection, schema)
    ja_rodadas = _cards_already_scored(connection, schema)
    pending = sum(totals[situacao] for situacao in situacoes)
    return {
        "contract": CONTRACT,
        "valores_do_dono": owner_values,
        "valores_do_dono_total": len(owner_values),
        "transaction_read_only": True,
        "database_write": False,
        "schema": schema,
        "cards_ja_rodados": ja_rodadas,
        "estado_das_cartas_no_motor": _estado_das_cartas_no_motor(connection, schema),
        "grupos": groups,
        **{chave + "_total": valor for chave, valor in totals.items()},
        "pendente_total": pending,
        "tudo_pronto": pending == 0,
        "significado": {
            "sem_valoracao": "entra no motor valendo zero, quando na verdade nunca foi avaliado",
            "sem_nome": "a tela mostra o código cru no lugar da etiqueta",
            "sem_etiqueta_do_jogo": "não há chave de texto oficial para puxar o nome do próprio jogo",
            "ausente_do_banco": "o jogo tem o insumo e o banco ainda não o conhece",
            "afeta_nota_de_cards_ja_rodados": "insumo novo que o otimizador pode escolher; as cartas rodadas antes dele existir podem subir de nota e precisam ser rodadas de novo",
            "ausente_incompleto_no_jogo": "o jogo tem o insumo mas já entrega sem nome ou sem pontuação; sobe assim e volta a ser apontado toda varredura",
        },
    }
