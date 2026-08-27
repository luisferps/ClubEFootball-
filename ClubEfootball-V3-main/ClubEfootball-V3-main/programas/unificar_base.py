# -*- coding: utf-8 -*-
"""
UNIFICAR BASE - monta a BASE UNICA de cards do Sistema Encaixe / TrueFootball.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
Hoje o mesmo dado de um card mora em varios arquivos ao mesmo tempo (cards.json,
cards_efhub.json, efscout_*, vaga_por_card, box_por_card, pe_ruim, falta, raras,
levelcap...). Quando dois arquivos discordam, ninguem sabe quem manda, e o
resultado muda dependendo de qual script rodou por ultimo.

Este script LE TODAS as fontes, aplica a precedencia ja decidida em 07/08
(precedencia.json) e grava UM registro por card em dados/base_unica.json, com um
campo `fonte_de_cada_campo` dizendo de onde veio cada dado importante. Assim da
para auditar qualquer numero sem abrir sete arquivos.

O QUE ELE NAO FAZ (de proposito)
--------------------------------
- NAO apaga e NAO altera nenhum arquivo existente. So cria dois arquivos novos:
  dados/base_unica.json e RELATORIO-BASE-UNICA.txt.
- NAO inventa dado: se uma fonte esta vazia, ela nunca sobrescreve um dado bom.
- NAO quebra se faltar arquivo: anota a falta no relatorio e segue em frente.

COMO RODAR
----------
    python unificar_base.py              -> grava de verdade
    python unificar_base.py --conferir   -> so relata na tela, nao grava nada
"""

# ===========================================================================
#  ⛔ 19/08 — ESTE PROGRAMA MORA NO ClubEfootball\programas.
#     "Nao existe mais essa pasta pro futebol. A pasta agora e ClubEfootball.
#      E tudo la." (Luis, 19/08)
#
#  ⛔ ESTE BLOCO VEM ANTES DOS IMPORTS, E POR MEDIDA. Quando ele ficava
#     DEPOIS, o `from equacao import ...` la de cima ja tinha rodado e pegava
#     o arquivo errado — o programa nem chegava a saber onde estava a casa.
#
#     Ele faz duas coisas, e as duas importam:
#       1. acha a pasta que tem o config.txt e trabalha LA (os dados nao se
#          mudaram: dados\, saida_v6\, encaixe\ continuam na casa);
#       2. poe `programas\` na frente do caminho de busca, para os modulos
#          vizinhos serem achados aqui e nao na raiz.
# ===========================================================================
import os as _os, sys as _sys

def _acha_a_casa(inicio):
    p = inicio
    for _ in range(5):
        if _os.path.exists(_os.path.join(p, 'config.txt')):
            return p
        pai = _os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None

_MEU_LUGAR = _os.path.dirname(_os.path.abspath(__file__))
_CASA = _acha_a_casa(_MEU_LUGAR) or _acha_a_casa(_os.getcwd())
if _CASA:
    if _os.path.abspath(_os.getcwd()) != _os.path.abspath(_CASA):
        _os.chdir(_CASA)
    if _CASA not in _sys.path:
        _sys.path.append(_CASA)          # a casa vem DEPOIS
if _MEU_LUGAR in _sys.path:
    _sys.path.remove(_MEU_LUGAR)
_sys.path.insert(0, _MEU_LUGAR)          # `programas` vem PRIMEIRO
# --------------------------------------------------------------------------

import json
import os
import time
import re
import sys
from collections import Counter, OrderedDict

# ⛔ 19/08 — a pasta dos DADOS e a CASA (a do config.txt), nao a

#    pasta deste arquivo. Ele mudou de lugar; os dados nao.

AQUI = _CASA or os.path.dirname(os.path.abspath(__file__))
SO_CONFERIR = "--conferir" in sys.argv

# ---------------------------------------------------------------------------
# LEITURA TOLERANTE
# Regra: nenhuma fonte ausente pode derrubar a rodada. O Luis roda por duplo
# clique; travar com traceback nao ajuda ninguem. Falta vira linha de relatorio.
# ---------------------------------------------------------------------------
AVISOS = []          # problemas para o relatorio
FONTES_LIDAS = {}    # nome do arquivo -> quantos registros


def ler_json(caminho_relativo, padrao):
    caminho = os.path.join(AQUI, caminho_relativo)
    if not os.path.exists(caminho):
        AVISOS.append("FONTE AUSENTE: %s (segui sem ela)" % caminho_relativo)
        FONTES_LIDAS[caminho_relativo] = 0
        return padrao
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except Exception as erro:
        AVISOS.append("FONTE ILEGIVEL: %s (%s) - segui sem ela" % (caminho_relativo, erro))
        FONTES_LIDAS[caminho_relativo] = 0
        return padrao
    FONTES_LIDAS[caminho_relativo] = len(dados) if hasattr(dados, "__len__") else 1
    return dados


# ---------------------------------------------------------------------------
# AS FONTES
# ---------------------------------------------------------------------------
precedencia = ler_json("precedencia.json", {})
datas_lancamento = ler_json("datas-lancamento-cartas.json", {})
cat_dom = ler_json("CAT_dom.json", [])
cards_base = ler_json(os.path.join("dados", "cards.json"), [])
cards_efhub = ler_json("cards_efhub.json", [])
efscout_impeto = ler_json("efscout_impeto_por_card.json", {})
efscout_boosters = ler_json("efscout_boosters.json", [])
vaga_por_card = ler_json("vaga_por_card.json", {})
box_por_card = ler_json("box_por_card.json", {})
pe_ruim_arq = ler_json("pe_ruim.json", {})
falta_por_card = ler_json(os.path.join("dados", "falta_por_card.json"), {})
raras_por_card = ler_json(os.path.join("dados", "raras_por_card.json"), {})
conferido_arq = ler_json("impeto_conferido_no_jogo.json", {})
# ⛔ 16/08 — O IMPETO DO EFOOTBASE. Coleta de 15/08 pelo navegador.
#    Ele mostra o EFEITO MAXIMO da carta base, e mostra os DOIS impetos.
#    As nossas fontes pegam de UMA so (a primeira que tiver dado), e por
#    isso 24 cards estavam com metade do impeto: o Neuer tinha o "Defesaca
#    +3" e nao tinha o "Passe +3". Conferido nas fotos do jogo pelo Luis.
#    ENTRA COMO COMPLEMENTO, nunca por cima: so acrescenta o que falta.
efootbase_imp = (ler_json("impeto_efootbase.json", {}) or {}).get("dados") or {}
# CONFERIDO.json: o que foi checado e fechado. Ganha de toda fonte, inclusive
# quando a resposta e VAZIO ("esse card nao tem" e resposta, nao buraco).
conferido_geral = ler_json("CONFERIDO.json", {})
tecnicos = ler_json("tecnicos.json", {})

# levelcap ja morou em dois lugares na historia do projeto; aceito os dois.
levelcap = ler_json(os.path.join("dados", "levelcap.json"), None)
if not levelcap:
    levelcap = ler_json("levelcap.json", {})

# pe_ruim.json tem cabecalho (gerado/fonte/campos/...); o que interessa e `dados`
pe_ruim = pe_ruim_arq.get("dados", pe_ruim_arq) if isinstance(pe_ruim_arq, dict) else {}
if not isinstance(pe_ruim, dict):
    pe_ruim = {}

# impeto_conferido_no_jogo.json tambem tem chaves de documentacao (_regra etc.)
conferidos = conferido_arq.get("conferidos", {}) if isinstance(conferido_arq, dict) else {}

# Quem manda em cada campo, direto do precedencia.json (nao duplico a regra aqui:
# se o Luis mudar o precedencia.json, este script acompanha).
EFHUB_MANDA = precedencia.get("efhub_manda", [
    "base", "max_ovr", "orc", "dt", "sl", "fab", "pos", "np", "sec", "modelo",
    "altura", "peso", "pe", "ovr", "nome", "levelCap", "boostId", "boostId2"])
DERIVADO_LOCAL_MANDA = precedencia.get("derivado_local_manda", ["falta", "raras"])

# ---------------------------------------------------------------------------
# CATALOGO DE IMPETOS (boosters)
# Regra ja fechada: dicionario UNICO por id, sem separar por lado/cor.
# ---------------------------------------------------------------------------
CATALOGO = {}
CATALOGO_POR_NOME = {}
for b in (efscout_boosters or []):
    if not isinstance(b, dict) or "id" not in b:
        continue
    CATALOGO[int(b["id"])] = b
    nome = (b.get("name") or "").strip().lower()
    if nome:
        CATALOGO_POR_NOME.setdefault(nome, b)


def vazio(valor):
    """O que conta como 'nao tenho esse dado'. Cuidado: 0 e False sao dados."""
    if valor is None:
        return True
    if isinstance(valor, str) and valor.strip() in ("", "?"):
        return True
    if isinstance(valor, (list, dict, tuple)) and len(valor) == 0:
        return True
    return False


def aplicar_modificadores(nm, nx, nmn, booster, orfaos, de_onde):
    """
    Soma um ímpeto do catalogo dentro dos 26 slots.

    A regra do condicional ja foi medida e esta fechada:
      conditional verdadeiro -> nm += v//3  e  nx += v - v//3
      (nm e o que vale sempre; nx e o que ainda falta pro +3 do condicional)
      conditional falso      -> nm += v
    """
    if booster is None:
        return False
    cond = bool(booster.get("conditional"))
    for par in (booster.get("stat_modifiers") or []):
        try:
            i, v = int(par[0]), int(par[1])
        except Exception:
            continue
        if not (0 <= i < 26):
            continue
        if cond:
            nm[i] += v // 3
            nx[i] += v - (v // 3)
        else:
            nm[i] += v
    nome = booster.get("name")
    if nome and nome not in nmn:
        nmn.append(nome)
    return True


def do_boost_id(boost_id, nm, nx, nmn, orfaos):
    """Converte um boostId pelo catalogo. Id desconhecido vira ORFAO no relatorio."""
    if boost_id in (None, 0, "0", ""):
        return False
    try:
        bid = int(boost_id)
    except Exception:
        return False
    if bid == 0:
        return False
    booster = CATALOGO.get(bid)
    if booster is None:
        orfaos.append(bid)   # catalogo do efscout esta desatualizado; anoto e sigo
        return False
    return aplicar_modificadores(nm, nx, nmn, booster, orfaos, "boostId")


# "Raphael Varane 87 — efscout: Rebuilding +3. Tem impeto de fabrica, ..."
# Do texto da conferencia manual eu so preciso do NOME do impeto, que casa com o
# catalogo. O resto e prosa do Luis.
RE_CONFERIDO = re.compile(r"efscout:\s*(.+?)\s*(?:\.|$)", re.IGNORECASE)


def impeto_do_conferido(texto):
    if not isinstance(texto, str):
        return None, None
    achou = RE_CONFERIDO.search(texto)
    if not achou:
        return None, None
    nome = achou.group(1).strip()
    return nome, CATALOGO_POR_NOME.get(nome.lower())


# ---------------------------------------------------------------------------
# MONTAGEM: um registro por card
# ---------------------------------------------------------------------------
registro = OrderedDict()   # id (str) -> card unificado
fonte = {}                 # id -> {campo: fonte}
conflitos = []             # lista de conflitos entre fontes
orfaos_por_card = {}       # id -> [boostIds que o catalogo nao conhece]


def poe(cid, campo, valor, de_onde, autoridade):
    """
    Grava um campo respeitando duas regras que nao mudam:
      1) fonte vazia NUNCA sobrescreve dado bom;
      2) quem tem mais autoridade ganha, e a divergencia vira linha de conflito.
    `autoridade`: numero maior ganha.
    """
    if vazio(valor):
        return
    card = registro[cid]
    marca = fonte.setdefault(cid, {})
    anterior = card.get(campo)
    aut_anterior = marca.get("_aut_" + campo, -1)

    if campo in card and not vazio(anterior) and anterior != valor:
        # divergencia real entre duas fontes: registro para o Luis conferir
        vence_novo = autoridade > aut_anterior
        conflitos.append({
            "card": cid,
            "nome": card.get("nome"),
            "campo": campo,
            "valor_anterior": anterior,
            "fonte_anterior": marca.get(campo),
            "valor_novo": valor,
            "fonte_nova": de_onde,
            "ganhou": de_onde if vence_novo else marca.get(campo),
            "por_que": ("fonte de maior autoridade pela precedencia"
                        if vence_novo else
                        "a fonte que ja estava tem autoridade igual ou maior"),
        })
        if not vence_novo:
            return
    elif not vazio(anterior) and autoridade <= aut_anterior:
        return

    card[campo] = valor
    marca[campo] = de_onde
    marca["_aut_" + campo] = autoridade


# --- 1) cards.json e o chao: todo card existe aqui ------------------------
for c in (cards_base or []):
    cid = str(c.get("id"))
    if not cid or cid == "None":
        continue
    registro[cid] = OrderedDict()
    fonte[cid] = {}
    for campo, valor in c.items():
        poe(cid, campo, valor, "dados/cards.json", 1)

# --- 2) cards_efhub.json: manda nos campos listados no precedencia.json ----
for c in (cards_efhub or []):
    cid = str(c.get("id"))
    if not cid or cid == "None":
        continue
    if cid not in registro:
        # card que so existe no efHub ainda entra na base (nao perco carta nova)
        registro[cid] = OrderedDict()
        fonte[cid] = {}
    for campo, valor in c.items():
        # autoridade 3 nos campos onde o efHub manda, 2 no resto (ainda melhor
        # que cards.json, que hoje e fonte de regressao segundo o precedencia)
        poe(cid, campo, valor, "cards_efhub.json", 3 if campo in EFHUB_MANDA else 2)

# --- 3) derivados locais: vaga, box, pe ruim, falta, raras, levelcap -------
for cid, v in (vaga_por_card or {}).items():
    cid = str(cid)
    if cid not in registro:
        continue
    # lista so de nulos ([null,null,null]) e "nao sei", nao e dado: nao entra,
    # senao a cobertura mente dizendo que 2.589 cards tem vaga conhecida.
    lista = v.get("v") if isinstance(v, dict) else None
    if lista and any(x is not None for x in lista):
        poe(cid, "vaga", lista, "vaga_por_card.json", 4)

for cid, v in (box_por_card or {}).items():
    cid = str(cid)
    if cid not in registro or not isinstance(v, dict):
        continue
    if not vazio(v.get("box")):
        poe(cid, "box", v.get("box"), "box_por_card.json", 4)
    if not vazio(v.get("dt")):
        poe(cid, "dt", v.get("dt"), "box_por_card.json", 4)
    # ⛔ 18/08 — A ETIQUETA DA CARTA NAO E BOX, MAS E DADO BOM.
    #    "Big Time Portugal 23 Jun '26" diz o TIPO do card e a partida que ele
    #    comemora. O vigia tirou isso do campo `box` (onde estava errado) e
    #    guardou em `etiqueta_do_card`. Aqui ela entra na base para a tela
    #    poder mostrar as duas coisas: de que box veio e que card e.
    if not vazio(v.get("etiqueta_do_card")):
        poe(cid, "etiqueta_do_card", v.get("etiqueta_do_card"), "box_por_card.json", 4)

for cid, v in (pe_ruim or {}).items():
    cid = str(cid)
    if cid in registro and not vazio(v):
        poe(cid, "pe_ruim", v, "pe_ruim.json", 4)

# falta e raras: o precedencia diz que o derivado local manda. E o ESPACO DE
# BUSCA do motor, nao um dado do card - por isso ganha de todo mundo.
for cid, v in (falta_por_card or {}).items():
    cid = str(cid)
    if cid in registro and "falta" in DERIVADO_LOCAL_MANDA and not vazio(v):
        poe(cid, "falta", v, "dados/falta_por_card.json", 5)

for cid, v in (raras_por_card or {}).items():
    cid = str(cid)
    if cid in registro and "raras" in DERIVADO_LOCAL_MANDA and not vazio(v):
        poe(cid, "raras", v, "dados/raras_por_card.json", 5)

for cid, v in (levelcap or {}).items():
    cid = str(cid)
    if cid in registro and not vazio(v):
        poe(cid, "levelCap", v, "levelcap.json", 2)

# ---------------------------------------------------------------------------
# 4) O IMPETO - a parte com precedencia propria
# Da maior autoridade para a menor:
#   (1) impeto_conferido_no_jogo.json  - conferido DENTRO do jogo, manda em tudo
#   (2) efscout_impeto_por_card.json
#   (3) boostId / boostId2 convertidos pelo catalogo
#   (4) o nm que ja estava no cards.json
# ---------------------------------------------------------------------------
nao_resolvidos = []      # cards com boostId orfao e sem fonte melhor
impeto_completado_efootbase = {}   # cid -> quantos atributos o efootbase completou
impeto_teto_efootbase = {}         # cid -> quantos tetos (nx) o efootbase corrigiu
impeto_fonte_conta = Counter()

# ============================================================================
#  A LISTA DE IMPETOS JA SEPARADA — 16/08/2026
#  Gerada pelo SEPARAR-OS-IMPETOS.bat a partir do catalogo do jogo
#  (efscout_boosters.json). Quando ela existe e diz que SABE os impetos de um
#  card, o `nm` daquele card sai DELA, e nao da fusao de vetor la embaixo.
#  Se o arquivo nao existir, tudo continua como antes.
# ============================================================================
IMPETOS_SEPARADOS = {}
try:
    with open("dados/impetos_por_card.json", encoding="utf-8") as _f:
        IMPETOS_SEPARADOS = (json.load(_f).get("cards") or {})
    print("   impetos ja separados .......... %d cards (dados/impetos_por_card.json)"
          % len(IMPETOS_SEPARADOS), flush=True)
except Exception:
    print("   impetos ja separados .......... nao ha (rode o SEPARAR-OS-IMPETOS.bat)",
          flush=True)

nm_veio_da_lista = 0
nm_corrigido_pela_lista = []
nm_pulado_por_um_impeto = 0

for cid, card in registro.items():
    nm = [0] * 26
    nx = [0] * 26
    nmn = []
    orfaos = []
    de_onde = None

    # (1) conferido no jogo
    texto = conferidos.get(cid)
    if texto:
        nome_conf, booster = impeto_do_conferido(texto)
        if booster is not None and aplicar_modificadores(nm, nx, nmn, booster, orfaos, "conferido"):
            de_onde = "impeto_conferido_no_jogo.json"
        elif nome_conf:
            # a conferencia existe mas o catalogo nao tem esse nome: e um orfao
            # por NOME. Registro para o Luis saber que precisa recoletar.
            orfaos.append("nome:" + nome_conf)

    # (2) efscout por card
    if de_onde is None:
        ef = efscout_impeto.get(cid)
        if isinstance(ef, dict) and not vazio(ef.get("efeito")):
            cond = bool(ef.get("conditional"))
            for par in ef.get("efeito") or []:
                try:
                    i, v = int(par[0]), int(par[1])
                except Exception:
                    continue
                if not (0 <= i < 26):
                    continue
                if cond:
                    nm[i] += v // 3
                    nx[i] += v - (v // 3)
                else:
                    nm[i] += v
            if ef.get("nome"):
                nmn.append(ef["nome"])
            de_onde = "efscout_impeto_por_card.json"

    # (3) boostId / boostId2 do efHub pelo catalogo
    if de_onde is None:
        pegou = False
        for campo in ("boostId", "boostId2"):
            if do_boost_id(card.get(campo), nm, nx, nmn, orfaos):
                pegou = True
        if pegou:
            de_onde = "boostId do efHub + efscout_boosters.json"

    # (4) o que ja estava no cards.json
    if de_onde is None and not vazio(card.get("nm")):
        for par in card.get("nm") or []:
            try:
                i, v = int(par[0]), int(par[1])
            except Exception:
                continue
            if 0 <= i < 26:
                nm[i] += v
        de_onde = "nm de dados/cards.json"
        if not vazio(card.get("nmn")):
            nmn = list(card["nmn"])

    if orfaos:
        orfaos_por_card[cid] = orfaos
        if de_onde is None:
            nao_resolvidos.append((cid, card.get("nome"), orfaos))

    # nm no formato da casa: [[indice, valor], ...] - so os slots que mexeram
    card["nm"] = [[i, nm[i]] for i in range(26) if nm[i]]
    card["nx"] = [[i, nx[i]] for i in range(26) if nx[i]]
    card["nmn"] = nmn
    card["impeto_orfao"] = orfaos or None

    # ---------------------------------------------------------------
    # (5) O EFOOTBASE COMPLETA o que ficou faltando — 16/08/2026
    #
    # ORDEM DO LUIS, 16/08: "qual e a condicao... o que interessa sao os
    # numeros que ela traz. Pode puxar." E tambem: "nao adianta puxar e nao
    # gravar; daqui uns dias troca alguma coisa e sumiu o impeto."
    #
    # Por isso entra AQUI, na fonte — assim o dado sobrevive a toda rodada do
    # UNIFICAR-BASE e sobe para a `cards_base` junto com o resto.
    #
    # Regra: NAO sobrescreve nada. Se o atributo ja veio de qualquer fonte, ele
    # fica. Só os atributos que NENHUMA fonte trouxe entram, e entram com a
    # mesma distribuicao que a casa ja usa para condicional: nm += v//3 e
    # nx += v - v//3 (com v=3 da o +1 no nm e +2 no nx — igual ao que o Messi
    # ja tinha, conferido na foto do jogo).
    # ---------------------------------------------------------------
    efb = efootbase_imp.get(str(cid).split("@")[0])
    if efb and not vazio(efb.get("efeito_maximo")):
        entrou = 0
        completou_teto = 0
        for par in efb.get("efeito_maximo") or []:
            try:
                i, v = int(par[0]), int(par[1])
            except Exception:
                continue
            if not (0 <= i < 26) or v <= 0:
                continue
            if nm[i] or nx[i]:
                # ⛔ 16/08 — o SEGUNDO furo, achado na foto do Messi: o card
                #    tinha o condicional em +1 e o nx VAZIO, isto e, o sistema
                #    nao sabia que aquele atributo ainda podia subir ate +3.
                #    Se o efootbase mostra um teto MAIOR do que o nosso, a
                #    diferenca entra no nx. Nunca reduz nada.
                if v > nm[i] + nx[i]:
                    nx[i] += v - (nm[i] + nx[i])
                    completou_teto += 1
                continue
            nm[i] += v // 3
            nx[i] += v - (v // 3)
            entrou += 1
        if completou_teto:
            impeto_teto_efootbase[cid] = completou_teto
            card["nx"] = [[i, nx[i]] for i in range(26) if nx[i]]
        if entrou:
            if efb.get("nome") and efb["nome"] not in nmn:
                nmn.append(efb["nome"])
            de_onde = ((de_onde + " + efootbase") if de_onde
                       else "impeto_efootbase.json")
            impeto_completado_efootbase[cid] = entrou
            card["nm"] = [[i, nm[i]] for i in range(26) if nm[i]]
            card["nx"] = [[i, nx[i]] for i in range(26) if nx[i]]
            card["nmn"] = nmn

    # -----------------------------------------------------------------
    #  O `nm` SAI DA LISTA DE IMPETOS — 16/08/2026
    #
    #  ⛔ POR QUE ISTO EXISTE. A fusao acima junta VETORES de 26 numeros sem
    #     saber quais impetos os produziram. Quando um card tem DOIS impetos
    #     que tocam o MESMO atributo, cada fonte so conhece um deles:
    #
    #       o efscout_impeto_por_card traz 4 atributos por card (medido:
    #       nunca 7, nunca 8) — ou seja, UM impeto so;
    #       o efootbase completa o que ficou vazio, mas encontra o atributo
    #       compartilhado JA COM VALOR e sai fora (o `continue` la em cima).
    #
    #     Resultado: o segundo impeto e descartado naquele atributo.
    #     Medido em 16/08, em 8 cards — Messi, Kane, Haaland, Bellingham,
    #     Alvarez, Lisandro Martinez, Pau Cubarsi, Felix Nmecha. O motor
    #     rodou os oito com um atributo mais baixo do que o jogo da.
    #
    #  ⛔ E NAO ADIANTA TROCAR AQUELE `continue` POR SOMA: isso dobraria a
    #     conta quando duas fontes falam do MESMO impeto — que e exatamente
    #     o que aquela linha evita. A regra de la nao e boba; ela e o melhor
    #     possivel enquanto o sistema fundir vetor sem saber o impeto.
    #
    #  ✅ O CERTO e derivar. A Equacao 1, passo 5, medida no jogo em 04/08
    #     com 265 medicoes e zero erro: "para cada impeto ativo que pegue o
    #     atributo: x += valor". Com a LISTA de impetos, a conta e essa e
    #     acabou — sem ambiguidade, sem `continue`, sem perda.
    #
    #  So entra quando a lista diz `valor`, isto e: os impetos daquele card
    #  foram identificados E conferidos contra o proprio dado. Card em
    #  `nao_sei` nao e tocado.
    # -----------------------------------------------------------------
    #  🔴 TRAVA, 16/08 — NAO MEXER EM CARD QUE TEM `nx`.
    #
    #     Achado no Eden Hazard, no primeiro uso de verdade. Ele guarda o
    #     impeto em DOIS pedacos: `nm` = quanto vale AGORA (degrau 1) e
    #     `nx` = quanto ainda pode subir. A base tinha posto nm=1 e nx=3
    #     (tem 1, chega a 4). A derivacao abaixo so conhece o `nm`: ela
    #     escreveu nm=4 e deixou o nx=3 — e o card passou a valer 4 agora
    #     E mais 3 depois. Numero inventado, do nada.
    #
    #     A lista de impetos ainda nao sabe separar "quanto esta ativo" de
    #     "quanto e o teto". Enquanto nao souber, ela NAO manda nesses cards.
    #     Sao 363 na base de 16/08.
    #
    #     ⛔ Quando isso for resolvido, a trava sai — mas so com o `nx`
    #        saindo da MESMA lista. Nunca por um lado so: foi exatamente
    #        assim que este defeito nasceu.
    #  🔴 A TRAVA, 2a versao — 16/08. A PRIMEIRA ESTAVA ERRADA DOS DOIS LADOS.
    #
    #     A 1a trava pulava card que tem `nx` (o teto do condicional). Medido:
    #       - NAO protegia quem devia: o `nx` de varios cards so e preenchido
    #         numa passada DEPOIS deste laco, entao na hora de olhar ainda
    #         estava vazio. O Eden Hazard passou e teve o numero estragado —
    #         nm=1 virou nm=4 com o nx=3 intacto: a carta passou a valer 7.
    #       - E pulava quem PRECISAVA: os 8 cards do defeito TEM `nx`, entao
    #         a trava excluia exatamente quem ela devia consertar.
    #
    #     A TRAVA CERTA nao depende de ordem nenhuma e sai do proprio defeito:
    #     o que se perdia era a contribuicao de UM impeto num atributo que
    #     DOIS impetos tocam. Card de um impeto so NAO TEM o que perder.
    #
    #        so deriva quando o card tem DOIS OU MAIS impetos.
    #
    #     Medido em 16/08: toca 104 cards, muda 8 — os oito conhecidos.
    #     O Hazard, com um impeto so, fica de fora por construcao.
    _sep = IMPETOS_SEPARADOS.get(str(cid))
    if _sep and len(_sep.get("impetos") or []) < 2:
        _sep = None
        nm_pulado_por_um_impeto += 1
    if _sep and _sep.get("estado") == "valor" and _sep.get("impetos"):
        _novo = [0] * 26
        for _it in _sep["impetos"]:
            _niv = _it.get("nivel")
            if not _niv:
                _novo = None
                break
            for _a in (_it.get("atributos") or []):
                if 0 <= _a < 26:
                    _novo[_a] += _niv
        if _novo is not None:
            _antes = {i: nm[i] for i in range(26) if nm[i]}
            _depois = {i: _novo[i] for i in range(26) if _novo[i]}
            if _antes != _depois:
                nm_corrigido_pela_lista.append(
                    (cid, card.get("nome"),
                     [(i, _antes.get(i), _depois.get(i))
                      for i in sorted(set(_antes) | set(_depois))
                      if _antes.get(i) != _depois.get(i)]))
            nm = _novo
            card["nm"] = [[i, nm[i]] for i in range(26) if nm[i]]
            card["nmn"] = [("%s +%d" % (x.get("nome"), x.get("nivel")))
                           for x in _sep["impetos"]]
            de_onde = "a lista de impetos separada (dados/impetos_por_card.json)"
            nm_veio_da_lista += 1

    fonte.setdefault(cid, {})["impeto"] = de_onde or "nenhuma"
    impeto_fonte_conta[de_onde or "nenhuma"] += 1

# ---------------------------------------------------------------------------
# 4b) O TETO DO CONDICIONAL — PASSADA FINAL, 16/08/2026
#
# ORDEM DO LUIS, 16/08, olhando a foto do Messi:
#   "Precisao, efeito +4. E no outro, Protecao de Posse, EFEITO MAXIMO +3.
#    Efeito maximo significa que e um, dois e tres."
#
# No jogo o impeto condicional mostra "Efeito maximo: +3" — o card comeca no
# +1 e sobe ate +3. O nosso `nm` guarda o que vale sempre e o `nx` o que ainda
# falta pro teto. Havia cards com o nm em +1 e o nx VAZIO: o sistema nao sabia
# que aquele atributo ainda subia.
#
# Esta passada e a garantia: roda por cima de TODOS os cards, depois de toda a
# precedencia, e so faz uma coisa — se o efootbase mostra um teto maior do que
# o nosso (nm + nx), a diferenca entra no nx. Nunca reduz, nunca sobrescreve o
# nm. Fica aqui no fim de proposito: nao depende de qual fonte ganhou.
# ---------------------------------------------------------------------------
# ⛔ 16/08 — O ORFAO CEDE O LUGAR AO EFOOTBASE.
#    Ordem do Luis: "nao e possivel que nao exista banco nenhum que ja tenha o
#    impeto deles". Estava certo: 12 dos 17 cards com boostId orfao ja vinham
#    com o impeto na coleta (Hazard = Rompe-barreira +4, Cahill = Guardiao +4...).
#    Nao entravam porque o codigo orfao ocupava o lugar sem trazer valor nenhum.
#    ORFAO NAO E DADO, E BURACO: se o card tem boostId orfao e nenhuma fonte
#    traduziu, o efeito do efootbase entra INTEIRO, do zero.
orfao_curado = {}
for cid, card in registro.items():
    if not card.get("impeto_orfao"):
        continue
    if card.get("nm") or card.get("nx"):
        continue                       # alguma fonte salvou: nao mexe
    efb = efootbase_imp.get(str(cid).split("@")[0])
    if not efb or vazio(efb.get("efeito_maximo")):
        continue
    nmd, nxd = {}, {}
    for par in efb.get("efeito_maximo") or []:
        try:
            i, v = int(par[0]), int(par[1])
        except Exception:
            continue
        if not (0 <= i < 26) or v <= 0:
            continue
        nmd[i] = v // 3
        nxd[i] = v - (v // 3)
    if not nmd:
        continue
    card["nm"] = [[i, nmd[i]] for i in sorted(nmd) if nmd[i]]
    card["nx"] = [[i, nxd[i]] for i in sorted(nxd) if nxd[i]]
    nome_efb = efb.get("nome")
    if nome_efb:
        card["nmn"] = [nome_efb]
    fonte.setdefault(cid, {})["impeto"] = "impeto_efootbase.json (orfao curado)"
    orfao_curado[str(cid).split("@")[0]] = len(nmd)

teto_final = {}
for cid, card in registro.items():
    efb = efootbase_imp.get(str(cid).split("@")[0])
    if not efb or vazio(efb.get("efeito_maximo")):
        continue
    nmd = {}
    for par in card.get("nm") or []:
        nmd[int(par[0])] = nmd.get(int(par[0]), 0) + int(par[1])
    nxd = {}
    for par in card.get("nx") or []:
        nxd[int(par[0])] = nxd.get(int(par[0]), 0) + int(par[1])
    mexeu = 0
    for par in efb.get("efeito_maximo") or []:
        try:
            i, v = int(par[0]), int(par[1])
        except Exception:
            continue
        if not (0 <= i < 26) or v <= 0:
            continue
        atual = nmd.get(i, 0) + nxd.get(i, 0)
        if v > atual:
            nxd[i] = nxd.get(i, 0) + (v - atual)
            mexeu += 1
    if mexeu:
        card["nx"] = [[i, nxd[i]] for i in sorted(nxd) if nxd[i]]
        teto_final[cid] = mexeu
if teto_final:
    for cid, n in teto_final.items():
        impeto_teto_efootbase[cid] = impeto_teto_efootbase.get(cid, 0) + n

# ⛔ 16/08 — A LISTA DE QUEM MUDOU, gravada aqui e nao deduzida depois.
#    O refazer_o_impeto_novo.py tentava DESCOBRIR quem mudou comparando a base
#    com o efootbase — mas depois da correcao os dois batem, entao ele nao
#    achava mais ninguem e 182 cards ficavam de fora da fila. Quem sabe quem
#    mudou e quem mudou: este arquivo.
_mudou = {}
for cid, n in orfao_curado.items():
    _mudou.setdefault(cid, {"impeto_novo": 0, "teto_corrigido": 0})
    _mudou[cid]["impeto_novo"] += n
for cid, n in impeto_completado_efootbase.items():
    c0 = str(cid).split("@")[0]
    _mudou.setdefault(c0, {"impeto_novo": 0, "teto_corrigido": 0})
    _mudou[c0]["impeto_novo"] += n
for cid, n in impeto_teto_efootbase.items():
    c0 = str(cid).split("@")[0]
    _mudou.setdefault(c0, {"impeto_novo": 0, "teto_corrigido": 0})
    _mudou[c0]["teto_corrigido"] += n
#  16/08 — os cards cujo `nm` foi CORRIGIDO pela lista de impetos separada.
#  Eles rodaram com um atributo mais baixo do que o jogo da; a linha deles
#  esta errada e tem de ser refeita. Entram na MESMA porta que o resto:
#  o refazer_o_impeto_novo.py le o IMPETO-MUDOU.json e poe na frente da fila.
for _cid, _nome, _dif in nm_corrigido_pela_lista:
    _c0 = str(_cid).split("@")[0]
    _mudou.setdefault(_c0, {"impeto_novo": 0, "teto_corrigido": 0})
    _mudou[_c0]["impeto_corrigido"] = len(_dif)
try:
    with open("IMPETO-MUDOU.json", "w", encoding="utf-8") as _f:
        json.dump({
            "_o_que_e": ("Os cards cujo IMPETO mudou nesta rodada do "
                         "UNIFICAR-BASE. A nota deles foi calculada com o "
                         "impeto velho: o motor precisa rodar a linha de novo."),
            "_quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "_como_usar": "o refazer_o_impeto_novo.py le daqui e poe na frente da fila",
            "cards": _mudou,
        }, _f, ensure_ascii=False, indent=1)
    print("Gravado: IMPETO-MUDOU.json (%d cards)" % len(_mudou))
except Exception as _e:
    print("nao consegui gravar o IMPETO-MUDOU.json: %s" % _e)

# ---------------------------------------------------------------------------
#  O QUE A LISTA DE IMPETOS CONSERTOU — 16/08/2026
#  Fica na tela E em arquivo, porque a janela do console e ilegivel.
# ---------------------------------------------------------------------------
print("")
print("  O NM SAIU DA LISTA DE IMPETOS ..... %d cards" % nm_veio_da_lista)
print("  pulados por terem um impeto so ......... %d cards" % nm_pulado_por_um_impeto)
if nm_corrigido_pela_lista:
    # ⛔ 16/08 15h45 — ESTE AVISO MANDAVA REFAZER PARA SEMPRE, E ESTAVA ERRADO.
    #    Ele dizia "a linha deles esta ERRADA, rode o REFAZER-DE-VERDADE".
    #    So que este programa monta a base do dados/cards.json, que continua
    #    com o numero velho — entao ele CORRIGE as mesmas cartas em TODA
    #    rodada, e gritava a mesma ordem em toda rodada, mesmo depois das
    #    linhas ja terem sido refeitas (foram, em 16/08 as 13h).
    #
    #    O aviso olhava a CORRECAO. Quem precisa ser olhado e o RESULTADO:
    #    a linha que existe hoje foi calculada antes ou depois? Isso quem
    #    responde e o ClubEfootball\A-VOLTA-AUTOMATICA.bat, e e o passo 7.
    print("  ✔ CORRIGI o numero de %d cards a partir da lista de impetos"
          % len(nm_corrigido_pela_lista))
    for _cid, _nome, _dif in nm_corrigido_pela_lista:
        print("     %-24s %s" % ((_nome or "?")[:24],
              " · ".join("atributo %d: %s -> %s" % t for t in _dif)))
    print("     A BASE ja esta certa. Isto se repete a cada rodada porque o")
    print("     dados/cards.json continua com o numero velho — nao e defeito novo.")
    print("     ⚠️ Se a LINHA precisa refazer, quem responde e o")
    print("        ClubEfootball\\A-VOLTA-AUTOMATICA.bat. Nao refaca por este aviso.")
else:
    print("  nenhum numero precisou de conserto.")
try:
    with open("IMPETO-CORRIGIDO.txt", "w", encoding="utf-8") as _f:
        _L = ["O QUE A LISTA DE IMPETOS CORRIGIU — %d cards"
              % len(nm_corrigido_pela_lista), ""]
        for _cid, _nome, _dif in nm_corrigido_pela_lista:
            _L.append("%-18s %-26s %s" % (_cid, (_nome or "?")[:26],
                      " · ".join("atributo %d: de %s para %s" % t for t in _dif)))
        _f.write("\r\n".join(_L) + "\r\n")
except Exception:
    pass

# ===========================================================================
# 5) A FICHA DO IMPETO — a RESPOSTA PRONTA, nao o dado cru
#
# Ordem do Luis (14/08):
#   "quantos impetos o card tem, quantos sao vazios, quantos nao sao e QUAIS
#    SAO ELES. Se e condicional ou nao. O numero que eles alteram."
#
# Ou seja: quem abrir a base nao pode precisar decorar catalogo nenhum. As
# colunas abaixo sao SO DE LEITURA — o `nm` (que e o que o motor usa) nao e
# tocado aqui, so descrito.
# ===========================================================================
DATA_DA_TRAVA = "2024-09-12"   # antes disso a carta nao tem vaga nenhuma

# os 26 atributos na ordem oficial, para escrever o efeito por extenso
ATRIBUTOS_26 = [
    "Ofensividade", "Controle de bola", "Drible", "Posse de bola",
    "Passe rasteiro", "Passe alto", "Finalização", "Cabeceio",
    "Cobrança de falta", "Efeito", "Velocidade", "Aceleração",
    "Potência de chute", "Salto", "Contato físico", "Equilíbrio",
    "Resistência", "Talento defensivo", "Desarme", "Envolv. defensivo",
    "Agressividade", "Talento de goleiro", "Encaixe", "Defesa (GO)",
    "Reflexos", "Alcance"]


def vetor_nm_do_booster(booster):
    """
    O que ESTE impeto soma no `nm` (o que vale sempre), em 26 casas.
    Repete a regra ja fechada do condicional: condicional soma v//3 no nm.
    E exatamente a mesma conta do aplicar_modificadores() — por isso a
    decomposicao fecha em cima do mesmo numero que a base gravou.
    """
    v = [0] * 26
    cond = bool(booster.get("conditional"))
    for par in (booster.get("stat_modifiers") or []):
        try:
            i, x = int(par[0]), int(par[1])
        except Exception:
            continue
        if 0 <= i < 26:
            v[i] += (x // 3) if cond else x
    return tuple(v)


# indice vetor -> boosters que produzem aquele vetor (varios ids dao o mesmo
# efeito: sao as variantes de cor/versao do mesmo impeto)
IMPETOS_POR_VETOR = {}
for _b in (efscout_boosters or []):
    if not isinstance(_b, dict) or not _b.get("stat_modifiers"):
        continue
    IMPETOS_POR_VETOR.setdefault(vetor_nm_do_booster(_b), []).append(_b)
VETORES = list(IMPETOS_POR_VETOR.keys())

# nome EM PORTUGUES, como o jogo mostra: o CAT_dom.json ja traz
# [nome_pt, condicional, modificadores] com o modificador ja no valor do nm.
NOME_PT_POR_VETOR = {}
for _e in (cat_dom or []):
    try:
        nome_pt, cond_pt, mods = _e[0], bool(_e[1]), _e[2]
    except Exception:
        continue
    v = [0] * 26
    for par in mods or []:
        try:
            i, x = int(par[0]), int(par[1])
        except Exception:
            continue
        if 0 <= i < 26:
            v[i] += x
    NOME_PT_POR_VETOR.setdefault(tuple(v), nome_pt)


def nome_do_impeto(booster):
    """Nome em portugues quando o CAT_dom conhece; senao o nome do catalogo."""
    return (NOME_PT_POR_VETOR.get(vetor_nm_do_booster(booster))
            or booster.get("name") or "?")


def escolhe_booster(candidatos, nomes_ja_conhecidos):
    """
    Varios ids dao o mesmo efeito. Se a base ja sabe o NOME do impeto do card
    (campo nmn), fico com o id daquele nome; senao pego o de menor id, que e
    sempre a variante base.
    """
    if nomes_ja_conhecidos:
        alvo = {str(n).strip().lower() for n in nomes_ja_conhecidos}
        for b in candidatos:
            if (b.get("name") or "").strip().lower() in alvo:
                return b
    return sorted(candidatos, key=lambda b: int(b.get("id", 10 ** 9)))[0]


def decompoe_impeto(vetor_alvo, nomes_ja_conhecidos):
    """
    Acha QUAIS impetos do catalogo somam exatamente o `nm` do card.
    Tenta um so; se nao fechar, tenta um par (o card pode ter DOIS impetos e o
    nm e a soma aritmetica deles — o caso do Lisandro, 3 do Duelo + 1 da
    Reconstrucao no atributo 17 = 4).
    Nao fechando exato, devolve None: nome de impeto nao se inventa.
    """
    if not any(vetor_alvo):
        return []
    if vetor_alvo in IMPETOS_POR_VETOR:
        return [escolhe_booster(IMPETOS_POR_VETOR[vetor_alvo], nomes_ja_conhecidos)]
    for v in VETORES:
        if not any(v):
            continue
        if all(v[i] <= vetor_alvo[i] for i in range(26)):
            resto = tuple(vetor_alvo[i] - v[i] for i in range(26))
            if any(resto) and resto in IMPETOS_POR_VETOR:
                return [escolhe_booster(IMPETOS_POR_VETOR[v], nomes_ja_conhecidos),
                        escolhe_booster(IMPETOS_POR_VETOR[resto], nomes_ja_conhecidos)]
    return None


# datas-lancamento-cartas.json e a segunda fonte de data (a primeira e o `dt`,
# que ja veio do efHub/box_por_card la em cima).
DATAS_EXTRA = {}
if isinstance(datas_lancamento, dict):
    DATAS_EXTRA = datas_lancamento.get("datas") or {}


def data_do_card(cid, card):
    d = card.get("dt")
    if isinstance(d, str) and len(d) >= 10:
        return d[:10]
    raiz = str(cid).split("@")[0]
    d = DATAS_EXTRA.get(raiz)
    if isinstance(d, str) and len(d) >= 10:
        return d[:10]
    return None


# como a fonte do impeto se chama na coluna de leitura (texto curto)
APELIDO_DA_FONTE = {
    "impeto_conferido_no_jogo.json": "conferido no jogo",
    "efscout_impeto_por_card.json": "efscout",
    "boostId do efHub + efscout_boosters.json": "boostId",
    "nm de dados/cards.json": "cards.json",
    None: "nenhuma",
    "nenhuma": "nenhuma",
}

# ---------------------------------------------------------------------------
# O CONFERIDO ENTRA ANTES DO IMPETO E GANHA DE TODO MUNDO
# ---------------------------------------------------------------------------
# Ordem do Luis, 14/08/2026. Tem de rodar ANTES do bloco do impeto: e la que se
# calcula o vetor, os nomes e a frase da situacao. Aplicar depois deixava o card
# com o nm certo e a frase errada ('A COLETAR' num card ja conferido).
# O `poe()` recusa valor vazio de proposito (fonte
# vazia nao pode apagar dado bom). Mas o conferido e outra coisa: vazio ali FOI
# medido. Por isso ele grava direto, sem passar pelo poe().
CONFERIDOS_GERAL = (conferido_geral.get("conferidos", {})
                    if isinstance(conferido_geral, dict) else {})
aplicados_conferido = []
for _cid, _campos in CONFERIDOS_GERAL.items():
    if not isinstance(_campos, dict):
        continue
    for _alvo in [k for k in registro if str(k).split("@")[0] == str(_cid)]:
        for _campo, _info in _campos.items():
            if not isinstance(_info, dict) or "valor" not in _info:
                continue
            _antes = registro[_alvo].get(_campo)
            registro[_alvo][_campo] = _info["valor"]
            fonte.setdefault(_alvo, {})[_campo] = "CONFERIDO"
            fonte[_alvo]["_conferido_" + _campo] = _info.get("como", "")
            aplicados_conferido.append((_alvo, _campo, _antes, _info["valor"]))


conta_impeto = Counter()          # situacao -> quantos (so cards base)
conta_quantos = Counter()         # 0/1/2 -> quantos (so cards base)
nao_decompostos = []              # (id, nome, nm) que o catalogo nao fecha
vagas_corrigidas = []             # (id, nome, sl_antes, sl_depois, data, motivo)
a_coletar = []                    # (id, nome, ovr, data)

for cid, card in registro.items():
    eh_card_base = "@" not in str(cid)

    # ---- o vetor de 26 casas que o card realmente tem hoje ----------------
    vetor = [0] * 26
    for par in (card.get("nm") or []):
        try:
            i, v = int(par[0]), int(par[1])
        except Exception:
            continue
        if 0 <= i < 26:
            vetor[i] += v
    vetor = tuple(vetor)
    tem = any(vetor)

    # ---- QUAIS SAO ELES --------------------------------------------------
    achados = decompoe_impeto(vetor, card.get("nmn"))
    if achados is None:
        nomes = ["não decomposto"]
        condic = []
        quantos = 1 if tem else 0
        if eh_card_base:
            nao_decompostos.append((cid, card.get("nome"), card.get("nm")))
    else:
        nomes = [nome_do_impeto(b) for b in achados]
        condic = [bool(b.get("conditional")) for b in achados]
        quantos = len(achados)

    # ---- o efeito por extenso -------------------------------------------
    efeito = " · ".join("%s +%d" % (ATRIBUTOS_26[i], vetor[i])
                        for i in range(26) if vetor[i]) or "sem efeito"

    # ---- A VAGA: a trava da data conserta o sl = [1,1], que nao existe ----
    sl = card.get("sl")
    sl = list(sl) if isinstance(sl, (list, tuple)) and len(sl) == 2 else None
    data_lanc = data_do_card(cid, card)
    corrigida = False
    if sl == [1, 1]:
        antes = [1, 1]
        if data_lanc and data_lanc < DATA_DA_TRAVA:
            sl = [0, 0]
            motivo = "lancada antes de %s: nao tem vaga nenhuma" % DATA_DA_TRAVA
        else:
            # posterior a trava (ou data desconhecida): NUNCA zerar por nao ter
            # achado impeto — hexagono ausente nao prova nada. Vira a coletar.
            sl = [0, 1]
            motivo = ("lancada em %s (depois da trava)" % data_lanc) if data_lanc \
                else "sem data conhecida: fica com uma vaga, a conferir"
        card["sl"] = sl
        corrigida = True
        fonte.setdefault(cid, {})["sl"] = "corrigido pela trava da data"
        if eh_card_base:
            vagas_corrigidas.append((cid, card.get("nome"), antes, sl, data_lanc, motivo))

    vagas_livres = int(sl[1] == 1) if sl else 0   # ⛔ nunca 2: sl[0]=1 nao existe

    # ---- a situacao em uma frase ----------------------------------------
    if tem:
        situacao = "tem ímpeto"
    elif corrigida and sl == [0, 0]:
        situacao = "vaga impossível — CORRIGIDA"
    elif vagas_livres:
        situacao = "vaga livre — A COLETAR"
    else:
        situacao = "sem ímpeto e sem vaga"

    de_onde_bruto = fonte.get(cid, {}).get("impeto")
    de_onde = APELIDO_DA_FONTE.get(de_onde_bruto, de_onde_bruto or "nenhuma")

    card["impeto_quantos"] = quantos
    card["impeto_tem"] = bool(tem)
    card["impeto_nomes"] = nomes if tem else []
    card["impeto_condicional"] = condic if tem else []
    card["impeto_efeito"] = efeito if tem else ""
    card["impeto_soma"] = sum(vetor)
    card["vagas_livres"] = vagas_livres
    card["impeto_situacao"] = situacao
    card["impeto_de_onde"] = de_onde if tem else "nenhuma"

    if eh_card_base:
        conta_impeto[situacao] += 1
        conta_quantos[quantos] += 1
        if situacao == "vaga livre — A COLETAR":
            a_coletar.append((cid, card.get("nome"), card.get("ovr"), data_lanc))

# quantos impetos condicionais no total (contando os dois de um card com dois)
condicionais_total = sum(
    sum(1 for x in (c.get("impeto_condicional") or []) if x)
    for cid, c in registro.items() if "@" not in str(cid))

# ---------------------------------------------------------------------------
# OS 15 CAMPOS QUE VEM DO BANCO — e nao daqui. 16/08/2026, 15h45
# ---------------------------------------------------------------------------
# ⛔ AQUI MORAVAM DOIS REMENDOS, E ELES SAIRAM DE PROPOSITO.
#
#    Durante o dia 16/08 este programa aprendeu a ler mais dois arquivos
#    soltos — o dados/efhub_bruto_por_card.json e o dados/metadados_da_tela.json
#    — para trazer campos que estavam salvos e nao chegavam em quem calcula.
#    Funcionou: 25.479 valores entraram. E era o sistema velho.
#
#    Ordem do Luis, no mesmo dia:
#      "a base da transformacao e ler os dados de UM LUGAR UNICO, que e o banco
#       de dados. Nao esquece disso nunca."
#
#    Ensinar este programa a ler mais um arquivo AFASTA da fonte unica. Ele ja
#    lia 20; passou a ler 22. Cada campo novo pediria mais uma linha escrita a
#    mao, em mais um lugar — que e como o sistema chegou a ter cinco de-paras e
#    duas pontuacoes maximas.
#
#    Em 16/08 15h28 o ciclo fechou:
#
#        as fontes -> o BANCO -> o BAIXAR-BASE -> este arquivo -> os motores
#
#    Estes campos JA ESTAO no banco, postos la pelo ENTRAR-COM-O-EFHUB, pelo
#    SUBIR-METADADOS-DA-TELA e pelo ESTADOS. Quem os traz de volta e o
#    BAIXAR-BASE.bat, que pergunta ao banco quais colunas existem:
#
#        com  mst  mx  maxOvr  age  wfa  inj  wfu  forma  cond
#        estado_de_cada_campo  nota_maxima_tela  e os tres *_bruto
#
# ⚠️ POR ISSO: rodar o UNIFICAR-BASE SOZINHO deixa a pasta sem eles ate o
#    BAIXAR-BASE rodar. Use o FECHAR-O-CICLO.bat, que trava a ordem:
#        1 unificar   2 subir   3 conferir   e ai o 4 baixar.
#
#    E o SUBIR-BASE nao apaga o que a pasta nao tem: campo vazio nao sobe.
#    Foi conferido em 16/08 — bloco 2 e bloco 3 vazios no conferir.

# ---------------------------------------------------------------------------
# fonte_de_cada_campo: so os campos que o Luis pediu, em texto limpo.
# (as chaves internas _aut_* saem daqui - sao contabilidade minha)
# ---------------------------------------------------------------------------
# `nm` e `sl` entraram na lista em 14/08: a base gravava o valor do impeto e
# nao gravava a procedencia dele — era o furo que o Luis apontou.
# ⛔ os oito que vem do banco SAIRAM desta lista em 16/08 15h45: este programa
#    nao os escreve mais, entao nao tem procedencia para declarar. Quem sabe de
#    onde vieram e o banco, nas colunas metadado_tela_de_onde e visto_na_casca.
CAMPOS_RASTREADOS = ["impeto", "nm", "sl", "vaga", "corpo", "pe_ruim", "box",
                     "orc", "base", "fab", "falta", "modelo"]
for cid, card in registro.items():
    marca = fonte.get(cid, {})
    # o `nm` E o impeto: a procedencia e a mesma, e agora fica escrita nas duas.
    if not marca.get("nm"):
        marca["nm"] = marca.get("impeto") or "nenhuma"
    card["fonte_de_cada_campo"] = {
        campo: marca.get(campo, "nao preenchido")
        for campo in CAMPOS_RASTREADOS
    }

# ---------------------------------------------------------------------------
# COBERTURA - quantos cards tem cada campo preenchido
# ---------------------------------------------------------------------------
CAMPOS_COBERTURA = ["nome", "ovr", "max_ovr", "pos", "np", "sec", "modelo", "orc",
                    "altura", "peso", "pe", "base", "fab", "falta", "raras",
                    "nm", "nx", "nmn", "sl", "corpo", "vaga", "box", "pe_ruim",
                    "dt", "levelCap", "boostId", "tier",
                    # ⚠️ estes oito ficam na conta DE PROPOSITO, e logo depois de
                    #    um UNIFICAR sozinho eles aparecem com 0 preenchidos.
                    #    NAO e defeito: eles vem do banco, pelo BAIXAR-BASE.
                    "com", "mst", "mx", "maxOvr", "age", "wfa", "inj", "wfu"]
total = len(registro)
cobertura = OrderedDict()
for campo in CAMPOS_COBERTURA:
    # vazio CONFERIDO conta como RESPONDIDO, nao como falta: "esse card nao tem"
    # e uma resposta. (Luis, 14/08/2026)
    tem = sum(1 for cid, c in registro.items()
              if (not vazio(c.get(campo)))
              or fonte.get(cid, {}).get(campo) == "CONFERIDO")
    cobertura[campo] = (tem, total - tem)

# ---------------------------------------------------------------------------
# RELATORIO
# ---------------------------------------------------------------------------
L = []
L.append("RELATORIO DA BASE UNICA")
L.append("=" * 70)
L.append("")
L.append("Modo: %s" % ("SO CONFERIR (nada foi gravado)" if SO_CONFERIR else "GRAVACAO"))
L.append("Total de cards na base unica: %d" % total)
L.append("Tecnicos no catalogo (tabela separada): %d" % (len(tecnicos) if tecnicos else 0))
L.append("")

L.append("FONTES LIDAS")
L.append("-" * 70)
for nome_arq, quantos in FONTES_LIDAS.items():
    L.append("  %-42s %6d registros" % (nome_arq, quantos))
L.append("")

if AVISOS:
    L.append("AVISOS (o que faltou, e segui em frente)")
    L.append("-" * 70)
    for a in AVISOS:
        L.append("  - " + a)
    L.append("")

L.append("COBERTURA DE CADA CAMPO (preenchidos / faltando)")
L.append("-" * 70)
for campo, (tem, falta) in cobertura.items():
    pct = (100.0 * tem / total) if total else 0
    L.append("  %-12s %6d preenchidos  %6d faltando   (%5.1f%%)" % (campo, tem, falta, pct))
L.append("")

if impeto_completado_efootbase:
    L.append("O QUE O EFOOTBASE COMPLETOU (16/08)")
    L.append("-" * 70)
    L.append("  %d cards ganharam atributo de impeto que NENHUMA outra fonte tinha"
             % len(impeto_completado_efootbase))
    L.append("  %d atributos ao todo" % sum(impeto_completado_efootbase.values()))
    L.append("  (nada foi sobrescrito: so entrou onde estava vazio)")
    if impeto_teto_efootbase:
        L.append("  %d cards tiveram o TETO do condicional corrigido "
                 "(%d atributos)" % (len(impeto_teto_efootbase),
                                     sum(impeto_teto_efootbase.values())))
        L.append("  — o card tinha o +1 mas o sistema nao sabia que subia ate +3")
    L.append("")

if orfao_curado:
    L.append("ORFAOS CURADOS PELO EFOOTBASE (16/08)")
    L.append("-" * 70)
    L.append("  %d cards tinham um codigo de impeto que ninguem sabia traduzir" % len(orfao_curado))
    L.append("  e ficavam SEM impeto nenhum. O efootbase tinha o efeito deles.")
    L.append("")

L.append("DE ONDE VEIO O IMPETO DE CADA CARD")
L.append("-" * 70)
for de_onde, quantos in impeto_fonte_conta.most_common():
    L.append("  %-45s %6d cards" % (de_onde, quantos))
L.append("")

# -- BLOCO IMPETO: a resposta pronta, sem precisar abrir o catalogo ---------
L.append("ÍMPETO — A FICHA PRONTA (só os cards base, sem os registros id@POS)")
L.append("-" * 70)
total_base = sum(conta_quantos.values())
com_impeto = conta_quantos[1] + conta_quantos[2]
L.append("  cards base ........................... %6d" % total_base)
L.append("  COM ímpeto ........................... %6d" % com_impeto)
L.append("  SEM ímpeto ........................... %6d" % conta_quantos[0])
L.append("     com 1 ímpeto ...................... %6d" % conta_quantos[1])
L.append("     com 2 ímpetos ..................... %6d" % conta_quantos[2])
L.append("  ímpetos CONDICIONAIS (contando os dois) %6d" % condicionais_total)
L.append("  NAO DECOMPOSTOS (o catálogo não fecha)  %6d" % len(nao_decompostos))
L.append("")
L.append("  Situação de cada card:")
for sit, quantos in conta_impeto.most_common():
    L.append("     %-32s %6d" % (sit, quantos))
L.append("")
L.append("  Vagas de ímpeto (depois da trava da data):")
dist_vagas = Counter(tuple(c.get("sl") or []) for cid, c in registro.items()
                     if "@" not in str(cid))
for par, quantos in sorted(dist_vagas.items(), key=lambda x: -x[1]):
    L.append("     sl = %-10s %6d cards" % (list(par), quantos))
com_duas = sum(1 for cid, c in registro.items()
               if "@" not in str(cid) and c.get("vagas_livres", 0) > 1)
L.append("     cards com 2 vagas livres (nao pode existir): %d" % com_duas)
L.append("")
L.append("  VAGAS IMPOSSIVEIS (sl = [1,1]) consertadas pela data: %d" % len(vagas_corrigidas))
for cid, nome, antes, depois, dl, motivo in vagas_corrigidas[:40]:
    L.append("     %-16s %-26s %s -> %s  (%s)" % (cid, (nome or "?")[:26], antes, depois, motivo))
if len(vagas_corrigidas) > 40:
    L.append("     ... e mais %d (a lista inteira esta na base_unica.json)" % (len(vagas_corrigidas) - 40))
L.append("")
L.append("  A COLETAR (vaga livre de verdade, falta o dado): %d cards" % len(a_coletar))
L.append("     lista completa em IMPETO-A-COLETAR.txt")
if nao_decompostos:
    L.append("")
    L.append("  NAO DECOMPOSTOS — o nm existe mas nenhum impeto (nem par) do")
    L.append("  catalogo soma exatamente esse vetor. Nome nao se inventa:")
    for cid, nome, nm in nao_decompostos[:40]:
        L.append("     %-16s %-26s nm=%s" % (cid, (nome or "?")[:26], json.dumps(nm)[:80]))
    if len(nao_decompostos) > 40:
        L.append("     ... e mais %d" % (len(nao_decompostos) - 40))
L.append("")

L.append("CONFLITOS ENTRE FONTES: %d" % len(conflitos))
L.append("-" * 70)
if not conflitos:
    L.append("  Nenhum conflito. As fontes concordam onde se cruzam.")
else:
    por_campo = Counter(c["campo"] for c in conflitos)
    L.append("  Resumo por campo:")
    for campo, quantos in por_campo.most_common():
        L.append("     %-12s %5d conflitos" % (campo, quantos))
    L.append("")
    L.append("  Lista (ate 300 primeiros):")
    for c in conflitos[:300]:
        L.append("   - card %s (%s), campo '%s'" % (c["card"], c["nome"], c["campo"]))
        L.append("       %s diz: %s" % (c["fonte_anterior"], json.dumps(c["valor_anterior"], ensure_ascii=False)[:160]))
        L.append("       %s diz: %s" % (c["fonte_nova"], json.dumps(c["valor_novo"], ensure_ascii=False)[:160]))
        L.append("       GANHOU: %s  (%s)" % (c["ganhou"], c["por_que"]))
    if len(conflitos) > 300:
        L.append("   ... e mais %d conflitos (a lista completa esta em dados/base_unica.json)" % (len(conflitos) - 300))
L.append("")

L.append("IMPETO QUE NAO DEU PARA RESOLVER: %d cards" % len(nao_resolvidos))
L.append("-" * 70)
L.append("  (boostId que o catalogo efscout_boosters.json nao conhece e sem")
L.append("   nenhuma fonte melhor. E exatamente o que falta recoletar.)")
if not nao_resolvidos:
    L.append("  Nenhum. Todo impeto conhecido foi resolvido.")
else:
    for cid, nome, orfs in nao_resolvidos:
        L.append("   - card %s (%s) -> boostId orfao: %s" % (cid, nome, orfs))
    ids_orfaos = sorted({o for _, _, orfs in nao_resolvidos for o in orfs if isinstance(o, int)})
    L.append("")
    L.append("  Lista unica de boostIds orfaos para recoletar: %s" % (ids_orfaos,))
L.append("")

todos_orfaos = sorted({o for orfs in orfaos_por_card.values() for o in orfs if isinstance(o, int)})
if todos_orfaos:
    L.append("BOOSTIDS ORFAOS EM QUALQUER CARD (mesmo os que outra fonte salvou): %s" % (todos_orfaos,))
    L.append("")

L.append("O QUE FAZER COM CONFLITO")
L.append("-" * 70)
L.append("  1. Quem ganha ja esta decidido no precedencia.json. Este script so obedece.")
L.append("  2. Se o vencedor estiver errado, o conserto e no precedencia.json - nao aqui.")
L.append("  3. Impeto conferido DENTRO do jogo ganha de todo mundo, sempre.")
relatorio = "\n".join(L)

# ===========================================================================
#  A VARIACAO DE POSICAO HERDA A CARTA ORIGINAL — 18/08/2026
# ===========================================================================
#  ORDEM DO LUIS, 18/08, perguntado com estas palavras — "quando voce compra
#  uma posicao para uma carta, muda alguma coisa nela alem da posicao?":
#
#      "Nao muda nada nao, so muda a posicao. So isso, muda nada,
#       absolutamente nada."
#
#  ⛔ O QUE ISTO CONSERTA — medido em 18/08 na base de 6.710 registros:
#
#        cartas de verdade ....................... 2.785
#        variacoes de posicao (`100995@PD`) ...... 3.684
#
#     As 3.684 variacoes estavam VAZIAS EM TUDO: estilo de jogo da IA, pe ruim,
#     nivel maximo, nome da box — 3.684 de 3.684, cem por cento. E isso fazia a
#     conta de pendencia dizer que faltava coletar 3.990 fichas quando o buraco
#     real e de 360. Nao era coleta que faltava: era COPIA.
#
#     Comprar posicao nao muda pe ruim, nem altura, nem atributo, nem estilo.
#     E a mesma carta. Entao a variacao herda tudo o que ela nao tem.
#
#  ⛔ SO PREENCHE BURACO. Campo que a variacao JA TEM nunca e sobrescrito —
#     se um dia o efHub responder algo proprio dela, a resposta dele ganha.
#  ⛔ NUNCA COPIA `id` NEM `pos`. Sao as duas unicas coisas que mudam de
#     verdade — copiar a posicao apagaria a razao de a variacao existir.
# ===========================================================================
NAO_HERDA = {"id", "pos", "fonte_de_cada_campo", "estado_de_cada_campo"}
_orig = {}
for _cid, _c in registro.items():
    if "@" not in str(_cid):
        _orig[str(_cid)] = _c
_herdou_cartas = 0
_herdou_campos = Counter()
for _cid, _c in registro.items():
    if "@" not in str(_cid):
        continue
    _mae = _orig.get(str(_cid).split("@")[0])
    if not _mae:
        continue
    _mexeu = False
    for _k, _v in _mae.items():
        if _k in NAO_HERDA:
            continue
        if _v in (None, "", [], {}):
            continue
        if _c.get(_k) in (None, "", [], {}):
            _c[_k] = _v
            _herdou_campos[_k] += 1
            _mexeu = True
    if _mexeu:
        _herdou_cartas += 1
        _f = _c.setdefault("fonte_de_cada_campo", {})
        if isinstance(_f, dict):
            _f["_herdado_da_carta_original"] = str(_cid).split("@")[0]

print("")
print("=" * 70)
print("  A VARIACAO DE POSICAO HERDOU A CARTA ORIGINAL")
print("=" * 70)
print("  ordem do Luis, 18/08: 'comprar posicao nao muda nada, so a posicao'")
print("  variacoes que receberam alguma coisa ... %d" % _herdou_cartas)
if _herdou_campos:
    print("  os campos que mais faltavam:")
    for _k, _n in _herdou_campos.most_common(14):
        print("     %-24s %5d variacoes" % (_k, _n))
print("  ⛔ campo que a variacao ja tinha nao foi tocado. `id` e `pos` nunca.")
print("=" * 70)

# ---------------------------------------------------------------------------
# GRAVACAO (so cria arquivo novo; nunca toca em arquivo existente)
# ---------------------------------------------------------------------------
print(relatorio)

if SO_CONFERIR:
    print("\n[--conferir] Nada foi gravado.")
else:
    # ---------------------------------------------------------------------
    # OS INSUMOS ENTRAM NA BASE — "o motor tem que procurar num lugar so"
    # (Luis, 14/08/2026). Ate aqui a base tinha o CARD e o motor abria mais
    # quatro arquivos por fora. Agora vai tudo junto.
    # ---------------------------------------------------------------------
    _molde = ler_json(os.path.join("dados", "molde.json"), [])
    _tec = ler_json("tecnicos.json", {})
    _hab = ler_json("HAB_EFEITOS_FINAL.json", {})
    _blo = ler_json("habilidades_por_posicao.json", {})
    _corpo = ler_json("CORPO_CHAVES.json", {})
    _nomes = ler_json("NOMES-HABILIDADES.json", {})

    saida = {
        "gerado_por": "unificar_base.py",
        "o_que_e": "A BASE UNICA: os cards E os insumos do motor, num arquivo so.",
        "o_motor_le_daqui": {
            "cards": "um registro por card, com fonte_de_cada_campo",
            "molde": "o denominador da nota — 19 funcoes",
            "tecnicos": "CHAVE = id, nunca o nome (1.664 tecnicos, 1.528 nomes)",
            "habilidades": "CHAVE = camelCase, nunca o nome PT",
            "bloqueio": "em que funcao cada habilidade NAO entra",
            "corpo_chaves": "posicao -> nome do campo (medido em 14/08)",
        },
        "conferido": {
            "quantos": len(aplicados_conferido),
            "regra": "campo com fonte CONFERIDO nao e cobrado como falta",
            "aplicados": [{"card": a, "campo": b, "antes": c, "agora": d}
                          for (a, b, c, d) in aplicados_conferido],
        },
        "total_cards": total,
        "fontes_lidas": FONTES_LIDAS,
        "avisos": AVISOS,
        "cobertura": {k: {"preenchidos": v[0], "faltando": v[1]} for k, v in cobertura.items()},
        "impeto_por_fonte": dict(impeto_fonte_conta),
        "impeto_completado_pelo_efootbase": {
            "cards": len(impeto_completado_efootbase),
            "atributos": sum(impeto_completado_efootbase.values()),
            "o_que_e": ("atributos de impeto que nenhuma outra fonte tinha e que "
                        "vieram da coleta do efootbase de 15/08. Nada foi "
                        "sobrescrito — so entrou onde estava vazio."),
        },
        "impeto_teto_corrigido_pelo_efootbase": {
            "cards": len(impeto_teto_efootbase),
            "atributos": sum(impeto_teto_efootbase.values()),
            "o_que_e": ("cards que tinham o condicional em +1 mas com o nx vazio: "
                        "o sistema nao sabia que aquele atributo ainda subia ate "
                        "+3. A diferenca entrou no nx. Nunca reduziu nada."),
        },
        "impeto_resumo": {
            "cards_base": total_base,
            "com_impeto": com_impeto,
            "sem_impeto": conta_quantos[0],
            "com_1_impeto": conta_quantos[1],
            "com_2_impetos": conta_quantos[2],
            "condicionais": condicionais_total,
            "nao_decompostos": len(nao_decompostos),
            "a_coletar": len(a_coletar),
            "vagas_corrigidas_pela_data": len(vagas_corrigidas),
            "por_situacao": dict(conta_impeto),
        },
        "impeto_vagas_corrigidas": [
            {"card": c, "nome": n, "sl_antes": a, "sl_depois": d,
             "data_lancamento": dl, "por_que": m}
            for c, n, a, d, dl, m in vagas_corrigidas],
        "impeto_a_coletar": [
            {"card": c, "nome": n, "ovr": o, "data_lancamento": dl}
            for c, n, o, dl in a_coletar],
        "impeto_nao_decomposto": [
            {"card": c, "nome": n, "nm": nm} for c, n, nm in nao_decompostos],
        "conflitos": conflitos,
        "impeto_nao_resolvido": [{"card": c, "nome": n, "orfaos": o} for c, n, o in nao_resolvidos],
        "cards": list(registro.values()),

        # ---- OS INSUMOS DO MOTOR, no mesmo arquivo -----------------------
        "molde": _molde,
        "tecnicos_catalogo": _tec,
        "habilidades": _hab,
        "bloqueio": _blo,
        "corpo_chaves": (_corpo or {}).get("corpo"),
        "nomes_habilidade": (_nomes or {}).get("nomes"),
        "tecnicos": tecnicos,   # catalogo, nao e por card: entra como tabela separada
    }
    destino_json = os.path.join(AQUI, "dados", "base_unica.json")
    os.makedirs(os.path.dirname(destino_json), exist_ok=True)
    with open(destino_json, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False)
    destino_txt = os.path.join(AQUI, "RELATORIO-BASE-UNICA.txt")
    with open(destino_txt, "w", encoding="utf-8") as f:
        f.write(relatorio + "\n")
    # ---- a lista do que falta coletar ------------------------------------
    # Sao os cards com vaga livre de verdade e sem o dado do impeto. Vaga vazia
    # NAO prova que o card nao tem impeto: prova que ninguem foi olhar ainda.
    C = []
    C.append("ÍMPETO — O QUE FALTA COLETAR")
    C.append("=" * 78)
    C.append("")
    C.append("Estes %d cards tem UMA vaga de ímpeto livre e a base ainda nao sabe" % len(a_coletar))
    C.append("qual ímpeto esta la (ou se esta vazia mesmo). Hexágono ausente nao")
    C.append("prova nada — por isso eles ficam AQUI em vez de virar zero na base.")
    C.append("")
    C.append("O BOTAO QUE TRAZ ESSE DADO (nesta ordem, duplo clique):")
    C.append("   1) COLETAR-EFSCOUT.bat        -> baixa o ímpeto de cada card do efScout")
    C.append("   2) APLICAR-IMPETO-EFSCOUT.bat -> escreve o que veio nos arquivos do sistema")
    C.append("   3) UNIFICAR-BASE.bat          -> refaz a base unica com o dado novo")
    C.append("   (o que o efScout nao tiver, so conferindo dentro do jogo e anotando")
    C.append("    no impeto_conferido_no_jogo.json, que ganha de todas as fontes)")
    C.append("")
    C.append("%-16s %-30s %5s  %-12s" % ("ID", "NOME", "OVR", "LANÇAMENTO"))
    C.append("-" * 78)
    for c, n, o, dl in sorted(a_coletar, key=lambda x: -(x[2] or 0)):
        C.append("%-16s %-30s %5s  %-12s" % (c, (n or "?")[:30], o if o is not None else "?",
                                             dl or "sem data"))
    C.append("-" * 78)
    C.append("Total: %d cards a coletar." % len(a_coletar))
    destino_coletar = os.path.join(AQUI, "IMPETO-A-COLETAR.txt")
    with open(destino_coletar, "w", encoding="utf-8") as f:
        f.write("\n".join(C) + "\n")

    print("\nGravado: dados/base_unica.json")
    print("Gravado: RELATORIO-BASE-UNICA.txt")
    print("Gravado: IMPETO-A-COLETAR.txt (%d cards)" % len(a_coletar))
