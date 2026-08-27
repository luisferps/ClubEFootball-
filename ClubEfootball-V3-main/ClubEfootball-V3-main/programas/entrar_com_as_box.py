# -*- coding: utf-8 -*-
r"""
ENTRAR COM AS BOX DO efHUB — 17/08/2026

Pergunta do Luis, e ela e a certa:
   "E ai quando voce nao estiver aqui, como e que eu vou puxar isso ai?
    Pelo navegador."

Este e o outro lado do COLETAR-AS-BOX-NO-EFHUB.html. O navegador colhe, este
programa entra com o que veio. Nenhum dos dois precisa de mim.

O CAMINHO QUE ELE USA — medido em 17/08 no Chrome do Luis
   O indice do efHub tem 46.862 cartas em 1.953 paginas, ordenado por nota.
   Procurar carta nova ali e agulha no palheiro. Mas existe outra porta:

      /api/public/packs            600 box, da mais recente para a mais velha
      /pt-BR/packs/<slug>          a pagina da box traz os ids das cartas dela

   Box nova aparece na PRIMEIRA pagina dessa lista. E ela ja entrega o nome da
   box e as cartas de uma vez — que e exatamente o que o `box_por_card.json`
   guarda.

⛔ A DATA DO efHUB NAO E A DATA DE LANCAMENTO
   Cada box vem com um campo de data. MEDIDO: as datas sao 13/08, 06/08, 30/07,
   23/07... de sete em sete dias. E a coleta SEMANAL do efHub, nao o lancamento.
   Prova: a box "Summer Transfer 17 Aug '26" vem com data 13/08.

   Entao este programa NAO escreve essa data no `dt`. Ela vai para um campo
   proprio, `datapack_do_efhub`. A data de lancamento continua saindo do NOME
   da box, pelo separar_a_data_do_box.py — que ja sabe recusar a familia
   "Big Time", onde a data do nome e da partida comemorada.

⛔ O QUE ELE SO ACRESCENTA, NUNCA SOBRESCREVE
   box   — so onde esta vazio. Se ja tem box e o efHub diz outra, vira BRIGA e
           fica guardada, sem escolher lado.
   Nada de `dt`. Nada no banco. Nada apagado.
"""
import json, os, shutil, sys, collections
from datetime import datetime

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
        open('RELATORIO-DAS-BOX.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    except Exception:
        pass
    sys.exit(codigo)


SO_OLHAR = '--conferir' in [a.lower() for a in sys.argv]

VEIO = 'efhub_boxes.json'
ARQ = 'box_por_card.json'

P('=' * 78)
P('  ENTRAR COM AS BOX DO efHUB  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')
P('  O navegador colheu, eu entro com o que veio.')
P('  ⛔ so acrescento box onde esta vazio. Nao escrevo data. Nao falo com o banco.')
if SO_OLHAR:
    P('')
    P('  ⚠️ MODO CONFERIR: nada vai ser gravado.')

# ------------------------------------------------------------------ o que veio
if not os.path.exists(VEIO):
    P('')
    P('⛔ PAREI: nao achei o %s na pasta.' % VEIO)
    P('')
    P('   Ele nasce assim:')
    P('     1. abra o ClubEfootball\\COLETAR-AS-BOX-NO-EFHUB.html')
    P('     2. siga os tres passos (cola um bloco no Console do Chrome)')
    P('     3. arraste o arquivo baixado para esta pasta')
    fim(1)

try:
    V = json.load(open(VEIO, encoding='utf-8'))
except Exception as e:
    P('⛔ PAREI: nao consegui ler o %s (%s)' % (VEIO, str(e)[:70]))
    fim(1)

BOX = V.get('box') or {}
if not BOX:
    P('⛔ PAREI: o %s nao tem nenhuma box dentro.' % VEIO)
    fim(1)

P('')
P('  colhido em ................ %s' % str(V.get('colhido_em'))[:19])
P('  box no arquivo ............ %s' % '{:,}'.format(len(BOX)))
if V.get('erros'):
    P('  ⚠️ box que deram erro na coleta  %s' % V['erros'])

# ------------------------------------------------------------ o que ja temos
if not os.path.exists(ARQ):
    P('⛔ PAREI: nao achei o %s' % ARQ)
    fim(1)
B = json.load(open(ARQ, encoding='utf-8'))

BASE = os.path.join('dados', 'base_unica.json')
temos_carta = set()
try:
    _b = json.load(open(BASE, encoding='utf-8'))
    _b = _b.get('cards') if isinstance(_b, dict) else _b
    for c in (_b or []):
        temos_carta.add(str(c.get('id') or '').split('@')[0])
except Exception as e:
    P('  ⚠️ nao consegui ler a base (%s) — nao vou saber dizer carta nova.'
      % str(e)[:60])

nossas_box = {str(v.get('box')) for v in B.values()
              if isinstance(v, dict) and v.get('box')}
P('  box que ja tinhamos ....... %s' % '{:,}'.format(len(nossas_box)))
P('  cartas na base ............ %s' % '{:,}'.format(len(temos_carta)))


def norm(s):
    return ' '.join(str(s or '').replace('™', '').split()).strip().lower()


nossas_norm = {norm(x) for x in nossas_box}

# ---------------------------------------------------------------- a conferencia
box_novas, cartas_novas = [], []
preenchi, ja_tinha, briga = 0, 0, []
sem_carta_na_base = 0

for slug, d in BOX.items():
    if not isinstance(d, dict):
        continue
    nome = d.get('nome')
    cartas = d.get('cartas') or []
    nova = norm(nome) not in nossas_norm
    if nova:
        box_novas.append((d.get('datapack_do_efhub'), nome, len(cartas), slug))
    for cid in cartas:
        cid = str(cid)
        if temos_carta and cid not in temos_carta:
            cartas_novas.append((cid, nome))
            sem_carta_na_base += 1
            continue
        v = B.get(cid)
        if not isinstance(v, dict):
            B[cid] = v = {}
        atual = v.get('box')
        if not atual:
            preenchi += 1
            if not SO_OLHAR:
                v['box'] = nome
                v['box_de_onde'] = 'efHub, lista de box (%s)' % slug
                v['datapack_do_efhub'] = d.get('datapack_do_efhub')
        elif norm(atual) == norm(nome):
            ja_tinha += 1
            if not SO_OLHAR and not v.get('datapack_do_efhub'):
                v['datapack_do_efhub'] = d.get('datapack_do_efhub')
        else:
            briga.append({'card': cid, 'ja_estava': atual, 'o_efhub_diz': nome})

P('')
P('-' * 78)
P('  AS BOX NOVAS — o efHub tem e nos nao')
P('-' * 78)
if not box_novas:
    P('     nenhuma. Toda box do efHub ja esta aqui.')
else:
    box_novas.sort(reverse=True)
    P('     %d box' % len(box_novas))
    P('')
    for data, nome, n, slug in box_novas[:40]:
        P('     %-12s %-46s %3d cartas' % (data, str(nome)[:46], n))
    if len(box_novas) > 40:
        P('     ... e mais %d' % (len(box_novas) - 40))

P('')
P('-' * 78)
P('  AS CARTAS QUE A BASE NAO TEM')
P('-' * 78)
if not temos_carta:
    P('     nao consegui ler a base — nao sei dizer.')
elif not cartas_novas:
    P('     nenhuma. Toda carta que o efHub mostra nas box ja esta na base.')
else:
    P('     %d cartas' % len(cartas_novas))
    for cid, nome in cartas_novas[:40]:
        P('     %-16s  %s' % (cid, str(nome)[:52]))
    if len(cartas_novas) > 40:
        P('     ... e mais %d' % (len(cartas_novas) - 40))
    P('')
    P('     ⛔ ESTAS NAO ENTRAM POR AQUI. Este programa so mexe na box.')
    P('        A ficha delas vem pelo ClubEfootball\\GERAR-COLETA-EFHUB.bat')
    P('        e entra pelo ENTRAR-COM-O-EFHUB.bat.')
    if not SO_OLHAR:
        json.dump({'o_que_e': 'cartas que aparecem nas box do efHub e nao estao na base',
                   'quando': datetime.now().isoformat(timespec='seconds'),
                   'quantas': len(cartas_novas),
                   'ids': [c for c, _n in cartas_novas],
                   'itens': [{'card': c, 'box': n} for c, n in cartas_novas]},
                  open('CARTAS-NOVAS-DAS-BOX.json', 'w', encoding='utf-8'),
                  ensure_ascii=False)
        P('        gravei CARTAS-NOVAS-DAS-BOX.json')

P('')
P('-' * 78)
P('  O NOME DA BOX NAS CARTAS QUE JA TEMOS')
P('-' * 78)
P('     ja estava igual .................. %s' % '{:,}'.format(ja_tinha))
P('     PREENCHI (estava vazio) .......... %s' % '{:,}'.format(preenchi))
P('     ⛔ briga — nao mexi ............... %s' % '{:,}'.format(len(briga)))
if briga:
    for b in briga[:8]:
        P('        %-16s tinha "%s" · o efHub diz "%s"'
          % (b['card'], str(b['ja_estava'])[:26], str(b['o_efhub_diz'])[:26]))
    if not SO_OLHAR:
        json.dump({'o_que_e': 'onde a box guardada e a box do efHub discordam. NADA foi sobrescrito.',
                   'quando': datetime.now().isoformat(timespec='seconds'),
                   'quantas': len(briga), 'itens': briga},
                  open('BRIGA-DE-BOX.json', 'w', encoding='utf-8'), ensure_ascii=False)
        P('        gravei BRIGA-DE-BOX.json')

if SO_OLHAR:
    P('')
    P('=' * 78)
    P('  MODO CONFERIR: nada foi gravado.')
    P('=' * 78)
    fim(0)

if not preenchi:
    P('')
    P('  Nenhuma box nova para preencher. O arquivo nao foi tocado.')
    fim(0)

carimbo = datetime.now().strftime('%Y%m%d-%H%M%S')
bkp = '%s.ANTES-DAS-BOX-%s' % (ARQ, carimbo)
shutil.copy2(ARQ, bkp)
tmp = ARQ + '.tmp'
json.dump(B, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
os.replace(tmp, ARQ)
P('')
P('  backup .................... %s' % bkp)
P('  gravei .................... %s' % ARQ)

C = json.load(open(ARQ, encoding='utf-8'))
com_box = sum(1 for v in C.values() if isinstance(v, dict) and v.get('box'))
P('')
P('  CONFERENCIA — lendo de volta do disco')
P('     cards no arquivo ....... %s' % '{:,}'.format(len(C)))
P('     com box ................ %s' % '{:,}'.format(com_box))

P('')
P('=' * 78)
P('  O QUE FAZER AGORA')
P('=' * 78)
P('     1. SEPARAR-A-DATA-DO-BOX.bat   tira a data do NOME da box')
P('        (a data do efHub NAO serve — e a coleta semanal deles)')
P('     2. UNIFICAR-BASE.bat -> SUBIR-BASE.bat -> BAIXAR-BASE.bat')
P('        ou de uma vez: FECHAR-O-CICLO.bat')
fim(0)
