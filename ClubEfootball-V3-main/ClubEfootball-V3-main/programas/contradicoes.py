# -*- coding: utf-8 -*-
"""
O DADO QUE NAO PODE SER VERDADE — o sistema achando sozinho o que esta errado.

ORDEM DO LUIS, 15/08/2026 (a bronca que fez isto existir):
    "Do que adianta gravar no banco que aquele card esta resolvido porque EU fui
     la e olhei? Voce acha que eu vou olhar card por card? E o seu metodo que
     esta errado. Nao e esperar eu falar pra voce que esta errado."

Ele esta certo. O caso que nos pegou — o Diego Costa rodando sem impeto e sem
vaga — era achavel SEM ninguem abrir o jogo, por duas vias:

    1. CONTRADICAO LOGICA
       card lancado depois de 12/09/2024 · sl [0,0] (nenhuma vaga)
       · nm vazio (nenhum efeito de fabrica)
       -> impossivel. Ou ele tem vaga, ou tem impeto de fabrica COM efeito.
          Os dois "nao" ao mesmo tempo nao existem no jogo.

    2. ANOMALIA DE COLETA
       boostId2 preenchido em 2 de 6.469 cards = 0,03% da base.
       Campo que aparece em 0,03% nao e regra: e lixo que veio na coleta.

Este programa nao pergunta nada a ninguem. Ele le a base e aplica as regras que
o proprio sistema ja tem escritas, e diz o que NAO PODE ser verdade.

⛔ Ele NAO conserta. Achar e consertar sao coisas diferentes: conserto sem
   medida vira suposicao, e suposicao e o que quebra este sistema.
   Ele lista, ordena pelo tamanho do estrago, e diz o que fazer com cada um.
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

D = 'dados/'
BASE = D + 'base_unica.json'
CARDS = D + 'cards.json'
CONFERIDO = 'CONFERIDO.json'
REL = 'RELATORIO-CONTRADICOES.txt'
DATA_DO_IMPETO = datetime.date(2024, 9, 12)   # antes disto o impeto nao existia
RARO = 0.005                                   # campo em menos de 0,5% da base = anomalia

L = []
def P(*a):
    t = ' '.join(str(x) for x in a); print(t, flush=True); L.append(t)

def pausa():
    try:
        if sys.stdin and sys.stdin.isatty(): input('\nEnter para fechar...')
    except Exception: pass

P('=' * 76)
P('  O DADO QUE NAO PODE SER VERDADE')
P('  o sistema conferindo a si mesmo — sem ninguem olhar card por card')
P('=' * 76)
P('')

if os.path.exists(BASE):
    lista = (json.load(open(BASE, encoding='utf-8')) or {}).get('cards') or []
    P('base ............ %s   (%d cards)' % (BASE, len(lista)))
elif os.path.exists(CARDS):
    lista = json.load(open(CARDS, encoding='utf-8'))
    P('base ............ %s   (%d registros)' % (CARDS, len(lista)))
else:
    P('NAO ACHEI a base.'); pausa(); sys.exit(1)

cards = {}
for c in lista:
    cid = str(c.get('id')).split('@')[0]
    if cid not in cards or (c.get('orc') or 0) > (cards[cid].get('orc') or 0):
        cards[cid] = c
N = len(cards)

conf = {}
if os.path.exists(CONFERIDO):
    try: conf = (json.load(open(CONFERIDO, encoding='utf-8')) or {}).get('conferidos') or {}
    except Exception: conf = {}
for cid, campos in conf.items():
    c = cards.get(cid)
    if not c: continue
    for campo, d in campos.items():
        if isinstance(d, dict) and 'valor' in d:
            c[campo] = d['valor']
P('conferido ....... %d cards ja conferidos entram por cima' % len(conf))
P('')

achados = collections.defaultdict(list)      # regra -> [(cid, detalhe)]
COMO = {}

def data_de(c):
    try: return datetime.date(*map(int, str(c.get('dt')).split('-')))
    except Exception: return None

# =====================================================================
# REGRA 1 — a vaga impossivel
# =====================================================================
COMO['VAGA IMPOSSIVEL: sem vaga E sem impeto, num card que nasceu depois do impeto'] = (
    'Card lancado a partir de 12/09/2024 com sl [0,0] E nm vazio. Se nao ha vaga\n'
    '   e porque as duas ja vieram de fabrica — e entao o efeito NAO pode estar\n'
    '   vazio. Um dos dois dados esta errado. O motor roda esse card sem impeto\n'
    '   NENHUM e ainda sem poder fabricar: perde dos dois lados.\n'
    '   O QUE FAZER: conferir a ficha no jogo (1 card resolve todos que usam o\n'
    '   mesmo boostId) ou rodar o COLETAR-EFSCOUT para atualizar o catalogo.')
COMO['VAGA SUSPEITA: sem vaga, sem impeto e sem boostId (pode ser a 2a trava)'] = (
    'Mesma cara do caso acima, MAS sem boostId nenhum. Pode ser legitimo: a 2a\n'
    '   trava diz que so Special e Epic tem vaga craftavel, entao card comum\n'
    '   lancado depois de 12/09/2024 pode mesmo nao ter vaga.\n'
    '   Fica aqui embaixo de proposito — e SUSPEITA, nao erro provado.\n'
    '   O QUE FAZER: so olhar se o numero crescer de repente (aí a coleta mudou).')
for cid, c in cards.items():
    d = data_de(c)
    sl = c.get('sl') or []
    if not (d and d >= DATA_DO_IMPETO and list(sl) == [0, 0] and not c.get('nm')):
        continue
    tem_boost = (c.get('boostId') or 0) or (c.get('boostId2') or 0)
    if tem_boost:
        # CERTEZA: ele TEM impeto de fabrica (o boostId prova), entao o efeito
        # nao pode estar vazio E a vaga nao pode estar zerada ao mesmo tempo.
        achados['VAGA IMPOSSIVEL: sem vaga E sem impeto, num card que nasceu depois do impeto'].append(
            (cid, 'lancado %s · boostId %s/%s' % (c.get('dt'), c.get('boostId'), c.get('boostId2'))))
    else:
        achados['VAGA SUSPEITA: sem vaga, sem impeto e sem boostId (pode ser a 2a trava)'].append(
            (cid, 'lancado %s' % c.get('dt')))

# =====================================================================
# REGRA 2 — a vaga que nao existe no jogo
# =====================================================================
COMO['VAGA [1,1]: nao existe no jogo'] = (
    'O jogo nunca da DUAS vagas livres. Ja foram consertados 145 cards assim em\n'
    '   14/08; se voltar a aparecer, a derivacao do sl quebrou de novo.\n'
    '   O QUE FAZER: CONSERTAR-VAGA-DO-MOTOR.bat')
for cid, c in cards.items():
    if list(c.get('sl') or []) == [1, 1]:
        achados['VAGA [1,1]: nao existe no jogo'].append((cid, 'sl [1,1]'))

# =====================================================================
# REGRA 3 — impeto de fabrica sem efeito
# =====================================================================
COMO['IMPETO SEM EFEITO: o card tem, o catalogo nao conhece'] = (
    'O card veio com boostId, mas o efeito (nm) esta vazio: o motor otimiza como\n'
    '   se o card nao tivesse aquele impeto. A nota fica SUBESTIMADA.\n'
    '\n'
    '   ⛔ MEDIDO EM 15/08 — NAO ADIANTA RODAR O COLETAR-EFSCOUT:\n'
    '      o catalogo do efScout (baixado na hora, versao 2026.08.14) tem 402\n'
    '      impetos, com ids de 1 a 516. Os ids que faltam vao de 1677 a 2074 —\n'
    '      estao FORA da faixa. Nao e catalogo velho: sao numeracoes DIFERENTES.\n'
    '      O efScout nao conhece esses ids (procurados um a um no boot.json).\n'
    '      O efHub, que emite esses ids, NAO tem rota publica de catalogo\n'
    '      (/api/public/boosters e /boosts dao 404) e a pagina do card so\n'
    '      renderiza por JS, que a leitura automatica nao alcanca.\n'
    '\n'
    '   O QUE FAZER (o unico caminho provado): abrir a ficha do card NO JOGO e\n'
    '   anotar o impeto. UM card resolve TODOS os que usam o mesmo id — foi assim\n'
    '   que o Hazard (id 1834 = Rompe-barreira +4) foi resolvido em 14/08.\n'
    '   Hoje sao 15 ids para 16 cards: quase um card por id.')
for cid, c in cards.items():
    if ((c.get('boostId') or 0) or (c.get('boostId2') or 0)) and not c.get('nm'):
        achados['IMPETO SEM EFEITO: o card tem, o catalogo nao conhece'].append(
            (cid, 'boostId %s/%s' % (c.get('boostId'), c.get('boostId2'))))

# =====================================================================
# REGRA 4 — campo que quase nao existe = lixo de coleta
# =====================================================================
COMO['CAMPO RARO DEMAIS: aparece em menos de 0,5% da base'] = (
    'Um campo preenchido em pouquissimos cards nao e regra do jogo: e sobra da\n'
    '   coleta. Foi assim que o `boostId2` (2 cards em 6.469 = 0,03%) zerou a vaga\n'
    '   de impeto do Diego Costa e do Elliot Anderson.\n'
    '   O QUE FAZER: olhar 1 desses cards no jogo e, se for lixo, o CONFERIDO manda.')
freq = collections.Counter()
for c in cards.values():
    for k, v in c.items():
        if v in (None, '', [], {}, 0): continue
        freq[k] += 1
raros = {k: q for k, q in freq.items() if 0 < q <= max(3, int(N * RARO))}
for k, q in sorted(raros.items(), key=lambda t: t[1]):
    quem = [cid for cid, c in cards.items() if c.get(k) not in (None, '', [], {}, 0)][:6]
    achados['CAMPO RARO DEMAIS: aparece em menos de 0,5% da base'].append(
        ('campo `%s`' % k, '%d de %d cards (%.2f%%) — ex.: %s'
         % (q, N, 100.0 * q / N, ', '.join((cards[x].get('nome') or x) for x in quem if x in cards))))

# =====================================================================
# REGRA 5 — tem orcamento mas nao tem pool
# =====================================================================
COMO['SEM POOL: tem nivel para evoluir, mas nao tem habilidade a escolher'] = (
    'Card com orcamento > 0 e `falta` vazio: o motor nao tem o que adicionar.\n'
    '   Pode ser legitimo (POTW nao adiciona), mas em card comum e furo de coleta.\n'
    '   O QUE FAZER: TAPAR-FUROS.bat')
for cid, c in cards.items():
    if (c.get('orc') or 0) > 0 and not (c.get('falta') or []):
        achados['SEM POOL: tem nivel para evoluir, mas nao tem habilidade a escolher'].append(
            (cid, 'orcamento %s' % c.get('orc')))

# =====================================================================
# REGRA 6 — o vetor dos 26 atributos
# =====================================================================
COMO['ATRIBUTO FORA DO LUGAR: o vetor nao tem 26 numeros'] = (
    'Todo card tem exatamente 26 atributos, na ordem fixa. Vetor com outro\n'
    '   tamanho desliza TODOS os atributos e a nota vira ficcao.\n'
    '   O QUE FAZER: parar tudo e refazer a coleta desse card.')
for cid, c in cards.items():
    b = c.get('base')
    if b is not None and len(b) != 26:
        achados['ATRIBUTO FORA DO LUGAR: o vetor nao tem 26 numeros'].append(
            (cid, '%d valores' % len(b)))

# ===================================================================== SAIDA
P('-' * 76)
P('O QUE NAO PODE SER VERDADE')
P('-' * 76)
if not achados:
    P('')
    P('   Nada. Toda contradicao conhecida esta zerada.')
else:
    for regra, itens in sorted(achados.items(), key=lambda t: -len(t[1])):
        P('')
        P('🔴 %s' % regra)
        P('   %d casos' % len(itens))
        P('')
        P('   %s' % COMO.get(regra, ''))
        P('')
        for cid, det in itens[:8]:
            nome = (cards.get(cid, {}).get('nome') or cid) if cid in cards else cid
            ovr = cards.get(cid, {}).get('ovr') if cid in cards else ''
            P('      %-26s %-4s %s' % (str(nome)[:26], ovr or '', det))
        if len(itens) > 8:
            P('      ... e mais %d (a lista inteira esta no %s)' % (len(itens) - 8, REL))

P('')
P('=' * 76)
P('  %d contradicoes em %d cards.' % (sum(len(v) for v in achados.values()), N))
P('  Nada foi consertado — achar e consertar sao coisas diferentes.')
P('  Relatorio completo: %s' % REL)
P('=' * 76)

# o resumo que o PAINEL le (o painel so mostra; quem acha e este programa)
try:
    json.dump({'quando': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
               'total': sum(len(v) for v in achados.values()),
               'regras': {k: len(v) for k, v in achados.items()}},
              open('CONTRADICOES.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
except Exception:
    pass

with open(REL, 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n\n')
    f.write('=' * 76 + '\nA LISTA INTEIRA\n' + '=' * 76 + '\n')
    for regra, itens in sorted(achados.items(), key=lambda t: -len(t[1])):
        f.write('\n### %s (%d)\n' % (regra, len(itens)))
        for cid, det in itens:
            nome = (cards.get(cid, {}).get('nome') or cid) if cid in cards else cid
            f.write('   %-30s %-18s %s\n' % (str(nome)[:30], cid, det))
pausa()
