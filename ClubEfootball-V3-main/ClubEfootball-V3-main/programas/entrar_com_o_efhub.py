# -*- coding: utf-8 -*-
"""
ENTRAR COM O efHUB — passo 5. 16/08/2026

Pega o efhub_fichas.json que a coleta do Console baixou e poe cada campo no
lugar certo, com recibo, contraprova e sem sobrescrever dado bom.

ONDE CADA COISA VAI — e por que ali:

  pe ruim (uso e precisao) -> pe_ruim.json
        o unificar_base.py JA le esse arquivo, e o formato ja e {card: [uso, prec]}.
        A escala 0..3 esta PROVADA la dentro desde 11/08 (Rui Costa, conferido
        no jogo). Nao invento formato novo onde ja existe um provado.

  progressao (levelCap)    -> dados/levelcap.json
        idem: o unificar ja le.

  a ficha inteira, crua    -> dados/efhub_bruto_por_card.json
        para nao ter de voltar na fonte quando aparecer campo novo.

  idade, lesao, estilo da IA, forma, condicao, corpo, nota maxima
                           -> o BANCO (cards_base)
        estes o unificar_base.py NAO le hoje. Em vez de mexer no motor, eles vao
        para o banco, que e o destino final de todo mundo no passo 8.

⛔ NUNCA APAGA DADO BOM. So escreve onde estava vazio.
⛔ CONTRAPROVA: se o efHub disser algo DIFERENTE do que ja esta guardado, ele
   NAO sobrescreve e NAO escolhe. Guarda os dois lados em dados/divergencias.json.
"""
import json, os, sys, io, shutil, urllib.request, urllib.error
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def P(*a):
    print(*a, flush=True)


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

FICHAS = 'efhub_fichas.json'
PERUIM = 'pe_ruim.json'
LEVELCAP = os.path.join('dados', 'levelcap.json')
BRUTO = os.path.join('dados', 'efhub_bruto_por_card.json')
DIVERG = os.path.join('dados', 'divergencias.json')
JA = os.path.join('dados', 'ja_perguntei.json')
RECIBOS = os.path.join('dados', 'recibos_de_coleta.jsonl')

# as 12 posicoes do corpo — CORPO_CHAVES.json, medido em 14/08
CORPO = [('altura', None), ('coxa', 'thighSize'), ('panturrilha', 'calfSize'),
         ('cintura', 'waistSize'), ('peito', 'chestMeasurement'), ('tamBraco', 'armSize'),
         ('tamPescoco', 'neckSize'), ('comprPerna', 'legLength'),
         ('comprBraco', 'armLength'), ('comprPescoco', 'neckLength'),
         ('largOmbro', 'shoulderWidth'), ('altOmbro', 'shoulderHeight')]


def ler(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    try:
        return json.load(open(caminho, encoding='utf-8'))
    except Exception:
        return padrao


def vazio(v):
    return v is None or v == '' or v == [] or v == {}


P('=' * 78)
P('  ENTRAR COM O efHUB  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')

if not os.path.exists(FICHAS):
    P('⛔ nao achei o %s nesta pasta.' % FICHAS)
    P('')
    P('   Ele e baixado pelo Console, na pasta Downloads. Recorte de la e cole')
    P('   aqui:  %s' % CASA)
    sys.exit(1)

PAC = json.load(open(FICHAS, encoding='utf-8'))
F = PAC.get('fichas') or {}
P('  arquivo lido .............. %s' % FICHAS)
P('  colhido em ................ %s' % (PAC.get('colhido_em') or '?')[:16])
P('  pedidas ................... %s' % PAC.get('pedidas'))
P('  vieram .................... %d' % len(F))
if PAC.get('falhas'):
    P('  falhas na coleta .......... %d  (voltam na proxima rodada)' % len(PAC['falhas']))

# ======================================================================= backup
carimbo = datetime.now().strftime('%Y%m%d-%H%M%S')
for cam in (PERUIM, LEVELCAP):
    if os.path.exists(cam):
        shutil.copy2(cam, cam + '.ANTES-DO-EFHUB-' + carimbo)
P('  backup feito .............. .ANTES-DO-EFHUB-%s' % carimbo)

PR = ler(PERUIM, {})
LC = ler(LEVELCAP, {})
JAP = (ler(JA, {}) or {}).get('perguntas') or {}
divergencias = []
recibos = []

pr_dados = PR.get('dados')
if pr_dados is None:
    pr_dados = {}
    PR['dados'] = pr_dados

conta = {'pe_ruim': 0, 'levelCap': 0, 'idade': 0, 'lesao': 0, 'estilo_ia': 0,
         'forma': 0, 'condicao': 0, 'corpo': 0, 'nota_maxima': 0}
ja = {k: 0 for k in conta}
sem = {k: 0 for k in conta}
diverg_n = 0
bruto = {}
linhas_banco = []


def marca(cid, campo, resposta):
    JAP.setdefault(cid, {})[campo] = {
        'fonte': 'efhub',
        'quando': datetime.now().isoformat(timespec='seconds'),
        'resposta': resposta}


def confere(cid, campo, novo, velho, onde):
    global diverg_n
    if vazio(novo) or vazio(velho):
        return False
    if json.dumps(novo, sort_keys=True) == json.dumps(velho, sort_keys=True):
        return False
    divergencias.append({'card': cid, 'campo': campo,
                         'ja_estava': velho, 'de_onde': onde,
                         'agora_disse': novo, 'quem_disse': 'efhub',
                         'quando': datetime.now().isoformat(timespec='seconds'),
                         'o_que_fazer': 'terceira fonte desempata. NAO foi sobrescrito.'})
    diverg_n += 1
    return True


# ============================================================================
#  ⛔ 18/08 — SO ENTRA FICHA DE CARTA QUE EXISTE NA BASE
# ============================================================================
#  O que aconteceu sem isto, medido em duas rodadas seguidas:
#     17/08 22:21 ... 241 fichas de carta que a base nao tem  -> a base foi de
#                     6.469 para 6.710 registros
#     17/08 23:33 ... mais 192  -> 6.902
#  Elas viram CARTA FANTASMA no banco: tem idade, lesao, corpo e estilo da IA,
#  e nao tem nome, nota, posicao nem atributos. Nao da para calcular nada com
#  elas, e toda contagem do sistema passa a mentir — a marca dos campos
#  contava 6.710 cartas quando existiam 6.469.
#
#  A ficha delas NAO se perde: fica no dados/efhub_bruto_por_card.json,
#  esperando a carta entrar na base pela porta certa (o inserir_novos.py).
#  No dia em que ela entrar, a ficha ja esta aqui.
_ids_da_base = set()
try:
    _b = json.load(open(os.path.join('dados', 'base_unica.json'), encoding='utf-8'))
    _b = _b.get('cards') if isinstance(_b, dict) else _b
    _ids_da_base = {str(x.get('id')) for x in (_b or []) if x.get('id')}
except Exception as _e:
    P('  ⚠️ nao consegui ler a base para conferir os ids (%s).' % str(_e)[:60])
    P('     Nesta rodada TODAS as fichas entram, como antes.')

_fora_da_base = []

for cid, j in F.items():
    if not isinstance(j, dict):
        continue
    cid = str(cid)
    bruto[cid] = j          # o bruto guarda TUDO — a ficha nunca se perde
    if _ids_da_base and cid not in _ids_da_base:
        _fora_da_base.append(cid)
        continue
    lin = {'card_id': cid}

    # ---- pe ruim: uso e precisao (escala 0..3, provada em 11/08) -------------
    wfu, wfa = j.get('weakFootUsage'), j.get('weakFootAccuracy')
    if wfu is None or wfa is None:
        sem['pe_ruim'] += 1
        marca(cid, 'wfu', 'nao tem')
        marca(cid, 'wfa', 'nao tem')
    else:
        antes = pr_dados.get(cid)
        if antes is None:
            pr_dados[cid] = [int(wfu), int(wfa)]
            conta['pe_ruim'] += 1
        elif confere(cid, 'pe_ruim', [int(wfu), int(wfa)], list(antes), PERUIM):
            pass
        else:
            ja['pe_ruim'] += 1
        marca(cid, 'wfu', 'trouxe')
        marca(cid, 'wfa', 'trouxe')
        lin['pe_ruim_uso'] = int(wfu)
        lin['pe_ruim_precisao'] = int(wfa)

    # ---- progressao ---------------------------------------------------------
    lc = j.get('levelCap')
    if lc in (None, ''):
        sem['levelCap'] += 1
        marca(cid, 'levelCap', 'nao tem')
    else:
        antes = LC.get(cid)
        if antes is None:
            LC[cid] = lc
            conta['levelCap'] += 1
        elif confere(cid, 'levelCap', lc, antes, LEVELCAP):
            pass
        else:
            ja['levelCap'] += 1
        marca(cid, 'levelCap', 'trouxe')
        lin['level_cap'] = int(lc)

    # ---- os que vao para o banco -------------------------------------------
    for nosso, dele, coluna in (('age', 'age', 'idade'),
                                ('inj', 'injuryResistance', 'lesao'),
                                ('forma', 'form', 'forma'),
                                ('cond', 'condition', 'condicao')):
        v = j.get(dele)
        chave = {'age': 'idade', 'inj': 'lesao', 'forma': 'forma', 'cond': 'condicao'}[nosso]
        if v in (None, ''):
            sem[chave] += 1
            marca(cid, nosso, 'nao tem')
        else:
            lin[coluna] = int(v)
            conta[chave] += 1
            marca(cid, nosso, 'trouxe')

    com = j.get('comSkills')
    if com is None:
        sem['estilo_ia'] += 1
        marca(cid, 'com', 'nao tem')
    else:
        # ⛔ lista vazia AQUI e resposta: o efHub achou a carta e ela nao tem
        #    estilo de jogo da IA. Nao e "ninguem puxou".
        lin['estilo_ia'] = com
        conta['estilo_ia'] += 1
        marca(cid, 'com', 'trouxe')

    pm = j.get('playerModel') or {}
    if pm and j.get('height'):
        vetor = [j.get('height')] + [pm.get(k) for _, k in CORPO[1:]]
        if all(x is not None for x in vetor):
            lin['corpo'] = vetor
            conta['corpo'] += 1
            marca(cid, 'corpo', 'trouxe')
        else:
            sem['corpo'] += 1
    else:
        sem['corpo'] += 1
        marca(cid, 'corpo', 'nao tem')

    ovr = j.get('overallRating')
    if ovr not in (None, ''):
        lin['nota_maxima_tela'] = float(ovr)
        conta['nota_maxima'] += 1

    if len(lin) > 1:
        linhas_banco.append(lin)
    recibos.append({'card': cid, 'fonte': 'efhub',
                    'quando': datetime.now().isoformat(timespec='seconds'),
                    'resposta': 'respondeu',
                    'trouxe': sorted(k for k in lin if k != 'card_id')})

# ======================================================================= gravar
json.dump(PR, open(PERUIM, 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(LC, open(LEVELCAP, 'w', encoding='utf-8'), ensure_ascii=False)
os.makedirs('dados', exist_ok=True)
json.dump({'o_que_e': 'a ficha crua do efHub, uma por carta, como o site devolveu',
           'colhido_em': PAC.get('colhido_em'), 'quantas': len(bruto), 'fichas': bruto},
          open(BRUTO, 'w', encoding='utf-8'), ensure_ascii=False)
json.dump({'o_que_e': 'quem ja foi perguntado, quando, e o que respondeu',
           'atualizado_em': datetime.now().isoformat(timespec='seconds'),
           'perguntas': JAP}, open(JA, 'w', encoding='utf-8'), ensure_ascii=False)
with open(RECIBOS, 'a', encoding='utf-8') as f:
    for r in recibos:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
if divergencias:
    antigas = ler(DIVERG, {'itens': []})
    antigas['o_que_e'] = ('onde duas fontes disseram coisas diferentes sobre o mesmo campo '
                          'da mesma carta. NADA foi sobrescrito.')
    antigas.setdefault('itens', []).extend(divergencias)
    json.dump(antigas, open(DIVERG, 'w', encoding='utf-8'), ensure_ascii=False)

P('')
P('  O QUE ENTROU')
P('')
P('  %-16s %8s %8s %8s' % ('campo', 'NOVO', 'ja tinha', 'nao tem'))
P('  ' + '-' * 46)
for k in ('pe_ruim', 'levelCap', 'idade', 'lesao', 'estilo_ia', 'forma', 'condicao', 'corpo'):
    P('  %-16s %8d %8d %8d' % (k, conta[k], ja[k], sem[k]))
P('')
P('  divergiu .................. %d   (nada sobrescrito)' % diverg_n)
if _fora_da_base:
    P('')
    P('  ⛔ FORA DA BASE — nao entraram: %d fichas' % len(_fora_da_base))
    P('     Sao cartas que o efHub respondeu e que a nossa base ainda nao tem.')
    P('     A ficha delas ficou guardada no dados/efhub_bruto_por_card.json.')
    P('     Quando a carta entrar pela porta certa (inserir_novos), o dado ja')
    P('     esta aqui esperando. Antes desta trava elas viravam carta fantasma:')
    P('     idade e corpo sem nome, sem nota e sem atributo.')
    for _x in _fora_da_base[:8]:
        P('        %s' % _x)
    if len(_fora_da_base) > 8:
        P('        ... e mais %d' % (len(_fora_da_base) - 8))
P('')
P('  gravei .................... %s' % PERUIM)
P('  gravei .................... %s' % LEVELCAP)
P('  gravei .................... %s' % BRUTO)

# ======================================================================= o banco
P('')
P('-' * 78)
P('  O BANCO')
P('')


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
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}


def conta_banco(u):
    try:
        r = urllib.request.Request(URL + '/rest/v1/' + u,
                                   headers=dict(H, Prefer='count=exact'), method='HEAD')
        with urllib.request.urlopen(r, timeout=90) as f:
            cr = f.headers.get('Content-Range') or ''
            return int(cr.split('/')[-1]) if '/' in cr else -1
    except Exception:
        return -1


if not URL or not KEY:
    P('  ⚠️  sem chave no config.txt — o que e do banco nao subiu.')
    P('      O que e de arquivo ja esta gravado. Nada se perdeu.')
    sys.exit(0)

# as colunas novas existem?
try:
    r = urllib.request.Request(
        URL + '/rest/v1/cards_base?select=idade,lesao,forma,condicao,corpo,estilo_ia&limit=1',
        headers=H)
    urllib.request.urlopen(r, timeout=60).read()
except urllib.error.HTTPError as e:
    P('  ⚠️  faltam colunas no banco:')
    P('      %s' % e.read().decode('utf-8', 'replace')[:200])
    P('')
    P('      Abra o CRIAR-COLUNAS-EFHUB-NO-SUPABASE.html e cole o comando.')
    P('      O que e de arquivo ja esta gravado. Rode este .bat de novo depois.')
    sys.exit(0)
except Exception as e:
    P('  ⚠️  nao consegui falar com o banco (%s)' % str(e)[:60])
    P('      O que e de arquivo ja esta gravado. Nada se perdeu.')
    sys.exit(0)

antes_idade = conta_banco('cards_base?select=card_id&idade=not.is.null')
antes_ia = conta_banco('cards_base?select=card_id&estilo_ia=not.is.null')
P('  no banco ANTES ............ idade %s · estilo da IA %s' % (antes_idade, antes_ia))

# ⛔ o PostgREST exige colunas iguais dentro do mesmo lote
grupos = {}
for lin in linhas_banco:
    grupos.setdefault(tuple(sorted(lin)), []).append(lin)
P('  grupos de colunas ......... %d' % len(grupos))

mandei = gravou = 0
for chaves, grupo in sorted(grupos.items(), key=lambda x: -len(x[1])):
    for i in range(0, len(grupo), 200):
        lote = grupo[i:i + 200]
        u = URL + '/rest/v1/cards_base?on_conflict=card_id'
        d = json.dumps(lote, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(u, data=d, headers=dict(
            H, Prefer='resolution=merge-duplicates,return=representation'), method='POST')
        try:
            with urllib.request.urlopen(req, timeout=180) as f:
                volta = json.loads(f.read().decode('utf-8', 'replace'))
            gravou += len(volta) if isinstance(volta, list) else 0
        except urllib.error.HTTPError as e:
            P('')
            P('  ⛔ o banco recusou (HTTP %s):' % e.code)
            P('     %s' % e.read().decode('utf-8', 'replace')[:300])
            P('     colunas deste lote: %s' % ', '.join(chaves))
            sys.exit(1)
        mandei += len(lote)
        print('   %d de %d...' % (mandei, len(linhas_banco)), end='\r', flush=True)
print(' ' * 40, end='\r')

P('  mandei .................... %d' % mandei)
P('  o BANCO gravou ............ %d' % gravou)
if gravou != mandei:
    P('  ⛔ o banco gravou menos do que eu mandei. PAREI.')
    sys.exit(1)

P('')
P('  CONFERENCIA — lendo de volta do banco')
for nome, u, esp in (('idade', 'cards_base?select=card_id&idade=not.is.null', conta['idade']),
                     ('estilo da IA', 'cards_base?select=card_id&estilo_ia=not.is.null', conta['estilo_ia']),
                     ('lesao', 'cards_base?select=card_id&lesao=not.is.null', conta['lesao']),
                     ('corpo', 'cards_base?select=card_id&corpo=not.is.null', conta['corpo'])):
    n = conta_banco(u)
    P('     %-14s %6d   (subi %d) %s' % (nome, n, esp, '✅' if n >= esp else '⛔'))

P('')
P('  ✅ PRONTO E CONFERIDO.')
P('')
P('  O QUE FAZER AGORA:')
P('     1. UNIFICAR-BASE.bat   - poe o pe ruim e a progressao na base')
P('     2. FILA-DE-COLETA.bat  - refaz a fila com o que ainda falta')
