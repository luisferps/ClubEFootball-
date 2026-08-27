# -*- coding: utf-8 -*-
"""
===============================================================================
  REGRAS DO CARD — O LUGAR ONDE A REGRA MORA
===============================================================================

  ORDEM DO LUIS, 18/08:
    "Esse e o problema de ter tanto arquivo, tanto .bat."

  Ele disse isso depois que a MESMA regra teve que ser consertada em CINCO
  programas diferentes, porque cada um tinha a sua copia da resposta para a
  pergunta "isto e box?". Cinco copias, cinco chances de uma delas ficar para
  tras — e foi o que aconteceu: a regra ja tinha sido consertada uma vez, em
  17/08, e voltou em 18/08 porque o conserto pegou so o ultimo da fila.

  ⛔ ESTE ARQUIVO E A UNICA RESPOSTA. Quem precisa saber o que e box PERGUNTA
     aqui. Nao copia, nao reimplementa, nao "so desta vez".

  Quem pergunta hoje:
     ClubEfootball/programas/braco_efootballdb.py
     ClubEfootball/programas/fila_de_coleta.py
     ClubEfootball/programas/o_vigia.py
     coletar_so_os_furados.py
     tapar_furos.py
     gera_encaixe.py

  ⛔ ELE MORA EM ClubEfootball\\programas\\, NAO NA RAIZ.
     Regra do Luis, 17/08 e repetida em 18/08: "quantas vezes eu tenho que
     falar que e pra colocar os arquivos uteis na pasta do ClubEfootball? A
     pasta raiz nao vai existir mais." Coisa nova vai no ClubEfootball. A raiz
     da v6 e legado — so o que ja esta la.

  Como usar, de qualquer uma das duas pastas:
     import sys as _sys, os as _os
     _AQUI = _os.path.dirname(_os.path.abspath(__file__))
     for _d in (_AQUI,
                _os.path.join(_os.getcwd(), 'ClubEfootball', 'programas'),
                _os.path.join(_os.path.dirname(_AQUI), 'programas')):
         if _os.path.isdir(_d) and _d not in _sys.path:
             _sys.path.insert(0, _d)
     import regras_do_card as REGRA
===============================================================================
"""

import io
import json
import os
import re
import unicodedata

# ---------------------------------------------------------------------------
#  1) DE QUEM E CADA CAMPO
# ---------------------------------------------------------------------------
#  ⛔ Isto nao e documentacao: e a tabela que a fila de coleta e o tapar_furos
#     leem para saber a quem perguntar. Trocar aqui troca no sistema inteiro.
DONO_DO_CAMPO = {
    # BOX e onde voce roda a moeda. Quem LISTA box e o efHub — ele nao "acha",
    # ele publica a box e as cartas de cada uma em /api/public/packs.
    'box': 'efhub',
    # ETIQUETA e o tipo do card e, quando existe, a partida que ele comemora:
    # "Big Time Portugal 23 Jun '26", "Uruguay 2010". Vem do efootballdb, no
    # campo variation_details.name.
    'etiqueta_do_card': 'efootballdb',
}

ARQ_NOMES_DE_BOX = 'NOMES-DE-BOX.json'

# ⛔ A SEGUNDA TRAVA. Medido na base de 18/08: 598 nomes aparecem em UMA carta
#    so, 240 em duas, e apenas 74 em seis ou mais. Etiqueta e coisa de 1 ou 2
#    cartas; box de verdade tem varias. Nome usado por MUITA_CARTA ou mais nao
#    e trocado por ninguem — vai para a briga e o Luis decide.
MUITA_CARTA = 5

# ---------------------------------------------------------------------------
#  ⛔ 18/08 (tarde) — O LUIS DE NOVO: "as boxes continuam com o erro ja
#     detectado". Ele olhava a aba `Boxes anteriores`: 1.163 nomes, e no topo
#     "Big Time 14 Nov '98", "Big Time 13 Jul '94", "Big Time 1 Jul '90" — uma
#     carta cada. Box de 1990 nao existe: o eFootball nem existia.
#
#     O conserto da manha fechou as cinco torneiras que CRIAVAM nome novo, mas
#     nao alcancou o que ja estava gravado, e nao alcancou o PACOTE (a sexta
#     torneira, no patch_pacote do gera_encaixe: ele carimba o nome do
#     box_por_card em cada card, e e desse carimbo que a home monta os blocos).
#
#     Aqui entram as duas unicas provas que dispensam o efHub:
#       1. LIXO — nome vazio, "dummy", "0". Vieram da propria lista do efHub
#          em 18/08, com 30 cartas cada, e viraram duas prateleiras na tela.
#       2. TIPO DE CARD + DATA DE PARTIDA — "Big Time" e o TIPO da carta
#          (palavra do Luis, 18/08: "e um card lancado para comemorar uma
#          partida, por isso vem com a data"). Se o efHub nunca listou aquele
#          nome como box, ele e etiqueta. Idem qualquer nome com data anterior
#          a 2021: nao ha box mais velha que o proprio jogo.
#
#     ⛔ A PROVA NAO SE ESTENDE POR SEMELHANCA. "AC Milan 02-03" e
#        "POTW 26 Oct '23" continuam de pe: sao suspeitos, nao provados. Nome
#        so sai quando da para mostrar por que.
# ---------------------------------------------------------------------------
NOMES_LIXO = {'', '0', 'dummy', 'none', 'null', 'test', 'undefined'}

# O tipo do card entra no lugar do nome da box quando a fonte e o efootballdb.
TIPOS_DE_CARD = ('big time',)

# O eFootball comecou em 2021. Data anterior no nome e a data da PARTIDA que a
# carta comemora — nunca a data de uma box.
ANO_MINIMO_DE_BOX = 2021

_MES = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
_RX_DATA = re.compile(r"\b(\d{1,2})\s+" + _MES + r"\s*'?(\d{2})\b", re.I)
# "AC Milan 02-03", "Manchester United 98-99" — a TEMPORADA da carta Epic.
_RX_TEMPORADA = re.compile(r"\b(\d{2})\s*[-/]\s*(\d{2})\b")
# "Italy 2006", "Brazil 1994" — o ano da selecao que a carta homenageia.
_RX_ANO = re.compile(r"\b(19|20)\d{2}\b")

# ⛔ A PALAVRA QUE SALVA O NOME. Se aparece uma destas, o nome esta se
#    apresentando como box e a data velha nao prova nada contra ele
#    ("Epic Nostalgia 26 Jun '25" fala de carta velha e e box de verdade).
PALAVRAS_DE_BOX = ('pack', 'box', 'selection', 'campaign', 'reward', 'edition',
                   'set', 'vol', 'potw', 'potm', 'pots', 'potd', 'season',
                   'showtime', 'featured', 'nostalgia', 'greats', 'icons',
                   'legends', 'collaboration', 'anniversary', 'downloads')


def e_nome_lixo(nome):
    return str(nome or '').strip().lower() in NOMES_LIXO


def ano_no_nome(nome):
    """O ano que o nome carrega, nos tres formatos que aparecem na base:
       "14 Nov '98" (data da partida) · "02-03" (temporada) · "2006" (ano).
       None quando o nome nao tem data nenhuma."""
    s = str(nome or '')
    m = _RX_DATA.search(s)
    if m:
        a = int(m.group(3))
        return 2000 + a if a < 70 else 1900 + a
    m = _RX_TEMPORADA.search(s)
    if m:
        a = int(m.group(1))
        return 2000 + a if a < 70 else 1900 + a
    m = _RX_ANO.search(s)
    if m:
        return int(m.group(0))
    return None


def fala_de_box(nome):
    """O proprio nome se apresenta como box?"""
    n = norm(nome)
    return any((' ' + p) in (' ' + n) for p in PALAVRAS_DE_BOX)


def e_etiqueta_provada(nome, conhecidas=None, pasta='.'):
    """Da para PROVAR que isto nao e box? So entao devolve True."""
    if not nome:
        return False
    if e_nome_lixo(nome):
        return True
    # ⛔ O TIPO DE CARD GANHA ATE DO efHUB. Medido em 18/08: o efHub publica 19
    #    "packs" cujo nome comeca com Big Time, TODOS com uma carta so — e o
    #    Cristiano de "Big Time Portugal 23 Jun '26" aparece ao mesmo tempo
    #    dentro de Living Legends 2026, que tem 15. O efHub abre uma pagina por
    #    carta; isso nao faz do tipo do card uma box. Palavra do Luis: "Big Time
    #    e o TIPO da carta, um card lancado para comemorar uma partida".
    n = norm(nome)
    if any(n.startswith(t) for t in TIPOS_DE_CARD):
        return True
    if e_nome_de_box(nome, conhecidas, pasta):
        return False          # o efHub listou: e box, e acabou
    if fala_de_box(nome):
        return False
    a = ano_no_nome(nome)
    return a is not None and a < ANO_MINIMO_DE_BOX


def norm(s):
    """Compara nome sem acento, sem caixa e sem pontuacao."""
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


# ---------------------------------------------------------------------------
#  2) A MEMORIA DO QUE O efHUB JA CHAMOU DE BOX
# ---------------------------------------------------------------------------
def le_nomes_de_box(pasta='.'):
    """Devolve {chave_normalizada: {'nome','slug','visto','cartas'}}.

    ⛔ E ACUMULADA, e nunca se apaga nada dela. Motivo medido em 18/08: a lista
       viva do efHub devolve ~50 box, e o historico tem 1.198 nomes. Se o teste
       "isto e box?" usasse so a lista de hoje, uma box de verdade que ja saiu
       do ar ("Italy Selection 11 Jun '26") seria tratada como etiqueta e
       sobrescrita.
    """
    p = os.path.join(pasta, ARQ_NOMES_DE_BOX)
    if not os.path.exists(p):
        return {}
    try:
        return (json.load(io.open(p, encoding='utf-8')) or {}).get('box') or {}
    except Exception:
        return {}


def grava_nomes_de_box(caixas, pasta='.', hoje=None):
    """Junta a lista de box de hoje na memoria. `caixas` = {slug: {nome, cartas}}."""
    conhecidas = le_nomes_de_box(pasta)
    for slug, d in (caixas or {}).items():
        nome = (d or {}).get('nome')
        if not nome or e_nome_lixo(nome):
            continue   # ⛔ "dummy" e "0" vieram da lista do efHub em 18/08
        r = conhecidas.setdefault(norm(nome), {'nome': nome, 'slug': slug, 'cartas': []})
        r['nome'] = nome
        r['slug'] = slug
        if hoje:
            r['visto'] = hoje
        r['cartas'] = sorted(set(r.get('cartas') or []) | {str(c) for c in (d.get('cartas') or [])})
    for _k in [k for k, v in conhecidas.items() if e_nome_lixo((v or {}).get('nome'))]:
        del conhecidas[_k]          # limpa o lixo que ja tinha entrado
    try:
        json.dump({'o_que_e': ('todo nome que o efHub ja chamou de BOX, acumulado. '
                               'Quem nao esta aqui nao e box — e etiqueta de carta.'),
                   'quantas': len(conhecidas), 'box': conhecidas},
                  io.open(os.path.join(pasta, ARQ_NOMES_DE_BOX), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    except Exception:
        pass
    return conhecidas


# ---------------------------------------------------------------------------
#  3) AS DUAS PERGUNTAS — e nao existe uma terceira
# ---------------------------------------------------------------------------
def e_nome_de_box(nome, conhecidas=None, pasta='.'):
    """O efHub ja chamou isto de box?"""
    if not nome or e_nome_lixo(nome):
        return False
    if conhecidas is None:
        conhecidas = le_nomes_de_box(pasta)
    return norm(nome) in conhecidas


def onde_guardar(nome, conhecidas=None, cartas_por_nome=None, pasta='.'):
    """Devolve 'box', 'etiqueta_do_card' ou 'nao_mexer'.

      box            -> o efHub ja chamou isto de box
      nao_mexer      -> nao e box conhecida, mas MUITA carta usa: pode ser box
                        antiga que saiu do ar. Vira briga, ninguem sobrescreve.
      etiqueta_do_card -> o resto
    """
    if not nome:
        return 'etiqueta_do_card'
    # ⛔ A PROVA MANDA MAIS QUE A CONTAGEM: um "Big Time" com 6 cartas continua
    #    sendo tipo de card. Por isso este teste vem antes do MUITA_CARTA.
    if e_etiqueta_provada(nome, conhecidas, pasta):
        return 'etiqueta_do_card'
    if e_nome_de_box(nome, conhecidas, pasta):
        return 'box'
    if (cartas_por_nome or {}).get(norm(nome), 0) >= MUITA_CARTA:
        return 'nao_mexer'
    return 'etiqueta_do_card'


def conta_cartas_por_nome(registros):
    """{chave_normalizada: quantas cartas usam esse nome no campo box}."""
    c = {}
    for v in (registros or {}).values():
        if isinstance(v, dict) and v.get('box'):
            k = norm(v['box'])
            c[k] = c.get(k, 0) + 1
    return c


# ---------------------------------------------------------------------------
#  4) O UNICO ESCRITOR
# ---------------------------------------------------------------------------
def guarda_o_nome(registro, nome, de_onde, conhecidas=None,
                  cartas_por_nome=None, pasta='.'):
    """Guarda `nome` no campo certo de `registro` e diz o que fez.

    Devolve: 'box', 'etiqueta_do_card', 'briga', 'igual' ou 'nada'.

    ⛔ NENHUM programa deve escrever no campo `box` sem passar por aqui. Foi
       escrevendo direto que cinco programas criaram 598 prateleiras de um
       card so — entre elas a do Messi e a do Cristiano, que na verdade estao
       os dois dentro de Living Legends 2026, 17 cartas.
    """
    if not nome or not isinstance(registro, dict):
        return 'nada'
    destino = onde_guardar(nome, conhecidas, cartas_por_nome, pasta)

    if destino == 'etiqueta_do_card':
        if not registro.get('etiqueta_do_card'):
            registro['etiqueta_do_card'] = nome
            registro['etiqueta_de_onde'] = de_onde
            return 'etiqueta_do_card'
        return 'igual' if norm(registro['etiqueta_do_card']) == norm(nome) else 'nada'

    if destino == 'nao_mexer':
        return 'briga'

    atual = registro.get('box')
    if not atual:
        registro['box'] = nome
        registro['box_de_onde'] = de_onde
        return 'box'
    if norm(atual) == norm(nome):
        return 'igual'
    # o que estava la nao e box conhecida -> era etiqueta. A etiqueta nao se
    # perde: ela e dado bom, so nao e box.
    if not e_nome_de_box(atual, conhecidas, pasta):
        if (cartas_por_nome or {}).get(norm(atual), 0) >= MUITA_CARTA:
            return 'briga'
        registro['etiqueta_do_card'] = atual
        registro['box'] = nome
        registro['box_de_onde'] = de_onde
        return 'box'
    return 'briga'
