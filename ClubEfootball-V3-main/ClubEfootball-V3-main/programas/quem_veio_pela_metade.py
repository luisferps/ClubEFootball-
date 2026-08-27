# -*- coding: utf-8 -*-
"""
QUEM VEIO PELA METADE — o card que a fonte entregou incompleto, e o relogio dele.

ORDEM DO LUIS, 15/08/2026:
    "Esse é um típico caso que, quando a gente começar a colocar o atualizador
     pra rodar, não pode acontecer. Se já é de dois ou três dias, ele já deve ter
     sido publicado em algum lugar."
    e depois, cravando o prazo:
    "SE PASSAR DE 24H JA ESTA ERRADO."

O QUE ACONTECEU E FEZ ISTO EXISTIR (box de 13/08, medido em 15/08):
    136 cards entraram · 34 sem progressao (orcamento zero) · 16 com impeto de
    fabrica cujo efeito o catalogo nao conhece · 2 com o segundo impeto vindo
    LIXO na coleta (Diego Costa e Elliot Anderson — os unicos 2 em 6.469 cards
    com boostId2 preenchido). O Diego Costa rodou como se nao tivesse impeto
    NENHUM e ainda sem vaga para fabricar: perdeu dos dois lados.
    570 linhas ja gastas (3,3 h de motor) que vao ter de ser refeitas.

O RELOGIO — por que NAO e a data de lancamento
    Medido: dos 1.271 cards esperando progressao, 1.237 NAO TEM data de
    lancamento. Cobrar 24h pela data deixaria 97% de fora. Entao o relogio
    comeca quando NOS VEMOS o card incompleto pela primeira vez, e isso fica
    carimbado no VISTO-INCOMPLETO.json.

O QUE ELE FAZ
    (sem argumento)  so olha e escreve o relatorio. Nao toca em nada.
    --refilar        devolve para a fila as linhas que JA PODEM rodar melhor:
                       A) o card tem orcamento hoje e a linha rodou sem gastar
                          um ponto (a progressao chegou depois)
                       B) o card tem vaga de impeto livre hoje e a linha nao
                          fabricou impeto nenhum (a vaga apareceu depois)
                     Backup de tudo que toca, com carimbo de hora.

⛔ O --refilar so COM O MOTOR PARADO (ele mexe no feitos.txt e na saida).
   Sem argumento pode rodar a qualquer hora — so le.
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
import json, os, sys, io, time, shutil, collections, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))
REFILAR = '--refilar' in sys.argv
ADIAR   = '--adiar' in sys.argv

D = 'dados/'
BASE = D + 'base_unica.json'
CARDS = D + 'cards.json'
CONFERIDO = 'CONFERIDO.json'
CARIMBO = 'VISTO-INCOMPLETO.json'
FILA = 'fila_v6.json'
PRIORIDADE = 'fila_PRIORIDADE.json'
FEITOS = 'feitos.txt'
SAIDA = 'saida_v6'
LINHAS = os.path.join(SAIDA, 'linhas.jsonl')
REL = 'RELATORIO-VEIO-PELA-METADE.txt'
ADIADA = 'fila_ADIADA_INCOMPLETO.json'
PRAZO_HORAS = 24

L = []
def P(*a):
    t = ' '.join(str(x) for x in a); print(t, flush=True); L.append(t)

def pausa():
    try:
        if sys.stdin and sys.stdin.isatty(): input('\nEnter para fechar...')
    except Exception: pass

def grava_rel():
    open(REL, 'w', encoding='utf-8').write('\n'.join(L) + '\n')

P('=' * 74)
P('  QUEM VEIO PELA METADE   ·   o prazo e de %d horas' % PRAZO_HORAS)
P('=' * 74)
P('')

# ------------------------------------------------------------------ os cards
if os.path.exists(BASE):
    _b = json.load(open(BASE, encoding='utf-8'))
    lista = _b.get('cards') or []
    P('base ................... %s (%d cards)' % (BASE, len(lista)))
elif os.path.exists(CARDS):
    lista = json.load(open(CARDS, encoding='utf-8'))
    P('base ................... %s (%d registros)' % (CARDS, len(lista)))
else:
    P('NAO ACHEI nem o %s nem o %s' % (BASE, CARDS)); grava_rel(); pausa(); sys.exit(1)

cards = {}
for c in lista:
    cid = str(c.get('id')).split('@')[0]
    if cid not in cards or (c.get('orc') or 0) > (cards[cid].get('orc') or 0):
        cards[cid] = c

# ---- o CONFERIDO manda em tudo (pode nao ter passado pelo unificar ainda)
conf = {}
if os.path.exists(CONFERIDO):
    try:
        conf = (json.load(open(CONFERIDO, encoding='utf-8')) or {}).get('conferidos') or {}
    except Exception:
        conf = {}
aplicados = 0
for cid, campos in conf.items():
    c = cards.get(cid)
    if not c: continue
    for campo, d in campos.items():
        if isinstance(d, dict) and 'valor' in d:
            c[campo] = d['valor']; aplicados += 1
P('conferido no jogo ...... %d campos aplicados por cima' % aplicados)

# ------------------------------------------------------- quem esta incompleto
def motivos_de(c):
    m = []
    lc = c.get('levelCap')
    # so e "incompleto" quem esta SEM ORCAMENTO por falta do nivel.
    # ⚠️ levelCap 1 e LEGITIMO (card Standard que nao evolui, decisao de 08/08)
    #    e card antigo sem o campo mas com orcamento nao esta esperando nada.
    if (c.get('orc') or 0) == 0 and lc in (None, 0):
        m.append('sem progressao (o efHub ainda nao publicou o nivel)')
    if ((c.get('boostId') or 0) or (c.get('boostId2') or 0)) and not c.get('nm'):
        m.append('impeto de fabrica sem efeito conhecido')
    # =====================================================================
    # 17/08 - O CRITERIO 'sem pool de habilidade' FOI RETIRADO DAQUI.
    #
    #    Ele dizia:
    #        if not (c.get('falta') or []) and (c.get('levelCap') or 0) > 1:
    #            m.append('sem pool de habilidade')
    #
    # ⛔ Isso REPOS a trava de pool vazio que CAIU em 08/08 por ordem do Luis.
    #    O `monta_fila.py` avisa em letra garrafal: "A TRAVA DE POOL VAZIO CAIU
    #    - 08/08, ordem do Luis. NAO REPOR." Ela voltou aqui, por outra porta,
    #    escrita em 15/08 para outro fim.
    #
    #    Por que ela nao tem objeto: o pool NAO vem mais do `falta`. Desde 08/08
    #    o roda_lote_v6.py roda com POOL='regra' e faz, na linha 419:
    #        c['falta'] = _pool_de(c, bid, r['funcao'])
    #    ou seja, ele SOBRESCREVE o `falta` do card com as 44 comuns do jogo
    #    menos as que o card ja tem. Card com `falta` vazio tem pool de 34 a 42.
    #
    #    Custo medido do estrago, em 17/08: 131 linhas / 31 cards segurados -
    #    entre eles Ilkay Gundogan 90, Ricardo Horta 84 e Douglas Luiz 83.
    #    (Em 08/08, quando a trava voltou de carona numa copia velha, o custo
    #     foi 209 linhas / 73 cards, incluindo 14 dos 21 cards novos da home.)
    # =====================================================================
    return m

incompletos = {}
for cid, c in cards.items():
    m = motivos_de(c)
    if m: incompletos[cid] = m

# ------------------------------------------------------------- o RELOGIO
hoje = datetime.datetime.now()
carimbos = {}
if os.path.exists(CARIMBO):
    try: carimbos = json.load(open(CARIMBO, encoding='utf-8'))
    except Exception: carimbos = {}

novos = 0
for cid in incompletos:
    if cid not in carimbos:
        carimbos[cid] = hoje.strftime('%Y-%m-%d %H:%M'); novos += 1
curados = [cid for cid in list(carimbos) if cid not in incompletos]
for cid in curados:
    del carimbos[cid]

def horas_de(cid):
    try:
        t = datetime.datetime.strptime(carimbos[cid], '%Y-%m-%d %H:%M')
        return (hoje - t).total_seconds() / 3600.0
    except Exception:
        return 0.0

vencidos = [cid for cid in incompletos if horas_de(cid) > PRAZO_HORAS]

P('')
P('-' * 74)
P('O QUE ESTA INCOMPLETO')
P('-' * 74)
conta = collections.Counter()
for m in incompletos.values():
    for x in m: conta[x] += 1
for k, v in conta.most_common():
    P('   %-46s %5d cards' % (k, v))
P('   %-46s %5d cards' % ('COM ALGUM PROBLEMA (sem repetir)', len(incompletos)))
P('')
P('   vistos AGORA pela primeira vez ............. %5d' % novos)
P('   que se resolveram desde a ultima olhada .... %5d' % len(curados))
P('')
P('   🔴 VENCIDOS (mais de %dh esperando) ......... %5d' % (PRAZO_HORAS, len(vencidos)))
if vencidos:
    P('')
    P('   ESTES JA DEVIAM TER SAIDO EM ALGUM LUGAR — PROCURAR NA MAO:')
    for cid in sorted(vencidos, key=lambda i: -(cards[i].get('ovr') or 0))[:20]:
        c = cards[cid]
        P('      ovr %-3s %-24s %5.0fh   %s'
          % (c.get('ovr'), (c.get('nome') or cid)[:24], horas_de(cid),
             ' · '.join(incompletos[cid])[:44]))
    if len(vencidos) > 20:
        P('      ... e mais %d (a lista inteira esta no %s)' % (len(vencidos) - 20, REL))

# --------------------------------------------- quem JA PODE rodar melhor
try:
    from equacao import ACCU
except Exception:
    ACCU = None

def gasto(bar):
    if not bar or ACCU is None: return 0
    t = 0
    for k, n in bar.items():
        try: t += ACCU[int(n)]
        except Exception: pass
    return t

refazer, porque = set(), collections.defaultdict(set)
if os.path.exists(LINHAS):
    for l in open(LINHAS, encoding='utf-8'):
        if not l.strip(): continue
        try: x = json.loads(l)
        except Exception: continue
        cid = str(x.get('card_id', '')).split('@')[0]
        c = cards.get(cid)
        if not c: continue
        k = '%s|%s' % (cid, x.get('funcao'))
        orc = c.get('orc') or 0
        if orc > 0 and gasto(x.get('barras')) == 0:
            refazer.add(k); porque['a progressao chegou depois de a linha rodar'].add(cid)
        sl = c.get('sl') or []
        if any(v == 1 for v in sl) and not x.get('impeto'):
            refazer.add(k); porque['a vaga de impeto apareceu depois'].add(cid)

P('')
P('-' * 74)
P('O QUE JA PODE RODAR MELHOR AGORA')
P('-' * 74)
if not refazer:
    P('   Nada. Nenhuma linha rodou com dado que hoje esta melhor.')
else:
    for k, v in sorted(porque.items(), key=lambda t: -len(t[1])):
        P('   %-46s %4d cards' % (k, len(v)))
    feitos = set()
    if os.path.exists(FEITOS):
        feitos = {l.strip() for l in open(FEITOS, encoding='utf-8') if l.strip()}
    ja = refazer & feitos
    P('')
    P('   linhas para refazer ....... %d   (~%.1f h de motor)' % (len(ja), len(ja) * 21 / 3600.0))
    nomes = {cid: cards[cid].get('nome') for cid in set().union(*porque.values())} if porque else {}
    cont = collections.Counter(k.split('|')[0] for k in ja)
    for cid, q in cont.most_common(10):
        P('      %-26s %2d linhas' % ((nomes.get(cid) or cid)[:26], q))

json.dump(carimbos, open(CARIMBO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# o resumo que o PAINEL le
try:
    json.dump({'quando': hoje.strftime('%d/%m/%Y %H:%M'),
               'incompletos': len(incompletos), 'vencidos': len(vencidos),
               'prazo_horas': PRAZO_HORAS,
               'motivos': {k: v for k, v in conta.items()},
               'lista_vencidos': [{'id': i, 'nome': cards[i].get('nome'),
                                   'ovr': cards[i].get('ovr'),
                                   'horas': round(horas_de(i)),
                                   'porque': incompletos[i]}
                                  for i in sorted(vencidos,
                                      key=lambda x: -(cards[x].get('ovr') or 0))[:60]]},
              open('VEIO-PELA-METADE.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
except Exception:
    pass
P('')
P('carimbo do relogio ..... %s (%d cards sendo cronometrados)' % (CARIMBO, len(carimbos)))

# =================================================================== ADIAR
# ORDEM DO LUIS, 15/08: "vai pegar os cards que estao faltando, vai rodar eles
# pra depois achar e rodar de novo?"
# Ele esta certo: o porteiro tem de ficar na ENTRADA. Card incompleto NAO ENTRA
# na fila — fica adiado, sem gastar um segundo de motor — e volta sozinho
# quando o dado chegar (e o --refilar que devolve).
# Mesmo padrao do separa_fila_adiada.py, que ja faz isso com quem nao tem
# impeto de fabrica.
if ADIAR:
    if not os.path.exists(FILA):
        P(''); P('NAO ACHEI o %s' % FILA); grava_rel(); pausa(); sys.exit(1)
    fila = json.load(open(FILA, encoding='utf-8'))
    feitos_ = set()
    if os.path.exists(FEITOS):
        feitos_ = {l.strip() for l in open(FEITOS, encoding='utf-8') if l.strip()}
    fica, sai = [], []
    for r in fila:
        raiz = str(r.get('card_id', '')).split('@')[0]
        k = '%s|%s' % (raiz, r.get('funcao'))
        # ⛔ linha JA RODADA nao e adiada: tirar da fila nao apaga a nota, e
        #    quem devolve ela para a fila e o --refilar, quando o dado chegar.
        if raiz in incompletos and k not in feitos_:
            x = dict(r); x['_porque_adiada'] = incompletos[raiz]; sai.append(x)
        else:
            fica.append(r)
    P('')
    P('-' * 74)
    P('ADIANDO — o card incompleto nao entra na fila')
    P('-' * 74)
    P('   linhas na fila antes ....... %d' % len(fila))
    P('   ADIADAS (dado incompleto) .. %d   (~%.1f h de motor que NAO vao ser gastas)'
      % (len(sai), len(sai) * 21 / 3600.0))
    P('   ficam para rodar ........... %d' % len(fica))
    quem = collections.Counter()
    for x in sai:
        for m in x['_porque_adiada']: quem[m] += 1
    for k2, v2 in quem.most_common():
        P('      %-46s %4d linhas' % (k2, v2))
    if sai:
        carimbo_a = time.strftime('%Y%m%d-%H%M%S')
        shutil.copy2(FILA, FILA + '.ANTES-DE-ADIAR-' + carimbo_a)
        json.dump(fica, open(FILA, 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(sai, open(ADIADA, 'w', encoding='utf-8'), ensure_ascii=False)
        P('')
        P('   gravado: %s (a fila so com o que da para rodar)' % FILA)
        P('   gravado: %s (as adiadas, com o motivo de cada uma)' % ADIADA)
        P('')
        P('   ⚠️ Elas voltam SOZINHAS quando o dado chegar — quem devolve e o')
        P('      REFAZER-QUEM-VEIO-PELA-METADE.bat, que a rodada diaria roda.')
    grava_rel(); pausa(); sys.exit(0)

if not REFILAR:
    P('')
    P('=' * 74)
    P('  SO OLHEI. Nada foi mexido.')
    P('  Para devolver as linhas para a fila:  REFAZER-QUEM-VEIO-PELA-METADE.bat')
    P('  ⛔ e SO com o motor parado.')
    P('=' * 74)
    grava_rel(); pausa(); sys.exit(0)

# ---- devolve para a fila quem estava ADIADO e ja curou
if REFILAR and os.path.exists(ADIADA):
    try:
        adiadas = json.load(open(ADIADA, encoding='utf-8'))
    except Exception:
        adiadas = []
    voltam = [r for r in adiadas if str(r.get('card_id', '')).split('@')[0] not in incompletos]
    if voltam:
        fila = json.load(open(FILA, encoding='utf-8')) if os.path.exists(FILA) else []
        tem = {'%s|%s' % (str(r.get('card_id', '')).split('@')[0], r.get('funcao')) for r in fila}
        novas = [r for r in voltam
                 if '%s|%s' % (str(r.get('card_id', '')).split('@')[0], r.get('funcao')) not in tem]
        for r in novas: r.pop('_porque_adiada', None)
        if novas:
            shutil.copy2(FILA, FILA + '.ANTES-DE-VOLTAR-' + time.strftime('%Y%m%d-%H%M%S'))
            json.dump(fila + novas, open(FILA, 'w', encoding='utf-8'), ensure_ascii=False)
        resto = [r for r in adiadas if str(r.get('card_id', '')).split('@')[0] in incompletos]
        json.dump(resto, open(ADIADA, 'w', encoding='utf-8'), ensure_ascii=False)
        P('')
        P('  0. %s .. -%d linhas (o dado chegou; voltaram para a fila)' % (ADIADA, len(voltam)))

# ================================================================== GRAVACAO
feitos = set()
if os.path.exists(FEITOS):
    feitos = {l.strip() for l in open(FEITOS, encoding='utf-8') if l.strip()}
ja = refazer & feitos
if not ja:
    P(''); P('Nada para devolver. A fila fica como esta.')
    grava_rel(); pausa(); sys.exit(0)

carimbo_h = time.strftime('%Y%m%d-%H%M%S')
P('')
P('-' * 74)
P('GRAVANDO')
P('-' * 74)

shutil.copy2(FEITOS, FEITOS + '.ANTES-DA-METADE-' + carimbo_h)
fica = [l for l in open(FEITOS, encoding='utf-8') if l.strip() not in ja]
open(FEITOS, 'w', encoding='utf-8').writelines(fica)
P('  1. %s ......... -%d linhas (sobram %d)' % (FEITOS, len(ja), len(fica)))

tirou = 0
if os.path.exists(LINHAS):
    bkl = LINHAS + '.ANTES-DA-METADE-' + carimbo_h
    if not os.path.exists(bkl): shutil.copy2(LINHAS, bkl)
    tmp = LINHAS + '.tmp'
    with open(LINHAS, encoding='utf-8') as ent, open(tmp, 'w', encoding='utf-8') as sai:
        for l in ent:
            s = l.strip()
            if not s: continue
            try:
                x = json.loads(s)
                k = '%s|%s' % (str(x.get('card_id', '')).split('@')[0], x.get('funcao'))
            except Exception:
                sai.write(l); continue
            if k in ja: tirou += 1
            else: sai.write(l)
    os.replace(tmp, LINHAS)
    P('  2. %s ... -%d linhas' % (LINHAS, tirou))

tl = 0
if os.path.isdir(SAIDA):
    for nome in sorted(os.listdir(SAIDA)):
        if not nome.endswith('.json'): continue
        cam = os.path.join(SAIDA, nome)
        try: dados = json.load(open(cam, encoding='utf-8'))
        except Exception: continue
        if not isinstance(dados, list): continue
        fica2 = [x for x in dados
                 if '%s|%s' % (str(x.get('card_id', '')).split('@')[0], x.get('funcao')) not in ja]
        if len(fica2) != len(dados):
            shutil.copy2(cam, cam + '.ANTES-DA-METADE-' + carimbo_h)
            json.dump(fica2, open(cam, 'w', encoding='utf-8'), ensure_ascii=False)
            tl += len(dados) - len(fica2)
    P('  3. lotes do %s ....... -%d linhas' % (SAIDA, tl))

# ---- na PONTA da fila, sem sorted() (a ordem do arquivo e que manda)
ordem = []
if os.path.exists(PRIORIDADE):
    try: ordem = list(json.load(open(PRIORIDADE, encoding='utf-8')))
    except Exception: ordem = []
    shutil.copy2(PRIORIDADE, PRIORIDADE + '.ANTES-DA-METADE-' + carimbo_h)
tem = set(ordem)
nova = [k for k in sorted(ja) if k not in tem] + ordem
json.dump(nova, open(PRIORIDADE, 'w', encoding='utf-8'), ensure_ascii=False)
P('  4. %s .. +%d na FRENTE (total %d)' % (PRIORIDADE, len(nova) - len(ordem), len(nova)))

P('')
P('=' * 74)
P('  PRONTO. %d linhas voltaram para a fila, na frente.' % len(ja))
P('  Agora e so rodar o COMECAR-TUDO.')
P('=' * 74)
grava_rel(); pausa()
