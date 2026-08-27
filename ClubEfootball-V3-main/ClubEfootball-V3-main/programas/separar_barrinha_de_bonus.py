# -*- coding: utf-8 -*-
r"""
SEPARAR A BARRINHA DO BONUS — 17/08/2026

Ordem do Luis, palavra por palavra:

  "Voce vai separar o que tem que ser rodado com as das barrinha. Por exemplo,
   o que alterou o impeto, esse tem que ser rodado. Se alterou a habilidade
   nativa, tem que ser rodado tambem. O resto e bonus."

E antes, com razao:

  "Voce quer rodar motor de maximizar barrinha pra coisa que e bonus, nem entra
   nisso. Isso ai e outro motor, e motor de bonus."

⛔ O ERRO QUE ISTO CONSERTA
   O A-VOLTA-AUTOMATICA marca pela HORA: carta tocada depois da linha, marca.
   O SO-O-QUE-MUDA-A-CONTA filtrava por uma lista INVERSA ("o que nao conta"),
   e nessa lista nao estavam os campos de BONUS. Resultado: estilo de jogo da
   IA, corpo e pe ruim entravam como motivo para rodar o motor de barrinhas —
   que nao le nenhum dos tres. Deu 5.756 linhas para refazer e 0% de economia.

⛔ AS DUAS LISTAS NAO SAO ESCRITAS A MAO
   Escrever mapa a mao foi o que trocou o `goalkeeping` com o `clearing` e
   inventou 149 divergencias falsas em 16/08. Entao este programa ABRE os dois
   motores e pergunta a eles quais campos do card cada um le. Se a leitura vier
   vazia ou sem o `base`, ele PARA — melhor parar que filtrar por lista velha.

AS TRES PILHAS
   1. RODA A BARRINHA   mudou algo que o motor.py le
   2. RODA SO O BONUS   mudou so algo que o motor_bonus.py le
   3. NAO RODA NADA     mudou so data, nome de box, carimbo, procedencia

⛔ NAO MEXE NO BANCO, NA FILA NEM NO feitos.txt. Le duas bases e escreve listas.
   No modo --conferir nao grava nada.
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
        open('RELATORIO-BARRINHA-X-BONUS.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    except Exception:
        pass
    sys.exit(codigo)


SO_OLHAR = '--conferir' in [a.lower() for a in sys.argv]

AGORA = os.path.join('dados', 'base_unica.json')
LISTA = 'PRECISA-REFAZER.txt'
SAIDA_BARRA = 'REFAZER-A-BARRINHA.txt'
SAIDA_BONUS = 'SO-O-BONUS.txt'

# ============================================================================
#  PERGUNTAR AOS MOTORES — nao escrever a lista a mao
# ============================================================================
#  ⛔ NAO adianta eu adivinhar de qual variavel o motor le. O `motor_bonus.py`
#     pega a altura de `f.get('altura')`, nao de `c.get(...)` — restringir a
#     variavel `c` perdia a altura calada. Entao pego TODO nome pedido no
#     arquivo e CRUZO com os campos que a base realmente tem. A realidade filtra
#     o ruido; eu nao preciso acertar o nome da variavel.
PEDE = re.compile(r"\.\s*get\(\s*'([a-zA-Z_][a-zA-Z_0-9]*)'"
                  r"|\[\s*'([a-zA-Z_][a-zA-Z_0-9]*)'\s*\]")

# o que e conta nossa, nunca motivo para refazer
NUNCA = {'id', 'nome', 'cards', 'dados', 'ovr',
         'fonte_de_cada_campo', 'estado_de_cada_campo', 'atualizado_em'}


def o_que_esse_motor_le(caminho, campos_que_a_base_tem):
    if not os.path.exists(caminho):
        return None
    txt = open(caminho, encoding='utf-8', errors='replace').read()
    achados = set()
    for a, b in PEDE.findall(txt):
        nome = a or b
        if nome and nome in campos_que_a_base_tem and nome not in NUNCA:
            achados.add(nome)
    return achados

P('=' * 78)
P('  SEPARAR A BARRINHA DO BONUS  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')
P('  Duas coisas diferentes, dois motores diferentes:')
P('     o motor de BARRINHAS  distribui os niveis, escolhe impeto, tecnico e')
P('                           habilidade. So ele precisa refazer a build.')
P('     o motor de BONUS      corpo, estilo de jogo da IA, pe ruim. Entra na')
P('                           nota por cima, sem mexer na build.')
if SO_OLHAR:
    P('')
    P('  ⚠️ MODO CONFERIR: nada vai ser gravado.')


# ============================================================================
def le_o_marco():
    """A base de referencia tem que ser ANTERIOR ao marco — senao eu comparo
       contra uma foto tirada DEPOIS da mudanca e nao vejo mudanca nenhuma."""
    if not os.path.exists('MARCO-DA-VOLTA.txt'):
        return None
    try:
        txt = open('MARCO-DA-VOLTA.txt', encoding='utf-8', errors='replace').read()
        m = re.search(r'(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})', txt)
        if m:
            return datetime(*[int(x) for x in m.groups()]).timestamp()
    except Exception:
        pass
    return None


def candidatas():
    cand = []
    if os.path.isdir('dados'):
        for n in os.listdir('dados'):
            if n.startswith('base_unica.json.ANTES'):
                p = os.path.join('dados', n)
                cand.append((os.path.getmtime(p), p))
    if os.path.isdir('backups_base'):
        for pasta in os.listdir('backups_base'):
            p = os.path.join('backups_base', pasta, 'base_unica.json')
            if os.path.exists(p):
                cand.append((os.path.getmtime(p), p))
    cand.sort(reverse=True)
    return cand


def acha_a_base_de_antes():
    cand = candidatas()
    if not cand:
        return None
    marco = le_o_marco()
    if marco:
        antes = [c for c in cand if c[0] < marco]
        if antes:
            return antes[0][1]
    return cand[-1][1] if len(cand) > 1 else cand[0][1]


def carrega(caminho):
    B = json.load(open(caminho, encoding='utf-8'))
    cards = B.get('cards') if isinstance(B, dict) else B
    fora = {}
    for c in (cards or []):
        i = str(c.get('id') or '')
        if i:
            fora[i] = c
    return fora


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
    fim(1)
if not os.path.exists(LISTA):
    P('PAREI: nao achei o %s. Rode o A-VOLTA-AUTOMATICA.bat antes.' % LISTA)
    fim(1)

_m = le_o_marco()
P('')
P('  as bases que existem para comparar:')
for _t, _p in candidatas():
    _marca = '  <- anterior ao marco' if (_m and _t < _m) else ''
    if _p == ANTES:
        _marca += '   *** ESCOLHIDA'
    P('     %s  %s%s' % (datetime.fromtimestamp(_t).strftime('%d/%m %H:%M'), _p, _marca))
P('')
P('  a base de ANTES ..... %s  (de %s)'
  % (ANTES, datetime.fromtimestamp(os.path.getmtime(ANTES)).strftime('%d/%m %H:%M')))

A = carrega(ANTES)
B = carrega(AGORA)
P('  cartas antes / agora . %s / %s' % ('{:,}'.format(len(A)), '{:,}'.format(len(B))))

# ⛔ AS DUAS BASES, nao so a de agora. Campo que esta vazio na base de hoje some
#    da lista se eu olhar so ela — e o `com` (estilo de jogo da IA) fica vazio
#    justamente no meio do ciclo, entre o UNIFICAR e o BAIXAR. Como todo campo
#    que MUDOU existe em pelo menos uma das duas, a uniao e o universo certo.
CAMPOS_DA_BASE = set()
for _fonte in (A, B):
    for _c in _fonte.values():
        CAMPOS_DA_BASE.update(_c.keys())

LE_A_BARRINHA = o_que_esse_motor_le('motor.py', CAMPOS_DA_BASE)
LE_O_BONUS = o_que_esse_motor_le('motor_bonus.py', CAMPOS_DA_BASE)

P('')
P('  O QUE CADA MOTOR LE — perguntado a eles agora, nao escrito a mao')
if not LE_A_BARRINHA or 'base' not in LE_A_BARRINHA:
    P('')
    P('  ⛔ PAREI: nao consegui ler os campos do motor.py (ou veio sem o `base`).')
    P('     Filtrar por lista velha e pior que nao filtrar.')
    fim(1)
if not LE_O_BONUS:
    P('')
    P('  ⛔ PAREI: nao consegui ler os campos do motor_bonus.py.')
    fim(1)
P('     motor.py (barrinhas) .... %s' % ' '.join(sorted(LE_A_BARRINHA)))
P('     motor_bonus.py .......... %s' % ' '.join(sorted(LE_O_BONUS)))

# campo que os dois leem vale como BARRINHA: quem manda refazer a build ganha
LE_O_BONUS = LE_O_BONUS - LE_A_BARRINHA


def vazio(v):
    """⛔ VAZIO E VAZIO. A ida-e-volta ao banco troca [] por null, e isso NAO e
       mudanca de dado — fez o `nx` aparecer como mexido em 6.106 cartas."""
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


BARRA, BONUS, NADA, NOVA = set(), set(), set(), set()
campo_barra = collections.Counter()
campo_bonus = collections.Counter()
exemplos = collections.defaultdict(list)

for cid, agora in B.items():
    antes = A.get(cid)
    if antes is None:
        NOVA.add(cid)
        continue
    mexeu_barra, mexeu_bonus, mexeu_algo = [], [], False
    for campo in set(list(antes.keys()) + list(agora.keys())):
        if igual(antes.get(campo), agora.get(campo)):
            continue
        mexeu_algo = True
        if campo in LE_A_BARRINHA:
            mexeu_barra.append(campo)
        elif campo in LE_O_BONUS:
            mexeu_bonus.append(campo)
    if mexeu_barra:
        BARRA.add(cid)
        for campo in mexeu_barra:
            campo_barra[campo] += 1
            if len(exemplos[campo]) < 3:
                exemplos[campo].append(
                    (agora.get('ovr'), agora.get('nome'),
                     json.dumps(antes.get(campo), ensure_ascii=False)[:30],
                     json.dumps(agora.get(campo), ensure_ascii=False)[:30]))
    elif mexeu_bonus:
        BONUS.add(cid)
        for campo in mexeu_bonus:
            campo_bonus[campo] += 1
    elif mexeu_algo:
        NADA.add(cid)

P('')
P('-' * 78)
P('  AS TRES PILHAS — por CARTA')
P('-' * 78)
P('     cartas novas ............................ %s' % '{:,}'.format(len(NOVA)))
P('     1. RODA A BARRINHA ...................... %s' % '{:,}'.format(len(BARRA)))
P('     2. RODA SO O BONUS ...................... %s' % '{:,}'.format(len(BONUS)))
P('     3. NAO RODA NADA (data, box, carimbo) ... %s' % '{:,}'.format(len(NADA)))

if campo_barra:
    P('')
    P('  POR QUE A BARRINHA — o campo que mandou, e quantas cartas:')
    for campo, n in campo_barra.most_common():
        P('     %-12s %6d' % (campo, n))
    P('')
    _top = campo_barra.most_common(1)[0][0]
    P('  exemplos do campo mais mexido (%s):' % _top)
    for o, nome, a, b in exemplos[_top]:
        P('     geral %-4s %-22s  %s  ->  %s' % (o, str(nome)[:22], a, b))
else:
    P('')
    P('  ✅ NENHUMA carta mudou campo que o motor de barrinhas le.')

if campo_bonus:
    P('')
    P('  POR QUE SO O BONUS:')
    for campo, n in campo_bonus.most_common():
        P('     %-12s %6d' % (campo, n))

# --------------------------------------------------- separar o PRECISA-REFAZER
linhas = [l.rstrip('\n') for l in open(LISTA, encoding='utf-8') if l.strip()]
VALE = BARRA | NOVA
fica, sai = [], []
for l in linhas:
    cid = l.split('|')[0].split('\t')[0].strip().split('@')[0]
    (fica if cid in VALE else sai).append(l)

P('')
P('-' * 78)
P('  AS LINHAS DO PRECISA-REFAZER')
P('-' * 78)
P('     tinha ................................... %s linhas' % '{:,}'.format(len(linhas)))
P('     RODAM A BARRINHA ........................ %s' % '{:,}'.format(len(fica)))
P('     saem (bonus ou nada) .................... %s' % '{:,}'.format(len(sai)))
if linhas:
    P('     economia ................................ %.0f%%' % (100.0 * len(sai) / len(linhas)))

if SO_OLHAR:
    P('')
    P('=' * 78)
    P('  MODO CONFERIR: nada foi gravado. O %s esta intacto.' % LISTA)
    P('=' * 78)
    fim(0)

open(SAIDA_BARRA, 'w', encoding='utf-8').write('\n'.join(fica) + ('\n' if fica else ''))
open(SAIDA_BONUS, 'w', encoding='utf-8').write('\n'.join(sorted(BONUS)) + ('\n' if BONUS else ''))
P('')
P('  gravei .................. %s  (%s linhas)' % (SAIDA_BARRA, '{:,}'.format(len(fica))))
P('  gravei .................. %s  (%s cartas)' % (SAIDA_BONUS, '{:,}'.format(len(BONUS))))

if len(sai):
    shutil.copy2(LISTA, LISTA + '.ANTES-DA-SEPARACAO')
    with open(LISTA, 'w', encoding='utf-8') as f:
        for l in fica:
            f.write(l + '\n')
    P('  guardei o original ...... %s.ANTES-DA-SEPARACAO' % LISTA)
    P('  o %s agora tem so a barrinha' % LISTA)
else:
    P('')
    P('  Nada saiu — todas as linhas mexem na barrinha mesmo.')

P('')
P('=' * 78)
P('  O QUE FAZER AGORA')
P('=' * 78)
P('     a barrinha .... REFAZER-O-QUE-ENVELHECEU.bat  (com o motor PARADO)')
P('     o bonus ....... MOTOR-BONUS.bat')
P('  ⛔ o bonus NAO precisa do motor de barrinhas. Sao motores diferentes.')
fim(0)
