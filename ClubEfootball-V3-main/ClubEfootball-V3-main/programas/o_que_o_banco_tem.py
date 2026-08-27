# -*- coding: utf-8 -*-
r"""
O QUE O BANCO TEM — 16/08/2026

⛔ POR QUE ISTO EXISTE, palavra do Luis em 16/08:
   "a base da transformacao e ler os dados de UM LUGAR UNICO, que e o banco de
    dados. Nao esquece disso nunca."

   Antes de o banco poder ser a fonte unica, tem que saber o que ele TEM. Este
   programa nao supoe nada e nao le lista escrita a mao: ele PERGUNTA AO BANCO
   quais colunas a cards_base tem, conta quantas cartas tem cada uma preenchida,
   e cruza com o dados/base_unica.json — o arquivo de onde os motores leem hoje.

   Sai daqui a resposta de tres perguntas, e so com elas da para virar a chave:

     1. o que o motor LE e o banco NAO TEM      -> falta coluna
     2. o que o banco TEM e o motor NAO RECEBE  -> falta ligar a volta
     3. duas colunas para a mesma coisa         -> o "lugar unico" ja quebrou

⛔ NAO ESCREVE NADA. So le e conta. Pode rodar com o motor rodando.
"""
import json, os, sys, urllib.request, urllib.error
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
    print('⛔ nao achei o config.txt nem aqui nem nas pastas de cima.')
    sys.exit(1)
os.chdir(CASA)

L = []
def P(*a):
    s = ' '.join(str(x) for x in a)
    L.append(s)
    print(s, flush=True)
def A(*a):
    L.append(' '.join(str(x) for x in a))

# ============================================================================
# O DE-PARA — como cada campo do arquivo se chama no banco
# ============================================================================
# ⛔ Tirado do subir_base.py, linha por linha. Se ele mudar, isto muda junto.
DE_PARA = {
    'id': 'card_id', 'nome': 'nome', 'ovr': 'ovr', 'max_ovr': 'max_ovr',
    'tier': 'tier', 'votos': 'votos', 'pos': 'posicao', 'np': 'posicao_nativa',
    'sec': 'posicoes_sec', 'modelo': 'estilo_de_jogo', 'orc': 'orcamento',
    'levelCap': 'level_cap', 'base': 'atributos_base',
    'nm': 'impeto_efeito', 'nmn': 'impeto_nomes', 'nx': 'impeto_delta_condicional',
    'impeto_orfao': 'impeto_orfao', 'impeto_nativo': 'impeto_nativo',
    'impeto_quantos': 'impeto_quantos', 'impeto_tem': 'impeto_tem',
    'impeto_nomes': 'impeto_nomes_decompostos',
    'impeto_condicional': 'impeto_condicional',
    'impeto_efeito': 'impeto_efeito_legivel', 'impeto_soma': 'impeto_soma',
    'vagas_livres': 'vagas_livres', 'impeto_situacao': 'impeto_situacao',
    'impeto_de_onde': 'impeto_de_onde', 'sl': 'vagas_impeto',
    'vaga': 'vaga_detalhe', 'fab': 'hab_nativas', 'falta': 'hab_faltantes',
    'raras': 'hab_raras', 'corpo': 'corpo', 'pe': 'pe', 'altura': 'altura',
    'peso': 'peso', 'pe_ruim': 'pe_ruim', 'box': 'box', 'dt': 'data_lancamento',
    'boostId': 'boost_id', 'boostId2': 'boost_id2', 'origem_ficha': 'origem_ficha',
    'age': 'idade', 'wfu': 'pe_ruim_uso', 'wfa': 'pe_ruim_prec',
    'inj': 'resist_lesao', 'forma': 'forma', 'cond': 'condicao',
    'capdesc': 'cap_desbloq', 'fonte_de_cada_campo': 'fonte_de_cada_campo',
    # sem coluna conhecida — o programa confirma perguntando ao banco
    'com': 'estilo_ia', 'mst': None, 'mx': None, 'maxOvr': 'nota_maxima_tela',
}

# Pares que eu SUSPEITO serem a mesma coisa com dois nomes. O programa so
# acusa se as DUAS existirem no banco de verdade.
SUSPEITA_DE_GEMEO = [
    ('resist_lesao', 'lesao',            'resistencia a lesao'),
    ('pe_ruim_prec', 'pe_ruim_precisao', 'precisao do pe ruim'),
    ('max_ovr',      'nota_maxima_tela', 'nota maxima'),
    ('estilo_de_jogo', 'estilo_ia',      'estilo de jogo — do jogador x da IA'),
]

QUEM_ESCREVE = {
    'idade': 'entrar_com_o_efhub + subir_base',
    'lesao': 'entrar_com_o_efhub',
    'resist_lesao': 'subir_base',
    'forma': 'entrar_com_o_efhub + subir_base',
    'condicao': 'entrar_com_o_efhub + subir_base',
    'estilo_ia': 'entrar_com_o_efhub',
    'corpo': 'entrar_com_o_efhub + subir_base',
    'pe_ruim_uso': 'entrar_com_o_efhub + subir_base',
    'pe_ruim_precisao': 'entrar_com_o_efhub',
    'pe_ruim_prec': 'subir_base',
    'nota_maxima_tela': 'entrar_com_o_efhub',
    'level_cap': 'entrar_com_o_efhub + subir_base',
    'estado_de_cada_campo': 'estados',
}

# ============================================================================
def config():
    cfg = {}
    for ln in open('config.txt', encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if '=' in ln and not ln.startswith('#'):
            k, v = ln.split('=', 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

C = config()
URL = (C.get('SUPABASE_URL') or '').rstrip('/')
KEY = C.get('SUPABASE_KEY') or C.get('SUPABASE_SERVICE_KEY') or ''
if not URL or not KEY:
    print('⛔ nao achei a chave no config.txt.')
    sys.exit(1)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY}

P('=' * 74)
P('  O QUE O BANCO TEM  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 74)

# ---------------------------------------------------- 1) as colunas, do banco
try:
    r = urllib.request.Request(URL + '/rest/v1/cards_base?select=*&limit=1', headers=H)
    with urllib.request.urlopen(r, timeout=90) as f:
        amostra = json.loads(f.read().decode('utf-8', 'replace'))
except Exception as e:
    P('⛔ nao consegui falar com o banco: %s' % str(e)[:120])
    sys.exit(1)
if not amostra:
    P('⛔ a cards_base voltou vazia.')
    sys.exit(1)
COLUNAS = sorted(amostra[0].keys())

def conta(u):
    try:
        r = urllib.request.Request(URL + '/rest/v1/' + u,
                                   headers=dict(H, Prefer='count=exact'), method='HEAD')
        with urllib.request.urlopen(r, timeout=90) as f:
            cr = f.headers.get('Content-Range') or ''
            return int(cr.split('/')[-1]) if '/' in cr else -1
    except Exception:
        return -1

TOTAL = conta('cards_base?select=card_id')
P('')
P('cards_base ................ %s linhas · %d colunas' % ('{:,}'.format(TOTAL), len(COLUNAS)))

P('')
P('perguntando quantas cartas tem cada coluna preenchida...')
CHEIA = {}
for i, col in enumerate(COLUNAS):
    CHEIA[col] = conta('cards_base?select=card_id&%s=not.is.null' % col)
    print('   %d de %d' % (i + 1, len(COLUNAS)), end='\r', flush=True)
print(' ' * 30, end='\r')

# ---------------------------------------------------- 2) o que o motor le hoje
CAM = os.path.join('dados', 'base_unica.json')
NA_BASE = {}
if os.path.exists(CAM):
    _b = json.load(open(CAM, encoding='utf-8'))
    for c in _b['cards']:
        for k, v in c.items():
            if not (v is None or v == '' or v == [] or v == {}):
                NA_BASE[k] = NA_BASE.get(k, 0) + 1
    P('base_unica.json ........... %s registros · %d campos'
      % ('{:,}'.format(len(_b['cards'])), len(NA_BASE)))
else:
    P('⚠️ nao achei o %s — a comparacao com o motor fica de fora.' % CAM)

# ---------------------------------------------------- 3) as tres perguntas
P('')
P('1) O MOTOR LE E O BANCO NAO TEM')
falta_coluna = []
for campo in sorted(NA_BASE):
    col = DE_PARA.get(campo, campo)
    if col is None or col not in COLUNAS:
        falta_coluna.append((campo, NA_BASE[campo]))
if falta_coluna:
    for campo, n in falta_coluna:
        P('   ⛔ %-22s %s cartas na pasta, NENHUMA coluna no banco'
          % (campo, '{:,}'.format(n)))
    P('')
    P('   Enquanto isto existir, baixar do banco APAGA esses campos.')
else:
    P('   ✅ nenhum. Tudo que o motor le tem coluna no banco.')

P('')
P('2) O BANCO TEM E O MOTOR NAO RECEBE')
volta = []
inverso = {}
for k, v in DE_PARA.items():
    if v:
        inverso.setdefault(v, k)
for col in COLUNAS:
    if CHEIA.get(col, 0) <= 0:
        continue
    campo = inverso.get(col)
    if campo is None or NA_BASE.get(campo, 0) == 0:
        volta.append((col, CHEIA[col], NA_BASE.get(campo, 0) if campo else 0))
if volta:
    P('   %-24s %10s %12s' % ('coluna', 'no banco', 'na pasta'))
    P('   ' + '-' * 48)
    for col, nb, npasta in sorted(volta, key=lambda x: -x[1]):
        P('   %-24s %10s %12s' % (col, '{:,}'.format(nb), '{:,}'.format(npasta)))
    P('')
    P('   Este e o defeito do dia: dado colhido, conferido, no banco — e o')
    P('   motor nao ve. Coletar de novo nao resolve.')
else:
    P('   ✅ nenhum.')

P('')
P('3) DUAS COLUNAS PARA A MESMA COISA')
gemeos = []
for a, b, oque in SUSPEITA_DE_GEMEO:
    if a in COLUNAS and b in COLUNAS:
        gemeos.append((a, b, oque))
if gemeos:
    for a, b, oque in gemeos:
        P('   ⛔ %-18s %8s   x   %-18s %8s    %s'
          % (a, '{:,}'.format(CHEIA.get(a, 0)), b, '{:,}'.format(CHEIA.get(b, 0)), oque))
    P('')
    P('   O "lugar unico" ja quebrou aqui. Cada par precisa de UMA decisao:')
    P('   qual fica. Nao apague nada antes de decidir.')
else:
    P('   ✅ nenhum par suspeito existe nas duas formas.')

# ---------------------------------------------------- 4) a tabela inteira
A('')
A('=' * 74)
A('A TABELA INTEIRA — coluna por coluna')
A('')
A('  %-30s %10s %8s   %s' % ('coluna', 'preenchida', '%', 'quem escreve'))
A('  ' + '-' * 72)
for col in sorted(COLUNAS, key=lambda c: -CHEIA.get(c, 0)):
    n = CHEIA.get(col, 0)
    pc = round(100.0 * n / TOTAL) if TOTAL > 0 else 0
    A('  %-30s %10s %7d%%   %s'
      % (col, '{:,}'.format(n), pc, QUEM_ESCREVE.get(col, '')))

A('')
A('OS CAMPOS DO base_unica.json E A COLUNA DE CADA UM')
A('')
A('  %-22s %10s %-26s %10s' % ('campo na pasta', 'na pasta', 'coluna no banco', 'no banco'))
A('  ' + '-' * 72)
for campo in sorted(NA_BASE, key=lambda k: -NA_BASE[k]):
    col = DE_PARA.get(campo, campo)
    if col is None:
        col, nb = '(nenhuma)', ''
    elif col not in COLUNAS:
        nb = ''
        col = col + ' (NAO EXISTE)'
    else:
        nb = '{:,}'.format(CHEIA.get(col, 0))
    A('  %-22s %10s %-26s %10s' % (campo, '{:,}'.format(NA_BASE[campo]), col, nb))

open('RELATORIO-O-QUE-O-BANCO-TEM.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
P('')
P('=' * 74)
P('  A tabela coluna por coluna esta no RELATORIO-O-QUE-O-BANCO-TEM.txt')
P('  Nada foi escrito no banco.')
P('=' * 74)
