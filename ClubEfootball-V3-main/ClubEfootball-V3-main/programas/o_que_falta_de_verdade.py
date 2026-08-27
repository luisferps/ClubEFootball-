# -*- coding: utf-8 -*-
"""
O QUE FALTA DE VERDADE — as tres perguntas juntas, numa tela so.

ORDEM DO LUIS, 14/08/2026:
    "Voce precisa cruzar fontes, pelo amor de Deus."
    "Cruza com o que voce ve nos cards. Se voce esta vendo um card que tem uma
     coisa que voce nao tem no catalogo, o que voce vai fazer? Vai procurar
     nas fontes se ela existe ou nao existe."

AS TRES PERGUNTAS
  1. QUANTO cada fonte tem, e quanto mudou desde ontem
  2. as fontes CONCORDAM entre si?
  3. o que os CARDS CITAM e nenhum catalogo nosso tem   <- este e o que acha

⚠️ A LICAO DE 14/08: contar fonte contra fonte NAO BASTA.
   O efScout dizia 65 habilidades e nos tinhamos 65 — parecia perfeito.
   Mas 54 cards usam "Dominio aereo", que nao esta no nosso catalogo.
   Bater no numero nao quer dizer serem as mesmas. So o cruzamento com o
   CARD pega isso.

COMO USAR
   Sozinho (le so o que esta na pasta):        python o_que_falta_de_verdade.py
   Com a resposta das fontes ao vivo:          coloque FONTES-AO-VIVO.json na
   pasta (o Claude gera pelo seu Chrome) e ele entra na conta.

So le. Nao muda nada.
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
import json, os, sys, io, collections, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.join('dados', 'base_unica.json')
HIST = 'o_que_falta_historico.json'
AOVIVO = 'FONTES-AO-VIVO.json'
SAIDA = 'O-QUE-FALTA-DE-VERDADE.txt'

L = []
def P(*a):
    t = ' '.join(str(x) for x in a); print(t, flush=True); L.append(t)


def le(p, padrao=None):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return padrao


if not os.path.exists(BASE):
    print('nao achei o %s. Rode o UNIFICAR-BASE antes.' % BASE)
    raise SystemExit(1)

B = le(BASE, {})
cards = [c for c in (B.get('cards') or [])]
base_cards = [c for c in cards if '@' not in str(c.get('id'))]

# ---------------------------------------------------------------- catalogos
boosters = le('efscout_boosters.json', []) or []
CATB = {int(b['id']): b.get('name') for b in boosters if isinstance(b, dict) and 'id' in b}
HAB = le('HAB_EFEITOS_FINAL.json', {}) or {}
CATH = {v.get('arquivo') for v in HAB.values() if isinstance(v, dict)}
TEC = le('tecnicos.json', {}) or {}
n_tec = len(TEC if not isinstance(TEC, dict) else TEC)

NOSSO = collections.OrderedDict([
    ('cards', len(base_cards)),
    ('impetos (catalogo)', len(CATB)),
    ('habilidades (catalogo)', len(CATH)),
    ('tecnicos', n_tec),
])

vivo = le(AOVIVO, {}) or {}

P('=' * 80)
P('  O QUE FALTA DE VERDADE   %s' % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
P('=' * 80)

# =====================================================================
# 1 e 2 — QUANTO CADA FONTE TEM, E SE ELAS CONCORDAM
# =====================================================================
P('')
P('1 e 2. QUANTO CADA FONTE TEM  ·  e se elas concordam')
P('-' * 80)
if vivo:
    P('  resposta das fontes de %s' % vivo.get('quando', '?'))
    P('')
    P('  %-26s %10s %10s %12s %10s' % ('', 'efScout', 'efHub', 'efootballdb', 'NOS'))
    linhas = [
        ('cards',       vivo.get('efscout_cards'), vivo.get('efhub_cards'),
         vivo.get('efdb_cards'), NOSSO['cards']),
        ('impetos',     vivo.get('efscout_boosters'), None, None, NOSSO['impetos (catalogo)']),
        ('habilidades', vivo.get('efscout_skills'), None, None, NOSSO['habilidades (catalogo)']),
        ('tecnicos',    vivo.get('efscout_coaches'), None, vivo.get('efdb_managers'), NOSSO['tecnicos']),
    ]
    for nome, a, b_, c_, n in linhas:
        f = lambda x: ('%d' % x) if isinstance(x, int) else '-'
        P('  %-26s %10s %10s %12s %10s' % (nome, f(a), f(b_), f(c_), f(n)))
    if vivo.get('efscout_versao'):
        P('')
        P('  versao do efScout: %s' % vivo['efscout_versao'])
        ont = (le(HIST, {}) or {}).get('efscout_versao')
        if ont and ont != vivo['efscout_versao']:
            P('  ⚠️  MUDOU desde a ultima vez (era %s) — tem dado novo la.' % ont)
        elif ont:
            P('  (mesma da ultima vez — o efScout nao publicou nada novo)')
else:
    P('  Sem o %s nesta pasta, so consigo contar o que esta aqui:' % AOVIVO)
    for k, v in NOSSO.items():
        P('     %-26s %8d' % (k, v))
    P('')
    P('  ⚠️  As fontes so respondem pelo Chrome logado (403 de fora).')
    P('     Peca ao Claude: "vai nas fontes e me diz quantos tem".')

# =====================================================================
# 3 — O QUE OS CARDS CITAM E NINGUEM TEM
# =====================================================================
P('')
P('3. O QUE OS CARDS CITAM E O NOSSO CATALOGO NAO TEM')
P('-' * 80)
P('  ⛔ E aqui que mora o buraco de verdade. Se um card usa uma coisa e o')
P('     catalogo nao conhece, o motor calcula esse card sem ela.')

# impetos
falta_b = collections.defaultdict(list)
for c in cards:
    for k in ('boostId', 'boostId2'):
        v = c.get(k)
        try:
            v = int(v or 0)
        except Exception:
            v = 0
        if v and v not in CATB:
            falta_b[v].append((str(c['id']), c.get('nome'), c.get('ovr') or 0))

P('')
P('  IMPETO — numeros que os cards usam e o catalogo nao tem')
if not falta_b:
    P('     nenhum. Todos os impetos citados estao no catalogo.')
else:
    P('     %d impetos diferentes, em %d cards.'
      % (len(falta_b), sum(len(v) for v in falta_b.values())))
    P('     Conferir UM card no jogo resolve TODOS os que usam aquele impeto.')
    P('')
    for bid, li in sorted(falta_b.items(), key=lambda t: -len(t[1])):
        li.sort(key=lambda x: -x[2])
        i, n, o = li[0]
        P('       impeto %-6s %2d cards   abra no jogo: %s (ovr %s)'
          % (bid, len(li), (n or '?')[:26], o))

# habilidades
falta_h = collections.Counter()
exemplo_h = {}
for c in cards:
    for h in (c.get('fab') or []) + (c.get('raras') or []):
        if h and h not in CATH:
            falta_h[h] += 1
            exemplo_h.setdefault(h, (c.get('nome'), c.get('ovr')))
P('')
P('  HABILIDADE — nomes que os cards tem e o catalogo nao tem')
if not falta_h:
    P('     nenhuma.')
else:
    for h, n in falta_h.most_common():
        nm, ov = exemplo_h.get(h, ('?', '?'))
        P('       %-30s %4d cards   ex: %s (ovr %s)' % (h, n, nm, ov))
    P('')
    P('     ⚠️  O motor NAO sabe quanto essas valem. Ele calcula esses cards')
    P('        sem elas — a nota sai por baixo.')

# estilos
mod = collections.Counter(c.get('modelo') for c in base_cards if c.get('modelo'))
P('')
P('  ESTILO DE JOGO — %d diferentes vistos nos cards' % len(mod))
if vivo.get('efscout_playingstyles'):
    d = vivo['efscout_playingstyles'] - len(mod)
    if d > 0:
        P('     o efScout diz %d. Faltam %d que nunca vimos num card nosso.'
          % (vivo['efscout_playingstyles'], d))
    else:
        P('     bate com o efScout (%d).' % vivo['efscout_playingstyles'])

# =====================================================================
hoje = {
    'quando': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    'impetos_orfaos': sorted(falta_b),
    'habilidades_orfas': sorted(falta_h),
    'efscout_versao': vivo.get('efscout_versao'),
}
ontem = le(HIST, {}) or {}
if ontem:
    P('')
    P('-' * 80)
    P('DESDE A ULTIMA VEZ (%s)' % ontem.get('quando', '?'))
    P('-' * 80)
    a = set(ontem.get('impetos_orfaos') or [])
    b_ = set(hoje['impetos_orfaos'])
    P('  impetos que o catalogo aprendeu ... %d' % len(a - b_))
    P('  impetos orfaos novos ............... %d' % len(b_ - a))
    ah = set(ontem.get('habilidades_orfas') or [])
    bh = set(hoje['habilidades_orfas'])
    P('  habilidades que entraram ........... %d' % len(ah - bh))
    P('  habilidades orfas novas ............ %d' % len(bh - ah))

P('')
P('=' * 80)
P('  So leitura. Nada foi alterado.')
P('=' * 80)

open(SAIDA, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
json.dump(hoje, open(HIST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nGravado: %s' % SAIDA)
