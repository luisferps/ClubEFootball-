# -*- coding: utf-8 -*-
"""
MONTAR A PASTA — 16/08/2026

Copia para a ClubEfootball SO o que o sistema precisa para funcionar.
O resto fica onde esta. NADA E APAGADO.

COMO ELE DECIDE O QUE PRECISA — medindo, nao chutando:

  1. Todo .bat da pasta e uma PORTA DE ENTRADA. E o que voce clica.
  2. De cada .bat, le qual .py ele chama.
  3. De cada .py, segue os `import` ate o fim (o programa que o programa usa).
  4. De cada .py, procura no texto o nome de arquivo que ele abre — se o nome
     bate com um arquivo que existe na pasta, aquele arquivo e necessario.
  5. Repete ate parar de crescer.

  O que nao for alcancado por nenhuma porta de entrada e ORFAO: nenhum clique
  seu chega nele. Esses ficam para tras, e a lista deles e escrita num arquivo
  para voce olhar e dizer "traz esse de volta".

⛔ NAO APAGA NADA. So copia.
⛔ O config.txt e copiado (o sistema precisa dele) mas o .gitignore da pasta
   nova o mantem fora do GitHub.
"""
import json, os, sys, io, re, shutil, collections
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

DESTINO = os.path.join(CASA, 'ClubEfootball')

# pastas que nunca entram — sao saida, backup ou lixo
FORA = {'backups_banco', 'backups_base', 'VOLTAR-ATRAS', 'saida_v6', '__pycache__',
        'TRUEFOOTBALL-V7', 'ClubEfootball', '.git'}

P('=' * 78)
P('  MONTAR A PASTA  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')
P('  de ...... %s' % CASA)
P('  para .... %s' % DESTINO)
P('')
P('  ⛔ nada e apagado. So copia.')
P('')

# ------------------------------------------------------- o que existe na pasta
todos = {}          # caminho relativo -> tamanho
for raiz, dirs, arqs in os.walk(CASA):
    dirs[:] = [d for d in dirs if d not in FORA and not d.startswith('.')]
    for a in arqs:
        full = os.path.join(raiz, a)
        rel = os.path.relpath(full, CASA).replace('\\', '/')
        if rel.split('/')[0] in FORA:
            continue
        try:
            todos[rel] = os.path.getsize(full)
        except OSError:
            pass

por_base = collections.defaultdict(list)
for rel in todos:
    por_base[os.path.basename(rel).lower()].append(rel)

P('  arquivos na pasta ......... %d   (%.0f MB)' % (len(todos), sum(todos.values()) / 1e6))


def texto(rel):
    try:
        with open(os.path.join(CASA, rel), 'rb') as f:
            return f.read(400_000).decode('utf-8', 'replace')
    except Exception:
        return ''


# ============================================================================
#  A BUSCA — do .bat ate o ultimo arquivo que ele precisa
# ============================================================================
LIT = re.compile(r"""['"]([^'"\n]{2,80})['"]""")
IMP = re.compile(r'^\s*(?:from\s+([A-Za-z_][\w]*)|import\s+([A-Za-z_][\w]*))', re.M)

precisa = set()
fila = []

# 1) toda porta de entrada
for rel in todos:
    if rel.lower().endswith(('.bat', '.hta')):
        precisa.add(rel)
        fila.append(rel)

# a documentacao inteira entra: e a memoria do sistema, e cabe em 0,6 MB
for rel in todos:
    if rel.lower().endswith(('.md', '.sql')) or rel.split('/')[0] in ('docs', 'sql'):
        precisa.add(rel)

# o config e a chave: o sistema nao anda sem ele
if 'config.txt' in todos:
    precisa.add('config.txt')

P('  portas de entrada (.bat) .. %d' % sum(1 for r in precisa if r.lower().endswith('.bat')))
P('')
P('  seguindo o rastro...')

voltas = 0
while fila:
    voltas += 1
    if voltas > 20000:
        break
    rel = fila.pop()
    t = texto(rel)
    if not t:
        continue

    # os imports (so para .py)
    if rel.lower().endswith('.py'):
        for m in IMP.finditer(t):
            nome = (m.group(1) or m.group(2) or '').split('.')[0]
            cand = nome.lower() + '.py'
            for alvo in por_base.get(cand, []):
                if alvo not in precisa:
                    precisa.add(alvo)
                    fila.append(alvo)

    # todo texto entre aspas que seja o nome de um arquivo que existe
    for m in LIT.finditer(t):
        v = m.group(1).strip().replace('\\', '/')
        if not v or v.startswith(('http', '--', 'select ', 'SELECT ')):
            continue
        base = os.path.basename(v).lower()
        alvos = []
        if v.lower() in (x.lower() for x in todos):
            alvos = [x for x in todos if x.lower() == v.lower()]
        elif base in por_base:
            alvos = por_base[base]
        for alvo in alvos:
            if alvo not in precisa:
                precisa.add(alvo)
                if alvo.lower().endswith(('.py', '.bat')):
                    fila.append(alvo)

    # o .bat chama "python X.py"
    if rel.lower().endswith(('.bat', '.hta')):
        for m in re.finditer(r'([A-Za-z0-9_\-]+\.py)', t):
            for alvo in por_base.get(m.group(1).lower(), []):
                if alvo not in precisa:
                    precisa.add(alvo)
                    fila.append(alvo)

# ---------------------------------------------------------------------------
#  OS PROGRAMAS QUE JA ESTAO NA ClubEfootball TAMBEM PEDEM COISA
# ---------------------------------------------------------------------------
#  Eles nao entram na copia (ja estao la), mas leem arquivos da pasta do motor:
#  pe_ruim.json, box_por_card.json, dados/levelcap.json... Sem isto, a pasta
#  nova nasceria sem o que os proprios programas dela abrem.
lidos_da_nova = 0
for sub in ('', 'programas'):
    d = os.path.join(DESTINO, sub) if sub else DESTINO
    if not os.path.isdir(d):
        continue
    for a in os.listdir(d):
        if not a.lower().endswith(('.bat', '.py')):
            continue
        try:
            with open(os.path.join(d, a), 'rb') as f:
                t = f.read(400_000).decode('utf-8', 'replace')
        except Exception:
            continue
        lidos_da_nova += 1
        for m in LIT.finditer(t):
            v = m.group(1).strip().replace('\\', '/')
            if not v or v.startswith(('http', '--')):
                continue
            base = os.path.basename(v).lower()
            alvos = [x for x in todos if x.lower() == v.lower()] or por_base.get(base, [])
            for alvo in alvos:
                precisa.add(alvo)

P('  programas da pasta nova ... %d lidos (para saber o que eles abrem)' % lidos_da_nova)

orfaos = sorted(set(todos) - precisa)
P('  precisa ................... %d arquivos  (%.1f MB)'
  % (len(precisa), sum(todos[r] for r in precisa) / 1e6))
P('  orfaos .................... %d arquivos  (%.1f MB)'
  % (len(orfaos), sum(todos[r] for r in orfaos) / 1e6))

# ------------------------------------- o que e orfao, por que ficou para tras
def por_que(rel):
    b = os.path.basename(rel).lower()
    if '.antes' in b or '-backup-' in b or b.endswith('.bak'):
        return 'copia de seguranca'
    if b.endswith('.pyc'):
        return 'lixo do python'
    if b.endswith('.html'):
        return 'tela gerada'
    if b.endswith(('.jsonl', '.bin', '.csv')):
        return 'coleta crua ou relatorio'
    if b.startswith(('relatorio', 'log_', 'sonda')) or b.endswith('.txt'):
        return 'relatorio - nasce de novo'
    if b.endswith('.py'):
        return 'PROGRAMA que nenhum .bat chama'
    if b.endswith('.json'):
        return 'dado que nenhum programa abre'
    return 'nao alcancado'


motivo = collections.Counter(por_que(r) for r in orfaos)
P('')
P('  POR QUE FICARAM PARA TRAS')
for k, n in motivo.most_common():
    mb = sum(todos[r] for r in orfaos if por_que(r) == k) / 1e6
    P('     %-34s %5d arquivos  %8.1f MB' % (k, n, mb))

# ============================================================================
P('')
P('-' * 78)
P('  COPIANDO')
P('')
os.makedirs(DESTINO, exist_ok=True)
copiados = pulados = 0
erros = []
for rel in sorted(precisa):
    orig = os.path.join(CASA, rel)
    dest = os.path.join(DESTINO, rel.replace('/', os.sep))
    if not os.path.exists(orig):
        continue
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest) and os.path.getsize(dest) == os.path.getsize(orig) \
           and abs(os.path.getmtime(dest) - os.path.getmtime(orig)) < 2:
            pulados += 1
            continue
        shutil.copy2(orig, dest)
        copiados += 1
        if copiados % 25 == 0:
            print('   %d copiados...' % copiados, end='\r', flush=True)
    except Exception as e:
        erros.append('%s -> %s' % (rel, str(e)[:60]))
print(' ' * 40, end='\r')
P('  copiados .................. %d' % copiados)
P('  ja estavam iguais ......... %d' % pulados)
if erros:
    P('  ⛔ nao consegui copiar %d:' % len(erros))
    for e in erros[:8]:
        P('     %s' % e)

# ------------------------------------------------------------ as duas listas
with open(os.path.join(DESTINO, 'O-QUE-VEIO.txt'), 'w', encoding='utf-8') as f:
    f.write('O QUE VEIO PARA A ClubEfootball - %s\n' % datetime.now().strftime('%d/%m/%Y %H:%M'))
    f.write('Criterio: alcancado a partir de algum .bat, seguindo import e nome de arquivo.\n')
    f.write('=' * 70 + '\n\n')
    for rel in sorted(precisa):
        f.write('%10d  %s\n' % (todos.get(rel, 0), rel))

with open(os.path.join(CASA, 'O-QUE-FICOU-PARA-TRAS.txt'), 'w', encoding='utf-8') as f:
    f.write('O QUE FICOU PARA TRAS - %s\n' % datetime.now().strftime('%d/%m/%Y %H:%M'))
    f.write('NADA FOI APAGADO. Estes arquivos continuam na pasta do motor.\n')
    f.write('Se algum aqui fizer falta, e so avisar que ele volta.\n')
    f.write('=' * 70 + '\n')
    for k, _ in motivo.most_common():
        f.write('\n\n### %s\n' % k.upper())
        for rel in orfaos:
            if por_que(rel) == k:
                f.write('%10d  %s\n' % (todos[rel], rel))

P('')
P('  gravei .................... ClubEfootball/O-QUE-VEIO.txt')
P('  gravei .................... O-QUE-FICOU-PARA-TRAS.txt')

# ---------------------------------------------------------- o .gitignore dela
GI = """# .gitignore da ClubEfootball — 16/08/2026
# Esta pasta ja nasce limpa. Isto aqui e a segunda tranca.

# ⛔ A CHAVE DO BANCO. Nunca, em hipotese nenhuma.
config.txt
*.env
.env

# estado e saida, que nascem de novo a cada rodada
__pycache__/
*.pyc
saida_v6/
backups_banco/
encaixe/*.html
*.ANTES-*
*.ANTES*
dados/base_unica.json
log_v6.txt
O-QUE-VAI-SUBIR.txt
github.txt
"""
with open(os.path.join(DESTINO, '.gitignore'), 'w', encoding='utf-8', newline='') as f:
    f.write(GI.replace('\n', '\r\n'))
P('  gravei .................... ClubEfootball/.gitignore')

# ------------------------------------------------------------- CONFERENCIA
P('')
P('  CONFERENCIA — contando o que ficou na pasta nova')
n = b = 0
for raiz, dirs, arqs in os.walk(DESTINO):
    dirs[:] = [d for d in dirs if d != '.git']
    for a in arqs:
        n += 1
        try:
            b += os.path.getsize(os.path.join(raiz, a))
        except OSError:
            pass
P('     ClubEfootball ......... %d arquivos  ·  %.1f MB' % (n, b / 1e6))
falta = [r for r in precisa if not os.path.exists(os.path.join(DESTINO, r.replace('/', os.sep)))]
if falta:
    P('     ⛔ %d nao chegaram: %s' % (len(falta), ', '.join(falta[:5])))
    sys.exit(1)
P('     ✅ todos os %d que precisavam estao la' % len(precisa))

P('')
P('  ⛔ A PASTA VELHA CONTINUA INTEIRA. Nao apague nada dela ainda —')
P('     abra o O-QUE-FICOU-PARA-TRAS.txt primeiro e veja se concorda.')
P('')
P('  PRONTO.')
