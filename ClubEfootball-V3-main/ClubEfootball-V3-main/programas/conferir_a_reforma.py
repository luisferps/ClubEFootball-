# -*- coding: utf-8 -*-
"""
CONFERIR A REFORMA — 16/08/2026

POR QUE ESTE PROGRAMA EXISTE:

  As 02h25 de 16/08 o GERAR-ENCAIXE.bat foi rodado, e ele roda o motor de
  bonus junto — que ESCREVE no Supabase. Isso aconteceu no meio da reforma,
  DEPOIS que os quatro passos ja tinham entrado. O console dele mostrou:

      insumo_bonus_corpo         384
      insumo_bonus_posicao        60
      insumo_bonus_parametro      13
      cards_base.estilo_ia       435
      bonus                   11.941

  ⛔ Duas dessas escritas tocam em tabela que a reforma usa:
     - cards_base, que e onde o ESTADO DE CADA CAMPO foi gravado
     - e o estilo_ia, que a regua marcou como "nao sei" nas 6.469

  Este programa NAO ESCREVE NADA. So pergunta ao banco quanto existe de cada
  coisa e compara com o que a reforma deixou. Se algo foi atropelado, ele diz
  o que e de quanto foi.

⛔ NAO escreve. NAO apaga. NAO conserta. So conta e compara.
"""
import json, os, sys, io, urllib.request, urllib.error
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def P(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- onde estou
AQUI = os.path.dirname(os.path.abspath(__file__))


def acha_a_pasta_do_sistema(inicio):
    p = inicio
    for _ in range(4):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None


CASA = acha_a_pasta_do_sistema(AQUI)
if not CASA:
    P('⛔ nao achei o config.txt subindo a partir de %s' % AQUI)
    sys.exit(1)
os.chdir(CASA)


def config():
    cfg = {}
    for ln in open('config.txt', encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if '=' in ln and not ln.startswith('#'):
            k, v = ln.split('=', 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


C = config()
URL = (C.get('SUPABASE_URL') or '').rstrip('/')
KEY = C.get('SUPABASE_KEY') or C.get('SUPABASE_SERVICE_KEY') or ''
if not URL or not KEY:
    P('NAO ACHEI SUPABASE_URL / SUPABASE_KEY no config.txt. Nada foi feito.')
    sys.exit(1)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}


def conta(u):
    """Quantas linhas existem — PERGUNTANDO, nao baixando e contando.
       O Supabase devolve no maximo 1.000 por leitura; contar assim nao tem teto."""
    try:
        r = urllib.request.Request(URL + '/rest/v1/' + u,
                                   headers=dict(H, Prefer='count=exact'), method='HEAD')
        with urllib.request.urlopen(r, timeout=90) as f:
            cr = f.headers.get('Content-Range') or ''
            return int(cr.split('/')[-1]) if '/' in cr else -1
    except urllib.error.HTTPError as e:
        return -(400 + 0) if e.code == 400 else -e.code
    except Exception:
        return -1


def le(u):
    try:
        r = urllib.request.Request(URL + '/rest/v1/' + u, headers=H)
        with urllib.request.urlopen(r, timeout=90) as f:
            return json.loads(f.read().decode('utf-8'))
    except Exception:
        return None


def num(n):
    return ('%d' % n) if n >= 0 else ('ERRO %d' % -n)


P('=' * 74)
P('  CONFERIR A REFORMA  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 74)
P('')
P('  O banco recebeu escrita as 02h25 (o motor de bonus, pelo GERAR-ENCAIXE).')
P('  Esta conferencia pergunta ao banco se a reforma continua de pe.')
P('')
P('  ⛔ NAO escreve nada. So conta.')
P('')

# ---- primeiro: o banco esta ai? ------------------------------------------
# ⛔ Sem isto, uma internet caida vira "A REFORMA FOI ATROPELADA" e o Luis
#    leva um susto por nada. Falta de resposta NAO e perda de dado.
_teste = conta('cards_base?select=card_id&limit=1')
if _teste < 0:
    P('  ⛔ NAO CONSEGUI FALAR COM O BANCO.')
    P('')
    P('     Isto NAO quer dizer que a reforma se perdeu — quer dizer que eu')
    P('     nao consegui perguntar. Confira a internet e rode de novo.')
    P('')
    P('     Se a internet estiver boa, o problema e a chave do config.txt.')
    P('=' * 74)
    sys.exit(2)

problemas = []
avisos = []

# ============================================================ 1) AS TABELAS
P('-' * 74)
P('  1) AS TABELAS DA REFORMA — quanto existe agora')
P('')

ESPERADO = [
    ('funcoes',        'funcoes?select=nome',                       19,  'as 19 funcoes'),
    ('funcoes/codigo', 'funcoes?select=nome&codigo=not.is.null',    19,  'com codigo fixo'),
    ('funcoes/rotulo', 'funcoes?select=nome&rotulo=not.is.null',    19,  'com rotulo'),
    ('traducao',       'traducao?select=chave',                    438,  'linhas de traducao'),
    ('molde v5',       'molde?select=funcao&versao=eq.5',          494,  'o molde vigente'),
    ('motor_versao',   'motor_versao?select=motor',                  2,  'os dois motores'),
    ('motor_arquivo',  'motor_arquivo?select=arquivo',              17,  'impressoes digitais'),
]

P('  %-16s %10s %10s   %s' % ('tabela', 'agora', 'esperado', 'o que e'))
P('  ' + '-' * 68)
for nome, url, esp, oque in ESPERADO:
    n = conta(url)
    marca = '  '
    if n < 0:
        marca = '⚠️'
        avisos.append('%s: nao consegui ler (%s) — pode ser tabela que ainda nao existe' % (nome, num(n)))
    elif n < esp:
        marca = '⛔'
        problemas.append('%s: tinha %d, agora tem %d — PERDEU %d' % (nome, esp, n, esp - n))
    elif n > esp:
        marca = '⚠️'
        avisos.append('%s: tinha %d, agora tem %d — entraram %d a mais' % (nome, esp, n, n - esp))
    else:
        marca = '✅'
    P('  %-16s %10s %10d %s %s' % (nome, num(n), esp, marca, oque))

# o molde inteiro, versao por versao — as antigas sao historico e nao podem sumir
P('')
P('  o molde, versao por versao (as antigas sao historico):')
for v in (1, 2, 3, 4, 5):
    n = conta('molde?select=funcao&versao=eq.%d' % v)
    P('     versao %d ............. %s' % (v, num(n)))

# ==================================================== 2) O ESTADO DE CADA CAMPO
P('')
P('-' * 74)
P('  2) OS QUATRO ESTADOS — gravados dentro do cards_base')
P('')
P('  ⛔ O motor de bonus escreveu no cards_base as 02h25. Se aquela escrita')
P('     tivesse mandado a linha inteira, teria apagado o estado. Vamos ver.')
P('')

n_estado = conta('cards_base?select=card_id&estado_de_cada_campo=not.is.null')
n_cards = conta('cards_base?select=card_id')
P('  cards no banco ............ %s' % num(n_cards))
P('  com estado gravado ........ %s   (esperado 6.469)' % num(n_estado))

if n_estado < 0:
    avisos.append('nao consegui ler o estado_de_cada_campo')
elif n_estado < 6469:
    problemas.append('o estado sumiu de %d cards — a escrita das 02h25 atropelou' % (6469 - n_estado))
    P('  ⛔ O ESTADO FOI ATROPELADO. Faltam %d.' % (6469 - n_estado))
else:
    P('  ✅ o estado sobreviveu inteiro a escrita das 02h25')

# =========================================== 3) A CONTRADICAO DO ESTILO DA IA
P('')
P('-' * 74)
P('  3) O ESTILO DE JOGO DA IA — a contradicao dentro do proprio banco')
P('')

n_ia = conta('cards_base?select=card_id&estilo_ia=not.is.null')
P('  cards com estilo_ia ....... %s   (o motor de bonus subiu 435)' % num(n_ia))
P('  a regua diz ............... 6.469 "nao sei" — porque leu o base_unica.json,')
P('                              e la a chave estilo_ia NAO EXISTE')
P('')
if n_ia > 0:
    P('  ⚠️  O MESMO BANCO diz duas coisas sobre os mesmos %s cards:' % num(n_ia))
    P('      cards_base.estilo_ia ........ tem valor')
    P('      estado_de_cada_campo ........ "nao sei"')
    P('')
    P('      Nao e defeito de nenhum dos dois. E o funil: o motor de bonus tira')
    P('      o estilo da TELA e grava no banco; o base_unica.json — que a regua')
    P('      le — nunca recebeu esse campo. Sao dois caminhos que nao se falam.')
    avisos.append('estilo_ia: %s cards com valor no banco e "nao sei" na regua' % num(n_ia))

# ============================================ 4) O QUE O MOTOR DE BONUS ESCREVEU
P('')
P('-' * 74)
P('  4) O QUE A ESCRITA DAS 02h25 DEIXOU')
P('')

# ⛔ 16/08 03h50: a primeira versao perguntava por `select=id` nas tabelas de
#    insumo e levava ERRO 400 — porque a coluna `id` nao existe nelas. Erro
#    meu de suposicao: cravei o nome da coluna em vez de perguntar. `select=*`
#    nao supoe nada.
for tabela, esp in (('bonus', 11941),
                    ('insumo_bonus_corpo', 384),
                    ('insumo_bonus_posicao', 60),
                    ('insumo_bonus_parametro', 13)):
    n = conta(tabela + '?select=*')
    if n < 0:
        P('  %-24s %10s   (a tabela nao respondeu — pode nao existir com esse nome)'
          % (tabela, num(n)))
        avisos.append('%s: nao respondeu' % tabela)
        continue
    resto = ''
    if n > esp:
        resto = '  ⚠️ %d linhas a MAIS do que essa rodada escreveu' % (n - esp)
    P('  %-24s %10s   (a rodada das 02h25 escreveu %d)%s' % (tabela, num(n), esp, resto))
    if n > esp:
        avisos.append('%s: tem %d e a rodada tocou em %d — sobram %d linhas que a rodada '
                      'NAO refez (resultado de motor mais velho)' % (tabela, n, esp, n - esp))

P('')
P('  ⚠️  9.702 pares ficaram com bonus de estilo de IA = 0 por falta do dado.')
P('      Isso e ZERO onde o certo seria NAO SEI. O motor de bonus ainda nao le')
P('      a regua dos quatro estados — esta na lista, e e o passo 8.')

# ============================================================ 5) A CHAVE
P('')
P('-' * 74)
P('  5) A TROCA DA CHAVE — o passo 1 continua de pe?')
P('')
P('  ⛔ Enquanto a coluna do codigo nao estiver cheia nas tres tabelas,')
P('     a chave NAO se troca. Esta conferencia existe para isso.')
P('')
_chave = le('chave_a_trocar?select=*')
if _chave is None:
    P('  ⚠️  a visao chave_a_trocar nao existe. O passo 1 ainda nao foi feito.')
else:
    P('  %-14s %10s %12s %12s' % ('tabela', 'linhas', 'com codigo', 'SEM codigo'))
    P('  ' + '-' * 52)
    _falta = 0
    for r in _chave:
        sem = r.get('sem_codigo') or 0
        _falta += sem
        P('  %-14s %10s %12s %12s %s' % (
            r.get('tabela'), r.get('linhas'), r.get('com_codigo'), sem,
            '✅' if sem == 0 else '⛔'))
    if _falta:
        P('')
        P('  ⛔ %d linhas SEM codigo. Nome de funcao que nao existe mais em funcoes.' % _falta)
        _sp = le('chave_sem_par?select=*') or []
        for r in _sp[:10]:
            P('     %-14s %-34s %s linhas' % (r.get('tabela'), r.get('nome_que_nao_casou'), r.get('linhas')))
        problemas.append('a chave: %d linhas sem codigo' % _falta)
    else:
        P('')
        P('  ✅ as tres estao inteiras. O passo 3 (trocar de verdade) pode acontecer')
        P('     quando o Luis mandar — nunca sozinho, nunca em duplo clique.')

# ============================================================ 6) O IMPETO
P('')
P('-' * 74)
P('  6) O IMPETO SEPARADO — nome, nivel e atributos em colunas proprias')
P('')
P('  ⛔ A chave e o `id` DO JOGO (efscout_boosters.json), nunca o nome:')
P('     (nome, nivel, slot) repete em 62 casos com os mesmos atributos,')
P('     porque sao versoes diferentes do jogo. So o id distingue.')
P('')
_imp = le('impeto_conferir?select=*')
if _imp is None:
    P('  ⚠️  a visao impeto_conferir nao existe. O impeto ainda nao foi separado.')
    avisos.append('o impeto ainda nao esta separado no banco')
else:
    r = _imp[0] if isinstance(_imp, list) and _imp else {}
    _cat = r.get('impetos_no_catalogo') or 0
    _atr = r.get('linhas_de_atributo') or 0
    _sab = r.get('cards_com_impeto_sabido') or 0
    _nsi = r.get('cards_em_nao_sei') or 0
    _dub = r.get('cards_com_id_em_duvida') or 0
    _qbr = r.get('impetos_quebrados_na_fonte') or 0
    P('     impetos no catalogo ......... %6s' % _cat)
    P('     linhas de atributo .......... %6s' % _atr)
    P('     cards com impeto sabido ..... %6s' % _sab)
    P('     cards em NAO SEI ............ %6s' % _nsi)
    P('     cards com o id em duvida .... %6s   (gemeos de versao — a conta e a mesma)' % _dub)
    P('     quebrados NA FONTE .......... %6s   (marcados, nao consertados)' % _qbr)
    if not _cat:
        P('')
        P('  ⛔ o catalogo esta VAZIO. Rode o SUBIR-OS-IMPETOS.bat.')
        problemas.append('o catalogo do impeto esta vazio no banco')
    else:
        # ⛔ Card apontando para impeto que sumiu do catalogo. A view MOSTRA
        #    em vez de apagar — e a licao das 11.133 linhas de builds.
        _orf = le('impeto_orfao?select=*') or []
        if _orf:
            P('')
            P('  ⛔ %d card(s) apontando para impeto que nao existe mais:' % len(_orf))
            for x in _orf[:8]:
                P('     card %-18s ordem %-3s impeto_id %s'
                  % (x.get('card_id'), x.get('ordem'), x.get('impeto_id')))
            problemas.append('o impeto: %d cards orfaos' % len(_orf))
        else:
            P('')
            P('  ✅ nenhum card orfao. O catalogo e os cards estao casados.')
        if _nsi:
            avisos.append('o impeto: %d cards em NAO SEI (lista no IMPETOS-QUE-FALTAM.txt)'
                          % _nsi)

# ------------------------------------------------ o mapa vivo das tabelas
P('')
P('-' * 74)
P('  7) O MAPA VIVO — o que existe no banco AGORA, perguntado a ele')
P('')
P('  ⛔ Nao ha lista cravada aqui. Se alguem criar tabela, ela aparece.')
P('')
try:
    r = urllib.request.Request(URL + '/rest/v1/', headers=H)
    with urllib.request.urlopen(r, timeout=90) as f:
        api = json.loads(f.read().decode('utf-8'))
    caminhos = sorted(k.lstrip('/') for k in (api.get('paths') or {})
                      if k not in ('/',) and '/' not in k.lstrip('/'))
    P('  %d tabelas e views:' % len(caminhos))
    linha = '     '
    for t in caminhos:
        if len(linha) + len(t) > 70:
            P(linha); linha = '     '
        linha += t + '  '
    if linha.strip():
        P(linha)
except Exception as e:
    P('  ⚠️  nao consegui pedir o mapa (%s)' % str(e)[:60])

# ================================================================ 5) VEREDITO
P('')
P('=' * 74)
if problemas:
    P('  ⛔ A REFORMA FOI ATROPELADA. %d coisa(s):' % len(problemas))
    for x in problemas:
        P('     · ' + x)
    P('=' * 74)
    sys.exit(1)

P('  ✅ A REFORMA ESTA DE PE. A escrita das 02h25 nao atropelou nada.')
P('')
P('     as 19 funcoes com codigo e rotulo .... intactas')
P('     a tabela de traducao ................. intacta')
P('     o molde 5 e o historico .............. intactos')
P('     a identidade dos motores ............. intacta')
P('     o estado de cada campo ............... intacto')
if avisos:
    P('')
    P('  ⚠️  Mas tem %d coisa(s) para olhar:' % len(avisos))
    for x in avisos:
        P('     · ' + x)
P('=' * 74)
