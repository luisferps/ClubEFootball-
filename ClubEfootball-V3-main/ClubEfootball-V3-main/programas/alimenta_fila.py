# -*- coding: utf-8 -*-
"""
ALIMENTADOR — pega o que a coleta baixou e joga no motor, com ele rodando.

Fica ligado ao lado do motor e da coleta. A cada ciclo:
  1. le as fichas novas do efhub_bruto.jsonl
  2. monta a TABELA DE CODIGOS cruzando por id com o dados/cards.json que ja existe
     (posicao, estilo e habilidade tem CODIGO UNICO no efHub — nada e adivinhado:
      o par codigo-efHub / codigo-do-motor sai do proprio banco do Luis)
  3. converte o card novo e grava em cards_efhub.json — NUNCA no dados/cards.json.
     🔑 Duas fontes de proposito: o atualizar.py REGENERA o cards.json e apagaria o que
     o alimentador escreveu. A precedencia por campo esta em precedencia.json e o motor
     faz o merge: o efHub manda em base/orc/dt/sl/fab/posicao/estilo; o `falta` e o
     `raras` sao derivacao LOCAL e o efHub nao tem isso.
  4. gera as linhas card x funcao e ACRESCENTA no fila_EXTRA.json
     o motor pega sozinho no proximo ciclo dele

Card com QUALQUER codigo ainda desconhecido — posicao, posicao secundaria, estilo ou
habilidade — NAO e convertido no chute e NAO entra pela metade: fica em
esperando_codigo.csv e tenta de novo no ciclo seguinte, quando a coleta ja tiver trazido
mais cards conhecidos. No fim da coleta a tabela fecha e eles entram.

⛔ TRAVA DO POOL DE HABILIDADE (conferido pela sessao do motor, 07/08 noite)
  Card com pool de habilidade VAZIO nao entra. Nota com pool zero nao e "deprimida",
  e INUTILIZAVEL: Musiala mediu 57,7 com pool 5 e -135,5 com pool 0. E o POOL='uniao'
  do motor nao salva card novo, porque ele nao esta no falta_por_card.json — os dois
  lados da uniao dao vazio juntos.
  Esses cards ficam em esperando_falta.csv e entram quando a regra do pool fechar.

O QUE ESTE ARQUIVO NAO INVENTA
  nm    -> null (falta a tabela boostId -> nome)
  tier  -> '?' nos cards novos, nunca null: tier nulo faz o card desaparecer do filtro
           do Encaixe sem avisar. A ordem entre eles sai pelo OVR.

Para fechar: feche a janela, ou crie o arquivo PARAR.txt na pasta.
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
import json, os, sys, io, csv, time, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from funcao_nativa import funcao_nativa, familia, normaliza, SA_FAMILIA

D        = 'dados/'
CARDS    = D + 'cards.json'      # SO LEITURA. O alimentador nunca escreve aqui.
EFHUB    = 'cards_efhub.json'    # a fonte que o alimentador mantem
BRUTO    = 'efhub_bruto.jsonl'
EXTRA    = 'fila_EXTRA.json'
TABELA   = 'codigos_efhub.json'
ESPERA   = 'esperando_codigo.csv'
SEM_POOL = 'esperando_falta.csv'
MARCA    = 'alimentados.txt'
PARAR    = 'PARAR.txt'
CICLO    = 180
CORTE_SL = '2024-09-12'   # antes disso a carta nao tem vaga de impeto


def agora(): return time.strftime('%Y-%m-%d %H:%M:%S')


def le_jsonl(caminho):
    if not os.path.exists(caminho): return
    with open(caminho, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if not l: continue
            try: yield json.loads(l)
            except Exception: pass


def data_do_datapack(dp):
    s = str(dp or '')
    if len(s) == 8 and s.isdigit():
        return '%s-%s-%s' % (s[:4], s[4:6], s[6:])
    return None


# ---------------------------------------------------------------- tabela de codigos

def monta_tabela(brutos, C):
    """Cruza por id: codigo do efHub -> codigo que o motor usa. Zero chute."""
    por_id = {}
    for c in C:
        b = str(c['id']).split('@')[0]
        por_id.setdefault(b, c)

    pos = collections.defaultdict(collections.Counter)
    est = collections.defaultdict(collections.Counter)
    hab_cand = {}
    for j in brutos:
        c = por_id.get(str(j.get('id')))
        if not c: continue
        p_pt = c.get('np') or c.get('pos')
        if j.get('position') and p_pt:
            pos[j['position']][str(p_pt).split('@')[-1].strip()] += 1
        if j.get('playingStyle') and c.get('modelo'):
            est[j['playingStyle']][c['modelo']] += 1
        fab = set(c.get('fab') or [])
        for s in (j.get('skills') or []):
            hab_cand[s] = fab if s not in hab_cand else (hab_cand[s] & fab)

    T = {'posicao': {k: v.most_common(1)[0][0] for k, v in pos.items()},
         'estilo':  {k: v.most_common(1)[0][0] for k, v in est.items()},
         'habilidade': {k: sorted(v)[0] for k, v in hab_cand.items() if len(v) == 1},
         'habilidade_ambigua': {k: len(v) for k, v in hab_cand.items() if len(v) != 1},
         'cruzados': sum(1 for j in brutos if str(j.get('id')) in por_id)}
    json.dump(T, open(TABELA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return T


# ---------------------------------------------------------------- pool de habilidade

REGRA_POOL = os.environ.get('REGRA_POOL', 'comskills')
# 'comskills' -> o pool sai de comSkills[] (traduzido pela tabela de codigos)
# 'nenhuma'   -> pool vazio: o card NAO entra (trava ligada)
# Quem decide qual regra vale e o deriva_falta.py. Enquanto nao provar, fica comskills;
# se comskills sair vazio, o card e SEGURADO, nunca entra com pool zero.


def pool_do_card(j, T):
    """As habilidades que o card AINDA PODE ganhar. Nunca devolve chute."""
    if REGRA_POOL == 'nenhuma':
        return []
    ja = set(T['habilidade'].get(s) for s in (j.get('skills') or []))
    fora = []
    for s in (j.get('comSkills') or []):
        nome = T['habilidade'].get(s)
        if nome and nome not in ja:
            fora.append(nome)
    return sorted(set(fora))


# ---------------------------------------------------------------- conversao

def converte(j, T):
    pos_pt = T['posicao'].get(j.get('position'))
    est_pt = T['estilo'].get(j.get('playingStyle'))
    if not pos_pt:
        return None, 'codigo de posicao ainda desconhecido: %s' % j.get('position')
    if not est_pt:
        return None, 'codigo de estilo ainda desconhecido: %s' % j.get('playingStyle')

    lc  = int(j.get('levelCap') or 0)
    orc = max(0, 2 * lc - 2)
    dt  = data_do_datapack(j.get('datapackId'))
    b1, b2 = j.get('boostId') or 0, j.get('boostId2') or 0
    if dt and dt < CORTE_SL:
        sl = [0, 0]
    else:
        sl = [0 if b1 else 1, 0 if b2 else 1]

    sec = []
    for a in (j.get('additionalPositions') or []):
        p = a.get('position') if isinstance(a, dict) else a
        q = T['posicao'].get(p)
        if not q:
            return None, 'codigo de posicao secundaria ainda desconhecido: %s' % p
        sec.append(q)

    pool = pool_do_card(j, T)
    if not pool:
        return None, ('POOL DE HABILIDADE VAZIO — nao entra. Nota com pool zero e '
                      'inutilizavel (Musiala caiu de 57,7 para -135,5 quando o pool '
                      'foi de 5 para 0). Falta derivar a regra do `falta`.')

    faltando = [s for s in (j.get('skills') or []) if s not in T['habilidade']]
    if faltando:
        return None, 'codigo de habilidade ainda desconhecido: %s' % ', '.join(faltando[:3])
    fab = [T['habilidade'][s] for s in (j.get('skills') or [])]

    return {
        'id': str(j['id']), 'nome': j.get('name'), 'tier': '?',
        'votos': None, 'ovr': j.get('overallRating'), 'max_ovr': None,
        'pos': pos_pt, 'np': pos_pt, 'sec': '/'.join(sec) or None,
        'modelo': est_pt, 'orc': orc,
        'altura': j.get('height'), 'peso': j.get('weight'),
        'pe': j.get('preferredFoot'),
        'base': list((j.get('stats') or {}).values()),
        'fab': fab, 'falta': pool, 'raras': [],
        'nm': None, 'sl': sl,
        'dt': dt, 'levelCap': lc,
        'boostId': b1, 'boostId2': b2,
        'origem_ficha': 'efhub',
    }, None


def linhas_do_card(c):
    nat_pt = normaliza(c['np'], None)[0]
    if nat_pt == 'SA':
        nat_pt = SA_FAMILIA.get(normaliza(c['np'], c['modelo'])[1]) or nat_pt
    funcs = {f: 'nativa' for f in familia(nat_pt)}
    for p in [x for x in (c['sec'] or '').split('/') if x]:
        if normaliza(p, None)[0] == nat_pt: continue
        f = funcao_nativa(p, c['modelo'])
        if f: funcs.setdefault(f, 'comprada:' + p)
    return [{'card_id': c['id'], 'nome': c['nome'], 'funcao': f, 'origem': o,
             'tier': c['tier'], 'ovr': c['ovr'] or 0, 'orc': c['orc'],
             'progressao': bool(c['orc']), 'estilo': c['modelo'],
             'lancamento': False} for f, o in funcs.items()]


# ---------------------------------------------------------------- ciclo

def ciclo():
    if not os.path.exists(BRUTO):
        return 'ainda nao tem ficha coletada'
    C = json.load(open(CARDS, encoding='utf-8'))
    E = json.load(open(EFHUB, encoding='utf-8')) if os.path.exists(EFHUB) else []
    tenho = ({str(c['id']).split('@')[0] for c in C} |
             {str(c['id']).split('@')[0] for c in E})
    feitos = set(open(MARCA, encoding='utf-8').read().split()) if os.path.exists(MARCA) else set()

    brutos = list(le_jsonl(BRUTO))
    T = monta_tabela(brutos, C)

    novos = [j for j in brutos
             if str(j.get('id')) not in tenho and str(j.get('id')) not in feitos]
    if not novos:
        return ('%d fichas coletadas · nenhuma nova · codigos: %d posicoes, %d estilos, '
                '%d habilidades' % (len(brutos), len(T['posicao']), len(T['estilo']),
                                    len(T['habilidade'])))

    convertidos, esperando, sem_pool = [], [], []
    for j in novos:
        c, motivo = converte(j, T)
        if c:
            convertidos.append(c)
        elif motivo.startswith('POOL'):
            sem_pool.append((j.get('id'), j.get('name'), motivo))
        else:
            esperando.append((j.get('id'), j.get('name'), motivo))

    if convertidos:
        E.extend(convertidos)
        tmp = EFHUB + '.tmp'
        json.dump(E, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
        os.replace(tmp, EFHUB)

        linhas = []
        for c in convertidos:
            linhas.extend(linhas_do_card(c))
        linhas.sort(key=lambda r: -(r['ovr'] or 0))

        antigas = []
        if os.path.exists(EXTRA):
            try: antigas = json.load(open(EXTRA, encoding='utf-8')) or []
            except Exception: antigas = []
        vistas = {'%s|%s' % (r['card_id'], r['funcao']) for r in antigas}
        acrescenta = [r for r in linhas if '%s|%s' % (r['card_id'], r['funcao']) not in vistas]
        todas = antigas + acrescenta
        for i, r in enumerate(todas, 1): r['n'] = i
        tmp = EXTRA + '.tmp'
        json.dump(todas, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
        os.replace(tmp, EXTRA)

        with open(MARCA, 'a', encoding='utf-8') as f:
            for c in convertidos: f.write(c['id'] + '\n')

    if sem_pool:
        novo = not os.path.exists(SEM_POOL)
        with open(SEM_POOL, 'a', encoding='utf-8', newline='') as f:
            w = csv.writer(f, delimiter=';')
            if novo: w.writerow(['id', 'nome', 'motivo'])
            w.writerows(sem_pool)

    if esperando:
        novo = not os.path.exists(ESPERA)
        with open(ESPERA, 'a', encoding='utf-8', newline='') as f:
            w = csv.writer(f, delimiter=';')
            if novo: w.writerow(['id', 'nome', 'motivo'])
            w.writerows(esperando)

    return ('%d fichas · %d cards NOVOS · %d linhas na fila · %d SEGURADOS por pool vazio · '
            '%d esperando codigo · codigos: %d pos / %d est / %d hab'
            % (len(brutos), len(convertidos),
               len(acrescenta) if convertidos else 0, len(sem_pool), len(esperando),
               len(T['posicao']), len(T['estilo']), len(T['habilidade'])))


print('=' * 70)
print('  ALIMENTADOR — da coleta para a fila do motor, com ele rodando')
print('=' * 70)
print('olhando %s a cada %d s' % (BRUTO, CICLO))
print('grava em %s e acrescenta em %s' % (EFHUB, EXTRA))
print('NAO escreve no %s — quem regenera aquele arquivo e o atualizar.py' % CARDS)
print('para fechar: crie o PARAR.txt')
print('=' * 70, flush=True)

while not os.path.exists(PARAR):
    try:
        print('[%s] %s' % (agora(), ciclo()), flush=True)
    except Exception as e:
        print('[%s] tropecei: %s — tento de novo no proximo ciclo' % (agora(), e), flush=True)
    time.sleep(CICLO)

print('[%s] fechado.' % agora())
