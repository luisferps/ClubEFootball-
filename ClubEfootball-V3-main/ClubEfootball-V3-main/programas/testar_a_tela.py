# -*- coding: utf-8 -*-
r"""
TESTAR A TELA NO BANCO — a prova com 50 linhas, antes de mandar as 12.370.

ORDEM DO LUIS, 17/08/2026:
    "Mas espera ai, temos que ver que funcionou primeiro antes de colocar mais
     dados dentro dele, ne?"

O QUE ELE FAZ
    1. Abre o encaixe que JA ESTA na sua pasta e tira 50 linhas de dentro dele
    2. Manda essas 50 para a tabela `tela_encaixe`
    3. Baixa as 50 de volta do banco
    4. Compara CAMPO A CAMPO com o que saiu daqui
    5. Diz se bateu, e mostra a diferenca se nao bateu

⛔ NAO MEXE EM NADA. Nao toca no encaixe, nao toca no gera_encaixe, nao apaga
   linha nenhuma do banco. Se der errado, a unica coisa que sobra sao 50 linhas
   numa tabela nova que ninguem le ainda.

⛔ NAO PRECISA DO INTERRUPTOR. Este teste roda com o SOBE-A-TELA.txt ligado ou
   desligado — ele nao passa pelo gera_encaixe.

A CHAVE sai do config.txt na hora de rodar. Nunca e impressa nem gravada aqui.
"""
import json, os, sys, io, time, urllib.request, urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))


def acha_a_casa(inicio):
    p = inicio
    for _ in range(4):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None


CASA = acha_a_casa(AQUI)
if not CASA:
    print('PAREI: nao achei o config.txt nem aqui nem nas pastas de cima.')
    sys.exit(1)
os.chdir(CASA)

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

QUANTAS = 50
ENCAIXE = os.path.join('encaixe', 'encaixe_v6_NOVO.html')
TABELA = 'tela_encaixe'


def P(*a):
    print(*a, flush=True)


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


cfg = {}
for _l in open('config.txt', encoding='utf-8'):
    _l = _l.strip()
    if _l and not _l.startswith('#') and '=' in _l:
        _k, _v = _l.split('=', 1)
        cfg[_k.strip()] = _v.strip()
URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')
if not URL or not KEY:
    P('O config.txt esta sem a URL ou a chave do Supabase.')
    pausa(); sys.exit(1)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY}


P('=' * 74)
P('  TESTAR A TELA NO BANCO   ·   50 linhas, so para provar o caminho')
P('=' * 74)

# ------------------------------------------------ 1. tirar as linhas do encaixe
P('')
P('[1/5] tirando 50 linhas do encaixe que ja esta na pasta')
if not os.path.exists(ENCAIXE):
    P('   ⛔ nao achei o %s' % ENCAIXE)
    P('      Rode o COMECAR-TUDO.bat uma vez para o encaixe ser gerado.')
    pausa(); sys.exit(1)

# ⛔ Mesma leitura que o gera_encaixe.py faz (funcao le_D). Nao inventei outra:
#    se o formato mudar, os dois quebram junto e ninguem trabalha com dado velho.
s = open(ENCAIXE, encoding='utf-8', errors='replace').read()
i = s.find('const D=')
if i < 0:
    i = s.find('const D =')
if i < 0:
    P('   ⛔ nao achei as linhas dentro do encaixe.')
    pausa(); sys.exit(1)
j = s.find('\n', i)
try:
    D = json.loads(s[s.find('[', i):j].rstrip().rstrip(';'))
except Exception as e:
    P('   ⛔ nao consegui ler as linhas: %s' % e)
    pausa(); sys.exit(1)

P('   o encaixe tem %s linhas · o arquivo tem %.1f MB'
  % ('{:,}'.format(len(D)).replace(',', '.'), len(s.encode('utf-8')) / 1048576))
if not D:
    P('   ⛔ o encaixe esta sem linhas dentro. Nada a testar.')
    pausa(); sys.exit(1)

# pega de pontos espalhados, nao as 50 primeiras: linha do comeco e do fim da
# lista tem formato diferente (as do fim sao as de nota baixa, com listas vazias)
passo = max(1, len(D) // QUANTAS)
amostra = [D[k] for k in range(0, len(D), passo)][:QUANTAS]
P('   peguei %d linhas espalhadas (de %d em %d)' % (len(amostra), passo, passo))
P('   exemplo: %s · %s · nota %s'
  % (amostra[0].get('nome'), amostra[0].get('tipo'), amostra[0].get('b1')))

# ------------------------------------------------------------- 2. mandar
P('')
P('[2/5] mandando as %d para a tabela %s' % (len(amostra), TABELA))
linhas = [{'card_id': str(r.get('id')), 'funcao': r.get('tipo'), 'linha': r,
           'gerado_em': time.strftime('%Y-%m-%dT%H:%M:%S')} for r in amostra]
req = urllib.request.Request(
    '%s/rest/v1/%s?on_conflict=card_id,funcao' % (URL, TABELA),
    data=json.dumps(linhas, ensure_ascii=False).encode('utf-8'),
    headers=dict(H, **{'Content-Type': 'application/json',
                       'Prefer': 'resolution=merge-duplicates,return=minimal'}),
    method='POST')
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()
    P('   subiram. %.1f KB no total.'
      % (len(json.dumps(linhas, ensure_ascii=False).encode()) / 1024))
except urllib.error.HTTPError as e:
    det = ''
    try:
        det = e.read().decode('utf-8', 'ignore')[:300]
    except Exception:
        pass
    P('   ⛔ o banco recusou: HTTP %s' % e.code)
    P('      %s' % det)
    if 'does not exist' in det or 'schema cache' in det:
        P('      -> falta rodar o ClubEfootball\\sql\\28-as-linhas-da-tela.sql')
    pausa(); sys.exit(1)
except Exception as e:
    P('   ⛔ nao consegui falar com o banco: %s' % e)
    pausa(); sys.exit(1)

# ------------------------------------------------------------- 3. baixar
P('')
P('[3/5] baixando as mesmas %d de volta' % len(amostra))
chaves = [(str(r.get('id')), r.get('tipo')) for r in amostra]
ids = sorted({c[0] for c in chaves})
volta = {}
try:
    for k in range(0, len(ids), 50):
        lote = ids[k:k + 50]
        q = ('%s/rest/v1/%s?select=card_id,funcao,linha&card_id=in.(%s)'
             % (URL, TABELA, ','.join('"%s"' % x for x in lote)))
        with urllib.request.urlopen(urllib.request.Request(q, headers=H),
                                    timeout=120) as r:
            for x in json.loads(r.read().decode('utf-8')):
                volta[(str(x['card_id']), x['funcao'])] = x['linha']
    P('   voltaram %d linhas' % len(volta))
except Exception as e:
    P('   ⛔ nao consegui baixar: %s' % e)
    pausa(); sys.exit(1)

# ------------------------------------------------- 4. comparar campo a campo
P('')
P('[4/5] comparando CAMPO A CAMPO')
sumiram, diferentes, iguais = [], [], 0
campos_ruins = {}
for r in amostra:
    ch = (str(r.get('id')), r.get('tipo'))
    b = volta.get(ch)
    if b is None:
        sumiram.append(ch)
        continue
    difs = []
    for campo in sorted(set(r) | set(b)):
        va, vb = r.get(campo), b.get(campo)
        # ⚠️ o JSON do Postgres devolve 92.0 onde o Python tinha 92. Numero
        #    igual em tipo diferente NAO e diferenca de dado.
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) \
           and not isinstance(va, bool) and not isinstance(vb, bool):
            if abs(float(va) - float(vb)) < 1e-9:
                continue
        if va != vb:
            difs.append(campo)
            campos_ruins[campo] = campos_ruins.get(campo, 0) + 1
    if difs:
        diferentes.append((ch, difs, r, b))
    else:
        iguais += 1

P('   linhas IGUAIS ....... %d de %d' % (iguais, len(amostra)))
P('   linhas que sumiram .. %d' % len(sumiram))
P('   linhas DIFERENTES ... %d' % len(diferentes))
if campos_ruins:
    P('')
    P('   os campos que nao bateram:')
    for c, n in sorted(campos_ruins.items(), key=lambda x: -x[1]):
        P('      %-14s em %d linhas' % (c, n))
for ch, difs, r, b in diferentes[:3]:
    P('')
    P('   %s · %s' % (r.get('nome'), ch[1]))
    for c in difs[:6]:
        P('      %-12s daqui: %s' % (c, json.dumps(r.get(c), ensure_ascii=False)[:80]))
        P('      %-12s banco: %s' % ('', json.dumps(b.get(c), ensure_ascii=False)[:80]))

# ------------------------------------------------------------- 5. o veredito
P('')
P('=' * 74)
if iguais == len(amostra):
    P('  ✅ PASSOU. As %d linhas voltaram do banco IDENTICAS.' % iguais)
    P('')
    P('  O caminho esta provado: a tela pode ler do banco sem perder nada.')
    P('  O proximo passo e ligar o SOBE-A-TELA.txt e deixar subir as 12.370.')
else:
    P('  ⛔ NAO PASSOU. %d linhas voltaram diferentes ou sumiram.'
      % (len(diferentes) + len(sumiram)))
    P('')
    P('  NAO ligue o SOBE-A-TELA.txt ainda. Me mande esta tela inteira.')
P('=' * 74)
pausa()
sys.exit(0 if iguais == len(amostra) else 1)
