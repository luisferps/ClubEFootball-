# -*- coding: utf-8 -*-
"""
SUBIR A BASE UNICA PARA O SUPABASE — a pasta manda para o banco.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
A `cards_base` no Supabase e o dono da verdade: e ali que o Luis olha, e dali
que qualquer tela puxa. Mas quem MONTA a linha completa e o `unificar_base.py`,
que roda aqui na maquina lendo todas as fontes. Este script e a ponte: pega o
dados/base_unica.json pronto e joga na tabela, uma linha por card.

E UPSERT: se o card ja existe, a linha e substituida; se nao existe, nasce.
Rodar duas vezes seguidas nao duplica nada.

⚠️ `atualizado_em` vai ESCRITO no corpo de cada linha. O `default now()` da
coluna NAO dispara de novo num upsert — tombo ja tomado em 07/08 com a tabela
builds, quando 5.297 linhas ficaram todas com a mesma hora.

A CHAVE
-------
Sai do config.txt, lido na hora de rodar, do mesmo jeito que o enviar_continuo.py
faz. Este arquivo nao guarda e nao imprime chave nenhuma.

ANTES DE RODAR PELA PRIMEIRA VEZ
--------------------------------
Cole o sql/20-cards-base.sql no editor SQL do Supabase, senao a tabela nem existe.

COMO RODAR
----------
    duplo clique em SUBIR-BASE.bat
    ou:  python subir_base.py
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
import sys
import io
import time
import urllib.request
import urllib.error

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))


def pausa(msg='Enter para fechar...'):
    """Nao trava quando o .bat chama sem teclado (o ALIMENTAR-TUDO chama assim)."""
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


BASE = os.path.join('dados', 'base_unica.json')
TABELA = 'cards_base'
LOTE = 200          # 200 linhas por requisicao: rapido sem estourar o corpo do POST
PAUSA = 0.05        # respiro entre lotes, para nao levar rate limit

# ---------------------------------------------------------------------------
# A CHAVE (lida do config.txt na hora, nunca gravada aqui)
# ---------------------------------------------------------------------------
if not os.path.exists('config.txt'):
    print('Falta o config.txt (com SUPABASE_URL e SUPABASE_KEY).')
    pausa()
    sys.exit(1)

cfg = {}
for linha in open('config.txt', encoding='utf-8'):
    linha = linha.strip()
    if linha and not linha.startswith('#') and '=' in linha:
        k, v = linha.split('=', 1)
        cfg[k.strip()] = v.strip()

URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')
if not URL or not KEY or 'COLE_AQUI' in KEY:
    print('O config.txt esta sem a URL ou a chave do Supabase.')
    pausa()
    sys.exit(1)

# ---------------------------------------------------------------------------
# OS 26 ATRIBUTOS, na ordem oficial. Sao gravados DUAS vezes de proposito:
#   `atributos_base` = o vetor cru, que e o que o motor le de volta;
#   `atr_*`          = uma coluna por atributo, para o Luis filtrar no painel
#                      sem contar indice de array na mao.
# ---------------------------------------------------------------------------
ATRIBUTOS = ['ofensividade', 'controle_de_bola', 'drible', 'posse_de_bola',
             'passe_rasteiro', 'passe_alto', 'finalizacao', 'cabeceio',
             'cobranca_de_falta', 'efeito', 'velocidade', 'aceleracao',
             'potencia_de_chute', 'salto', 'contato_fisico', 'equilibrio',
             'resistencia', 'talento_defensivo', 'desarme',
             'envolvimento_defensivo', 'agressividade', 'talento_de_goleiro',
             'encaixe', 'defesa_go', 'reflexos', 'alcance']


def inteiro(v):
    """Numero inteiro ou None. Dado torto vira None em vez de derrubar a linha."""
    if v is None or v is True or v is False:
        return None
    try:
        return int(v)
    except Exception:
        return None


def decimal(v):
    if v is None or v is True or v is False:
        return None
    try:
        return float(v)
    except Exception:
        return None


def texto(v):
    if v is None:
        return None
    if isinstance(v, str):
        return v.strip() or None
    return str(v)


def data(v):
    """So aceita AAAA-MM-DD. Qualquer outra coisa vira None: data torta faz o
    Postgres devolver 400 e derrubar o lote inteiro."""
    s = texto(v)
    if not s or len(s) != 10 or s[4] != '-' or s[7] != '-':
        return None
    return s


def linha_do_banco(c, agora):
    base = c.get('base') or []
    linha = {
        'card_id':            str(c.get('id')),
        'nome':               texto(c.get('nome')),
        'ovr':                inteiro(c.get('ovr')),
        'max_ovr':            decimal(c.get('max_ovr')),
        'tier':               texto(c.get('tier')),
        'votos':              inteiro(c.get('votos')),

        'posicao':            texto(c.get('pos')),
        'posicao_nativa':     texto(c.get('np')),
        'posicoes_sec':       texto(c.get('sec')),
        'estilo_de_jogo':     texto(c.get('modelo')),

        'orcamento':          inteiro(c.get('orc')),
        'level_cap':          inteiro(c.get('levelCap')),

        'atributos_base':     base or None,

        'impeto_efeito':            c.get('nm') or None,
        'impeto_nomes':             c.get('nmn') or None,
        'impeto_delta_condicional': c.get('nx') or None,
        'impeto_orfao':             c.get('impeto_orfao') or None,
        'impeto_nativo':            texto(c.get('impeto_nativo')),

        # A FICHA DO IMPETO: a resposta pronta, nao o dado cru (ordem de 14/08).
        # O `impeto_efeito` la de cima e o vetor; aqui vai o que da para LER.
        'impeto_quantos':           inteiro(c.get('impeto_quantos')),
        'impeto_tem':               bool(c.get('impeto_tem')) if c.get('impeto_tem') is not None else None,
        'impeto_nomes_decompostos': c.get('impeto_nomes') or None,
        'impeto_condicional':       c.get('impeto_condicional') if c.get('impeto_condicional') else None,
        'impeto_efeito_legivel':    texto(c.get('impeto_efeito')),
        'impeto_soma':              inteiro(c.get('impeto_soma')),
        'vagas_livres':             inteiro(c.get('vagas_livres')),
        'impeto_situacao':          texto(c.get('impeto_situacao')),
        'impeto_de_onde':           texto(c.get('impeto_de_onde')),

        'vagas_impeto':       c.get('sl') or None,
        'vaga_detalhe':       c.get('vaga') or None,

        'hab_nativas':        c.get('fab') or None,
        'hab_faltantes':      c.get('falta') or None,
        'hab_raras':          c.get('raras') or None,

        'corpo':              c.get('corpo') or None,
        'pe':                 texto(c.get('pe')),
        'altura':             inteiro(c.get('altura')),
        'peso':               inteiro(c.get('peso')),
        'pe_ruim':            c.get('pe_ruim') or None,

        # ⛔ 18/08 — O ESTILO DE JOGO DA IA TEM QUE SUBIR DAQUI TAMBEM.
        #    Ele so subia pelo motor_bonus, que processa as cartas ORIGINAIS.
        #    Resultado medido na rodada de 17/08 23:33: a heranca deu estilo da
        #    IA as 3.684 variacoes de posicao no arquivo, o subir_base nao
        #    mandou esse campo, e o do_banco trouxe a base de volta SEM ele —
        #    3.684 de 3.684 zeradas. Todo o resto da heranca sobreviveu (pe
        #    ruim, corpo, modelo, nivel, box, data); so este campo se perdia,
        #    toda rodada, em silencio.
        'estilo_ia':          c.get('com') or None,

        'box':                texto(c.get('box')),
        # ⛔ 18/08 — SOBE JUNTO OU SE PERDE. Mesmo caso do estilo_ia logo acima:
        #    o vigia tira a etiqueta do campo `box` e guarda em
        #    `etiqueta_do_card`; se ela nao subir, o do_banco traz a base de
        #    volta sem ela e o trabalho se desfaz toda rodada, em silencio.
        #    A coluna nasce no ClubEfootball\sql\32-a-etiqueta-do-card.sql.
        'etiqueta_do_card':   texto(c.get('etiqueta_do_card')),
        'data_lancamento':    data(c.get('dt')),

        'boost_id':           inteiro(c.get('boostId')),
        'boost_id2':          inteiro(c.get('boostId2')),
        'origem_ficha':       texto(c.get('origem_ficha')),
        'idade':              inteiro(c.get('age')),
        'pe_ruim_uso':        inteiro(c.get('wfu')),
        'pe_ruim_prec':       inteiro(c.get('wfa')),
        'resist_lesao':       inteiro(c.get('inj')),
        'forma':              inteiro(c.get('forma')),
        'condicao':           inteiro(c.get('cond')),
        'cap_desbloq':        c.get('capdesc') if isinstance(c.get('capdesc'), bool) else None,

        # 16/08: a pontuacao maxima que a CASCA mostrava. Coluna propria de
        # proposito — o nota_maxima_tela guarda o overallRating do efHub, e
        # medido em 16/08 os dois discordam em 2.444 de 2.785 cartas.
        'pontuacao_maxima_da_casca': decimal(c.get('maxOvr')),

        'fonte_de_cada_campo': c.get('fonte_de_cada_campo') or None,
        # escrito no corpo, de proposito (ver o aviso la em cima)
        'atualizado_em':      agora,
    }
    # as 26 colunas soltas
    for i, nome_attr in enumerate(ATRIBUTOS):
        linha['atr_' + nome_attr] = inteiro(base[i]) if i < len(base) else None
    return linha


def manda(linhas):
    """Um POST de upsert. Levanta excecao se o banco recusar."""
    corpo = json.dumps(linhas).encode('utf-8')
    req = urllib.request.Request(
        '%s/rest/v1/%s?on_conflict=card_id' % (URL, TABELA),
        data=corpo,
        headers={'apikey': KEY,
                 'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json',
                 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        method='POST')
    with urllib.request.urlopen(req, timeout=180) as r:
        r.read()


def detalhe(erro):
    """O texto que o Postgres devolve dentro do HTTP 400 — e ele que diz qual
    coluna nao existe ou qual tipo nao bate."""
    try:
        return erro.read().decode('utf-8', 'ignore')[:400]
    except Exception:
        return str(erro)


def barra(feitas, total):
    largura = 40
    cheio = int(largura * feitas / total) if total else largura
    return '[%s%s] %5.1f%%  %d/%d' % ('#' * cheio, '.' * (largura - cheio),
                                      100.0 * feitas / total if total else 100,
                                      feitas, total)


# ---------------------------------------------------------------------------
print('=' * 70)
print('  SUBIR A BASE UNICA -> Supabase, tabela %s' % TABELA)
print('=' * 70)

if not os.path.exists(BASE):
    print('Nao achei o %s.' % BASE)
    print('Rode antes o UNIFICAR-BASE.bat.')
    pausa()
    sys.exit(1)

with open(BASE, 'r', encoding='utf-8') as f:
    base_unica = json.load(f)

cards = base_unica.get('cards') or []
if not cards:
    print('A base unica esta vazia. Nada para subir.')
    pausa()
    sys.exit(1)

agora = time.strftime('%Y-%m-%dT%H:%M:%S')
print('cards na base unica ...... %d' % len(cards))
print('lote ..................... %d linhas por requisicao' % LOTE)
print('-' * 70)

todas = [linha_do_banco(c, agora) for c in cards]

# ===========================================================================
#  SO SOBE O QUE MUDOU — 16/08/2026, 15h40
# ===========================================================================
# ⛔ O DEFEITO: este programa carimbava `atualizado_em = agora` nas 6.469
#    linhas a cada vez que rodava, mesmo quando nada tinha mudado. Isso quebra
#    a peca mais importante do passo 7 — a volta automatica. A regra do Luis e
#    "se o insumo e mais novo que o produto, a linha volta para a fila". Com a
#    hora mudando sozinha, TODA carta fica mais nova que TODA linha depois de
#    qualquer upload, e a resposta vira "refaz as 11 mil" — que e o mesmo que
#    nao ter resposta nenhuma.
#
#    Agora ele LE o banco antes, compara campo por campo, e so manda quem
#    mudou de verdade. A hora passa a significar: "foi aqui que este dado
#    mudou pela ultima vez".
#
# ⚠️ NA DUVIDA, MANDA. Se a comparacao nao conseguir decidir (tipo estranho,
#    erro de leitura), a linha vai. Mandar de novo nao estraga nada; deixar de
#    mandar um dado que mudou estraga tudo.


def igual(a, b):
    """Dois valores sao o mesmo dado? Na duvida, devolve False (manda)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # o PostgREST devolve numeric como texto: 91.89 volta "91.89"
    try:
        if isinstance(a, bool) or isinstance(b, bool):
            return bool(a) == bool(b)
        fa, fb = float(a), float(b)
        return abs(fa - fb) < 1e-9
    except (TypeError, ValueError):
        pass
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    try:
        return json.dumps(a, sort_keys=True, ensure_ascii=False) == \
               json.dumps(b, sort_keys=True, ensure_ascii=False)
    except Exception:
        return False


def le_o_banco():
    """A tabela inteira, de mil em mil. Devolve {} se nao der — e ai sobe tudo."""
    fora, de = {}, 0
    while True:
        req = urllib.request.Request(
            '%s/rest/v1/%s?select=*&order=card_id' % (URL, TABELA),
            headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
                     'Range-Unit': 'items', 'Range': '%d-%d' % (de, de + 999)})
        with urllib.request.urlopen(req, timeout=180) as r:
            p = json.loads(r.read().decode('utf-8'))
        if not p:
            break
        for x in p:
            fora[str(x.get('card_id'))] = x
        if len(p) < 1000:
            break
        de += 1000
    return fora


# ---------------------------------------------------------------------------
# ⛔ 16/08/2026 — CAMPO VAZIO NAO SOBE. Antes subia, e APAGAVA o banco.
# ---------------------------------------------------------------------------
#   Medido em 16/08 14h26: o banco tinha idade em 2.760 cartas, condicao em
#   2.706 e corpo em 6.467 — tudo colhido pelo ENTRAR-COM-O-EFHUB, que escreve
#   DIRETO no banco. A pasta tinha 136, 136 e 6.424. Subir mandava `null`
#   nessas colunas e o upsert APAGAVA o que o efHub tinha acabado de colher.
#
#   Agora a linha sai sem as chaves vazias. Coluna que nao vai no corpo do
#   pedido o PostgREST NAO TOCA — fica como esta no banco.
#
# ⚠️ O PostgREST exige o MESMO conjunto de colunas dentro de um lote. Por isso
#    as linhas sao agrupadas por assinatura de colunas antes de ir. Medido:
#    sao 88 assinaturas nos 6.469 cards — nao e um pedido por carta.
#
#   E a mesma regra que o unificar_base.py ja seguia por dentro:
#   "fonte vazia NUNCA sobrescreve dado bom".
SEMPRE = ('card_id', 'atualizado_em')
enxutas = []
for linha in todas:
    enxutas.append({k: v for k, v in linha.items()
                    if v is not None or k in SEMPRE})
todas = enxutas


# ⛔ 16/08 16h10 — A COMPARACAO VEM DEPOIS DE ENXUGAR, E ISSO E O TODO.
#    Na primeira versao ela vinha ANTES, e o resultado foi "mudaram: 6469"
#    com nada tendo mudado. O motivo: a pasta tem `idade: None` para quem o
#    banco tem 30 — e None nunca e igual a 30. So que essa chave IA SER
#    JOGADA FORA logo em seguida, porque campo vazio nao sobe.
#    Comparar o que nao vai ser enviado e comparar fantasma.
#    Agora a conta e sobre EXATAMENTE o que vai no pedido.

print('lendo o banco para comparar...')
try:
    NO_BANCO = le_o_banco()
    print('   ja no banco .......... %d cartas' % len(NO_BANCO))
except Exception as erro:
    NO_BANCO = {}
    print('   ⚠️ nao consegui ler o banco (%s)' % str(erro)[:70])
    print('      sobe tudo, como antes. Nada se perde — so a hora fica generosa.')

if NO_BANCO:
    mudaram, iguais, novas = [], 0, 0
    for linha in todas:
        antes = NO_BANCO.get(linha['card_id'])
        if antes is None:
            novas += 1
            mudaram.append(linha)
            continue
        for k, v in linha.items():
            if k == 'atualizado_em':
                continue
            if not igual(v, antes.get(k)):
                mudaram.append(linha)
                break
        else:
            iguais += 1
    print('   cartas novas ......... %d' % novas)
    print('   mudaram .............. %d' % len(mudaram))
    print('   iguais, nao sobem .... %d' % iguais)
    todas = mudaram
    if not todas:
        print('-' * 70)
        print('NADA MUDOU. O banco ja esta igual a pasta.')
        print('A hora de cada carta continua sendo a da ultima mudanca de verdade.')
        pausa()
        sys.exit(0)
print('-' * 70)

grupos = {}
for linha in todas:
    grupos.setdefault(tuple(sorted(linha)), []).append(linha)
print('colunas cheias por card ...  %d assinaturas diferentes' % len(grupos))
print('   campo vazio NAO sobe — o banco nao perde o que a pasta nao tem')
print('-' * 70)

subiram = 0
falharam = 0
erros = []          # (card_id, motivo) — so os primeiros, para nao virar poluicao

ordenadas = []
for _chaves, grupo in sorted(grupos.items(), key=lambda x: -len(x[1])):
    for i in range(0, len(grupo), LOTE):
        ordenadas.append(grupo[i:i + LOTE])

feitas = 0
for bloco in ordenadas:
    k = feitas
    try:
        manda(bloco)
        subiram += len(bloco)
    except Exception as erro:
        # O lote caiu. Pode ser UMA linha torta levando as outras 199 junto —
        # entao tento uma por uma para nao perder as boas e para saber QUAL e a ruim.
        motivo = detalhe(erro) if isinstance(erro, urllib.error.HTTPError) else str(erro)
        print('\n   lote a partir da linha %d falhou (%s). Tentando uma a uma...'
              % (k + 1, motivo[:120]))
        for linha in bloco:
            try:
                manda([linha])
                subiram += 1
            except Exception as erro2:
                falharam += 1
                m = detalhe(erro2) if isinstance(erro2, urllib.error.HTTPError) else str(erro2)
                if len(erros) < 20:
                    erros.append((linha['card_id'], m[:200]))
    feitas += len(bloco)
    print('\r   ' + barra(feitas, len(todas)), end='', flush=True)
    time.sleep(PAUSA)

print()
print('-' * 70)
print('SUBIRAM ...... %d linhas' % subiram)
print('FALHARAM ..... %d linhas' % falharam)
if erros:
    print()
    print('As primeiras que falharam, com o motivo que o banco deu:')
    for cid, motivo in erros:
        print('   card %-16s %s' % (cid, motivo))
    print()
    print('Se o motivo falar em coluna que nao existe, rode de novo o')
    print('sql/20-cards-base.sql no editor SQL do Supabase — ele e idempotente.')
print()
print('Confira no painel: tabela %s, coluna atualizado_em = %s' % (TABELA, agora))
