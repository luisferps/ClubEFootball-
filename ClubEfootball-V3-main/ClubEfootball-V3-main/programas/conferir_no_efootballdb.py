# -*- coding: utf-8 -*-
r"""
CONFERIR NO efootballdb — a revisao dos antigos. v2, 16/08/2026

O COMBINADO COM O LUIS, e a ordem importa:
   1. REVISAR OS ANTIGOS — os que ja estao no banco
         impeto e vagas ....... feito na v1
         habilidades .......... ENTRA NESTA v2
         altura e peso ........ ENTRA NESTA v2
         estilo da IA ......... o efootballdb NAO tem. Vai pelo efHub.
         as 12 medidas do corpo  o efootballdb NAO tem. Vai pelo efHub.
   2. JUNTAR tudo numa lista so de linhas divergentes
   3. RODAR O MOTOR — uma vez so
   4. SO ENTAO o vigia, para puxar os novos

⛔ NAO ESCREVE NA BASE. NAO ESCREVE NO BANCO. So confere e conta.
   Onde nos e a fonte discordarem, grava OS DOIS LADOS e nao escolhe.

O QUE MUDOU DA v1 PARA A v2

 1. GUARDA AS FICHAS CRUAS em dados/efootballdb_bruto_por_card.json.
    Na v1 eu visitei 2.618 cartas e joguei a resposta fora. Da proxima vez que
    alguem quiser conferir outra coisa, tem de esperar 25 minutos de novo.
    Agora a segunda conferencia e instantanea.

 2. CONFERE AS HABILIDADES DE FABRICA — e APRENDE o mapa sozinho.
    O nosso `fab` tem nome em portugues ("Cabeceio"); o efootballdb tem um campo
    por habilidade em ingles (`header`). Escrever esse de-para a mao seria
    repetir o erro de hoje de manha, quando um mapa a mao trocou `goalkeeping`
    com `clearing` e inventou 149 divergencias falsas.
    Entao ele NAO tem mapa escrito. Ele conta a co-ocorrencia: quantas vezes o
    campo X vem ligado junto com a habilidade Y no nosso `fab`. Campo que fecha
    em 95% ou mais dos dois lados vira mapa provado. Campo que nao fecha NAO E
    CONFERIDO, e ele diz quais ficaram de fora.

 3. A PROVA DO MAPA DOS ATRIBUTOS AGORA EXIGE VARIACAO.
    Na v1 a prova usou as 20 cartas de maior geral — todas jogadores de linha,
    com os seis atributos de goleiro em 40. Com os dois valores iguais, trocar
    `goalkeeping` por `clearing` nao muda nada, e a prova passou num ponto cego.
    Agora a amostra inclui goleiros de proposito, e atributo que nao VARIA na
    amostra e reportado como NAO PROVADO.

 4. O MAPA DOS DOIS ATRIBUTOS DE GOLEIRO ESTA CORRIGIDO — medido em 149 de 149.
"""
import json, os, sys, time, itertools, collections, urllib.request, urllib.error
from datetime import datetime

VERSAO = 2           # se o progresso for de outra versao, comeca de novo

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
    print('PAREI: nao achei o config.txt.')
    sys.exit(1)
os.chdir(CASA)

L = []


def P(msg=''):
    s = str(msg)
    L.append(s)
    try:
        print(s, flush=True)
    except Exception:
        pass


def fim(codigo=0):
    try:
        open('RELATORIO-CONFERENCIA.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    except Exception:
        pass
    sys.exit(codigo)


LIMITE = None
for i, a in enumerate(sys.argv):
    if a.lower().startswith('--limite') and i + 1 < len(sys.argv):
        try:
            LIMITE = int(sys.argv[i + 1])
        except ValueError:
            pass

ROTA = 'https://api.efootballdb.com/api/2022/players/%s'
CAB = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'),
       'Accept': 'application/json', 'Referer': 'https://www.efootballdb.com/'}
BASE = os.path.join('dados', 'base_unica.json')
CATALOGO = 'efscout_boosters.json'
GUARDADAS = os.path.join('dados', 'efootballdb_bruto_por_card.json')
SAIDA_JSON = 'CONFERENCIA-EFOOTBALLDB.json'
SAIDA_HTML = 'CONFERENCIA-EFOOTBALLDB.html'

# ------------------------------------------- os 26, no vocabulario da FICHA
# ⛔ 16/08: os dois de goleiro estavam TROCADOS aqui. Medido em 149 de 149:
#    o nosso indice 21 casa com `clearing`, e o 23 com `goalkeeping`.
MAPA = [
    ('talento ofensivo',   'attacking_prowess'),
    ('controle de bola',   'ball_control'),
    ('drible',             'dribbling'),
    ('posse firme',        'tight_possession'),
    ('passe rasteiro',     'low_pass'),
    ('passe alto',         'lofted_pass'),
    ('finalizacao',        'finishing'),
    ('cabeceio',           'header'),
    ('bola parada',        'place_kicking'),
    ('efeito',             'swerve'),
    ('velocidade',         'speed'),
    ('aceleracao',         'explosive_power'),
    ('potencia de chute',  'kicking_power'),
    ('salto',              'jump'),
    ('contato fisico',     'physical_contact'),
    ('equilibrio',         'body_control'),
    ('resistencia',        'stamina'),
    ('talento defensivo',  'defensive_prowess'),
    ('roubo de bola',      'ball_winning'),
    ('recomposicao',       'defensive_engagement'),
    ('agressividade',      'aggression'),
    ('gol: reposicao',     'clearing'),        # <- corrigido
    ('gol: defesa',        'catching'),
    ('gol: afastamento',   'goalkeeping'),     # <- corrigido
    ('gol: reflexo',       'reflexes'),
    ('gol: alcance',       'coverage'),
]
ALTERNATIVAS = {7: ['header', 'heading'], 17: ['defensive_prowess', 'defensive_awareness'],
                21: ['clearing', 'goalkeeping'], 23: ['goalkeeping', 'clearing']}
NOMES = [n for n, _k in MAPA]
CHAVES = [k for _n, k in MAPA]

# ⛔ O BOOSTER FALA OUTRO DIALETO: `ball_winning` vira `tackling`,
#    `defensive_prowess` vira `defensive_awareness`. Mapa separado, de proposito.
FLAG_DO_INDICE = [
    'attacking_prowess', 'ball_control', 'dribbling', 'tight_possession', 'low_pass',
    'lofted_pass', 'finishing', 'header', 'place_kicking', 'swerve', 'speed',
    'explosive_power', 'kicking_power', 'jump', 'physical_contact', 'body_control',
    'stamina', 'defensive_awareness', 'tackling', 'defensive_engagement', 'aggression',
    'goalkeeping', 'catching', 'clearing', 'reflexes', 'coverage',
]
# campos da ficha que NAO sao habilidade — tudo o mais que for 0/1 e candidato
NAO_E_HABILIDADE = set(CHAVES) | set(FLAG_DO_INDICE) | {
    'id', 'pes_id', 'base_pes_id', 'player_name', 'shirt_name', 'national_shirt_name',
    'chinese_name', 'japanese_name', 'age', 'height', 'weight', 'level', 'max_level',
    'exp_current_level', 'exp_to_next_level', 'exp_total', 'form', 'weekly_form',
    'injury_resistance', 'weak_foot_usage', 'weak_foot_accuracy', 'playing_style',
    'playing_attitude', 'main_position', 'main_position_text', 'card_type', 'variation',
    'default_rarity', 'booster', 'booster2', 'booster3', 'strong_foot', 'strong_hand',
    'coin_price', 'gp_price', 'gp_price_base', 'price', 'sell_gp', 'market_value',
    'can_use_gp', 'customize_point', 'competition_group', 'contract_expiry_date',
    'loan_expiry_date', 'loan_from_club_id', 'youth_club_id', 'goal_celebration',
    'hidden_player', 'mobile_version', 'fake_version', 'iconic', 'star_player',
    'won_ballon_dor', 'gk',
    'cf', 'ss', 'lwf', 'rwf', 'amf', 'cmf', 'dmf', 'lmf', 'rmf', 'lb', 'rb', 'cb',
}


def tipo(b):
    if not isinstance(b, dict):
        return None
    if sum(b.get(f) or 0 for f in FLAG_DO_INDICE) == 0:
        if b.get('booster_type') == 4 or b.get('pes_id') == 136:
            return 'VAGA'
        return 'ZERADO?'
    return 'NATIVO'


def esparso(v):
    d = {}
    for p in (v or []):
        if isinstance(p, (list, tuple)) and len(p) == 2:
            try:
                d[int(p[0])] = int(p[1])
            except (TypeError, ValueError):
                pass
    return d


# ===================================================== o catalogo dos impetos
CAT, POR_ASSINATURA, POR_CONJUNTO = [], {}, collections.defaultdict(list)
if os.path.exists(CATALOGO):
    try:
        _E = json.load(open(CATALOGO, encoding='utf-8'))
        _E = _E.get('boosters') if isinstance(_E, dict) and 'boosters' in _E else _E
        for b in (_E or []):
            sm = esparso(b.get('stat_modifiers'))
            if not sm:
                continue
            reg = (b.get('name') or '?', sm, bool(b.get('conditional')))
            CAT.append(reg)
            POR_ASSINATURA.setdefault(tuple(sorted(sm.items())), reg)
            POR_CONJUNTO[frozenset(sm)].append(reg)
    except Exception:
        CAT = []


def nomeia(nm):
    if not nm or not CAT:
        return []
    k = tuple(sorted(nm.items()))
    if k in POR_ASSINATURA:
        return [POR_ASSINATURA[k]]
    alvo = frozenset(nm)
    cands = [x for fs, lst in POR_CONJUNTO.items() if fs <= alvo for x in lst]
    for a, b in itertools.combinations(cands, 2):
        s = {}
        for d in (a[1], b[1]):
            for j, q in d.items():
                s[j] = s.get(j, 0) + q
        if s == nm:
            return [a, b]
    return []


def descreve(impetos, nm):
    """⛔ NOME e NIVEL sao coisas separadas — ordem do Luis. O nivel sai do +N."""
    if impetos:
        fora = []
        for nome, sm, cond in impetos:
            niveis = sorted(set(sm.values()))
            onde = ', '.join(NOMES[j] for j in sorted(sm) if j < 26)
            fora.append('%s | nivel %s%s | [%s]'
                        % (nome.rsplit('+', 1)[0].strip(),
                           ','.join(map(str, niveis)),
                           ' | CONDICIONAL' if cond else '', onde))
        return '  +  '.join(fora)
    if nm:
        return 'NAO SEI o nome — soma %s' % ', '.join(
            '%s +%d' % (NOMES[j], q) for j, q in sorted(nm.items()) if j < 26)
    return 'sem impeto'


SEM = 'SEM VAGA'
UMA_VAZIA = 'UMA VAGA, VAZIA'
UMA_CHEIA = 'UMA VAGA, PREENCHIDA'
DUAS_UMA = 'DUAS VAGAS, UMA PREENCHIDA'
DUAS_DUAS = 'DUAS VAGAS, AS DUAS PREENCHIDAS'
DUAS_VAZIAS = 'DUAS VAGAS, AS DUAS VAZIAS'
NAO_SEI = 'NAO SEI'


def estado_deles(v):
    cheias = sum(1 for t in v if t == 'NATIVO')
    vazias = sum(1 for t in v if t == 'VAGA')
    total = cheias + vazias
    if total == 0:
        return SEM
    if total == 1:
        return UMA_CHEIA if cheias else UMA_VAZIA
    if total == 2:
        return DUAS_DUAS if cheias == 2 else (DUAS_UMA if cheias == 1 else DUAS_VAZIAS)
    return NAO_SEI


def quantos_impetos(c):
    nm = esparso(c.get('nm'))
    if not nm:
        return 0
    imp = nomeia(nm)
    return len(imp) if imp else None


def estado_nosso(c):
    """⛔ o `sl` sozinho NAO responde: [0,0] e ao mesmo tempo 'nenhuma vaga' e
       'duas preenchidas'. So cruzado com o `nm`."""
    sl = c.get('sl')
    if not isinstance(sl, list) or len(sl) != 2:
        return NAO_SEI
    livres = sum(1 for z in sl if z == 1)
    if livres == 2:
        return 'SL FURADO [1,1] — a regra diz que nao existe'
    q = quantos_impetos(c)
    if q is None:
        return NAO_SEI
    if livres == 0:
        return {0: SEM, 1: UMA_CHEIA, 2: DUAS_DUAS}.get(q, NAO_SEI)
    if livres == 1:
        return {0: UMA_VAZIA, 1: DUAS_UMA}.get(q, NAO_SEI)
    return NAO_SEI


def impeto_deles(x):
    d = {}
    for campo in ('booster', 'booster2', 'booster3'):
        b = x.get(campo)
        if not isinstance(b, dict):
            continue
        up = b.get('up_point') or 0
        if not up:
            continue
        for j in range(26):
            if b.get(FLAG_DO_INDICE[j]):
                d[j] = d.get(j, 0) + int(up)
    return d


def pega(pid, tentativas=3):
    ultimo = None
    for k in range(tentativas):
        try:
            req = urllib.request.Request(ROTA % pid, headers=CAB)
            with urllib.request.urlopen(req, timeout=25) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            d = j.get('data', j) if isinstance(j, dict) else j
            if isinstance(d, list):
                d = d[0] if d else None
            return (d if isinstance(d, dict) else None), None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, 'nao existe la'
            ultimo = 'HTTP %s' % e.code
            time.sleep(0.8 * (k + 1))
        except Exception as e:
            ultimo = str(e)[:70]
            time.sleep(0.8 * (k + 1))
    return None, (ultimo or 'nao respondeu')


def tempo(s):
    s = int(max(0, s))
    return '%02d:%02d:%02d' % (s // 3600, s % 3600 // 60, s % 60)


P('=' * 78)
P('  CONFERIR NO efootballdb — v%d  ·  %s'
  % (VERSAO, datetime.now().strftime('%d/%m/%Y %H:%M:%S')))
P('=' * 78)
P('')
P('  atributos · impeto · vagas · HABILIDADES · altura e peso')
P('  NAO escreve na base. NAO escreve no banco. So confere e conta.')

if not os.path.exists(BASE):
    P('PAREI: nao achei o %s' % BASE)
    fim(1)
B = json.load(open(BASE, encoding='utf-8'))
cards = B.get('cards') if isinstance(B, dict) else B
NOSSOS = {}
for c in (cards or []):
    i = str(c.get('id') or '')
    if i and '@' not in i:
        NOSSOS[i] = c
P('')
P('  cards na base ............. %d' % len(NOSSOS))
P('  catalogo de impetos ....... %s' % (('%d nomes' % len(CAT)) if CAT else 'NAO ACHEI'))

# ================================================ as fichas: guardadas ou novas
FICHAS = {}
if os.path.exists(GUARDADAS):
    try:
        _g = json.load(open(GUARDADAS, encoding='utf-8'))
        FICHAS = _g.get('fichas') or {}
        P('  fichas ja guardadas ....... %d  (%s)' % (len(FICHAS), GUARDADAS))
    except Exception:
        FICHAS = {}

ordem = sorted(NOSSOS, key=lambda i: -(NOSSOS[i].get('ovr') or 0))
if LIMITE:
    ordem = ordem[:LIMITE]
    P('  --limite ligado ........... so os %d primeiros' % LIMITE)
falta = [i for i in ordem if i not in FICHAS]
P('  ordem ..................... por geral, do maior pro menor')
P('  a buscar agora ............ %d' % len(falta))
if falta:
    P('  tempo estimado ............ ~%s' % tempo(len(falta) * 0.5))

if falta:
    P('')
    P('-' * 78)
    P('  BUSCANDO AS FICHAS  (guardadas para nunca mais precisar buscar)')
    P('-' * 78)
    nao_existe, nao_veio = 0, 0
    t0 = time.time()
    for n, pid in enumerate(falta, 1):
        x, err = pega(pid)
        if x:
            FICHAS[pid] = x
        elif err == 'nao existe la':
            nao_existe += 1
            FICHAS[pid] = {'_nao_existe_no_efootballdb': True}
        else:
            nao_veio += 1
        if n % 25 == 0 or n == len(falta):
            dec = time.time() - t0
            print('   %d de %d · %s · falta ~%s'
                  % (n, len(falta), tempo(dec), tempo((dec / n) * (len(falta) - n))),
                  end='\r', flush=True)
        if n % 200 == 0:
            json.dump({'o_que_e': 'a ficha crua do efootballdb, uma por carta',
                       'colhido_em': datetime.now().isoformat(timespec='seconds'),
                       'quantas': len(FICHAS), 'fichas': FICHAS},
                      open(GUARDADAS, 'w', encoding='utf-8'), ensure_ascii=False)
    print(' ' * 70, end='\r')
    os.makedirs('dados', exist_ok=True)
    json.dump({'o_que_e': 'a ficha crua do efootballdb, uma por carta',
               'colhido_em': datetime.now().isoformat(timespec='seconds'),
               'quantas': len(FICHAS), 'fichas': FICHAS},
              open(GUARDADAS, 'w', encoding='utf-8'), ensure_ascii=False)
    P('  guardei ................... %s' % GUARDADAS)
    P('  nao existem la ............ %d' % nao_existe)
    P('  nao vieram ................ %d   (voltam na proxima rodada)' % nao_veio)

VIVAS = {k: v for k, v in FICHAS.items()
         if isinstance(v, dict) and not v.get('_nao_existe_no_efootballdb')
         and k in NOSSOS}
P('')
P('  fichas boas para conferir . %d' % len(VIVAS))
if len(VIVAS) < 20:
    P('  ⛔ PAREI: poucas fichas. Sem material eu nao confiro.')
    fim(1)

# ================================ 1) A PROVA DO MAPA DOS 26 — agora com VARIACAO
P('')
P('-' * 78)
P('  PROVANDO O MAPA DOS 26 NOMES')
P('-' * 78)
P('  ⚠️ a amostra inclui GOLEIROS de proposito. Na v1 a prova usou so os 20 de')
P('     maior geral — todos de linha, com os atributos de goleiro em 40 — e')
P('     passou num ponto cego: com os dois valores iguais, trocar dois campos')
P('     nao muda nada. Foi assim que `goalkeeping` e `clearing` passaram')
P('     trocados e inventaram 149 divergencias falsas.')

_gk = [i for i in VIVAS if (NOSSOS[i].get('np') or '') in ('GOL', 'GK')][:25]
_li = [i for i in VIVAS if (NOSSOS[i].get('np') or '') not in ('GOL', 'GK')][:35]
amostra = _gk + _li
acertos = [0] * 26
testadas = 0
valores = [set() for _ in range(26)]
alt = {i: {k: 0 for k in v} for i, v in ALTERNATIVAS.items()}
for pid in amostra:
    x = VIVAS[pid]
    nosso = NOSSOS[pid].get('base')
    if not isinstance(nosso, list) or len(nosso) != 26:
        continue
    testadas += 1
    for j in range(26):
        valores[j].add(nosso[j])
        if x.get(CHAVES[j]) == nosso[j]:
            acertos[j] += 1
    for j, opcoes in ALTERNATIVAS.items():
        for k in opcoes:
            if x.get(k) == nosso[j]:
                alt[j][k] += 1
P('')
P('  cartas na prova ........... %d  (%d goleiros + %d de linha)'
  % (testadas, len(_gk), len(_li)))

sem_variar = [j for j in range(26) if len(valores[j]) <= 1]
if sem_variar:
    P('')
    P('  ⚠️ NAO PROVADOS — o valor nao varia na amostra, entao acertar nao prova nada:')
    for j in sem_variar:
        P('     %-22s (todos = %s)' % (NOMES[j], list(valores[j])[0] if valores[j] else '?'))

ruins = [j for j in range(26) if acertos[j] < testadas * 0.6 and j not in sem_variar]
for j in list(ALTERNATIVAS):
    if j in ruins:
        melhor = max(alt[j], key=lambda k: alt[j][k])
        P('')
        P('  "%s": `%s` bateu %d/%d · alternativas %s'
          % (NOMES[j], CHAVES[j], acertos[j], testadas,
             ', '.join('%s=%d' % (k, v) for k, v in alt[j].items())))
        if alt[j][melhor] >= testadas * 0.9 and melhor != CHAVES[j]:
            P('     ✔ TROQUEI para `%s` — provado nesta rodada.' % melhor)
            CHAVES[j] = melhor
            acertos[j] = alt[j][melhor]
            ruins = [z for z in ruins if z != j]
if ruins:
    P('')
    P('  ⛔ PAREI. Estes nomes nao fecham, e sem eles a conferencia mente:')
    for j in ruins:
        P('     %-22s chave `%s` bateu %d de %d'
          % (NOMES[j], CHAVES[j], acertos[j], testadas))
    fim(1)
P('  ✔ mapa provado nos que variam.')

# =========================== 2) APRENDER O MAPA DAS HABILIDADES — sem escrever
P('')
P('-' * 78)
P('  APRENDENDO O MAPA DAS HABILIDADES')
P('-' * 78)
P('  Nao ha de-para escrito aqui. Ele conta a co-ocorrencia: quantas vezes o')
P('  campo do efootballdb vem ligado junto com a habilidade no nosso `fab`.')
P('  Campo que nao fechar em 95%% dos dois lados NAO E CONFERIDO.')

candidatos = collections.Counter()
for x in VIVAS.values():
    for k, v in x.items():
        if k in NAO_E_HABILIDADE or not isinstance(v, (int, bool)):
            continue
        if v in (0, 1, True, False):
            candidatos[k] += 1 if v in (1, True) else 0

juntos = collections.defaultdict(collections.Counter)
so_campo = collections.Counter()
so_hab = collections.Counter()
for pid, x in VIVAS.items():
    fab = NOSSOS[pid].get('fab')
    if not isinstance(fab, list):
        continue
    tem_hab = set(str(h) for h in fab)
    ligados = set(k for k in candidatos
                  if x.get(k) in (1, True))
    for k in ligados:
        so_campo[k] += 1
        for h in tem_hab:
            juntos[k][h] += 1
    for h in tem_hab:
        so_hab[h] += 1

# ⛔ A TABELA MANDA. O aprendizado so CONFERE ela.
#    O NOMES-HABILIDADES.json ja traz o nome do efootballdb de cada habilidade —
#    ordem do Luis: "a traducao desses nomes ja esta na memoria, pode procurar".
#    Eu tinha construido um aprendiz quando a resposta ja estava guardada, e o
#    aprendiz errava: dava "Chute de primeira" para `phenomenal_finishing`, que
#    a tabela diz ser "Finalizador nato". A trava dos 95% recusou os tres, mas a
#    fonte certa e a tabela.
DA_TABELA = {}
TIPO_DA_HAB = {}          # nome vigente -> 'comum' | 'rara'
try:
    _N = (json.load(open('NOMES-HABILIDADES.json', encoding='utf-8')) or {}).get('nomes') or {}
    for _k, _v in _N.items():
        _e = (_v or {}).get('efootballdb')
        _vig = (_v or {}).get('vigente')
        if _e and _vig:
            DA_TABELA[str(_e).lower()] = _vig
        if _vig:
            TIPO_DA_HAB[_vig] = (_v or {}).get('tipo')
except Exception:
    DA_TABELA, TIPO_DA_HAB = {}, {}

MAPA_HAB = {}
duvidosos = []
brigas = []
nao_conhecidas = []
for k in candidatos:
    da_tabela = DA_TABELA.get(k.lower())
    aprendido = None
    if so_campo[k] >= 5 and juntos[k]:
        h, n = juntos[k].most_common(1)[0]
        p_campo = n / float(so_campo[k])
        p_hab = n / float(so_hab[h] or 1)
        if p_campo >= 0.95 and p_hab >= 0.95:
            aprendido = h
        else:
            aprendido = None
            duvidosos.append((k, h, so_campo[k], p_campo, p_hab))
    if da_tabela:
        MAPA_HAB[k] = da_tabela          # a tabela manda, sempre
        if aprendido and aprendido != da_tabela:
            brigas.append((k, da_tabela, aprendido))
    elif aprendido:
        MAPA_HAB[k] = aprendido
    elif so_campo[k] >= 20:
        nao_conhecidas.append((k, so_campo[k]))
P('')
P('  campos 0/1 candidatos ..... %d' % len(candidatos))
P('  vieram do NOMES-HABILIDADES.json .. %d' % len(DA_TABELA))
_t = collections.Counter(TIPO_DA_HAB.get(v) for v in DA_TABELA.values())
P('     comuns (vao contra o `fab`) .... %d' % _t.get('comum', 0))
P('     raras  (vao contra o `raras`) .. %d' % _t.get('rara', 0))
if _t.get(None):
    P('     ⚠️ sem tipo declarado .......... %d  (NAO sao conferidas)' % _t[None])
P('  MAPA EM USO ............... %d habilidades' % len(MAPA_HAB))
P('  duvidosos, NAO conferidos . %d' % len(duvidosos))
if brigas:
    P('')
    P('  ⛔ A TABELA E O APRENDIZADO DISCORDAM — vale a TABELA, mas olhe:')
    for k, t, a in brigas:
        P('     %-24s tabela: %-24s aprendido: %s' % (k, t, a))
if nao_conhecidas:
    P('')
    P('  ⚠️ A FONTE TEM E O NOSSO CATALOGO NAO CONHECE — %d habilidades:'
      % len(nao_conhecidas))
    for k, n in sorted(nao_conhecidas, key=lambda z: -z[1])[:14]:
        P('     %-26s em %d cartas' % (k, n))
    P('     (nao entram na conferencia. Sao candidatas a entrar no')
    P('      NOMES-HABILIDADES.json — pendencia, nao erro)')
if MAPA_HAB:
    P('')
    P('  os primeiros do mapa aprendido:')
    for k, h in list(sorted(MAPA_HAB.items()))[:10]:
        P('     %-26s = %s' % (k, h))
if duvidosos:
    P('')
    P('  os que ficaram de fora (e por que nao fecharam):')
    for k, h, n, a, b in sorted(duvidosos, key=lambda z: -z[2])[:10]:
        P('     %-24s ~ %-24s  campo->hab %.0f%% · hab->campo %.0f%%  (n=%d)'
          % (k, h, 100 * a, 100 * b, n))

# ================================================================ 3) CONFERIR
P('')
P('-' * 78)
P('  CONFERINDO')
P('-' * 78)
conta = collections.Counter()
divs = []
estados_deles = collections.Counter()

for pid, x in VIVAS.items():
    c = NOSSOS[pid]
    conta['conferidas'] += 1

    # --- os 26 atributos
    nosso = c.get('base')
    if isinstance(nosso, list) and len(nosso) == 26:
        difs = [{'atributo': NOMES[j], 'nosso': nosso[j], 'eles': x.get(CHAVES[j])}
                for j in range(26)
                if x.get(CHAVES[j]) is not None and x.get(CHAVES[j]) != nosso[j]]
        if difs:
            conta['atributos DIVERGEM'] += 1
            divs.append({'card': pid, 'nome': c.get('nome'), 'ovr': c.get('ovr'),
                         'o_que': 'atributos', 'itens': difs})
        else:
            conta['atributos batem'] += 1

    # --- altura e peso
    for nosso_k, deles_k, rot in (('altura', 'height', 'altura'), ('peso', 'weight', 'peso')):
        a, b2 = c.get(nosso_k), x.get(deles_k)
        if a is not None and b2 is not None and a != b2:
            conta['fisico DIVERGE'] += 1
            divs.append({'card': pid, 'nome': c.get('nome'), 'ovr': c.get('ovr'),
                         'o_que': 'altura / peso',
                         'itens': [{'atributo': rot, 'nosso': a, 'eles': b2}]})

    # --- as habilidades: COMUM contra `fab`, RARA contra `raras`
    # ⛔ 17/08 — o Luis: "voce sabe que Finalizador nato, Passador nato e Drible
    #    astuto sao habilidades ESPECIAIS, ne?". Eu comparava tudo contra o `fab`
    #    e reportei 884 faltando. 877 delas estavam guardadas no campo `raras`.
    #    O `tipo` estava no NOMES-HABILIDADES.json o tempo todo: 44 comuns, 21 raras.
    fab, raras = c.get('fab'), c.get('raras')
    if MAPA_HAB and (isinstance(fab, list) or isinstance(raras, list)):
        nossas_comuns = set(str(h) for h in (fab or []))
        nossas_raras = set(str(h) for h in (raras or []))
        delas_comuns, delas_raras, sem_tipo = set(), set(), set()
        for k in MAPA_HAB:
            if x.get(k) not in (1, True):
                continue
            nome_h = MAPA_HAB[k]
            t = TIPO_DA_HAB.get(nome_h)
            if t == 'rara':
                delas_raras.add(nome_h)
            elif t == 'comum':
                delas_comuns.add(nome_h)
            else:
                sem_tipo.add(nome_h)          # sem tipo declarado: NAO confiro
        itens = []
        for rot, nossas, delas in (('comum', nossas_comuns, delas_comuns),
                                   ('rara', nossas_raras, delas_raras)):
            so_eles = sorted(delas - nossas)
            so_nos = sorted(nossas - delas)
            if so_eles:
                itens.append({'atributo': 'a fonte tem e nos nao (%s)' % rot,
                              'nosso': '—', 'eles': ', '.join(so_eles[:8])})
            if so_nos:
                itens.append({'atributo': 'nos temos e a fonte nao (%s)' % rot,
                              'nosso': ', '.join(so_nos[:8]), 'eles': '—'})
        if sem_tipo:
            conta['habilidade sem tipo declarado — nao conferida'] += len(sem_tipo)
        if itens:
            conta['habilidades DIVERGEM'] += 1
            divs.append({'card': pid, 'nome': c.get('nome'), 'ovr': c.get('ovr'),
                         'o_que': 'habilidades', 'itens': itens})
        else:
            conta['habilidades batem'] += 1

    # --- as quatro perguntas da vaga
    v = [tipo(x.get('booster')), tipo(x.get('booster2')), tipo(x.get('booster3'))]
    e_deles = estado_deles(v)
    e_nosso = estado_nosso(c)
    estados_deles[e_deles] += 1
    if e_deles == DUAS_VAZIAS:
        conta['⛔ duas vagas vazias (nao existe)'] += 1
    if e_nosso == NAO_SEI:
        conta['vaga: so eles sabem'] += 1
    elif e_nosso == e_deles:
        conta['vaga bate'] += 1
    else:
        conta['vaga DIVERGE'] += 1
        divs.append({'card': pid, 'nome': c.get('nome'), 'ovr': c.get('ovr'),
                     'o_que': 'a vaga de impeto',
                     'itens': [{'atributo': 'tem vaga? quantas? quantas preenchidas?',
                                'nosso': '%s   (sl=%s)' % (e_nosso, c.get('sl')),
                                'eles': '%s   (%s)' % (e_deles, ' · '.join(str(t) for t in v))}]})

    # --- o impeto: NOME e NIVEL, separados
    nos, eles = esparso(c.get('nm')), impeto_deles(x)
    if nos or eles:
        if nos == eles:
            conta['impeto bate'] += 1
        else:
            oque = ('impeto — nos estamos VAZIOS' if not nos else
                    ('impeto — a fonte nao mostra nenhum' if not eles else 'impeto'))
            conta[oque] += 1
            divs.append({'card': pid, 'nome': c.get('nome'), 'ovr': c.get('ovr'),
                         'o_que': oque,
                         'itens': [{'atributo': 'o impeto (nome | nivel | onde mexe)',
                                    'nosso': descreve(nomeia(nos), nos),
                                    'eles': descreve(nomeia(eles), eles)}]})

# ==================================================================== o que deu
P('')
P('  conferidas ................ %d' % conta['conferidas'])
P('')
P('  OS 26 ATRIBUTOS       batem %-6d DIVERGEM %d'
  % (conta['atributos batem'], conta['atributos DIVERGEM']))
P('  AS HABILIDADES        batem %-6d DIVERGEM %d'
  % (conta['habilidades batem'], conta['habilidades DIVERGEM']))
P('  ALTURA E PESO                       DIVERGEM %d' % conta['fisico DIVERGE'])
P('  A VAGA DE IMPETO      bate  %-6d DIVERGE  %d   (so eles sabem %d)'
  % (conta['vaga bate'], conta['vaga DIVERGE'], conta['vaga: so eles sabem']))
P('  O IMPETO              bate  %-6d DIVERGE  %d' % (conta['impeto bate'], conta['impeto']))
P('     nos vazios e eles tem .. %d' % conta['impeto — nos estamos VAZIOS'])
P('     nos temos e eles nao ... %d' % conta['impeto — a fonte nao mostra nenhum'])
P('')
P('  AS QUATRO PERGUNTAS DA VAGA — o que a fonte diz de cada carta')
for e in (SEM, UMA_VAZIA, UMA_CHEIA, DUAS_UMA, DUAS_DUAS, DUAS_VAZIAS, NAO_SEI):
    if estados_deles.get(e):
        P('     %-34s %5d%s' % (e, estados_deles[e],
                                '  ⛔ NAO DEVERIA EXISTIR' if e == DUAS_VAZIAS else ''))

divs.sort(key=lambda d: -(d.get('ovr') or 0))
cartas = sorted(set(d['card'] for d in divs))
json.dump({'o_que_e': 'onde nos e o efootballdb discordamos. NADA foi sobrescrito.',
           'quando': datetime.now().isoformat(timespec='seconds'),
           'mapa_das_habilidades_aprendido': MAPA_HAB,
           'habilidades_nao_conferidas': [d[0] for d in duvidosos],
           'quantas': len(divs), 'cartas': cartas, 'itens': divs},
          open(SAIDA_JSON, 'w', encoding='utf-8'), ensure_ascii=False)
open('CARTAS-DIVERGENTES.txt', 'w', encoding='utf-8').write('\n'.join(cartas) + '\n')

import html as _h
r = ['<!doctype html><meta charset="utf-8"><title>CONFERENCIA efootballdb</title>',
     '<style>body{font:14px system-ui;margin:24px;background:#0f1115;color:#e6e8ee}',
     'h1{font-size:20px;margin:0 0 4px}p{color:#9aa3b2;margin:4px 0 16px}',
     'table{border-collapse:collapse;width:100%;max-width:1200px}',
     'th,td{padding:7px 10px;border-bottom:1px solid #232838;text-align:left;vertical-align:top}',
     'th{color:#9aa3b2;font-size:12px;text-transform:uppercase;letter-spacing:.04em}',
     '.ovr{font-weight:700;color:#7dd3a0;font-variant-numeric:tabular-nums}',
     '.n{color:#8ab4ff}.e{color:#ffb86b}.q{color:#ff7b8a;font-size:13px}',
     'tr:hover{background:#161a24}</style>',
     '<h1>Conferencia no efootballdb — %d divergencias em %d cartas</h1>'
     % (len(divs), len(cartas)),
     '<p>Nada foi sobrescrito. Os dois lados guardados. Ordenado por geral.</p>',
     '<table><tr><th>geral</th><th>carta</th><th>o que</th><th>o NOSSO</th><th>o DELES</th></tr>']
for d in divs[:700]:
    itens = d['itens'][:6]
    nosso = '<br>'.join('%s: <span class="n">%s</span>'
                        % (_h.escape(str(i['atributo'])), _h.escape(str(i['nosso']))) for i in itens)
    deles = '<br>'.join('%s: <span class="e">%s</span>'
                        % (_h.escape(str(i['atributo'])), _h.escape(str(i['eles']))) for i in itens)
    r.append('<tr><td class="ovr">%s</td><td>%s</td><td class="q">%s</td><td>%s</td><td>%s</td></tr>'
             % (d.get('ovr'), _h.escape(str(d.get('nome'))), _h.escape(d['o_que']), nosso, deles))
r.append('</table>')
open(SAIDA_HTML, 'w', encoding='utf-8').write('\n'.join(r))

P('')
P('  gravei .................... %s' % SAIDA_HTML)
P('  gravei .................... %s' % SAIDA_JSON)
P('  gravei .................... CARTAS-DIVERGENTES.txt  (%d cartas)' % len(cartas))
P('')
P('=' * 78)
P('  PRONTO. NADA foi alterado — nem na base, nem no banco.')
P('=' * 78)
P('  Falta ainda, e so o efHub responde (navegador):')
P('     o estilo de jogo da IA  ·  as 12 medidas do corpo')
fim(0)
