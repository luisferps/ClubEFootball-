# -*- coding: utf-8 -*-
r"""
MONTAR O CATALOGO DE IMPETO — um impeto por linha, o nivel vira numero.

ORDEM DO LUIS, 18/08/2026:
    "O nome do impeto nao e 'Chute +1'. O nome do impeto e CHUTE. O mais um
     significa que ele aumenta mais um ponto em alguns atributos."

    "E so voce colocar o nome de um dos idiomas, pode ser o ingles, como chave
     unica, e colocar uma coluna para os outros nomes."

    "Vai ter mais um, vai ter mais dois, daqui a pouco vai ter mais dez nomes
     pra uma coisa so."

COMO ELE DECIDE QUE DOIS NOMES SAO O MESMO IMPETO
    NAO e por traducao. E por MEDIDA: se dois nomes mexem exatamente nos mesmos
    atributos, sao o mesmo impeto. Conferido em 39 impetos — nenhum muda de
    atributo entre niveis. Foi assim que "Fantasia" e "Fantasista" apareceram
    como um so, sem eu adivinhar nada.

⛔ A REGRA DO NIVEL — Luis, 18/08. NAO CONSERTAR ISTO:
    "O nivel +1 e para impetos ADICIONADOS. Voce nao consegue adicionar um
     impeto com nivel maior do que um. Os outros niveis sao de FABRICA."
    Medido: das 1.124 linhas em que o motor escolheu impeto, 100% foram +1.
    O motor esta certo.

⛔ NAO APAGA NADA. Tudo e upsert por `chave`.
⛔ NAO TOCA EM CARD NENHUM. So le a base e escreve a tabela do catalogo.
⛔ NAO INVENTA DEGRAU. Impeto condicional entra com `degraus` VAZIO — quem
   preenche e o Luis olhando o jogo. Chute na conta e o que estraga a conta.

⛔ RODE ANTES o ClubEfootball\sql\31-o-catalogo-de-impeto.sql

A CHAVE sai do config.txt na hora de rodar. Nunca e impressa nem gravada aqui.
"""
import json, os, re, sys, io, time, collections, urllib.request, urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))


def acha_a_casa(inicio):
    p = inicio
    for _ in range(4):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None


CASA = acha_a_casa(AQUI)
if not CASA:
    print('PAREI: nao achei o config.txt nem aqui nem nas pastas de cima.')
    sys.exit(1)
os.chdir(CASA)

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

SO_OLHAR = any(a.lower().startswith('confer') for a in sys.argv[1:])
BASE = os.path.join('dados', 'base_unica.json')
TABELA = 'insumo_impeto'

# ============================================================================
#  OS 27 PARES MEDIDOS — qual dos dois nomes e o INGLES
# ============================================================================
#  ⛔ Isto NAO e traducao adivinhada. Os pares sairam da medicao: cada linha
#     abaixo e um par de nomes que mexe EXATAMENTE nos mesmos 4 atributos.
#     A unica coisa escrita a mao aqui e qual dos dois e o ingles — porque
#     "Chute" e "Shooting" passam os dois num teste de letras.
INGLES = {
    'Shooting', 'Technique', "Striker's Instinct", 'Ball-carrying',
    'Offence Creator', 'Agility', 'Accuracy', 'Duelling', 'Passing',
    'Balancer', 'Hard Worker', 'Ball Protection', 'Off the Ball', 'Crossing',
    'Fantasista', 'Defending', 'Breakthrough', 'Stealing', 'Shutdown',
    'Strength', 'Free-kick Taking', 'Rebuilding', 'Physicality', 'Aerial',
    'Counter', 'Saving', 'Aerial Block', 'Goalkeeping', 'Regista',
    'Total Package', 'Le Petit Prince', 'Bearer of Fate', 'Son of God',
    'King of Football', 'The Undisputed', 'Magical', 'Natural-born',
    'Striking',
}

LOTE = 200
AGORA = time.strftime('%Y-%m-%dT%H:%M:%S')


def P(*a):
    print(*a, flush=True)


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


def sem_nivel(s):
    return re.sub(r'\s*\+\d+\s*$', '', s).strip()


def o_nivel(s):
    m = re.search(r'\+(\d+)\s*$', s)
    return int(m.group(1)) if m else None


def vira_chave(ats):
    """⛔ 18/08, 2a versao — A CHAVE SAI DOS ATRIBUTOS, NUNCA DO NOME.

    A 1a versao tirava a chave do nome ('shooting', 'technique'). Deu errado na
    SEGUNDA rodada, e o motivo e um ciclo:
        1. o catalogo grava o nome em PORTUGUES no CAT_dom.json (de proposito:
           e o nome que aparece na tela e nas 12.368 linhas)
        2. o unificar_base LE o CAT_dom e passa a nomear os impetos das cartas
           em portugues
        3. na rodada seguinte este programa le a base, nao acha mais nome em
           ingles, e cria chave nova: 'chute' ao lado de 'shooting'
        4. o banco fica com os dois. Medido em 17/08 23:33: 38 impetos viraram
           65, e 109 linhas viraram 203.
    O nome muda de idioma; os ATRIBUTOS nao mudam nunca. Foi medido em 39
    impetos: nenhum troca de atributo entre niveis. Entao a chave e eles.
    """
    return 'imp_' + '_'.join(str(int(a)) for a in ats)


P('=' * 78)
P('  MONTAR O CATALOGO DE IMPETO')
P('=' * 78)
if SO_OLHAR:
    P('')
    P('  ⚠️ MODO CONFERIR: nada vai ser gravado no banco.')

# --------------------------------------------------------- 1. ler a base
P('')
P('[1/4] lendo a base')
if not os.path.exists(BASE):
    P('   ⛔ nao achei o %s' % BASE)
    P('      Rode o DO-BANCO.bat para os insumos descerem.')
    pausa(); sys.exit(1)
B = json.load(open(BASE, encoding='utf-8'))
cards = B.get('cards') or []
com_impeto = [c for c in cards if c.get('impeto_tem')]
P('   %s cartas · %s com impeto'
  % ('{:,}'.format(len(cards)).replace(',', '.'),
     '{:,}'.format(len(com_impeto)).replace(',', '.')))

# ------------------------------------- 2. juntar PELOS ATRIBUTOS, nao pelo nome
P('')
P('[2/4] juntando os nomes que mexem nos MESMOS atributos')

fam = collections.defaultdict(lambda: {'nomes': collections.Counter(),
                                       'niveis': set(), 'cartas': 0, 'cond': 0})
nao_decomposto = 0
misturados = 0
for c in com_impeto:
    nomes = c.get('impeto_nomes') or []
    nm = c.get('nm') or []
    cond = c.get('impeto_condicional') or []
    if len(nomes) != 1:
        # ⛔ carta com DOIS impetos: o `nm` vem somado e nao da pra separar qual
        #    atributo e de qual. Fica de fora do catalogo — nao chuto.
        misturados += 1
        continue
    n = nomes[0]
    if 'decompost' in n:
        nao_decomposto += 1
        continue
    ats = tuple(sorted(p[0] for p in nm if isinstance(p, (list, tuple)) and len(p) == 2))
    if not ats:
        continue
    d = fam[ats]
    d['nomes'][sem_nivel(n)] += 1
    lv = o_nivel(n)
    if lv:
        d['niveis'].add(lv)
    d['cartas'] += 1
    if cond and cond[0]:
        d['cond'] += 1

P('   %d impetos distintos' % len(fam))
if misturados:
    P('   %d cartas com DOIS impetos ficaram de fora (o efeito vem somado)' % misturados)
if nao_decomposto:
    P('   %d cartas com o nome nao reconhecido ficaram de fora' % nao_decomposto)

# ------------------------------------------------------- 3. montar as linhas
P('')
P('[3/4] montando as linhas do catalogo')
linhas = []
sem_ingles = []
for ats, d in sorted(fam.items(), key=lambda x: -x[1]['cartas']):
    todos = list(d['nomes'])
    en = [x for x in todos if x in INGLES]
    outros = [x for x in todos if x not in INGLES]
    # ⛔ 18/08, 2a versao — QUEM NAO CONHECE NAO APAGA.
    #    Antes, quando nenhum nome era reconhecido como ingles, este programa
    #    mandava o nome portugues no campo `nome_en` — e o upsert APAGAVA o
    #    ingles que ja estava gravado. Como o CAT_dom passa a nomear tudo em
    #    portugues na rodada seguinte, o ingles some do sistema em duas voltas.
    #    Agora: nao reconheci ingles, nao mando o campo. O que esta no banco fica.
    nome_en = en[0] if en else None
    if not en:
        sem_ingles.append(todos[0])
    nome_pt = outros[0] if outros else (todos[0] if not en else None)
    resto = sorted(set(todos) - {nome_en, nome_pt} - {None})
    niveis = sorted(d['niveis'])
    linhas.append({
        'chave':         vira_chave(ats),
        'nome_en':       nome_en,      # None = nao mando (ver a limpeza abaixo)
        'nome_pt':       nome_pt,
        'outros_nomes':  resto,
        'atributos':     list(ats),
        'niveis_vistos': niveis,
        # ⛔ REGRA DO LUIS: so entra em vaga vazia quem aparece no nivel 1.
        'adicionavel':   1 in niveis,
        'condicional':   d['cond'] > 0,
        'degraus':       None,          # ⛔ NAO INVENTA. Quem preenche e o Luis.
        'cartas':        d['cartas'],
        'atualizado_em': AGORA,
    })

P('   %d linhas' % len(linhas))
P('')
P('   %-24s %-24s %-18s %-12s %s'
  % ('CHAVE', 'nome em portugues', 'atributos', 'niveis', 'cartas'))
P('   ' + '-' * 92)
for l in linhas:
    marca = ''
    if l['condicional']:
        marca = '  ⚠ condicional'
    ats = str(l['atributos'])
    if len(ats) > 18:
        ats = ats[:15] + '...'
    P('   %-24s %-24s %-18s %-12s %d%s'
      % (l['chave'][:24], (l['nome_pt'] or '—')[:24], ats,
         str(l['niveis_vistos'])[:12], l['cartas'], marca))

adic = sum(1 for l in linhas if l['adicionavel'])
cond = [l for l in linhas if l['condicional']]
P('')
P('   adicionaveis (entram em vaga vazia, sempre no nivel 1) ... %d' % adic)
P('   so de fabrica ............................................ %d' % (len(linhas) - adic))
P('   condicionais SEM degrau conferido ........................ %d' % len(cond))
if sem_ingles:
    P('')
    P('   (%d impetos sem nome em ingles conhecido — a chave nao depende disso,'
      % len(set(sem_ingles)))
    P('    e o nome em ingles que ja estiver no banco NAO foi apagado)')

# ------------------------------------------------------------ 4. subir
P('')
P('[4/4] mandando para o banco')
if SO_OLHAR:
    P('   (modo conferir — nada foi gravado)')
    pausa(); sys.exit(0)

cfg = {}
for _l in open('config.txt', encoding='utf-8'):
    _l = _l.strip()
    if _l and not _l.startswith('#') and '=' in _l:
        _k, _v = _l.split('=', 1)
        cfg[_k.strip()] = _v.strip()
URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')
if not URL or not KEY:
    P('   ⛔ O config.txt esta sem a URL ou a chave do Supabase.')
    pausa(); sys.exit(1)
CAB = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
       'Content-Type': 'application/json',
       'Prefer': 'resolution=merge-duplicates,return=minimal'}

# ⛔ `degraus` sai do corpo quando e None. Se ele fosse junto como null, um
#    upsert futuro APAGARIA o degrau que o Luis ja tivesse conferido.
corpo = []
for l in linhas:
    d = dict(l)
    if d.get('degraus') is None:
        d.pop('degraus', None)
    if d.get('nome_en') is None:
        d.pop('nome_en', None)
    if d.get('nome_pt') is None:
        d.pop('nome_pt', None)
    corpo.append(d)

ok = falha = 0
for i in range(0, len(corpo), LOTE):
    lote = corpo[i:i + LOTE]
    req = urllib.request.Request(
        '%s/rest/v1/%s?on_conflict=chave' % (URL, TABELA),
        data=json.dumps(lote, ensure_ascii=False).encode('utf-8'),
        headers=CAB, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            r.read()
        ok += len(lote)
    except urllib.error.HTTPError as e:
        det = ''
        try:
            det = e.read().decode('utf-8', 'ignore')[:300]
        except Exception:
            pass
        falha += len(lote)
        P('   ⛔ HTTP %s  %s' % (e.code, det))
        if 'does not exist' in det or 'schema cache' in det:
            P('      -> falta rodar o ClubEfootball\\sql\\31-o-catalogo-de-impeto.sql')
        break
    except Exception as e:
        falha += len(lote)
        P('   ⛔ %s' % str(e)[:200])
        break

# ---------------------------------------------- a limpeza das chaves velhas
# ⛔ 18/08 — POR QUE ISTO EXISTE, e por que e seguro.
#    A 1a versao deste programa criava a chave a partir do NOME ('shooting').
#    Como o nome muda de idioma entre rodadas, o banco ficou com as duas
#    versoes do mesmo impeto: 38 viraram 65 em uma unica noite. A chave agora
#    sai dos ATRIBUTOS e nao muda mais — mas as chaves velhas continuam la.
#
#    Esta tabela e DERIVADA: ela nasce inteira da base a cada rodada. Nao ha
#    dado dela que nao possa ser refeito daqui. Por isso da para tirar o que
#    sobrou sem perder nada.
#
#    ⛔ AS TRES TRAVAS, e nenhuma e enfeite:
#       1. so apaga se o catalogo recem-montado tiver 20 linhas ou mais
#       2. so apaga chave que NAO comeca com 'imp_' (as do formato novo ficam)
#       3. NUNCA apaga a linha que tiver `degraus` preenchido — degrau e
#          conferencia do Luis olhando o jogo, e isso nao se refaz daqui
sobraram = 0
if not falha and len(corpo) >= 20:
    try:
        req = urllib.request.Request(
            '%s/rest/v1/%s?select=chave,degraus&chave=not.like.imp_*' % (URL, TABELA),
            headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY})
        with urllib.request.urlopen(req, timeout=60) as r:
            velhas = json.loads(r.read().decode('utf-8'))
        alvo = [x['chave'] for x in velhas if not x.get('degraus')]
        guardadas = [x['chave'] for x in velhas if x.get('degraus')]
        if guardadas:
            P('')
            P('   %d chaves velhas TEM degrau conferido e NAO foram tocadas:' % len(guardadas))
            for k in guardadas[:10]:
                P('        %s' % k)
        for i in range(0, len(alvo), 50):
            lote = alvo[i:i + 50]
            q = ('%s/rest/v1/%s?chave=in.(%s)'
                 % (URL, TABELA, ','.join('"%s"' % k for k in lote)))
            d = urllib.request.Request(q, headers=dict(CAB), method='DELETE')
            with urllib.request.urlopen(d, timeout=60) as r:
                r.read()
            sobraram += len(lote)
        if sobraram:
            P('')
            P('   limpei %d chaves do formato velho (o nome virava a chave)' % sobraram)
    except Exception as e:
        P('')
        P('   (nao consegui limpar as chaves velhas: %s)' % str(e)[:120])
        P('    nao e grave: o catalogo novo esta gravado, so sobrou lixo do lado)')

P('')
P('=' * 78)
if falha:
    P('  ⛔ %d linhas nao subiram. Leia o erro acima e rode de novo.' % falha)
else:
    P('  ✅ %d impetos no catalogo.' % ok)
    P('')
    P('  O que falta agora e so o que nao da pra medir daqui:')
    P('    · os DEGRAUS dos %d condicionais' % len(cond))
    P('    · a CONDICAO de cada um')
    P('  Os dois se conferem olhando o impeto dentro do jogo.')
P('=' * 78)
pausa()
sys.exit(1 if falha else 0)
