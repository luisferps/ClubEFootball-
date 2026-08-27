# -*- coding: utf-8 -*-
r"""
SO O QUE MUDA A CONTA — o filtro do PRECISA-REFAZER. 16/08/2026

Ordem do Luis, e ele esta certo:

  "Mas o que que tem a ver a data com o motor? Nada a ver. Eu nao vou rodar o
   motor de novo so pra mudar uma data. Voce tem que so inserir no banco."

O QUE ACONTECEU
   O A-VOLTA-AUTOMATICA marcou 5.814 linhas para refazer. Ele compara a HORA:
   viu que a carta foi tocada depois da linha ter sido calculada e marcou.
   ⛔ Ele nao olha QUAL campo mudou.

   Em 16/08 mudaram 1.437 cartas — e na quase totalidade mudou SO A DATA.
   Data nao entra na nota. Refazer essas linhas gasta maquina para chegar no
   mesmo numero.

O QUE ELE FAZ
   Compara a base de AGORA com uma base de ANTES, campo por campo, e mantem no
   PRECISA-REFAZER so as cartas em que mudou alguma coisa que o motor LE.

⛔ COMO ELE DECIDE O QUE IGNORAR — pela lista do que NAO conta
   Listar "o que o motor le" seria escrever um mapa a mao, e mapa a mao foi o
   que trocou `goalkeeping` com `clearing` e inventou 149 divergencias falsas
   hoje de manha. Entao a lista e a INVERSA, e curta: os campos que com certeza
   nao entram em conta nenhuma. Qualquer campo fora dessa lista, se mudou,
   MANDA REFAZER.

   Na duvida, refaz. Errar para mais custa maquina; errar para menos deixa nota
   errada de pe.

⛔ NAO MEXE EM NADA. Le duas bases, reescreve o PRECISA-REFAZER.txt e guarda o
   original em PRECISA-REFAZER.txt.ANTES-DO-FILTRO. Nao toca no banco, na fila
   nem no feitos.txt.
"""
import json, os, re, shutil, sys, collections
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
        open('RELATORIO-DO-FILTRO.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    except Exception:
        pass
    sys.exit(codigo)


SO_OLHAR = '--conferir' in [a.lower() for a in sys.argv]

AGORA = os.path.join('dados', 'base_unica.json')
LISTA = 'PRECISA-REFAZER.txt'

# ============================================================================
#  O QUE NAO ENTRA EM CONTA NENHUMA — a lista curta, e so ela
# ============================================================================
#  Mudanca SO nestes campos nao faz o motor mudar de resposta.
#  Qualquer outro campo que mude MANDA REFAZER, mesmo que eu nao saiba para que
#  serve. Na duvida, refaz.
NAO_ENTRA_NA_CONTA = {
    'dt',                       # a data de lancamento — decide a VAGA, e a vaga
                                # e o campo `sl`. Se a vaga mudou, o `sl` mudou
                                # junto e ESSE manda refazer. A data sozinha nao.
    'box',                      # o nome da campanha
    'dt_de_onde',
    'atualizado_em',            # carimbo de hora do banco
    'rodado_em',
    'fonte_de_cada_campo',      # procedencia — conta nossa
    'estado_de_cada_campo',
    'origem_ficha',
    'metadado_tela_de_onde',
    'visto_na_casca',
    'impeto_de_onde',
    'votos',                    # avaliacao da comunidade
    'tier',                     # S / S+ — nao entra na nota
    'nome', 'nameJa', 'nameZh', 'slug', 'imageUrl',
    'nacionalidade', 'nationality', 'team', 'league',
}


def carrega(caminho):
    B = json.load(open(caminho, encoding='utf-8'))
    cards = B.get('cards') if isinstance(B, dict) else B
    fora = {}
    for c in (cards or []):
        i = str(c.get('id') or '')
        if i:
            fora[i] = c
    return fora


def le_o_marco():
    """O marco e a hora do ponto zero que o A-VOLTA-AUTOMATICA usou. A base de
       referencia tem que ser ANTERIOR a ele — senao eu comparo contra uma foto
       tirada DEPOIS da mudanca e nao vejo mudanca nenhuma."""
    for nome in ('MARCO-DA-VOLTA.txt',):
        if not os.path.exists(nome):
            continue
        try:
            txt = open(nome, encoding='utf-8', errors='replace').read()
            m = re.search(r'(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})', txt)
            if m:
                return datetime(*[int(x) for x in m.groups()]).timestamp()
        except Exception:
            pass
    return None


def candidatas():
    cand = []
    d = 'dados'
    if os.path.isdir(d):
        for n in os.listdir(d):
            if n.startswith('base_unica.json.ANTES'):
                p = os.path.join(d, n)
                cand.append((os.path.getmtime(p), p))
    bb = 'backups_base'
    if os.path.isdir(bb):
        for pasta in os.listdir(bb):
            p = os.path.join(bb, pasta, 'base_unica.json')
            if os.path.exists(p):
                cand.append((os.path.getmtime(p), p))
    cand.sort(reverse=True)
    return cand


def acha_a_base_de_antes():
    """A mais recente que ainda seja ANTERIOR ao marco."""
    cand = candidatas()
    if not cand:
        return None
    marco = le_o_marco()
    if marco:
        antes = [c for c in cand if c[0] < marco]
        if antes:
            return antes[0][1]
    return cand[-1][1] if len(cand) > 1 else cand[0][1]


P('=' * 78)
P('  SO O QUE MUDA A CONTA  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')
P('  O A-VOLTA-AUTOMATICA marca pela HORA: se a carta foi tocada depois da')
P('  linha, ele marca. Nao olha QUAL campo mudou.')
P('  Este aqui olha. Data e nome de box nao fazem o motor mudar de resposta.')
if SO_OLHAR:
    P('')
    P('  ⚠️ MODO CONFERIR: nada vai ser gravado.')

ANTES = None
for i, a in enumerate(sys.argv):
    if a.lower().startswith('--antes') and i + 1 < len(sys.argv):
        ANTES = sys.argv[i + 1]
if not ANTES:
    ANTES = acha_a_base_de_antes()

if not os.path.exists(AGORA):
    P('PAREI: nao achei o %s' % AGORA)
    fim(1)
if not ANTES or not os.path.exists(ANTES):
    P('')
    P('⛔ PAREI: nao achei uma base de ANTES para comparar.')
    P('   Sem as duas eu nao sei o que mudou — e chutar aqui e pior que nao')
    P('   filtrar. Rode o REFAZER-O-QUE-ENVELHECEU.bat sem o filtro.')
    fim(1)
if not os.path.exists(LISTA):
    P('PAREI: nao achei o %s. Rode o A-VOLTA-AUTOMATICA.bat antes.' % LISTA)
    fim(1)

P('')
_m = le_o_marco()
P('')
P('  as bases que existem para comparar:')
for _t, _p in candidatas():
    _marca = ''
    if _m and _t < _m:
        _marca = '  <- anterior ao marco'
    if _p == ANTES:
        _marca += '   *** ESCOLHIDA'
    P('     %s  %s%s' % (datetime.fromtimestamp(_t).strftime('%d/%m %H:%M'), _p, _marca))
P('')
P('  a base de AGORA ..... %s' % AGORA)
P('  a base de ANTES ..... %s' % ANTES)
P('        (de %s)' % datetime.fromtimestamp(os.path.getmtime(ANTES)).strftime('%d/%m %H:%M'))

A = carrega(ANTES)
B = carrega(AGORA)
P('')
P('  cartas antes ........ %s' % '{:,}'.format(len(A)))
P('  cartas agora ........ %s' % '{:,}'.format(len(B)))


VAZIOS = (None, '', [], {}, ())


def vazio(v):
    """⛔ VAZIO E VAZIO. A ida-e-volta ao banco troca [] por null, e isso NAO e
       mudanca de dado — foi o que fez o `nx` aparecer como mexido em 6.106
       cartas. Tratar isso como mudanca manda o motor refazer o mundo a toa."""
    return v is None or v == '' or v == [] or v == {} or v == ()


def igual(a, b):
    if vazio(a) and vazio(b):
        return True
    if vazio(a) or vazio(b):
        return False
    try:
        if isinstance(a, bool) or isinstance(b, bool):
            return bool(a) == bool(b)
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        pass
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    try:
        return json.dumps(a, sort_keys=True, ensure_ascii=False) == \
               json.dumps(b, sort_keys=True, ensure_ascii=False)
    except Exception:
        return False


MUDOU_DE_VERDADE = set()
SO_COISA_QUE_NAO_CONTA = set()
NOVA = set()
por_campo = collections.Counter()
exemplos = collections.defaultdict(list)

for cid, agora in B.items():
    antes = A.get(cid)
    if antes is None:
        NOVA.add(cid)
        continue
    pesa = []
    for campo in set(list(antes.keys()) + list(agora.keys())):
        if campo in NAO_ENTRA_NA_CONTA:
            continue
        if not igual(antes.get(campo), agora.get(campo)):
            pesa.append(campo)
    if pesa:
        MUDOU_DE_VERDADE.add(cid)
        for campo in pesa:
            por_campo[campo] += 1
            if len(exemplos[campo]) < 3:
                exemplos[campo].append(
                    (agora.get('ovr'), agora.get('nome'),
                     json.dumps(antes.get(campo), ensure_ascii=False)[:34],
                     json.dumps(agora.get(campo), ensure_ascii=False)[:34]))
    else:
        # mudou alguma coisa? se mudou, foi so o que nao conta
        for campo in NAO_ENTRA_NA_CONTA:
            if not igual(antes.get(campo), agora.get(campo)):
                SO_COISA_QUE_NAO_CONTA.add(cid)
                break

P('')
P('  O QUE MUDOU ENTRE AS DUAS BASES')
P('     cartas novas ......................... %s' % '{:,}'.format(len(NOVA)))
P('     mudou algo que o MOTOR LE ............ %s' % '{:,}'.format(len(MUDOU_DE_VERDADE)))
P('     mudou SO data / box / carimbo ........ %s' % '{:,}'.format(len(SO_COISA_QUE_NAO_CONTA)))

if por_campo:
    P('')
    P('  os campos que pesam, e quantas cartas em cada:')
    for campo, n in por_campo.most_common(14):
        P('     %-24s %6d' % (campo, n))
    P('')
    P('  exemplos do campo mais mexido (%s):' % por_campo.most_common(1)[0][0])
    for o, nome, a, b in exemplos[por_campo.most_common(1)[0][0]]:
        P('     geral %-4s %-24s  %s  ->  %s' % (o, str(nome)[:24], a, b))

# --------------------------------------------------- filtrar o PRECISA-REFAZER
linhas = [l.rstrip('\n') for l in open(LISTA, encoding='utf-8') if l.strip()]
P('')
P('  o PRECISA-REFAZER tinha ................. %s linhas' % '{:,}'.format(len(linhas)))

VALE = MUDOU_DE_VERDADE | NOVA
fica, sai = [], 0
for l in linhas:
    cid = l.split('|')[0].split('\t')[0].strip().split('@')[0]
    if cid in VALE:
        fica.append(l)
    else:
        sai += 1
P('     FICAM (o calculo mudou) .............. %s' % '{:,}'.format(len(fica)))
P('     saem (so a data mudou) ............... %s' % '{:,}'.format(sai))
if linhas:
    P('     economia ............................. %.0f%%' % (100.0 * sai / len(linhas)))

if SO_OLHAR:
    P('')
    P('=' * 78)
    P('  MODO CONFERIR: o %s nao foi tocado.' % LISTA)
    P('=' * 78)
    fim(0)

if sai == 0:
    P('')
    P('  Nada a filtrar — todas as linhas mudaram de calculo mesmo.')
    fim(0)

shutil.copy2(LISTA, LISTA + '.ANTES-DO-FILTRO')
with open(LISTA, 'w', encoding='utf-8') as f:
    for l in fica:
        f.write(l + '\n')
P('')
P('  guardei o original ...... %s.ANTES-DO-FILTRO' % LISTA)
P('  gravei .................. %s  (%s linhas)' % (LISTA, '{:,}'.format(len(fica))))
P('')
P('=' * 78)
P('  PRONTO. Agora o REFAZER-O-QUE-ENVELHECEU vai mexer so no que mudou.')
P('=' * 78)
P('  Nada foi escrito no banco, na fila nem no feitos.txt.')
fim(0)
