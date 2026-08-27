# -*- coding: utf-8 -*-
r"""
SEPARAR A DATA DO NOME DO BOX — v2, 17/08/2026

⛔ ESTA VERSAO CONSERTA UM ERRO QUE A v1 COMETEU EM 1.437 CARTAS.

O QUE A v1 ERROU
   Ela tratou TODA data escrita no nome do box como data de LANCAMENTO da carta.
   Nao e. Existe uma familia de box — a "Big Time" — em que a data do nome e a
   data da PARTIDA HISTORICA que a carta comemora:

      "Big Time Italy 9 Jul '06"     -> 9/7/2006 e a final da Copa de 2006
      "Big Time Germany 13 Jul '14"  -> a final da Copa de 2014
      "Big Time Manchester United 29 May '68"  -> a final de 1968

   A v1 gravou 2006-07-09 como data de lancamento do Buffon. E a v1 tambem
   converteu '68 em 2068, porque somava 2000 no ano de dois digitos sem olhar.

O ESTRAGO — medido, carta por carta
   109 cartas em box "Big Time" receberam data de partida no campo `dt`
    66 delas ficaram ANTES de 12/09/2024
    37 dessas 66 a fonte diz que TEM vaga de impeto ou impeto nativo

   E a 1a TRAVA DO IMPETO diz: carta lancada antes de 12/09/2024 NAO TEM vaga.
   Ou seja: a trava apagaria a vaga REAL de 37 cartas, comecando pelo Buffon,
   que tem NATIVO + VAGA. A trava esta certa. A data e que estava mentindo.

   46 cartas ficaram com data anterior a setembro/2021 — o eFootball nem existia.
   8 ficaram no futuro (2068, 2081, 2086, 2090, 2094, 2096, 2098).

AS TRES RECUSAS NOVAS
   1. FAMILIA "Big Time" — a data do nome e da partida, nao do lancamento.
      Ela NAO vai para o `dt`. Vai para um campo proprio, `dt_da_partida`,
      porque e informacao boa — so nao e a informacao que o `dt` guarda.
   2. PISO 30/09/2021 — o eFootball nao existia antes. Data que sai do nome e
      cai antes disso nao e lancamento de carta. Recusa.
   3. TETO = hoje. Carta nao se lanca no futuro. Isso mata o bug do '68->2068
      sem precisar adivinhar seculo: se deu futuro, a leitura esta errada.

O QUE ELE DESFAZ SOZINHO
   A v1 deixou o recibo do que escreveu: DATAS-QUE-SAIRAM-DO-BOX.json, com o
   valor ANTERIOR de cada carta. Esta versao le esse recibo e DEVOLVE ao estado
   anterior toda carta cuja data a regra nova recusa. Quem fez a sujeira limpa,
   com o proprio recibo, sem chute.

O QUE CONTINUA IGUAL
   ⛔ O NOME DO BOX NAO E TOCADO. Cada POTW e uma box diferente — o nome inteiro
      e a chave unica dela. A data vai para o campo `dt`, separada. Junta de
      novo so na tela.
   ⛔ Nao inventa data de temporada ("25-26") nem de ano solto ("Germany '22").
   ⛔ NAO SOBRESCREVE DATA BOA. So preenche onde esta vazio ou onde esta a data
      do dump. Terceira data vira briga e fica guardada, sem escolher lado.
   ⛔ Nada aqui fala com o banco.

DEPOIS DELE: UNIFICAR-BASE.bat poe o `dt` na base; SUBIR-BASE.bat manda para o
banco como data_lancamento.
"""
import json, os, re, shutil, sys, collections
from datetime import datetime, date

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
        open('RELATORIO-DATA-DO-BOX.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    except Exception:
        pass
    sys.exit(codigo)


SO_OLHAR = '--conferir' in [a.lower() for a in sys.argv]

ARQ = 'box_por_card.json'
RECIBO = 'DATAS-QUE-SAIRAM-DO-BOX.json'
DATA_DO_DUMP = '2026-07-09'      # medida: 2.485 cards com ela. Nao e lancamento.
CORTE = date(2024, 9, 12)        # a 1a trava do impeto
PISO = date(2021, 9, 30)         # o eFootball nao existia antes disto
HOJE = date.today()

# ⛔ familias de box em que a data do nome e a data da PARTIDA comemorada.
#    Medido em 109 cartas: 46 delas com data anterior ao proprio jogo existir.
FAMILIA_DE_PARTIDA = ('Big Time',)

MES = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
       'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
# ⛔ so estes dois padroes viram data. Nada de temporada, nada de ano solto.
COMPLETA = re.compile(r"(\d{1,2})\s+([A-Z][a-z]{2})\s*'(\d{2})\s*$")   # 14 Jan '23
SO_MES = re.compile(r"(?<!\d)([A-Z][a-z]{2})\s*'(\d{2})\s*$")          # Aug '22


def e_de_partida(nome):
    n = str(nome or '').strip()
    return any(n.startswith(f) for f in FAMILIA_DE_PARTIDA)


def data_do_nome(nome):
    """Devolve (data, exata?) ou (None, None). Nunca chuta o seculo."""
    if not nome:
        return None, None
    m = COMPLETA.search(nome)
    if m:
        try:
            return date(2000 + int(m.group(3)), MES[m.group(2)], int(m.group(1))), True
        except (ValueError, KeyError):
            return None, None
    m = SO_MES.search(nome)
    if m:
        try:
            return date(2000 + int(m.group(2)), MES[m.group(1)], 1), False
        except (ValueError, KeyError):
            return None, None
    return None, None


def por_que_recuso(nome, d):
    """Devolve o motivo da recusa, ou None se a data serve de lancamento."""
    if e_de_partida(nome):
        return 'e data de PARTIDA, nao de lancamento (familia Big Time)'
    if d < PISO:
        return 'anterior a 30/09/2021 — o eFootball nao existia'
    if d > HOJE:
        return 'esta no futuro — a leitura do ano de dois digitos errou o seculo'
    return None


P('=' * 78)
P('  SEPARAR A DATA DO NOME DO BOX  ·  v2  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')
P('  O nome do box NAO e tocado — cada POTW e uma box diferente.')
P('  A data vai para o campo `dt`, separada. Junta de novo so na tela.')
P('')
P('  ⛔ v2: a data do box "Big Time" e a data da PARTIDA comemorada, nao do')
P('     lancamento. Ela sai do `dt` e vai para `dt_da_partida`.')
P('     Piso 30/09/2021 · teto hoje · o resto continua igual.')
if SO_OLHAR:
    P('')
    P('  ⚠️ MODO CONFERIR: nada vai ser gravado. So mostro o que aconteceria.')

if not os.path.exists(ARQ):
    P('PAREI: nao achei o %s' % ARQ)
    fim(1)
B = json.load(open(ARQ, encoding='utf-8'))
P('')
P('  cards no %s ..... %d' % (ARQ, len(B)))

# ============================================================================
#  0) DESFAZER O QUE A v1 ESCREVEU E A REGRA NOVA RECUSA
# ============================================================================
desfeitas = []
if os.path.exists(RECIBO):
    try:
        R = json.load(open(RECIBO, encoding='utf-8')).get('itens') or []
    except Exception:
        R = []
    for it in R:
        cid = str(it.get('card'))
        v = B.get(cid)
        if not isinstance(v, dict):
            continue
        escrita = str(it.get('para') or '')[:10]
        if not escrita or (v.get('dt') or '')[:10] != escrita:
            continue          # ja mudou depois; nao mexo
        try:
            d = date(int(escrita[:4]), int(escrita[5:7]), int(escrita[8:10]))
        except ValueError:
            continue
        motivo = por_que_recuso(it.get('box'), d)
        if not motivo:
            continue
        # ⛔ devolver a data do dump seria repor a mentira que tiramos em 16/08.
        #    Se o valor anterior era o dump, o certo e ficar VAZIO — "nao sei"
        #    e resposta honesta; 2026-07-09 nao e data de lancamento de nada.
        antes = it.get('de')
        antes = '' if (antes in (None, '', '(vazia)', DATA_DO_DUMP)) else str(antes)[:10]
        desfeitas.append({'card': cid, 'box': it.get('box'), 'tirei': escrita,
                          'devolvi_para': antes or '(vazia)', 'porque': motivo})
        if not SO_OLHAR:
            if antes:
                v['dt'] = antes
            else:
                v.pop('dt', None)
            v.pop('dt_de_onde', None)
            if e_de_partida(it.get('box')):
                v['dt_da_partida'] = escrita
                v['dt_da_partida_e'] = 'a data da partida que o box comemora. NAO e lancamento'

P('')
P('  0) DESFAZENDO O QUE A v1 ESCREVEU ERRADO — pelo proprio recibo')
if not os.path.exists(RECIBO):
    P('     (nao achei o %s — nada a desfazer)' % RECIBO)
elif not desfeitas:
    P('     nada a desfazer. Nenhuma data escrita antes cai nas regras novas.')
else:
    P('     datas devolvidas ao estado anterior ....... %d' % len(desfeitas))
    pm = collections.Counter(d['porque'] for d in desfeitas)
    for k, n in pm.most_common():
        P('        %-58s %4d' % (k, n))
    P('')
    P('     as primeiras:')
    for d in desfeitas[:8]:
        P('        %-34s %s -> %s' % (str(d['box'])[:34], d['tirei'], d['devolvi_para']))
    if not SO_OLHAR:
        json.dump({'o_que_e': 'as datas que a v1 escreveu no `dt` e a v2 recusou. '
                              'Devolvidas ao valor anterior. A data da partida foi '
                              'guardada em dt_da_partida.',
                   'quando': datetime.now().isoformat(timespec='seconds'),
                   'quantas': len(desfeitas), 'itens': desfeitas},
                  open('DATAS-DESFEITAS.json', 'w', encoding='utf-8'), ensure_ascii=False)

# ============================================================================
#  1) A PASSADA NORMAL
# ============================================================================
conta = collections.Counter()
mudou = []
briga = []
antes_do_corte = []
recusadas = collections.Counter()

for cid, v in B.items():
    if not isinstance(v, dict):
        conta['registro estranho'] += 1
        continue
    nome = v.get('box')
    if not nome:
        conta['sem nome de box'] += 1
        continue
    d, exata = data_do_nome(nome)
    if d is None:
        conta['o nome nao traz data'] += 1
        continue

    motivo = por_que_recuso(nome, d)
    if motivo:
        recusadas[motivo] += 1
        conta['RECUSADA — nao serve de lancamento'] += 1
        if not SO_OLHAR and e_de_partida(nome):
            v['dt_da_partida'] = d.isoformat()
            v['dt_da_partida_e'] = 'a data da partida que o box comemora. NAO e lancamento'
        continue

    conta['data exata (dia, mes, ano)' if exata else 'data sem o dia (mes e ano)'] += 1
    nova = d.isoformat()
    velha = (v.get('dt') or '')[:10]

    if velha == nova:
        conta['ja estava certa'] += 1
        continue
    if not velha:
        pq = 'estava vazia'
    elif velha == DATA_DO_DUMP:
        pq = 'estava com a data do dump'
    else:
        conta['⛔ BRIGA — nao mexi'] += 1
        briga.append({'card': cid, 'box': nome, 'ja_estava': velha, 'o_nome_diz': nova})
        continue
    conta['CONSERTEI'] += 1
    mudou.append({'card': cid, 'box': nome, 'de': velha or '(vazia)', 'para': nova,
                  'motivo': pq, 'exata': exata})
    if d < CORTE:
        antes_do_corte.append(cid)
    if not SO_OLHAR:
        v['dt'] = nova
        v['dt_de_onde'] = 'tirada do nome do box' + ('' if exata else ' (sem o dia)')

P('')
P('  1) O QUE O NOME DO BOX RESPONDE')
for k in ('data exata (dia, mes, ano)', 'data sem o dia (mes e ano)',
          'RECUSADA — nao serve de lancamento', 'o nome nao traz data', 'sem nome de box'):
    if conta.get(k):
        P('     %-38s %5d' % (k, conta[k]))
if recusadas:
    P('')
    P('     POR QUE RECUSEI:')
    for k, n in recusadas.most_common():
        P('        %-58s %4d' % (k, n))
    P('        (a data da partida ficou guardada em `dt_da_partida`)')

P('')
P('  2) O QUE MUDOU')
P('     ja estava certa .................. %5d' % conta['ja estava certa'])
P('     CONSERTEI ........................ %5d' % conta['CONSERTEI'])
P('     ⛔ briga de datas — NAO mexi ...... %5d' % conta['⛔ BRIGA — nao mexi'])

if mudou:
    P('')
    P('     os primeiros que mudaram:')
    for m in mudou[:10]:
        P('        %-38s %s -> %s' % (m['box'][:38], m['de'], m['para']))

P('')
P('  3) A 1a TRAVA DO IMPETO — lancadas antes de 12/09/2024')
P('     cartas que agora se sabe que NAO TEM vaga ..... %d' % len(antes_do_corte))
P('     ⛔ nenhuma delas e "Big Time" — essas sairam da conta, e por isso')
P('        a trava nao apaga mais vaga de carta comemorativa.')

if briga:
    P('')
    P('  ⛔ AS BRIGAS DE DATA — o nome do box diz uma coisa, o dt guardado diz outra.')
    P('     NAO sobrescrevi nenhuma. Estao no BRIGA-DE-DATAS.json.')
    for b in briga[:8]:
        P('     %-36s guardado %s · o nome diz %s'
          % (b['box'][:36], b['ja_estava'], b['o_nome_diz']))
    if not SO_OLHAR:
        json.dump({'o_que_e': 'onde a data guardada e a data do nome do box discordam. '
                              'NADA foi sobrescrito.',
                   'quando': datetime.now().isoformat(timespec='seconds'),
                   'quantas': len(briga), 'itens': briga},
                  open('BRIGA-DE-DATAS.json', 'w', encoding='utf-8'), ensure_ascii=False)

if SO_OLHAR:
    P('')
    P('=' * 78)
    P('  MODO CONFERIR: nada foi gravado.')
    P('=' * 78)
    fim(0)

if not mudou and not desfeitas:
    P('')
    P('  Nada a mudar. O arquivo nao foi tocado.')
    fim(0)

carimbo = datetime.now().strftime('%Y%m%d-%H%M%S')
bkp = '%s.ANTES-DA-DATA-SEPARADA-%s' % (ARQ, carimbo)
shutil.copy2(ARQ, bkp)
tmp = ARQ + '.tmp'
json.dump(B, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
os.replace(tmp, ARQ)
P('')
P('  backup .................... %s' % bkp)
P('  gravei .................... %s' % ARQ)
if desfeitas:
    P('  gravei .................... DATAS-DESFEITAS.json')
if mudou:
    json.dump({'o_que_e': 'as datas que sairam do nome do box',
               'quando': datetime.now().isoformat(timespec='seconds'),
               'quantas': len(mudou), 'itens': mudou},
              open('DATAS-QUE-SAIRAM-DO-BOX.json', 'w', encoding='utf-8'), ensure_ascii=False)
    P('  gravei .................... DATAS-QUE-SAIRAM-DO-BOX.json')

# ============================================================================
#  CONFERENCIA — lendo de volta do disco
# ============================================================================
C = json.load(open(ARQ, encoding='utf-8'))
com_box = sum(1 for v in C.values() if isinstance(v, dict) and v.get('box'))
com_dt = sum(1 for v in C.values() if isinstance(v, dict) and v.get('dt'))
com_part = sum(1 for v in C.values() if isinstance(v, dict) and v.get('dt_da_partida'))
fora = [cid for cid, v in C.items()
        if isinstance(v, dict) and v.get('dt')
        and not (PISO.isoformat() <= str(v['dt'])[:10] <= HOJE.isoformat())]
P('')
P('  CONFERENCIA — lendo o arquivo de volta do disco')
P('     cards ......................... %d' % len(C))
P('     com box ....................... %d' % com_box)
P('     com data de lancamento ........ %d' % com_dt)
P('     com data de partida guardada .. %d' % com_part)
if fora:
    P('     ⛔ AINDA HA %d data fora da faixa 30/09/2021..hoje:' % len(fora))
    for cid in fora[:10]:
        P('        %s  %s  %s' % (cid, C[cid].get('dt'), str(C[cid].get('box'))[:40]))
else:
    P('     ✅ nenhuma data de lancamento fora da faixa 30/09/2021..hoje')

P('')
P('=' * 78)
P('  PRONTO. O nome do box continua inteiro. A data agora e um campo — e a')
P('  data de partida nao se disfarca mais de data de lancamento.')
P('=' * 78)
P('  Isto mexeu SO no %s. Para chegar na base e no banco:' % ARQ)
P('     UNIFICAR-BASE.bat   -> poe o dt na base')
P('     SUBIR-BASE.bat      -> manda para o banco como data_lancamento')
fim(0)
