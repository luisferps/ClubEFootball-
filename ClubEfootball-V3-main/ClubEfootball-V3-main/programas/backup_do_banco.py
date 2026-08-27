# -*- coding: utf-8 -*-
"""
BACKUP DO BANCO -> arquivos na pasta, antes de apagar qualquer tabela.

Ordem do Luis, 14/08/2026:
    "faz um backup e ai voce pode apagar as tabelas e dados que nao
     necessitamos mais, pois em caso de erro rodamos o backup"

O QUE ELE FAZ
  Baixa CADA tabela do Supabase para  backups_banco\AAAA-MM-DD_HHhMM\<tabela>.jsonl
  e escreve um RESUMO.txt com a contagem de cada uma.
  ⛔ SO LE. Nao apaga, nao altera, nao cria nada no banco.

A CHAVE
  Lida do config.txt na hora de rodar, igual ao enviar_continuo.py.
  Nunca sai da sua maquina, nunca vai para lugar nenhum.

COMO CONFERIR QUE O BACKUP PRESTA
  O RESUMO.txt traz, por tabela, quantas linhas o banco disse ter e quantas
  linhas o arquivo tem. Os dois numeros TEM de bater. Se nao baterem, o
  script avisa e o backup daquela tabela NAO conta.
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
import json, os, sys, time, urllib.request, urllib.parse

# ⛔ 19/08 — a pasta dos DADOS e a CASA (a do config.txt), nao a

#    pasta deste arquivo. Ele mudou de lugar; os dados nao.

AQUI = _CASA or os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)

# ---- as tabelas que vao para o backup -------------------------------------
# As 8 mortas (as que serao apagadas) primeiro; depois as vivas, por seguranca.
MORTAS = ['builds_v4', 'builds_v5_backup', 'builds_backup_0508',
          'builds_backup_0508b', 'builds_backup_1008',
          'ordem_backup_0508', 'ordem_backup_0508b', 'cards_bruto']
VIVAS = ['builds', 'cards', 'cards_base', 'cards_efhub', 'cards_lancamento',
         'molde', 'molde_versao', 'funcoes', 'parametros', 'estilo_valor',
         'pacotes', 'arquivos_insumo', 'coletas', 'faltas',
         'comunidade_apurado', 'builds_bruto', 'vigia_log']

TUDO = (sys.argv[1:] or None)
if TUDO is None:
    TUDO = MORTAS + VIVAS
elif TUDO == ['--mortas']:
    TUDO = MORTAS

# ---- a chave, lida na hora -------------------------------------------------
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
    print('NAO ACHEI SUPABASE_URL / SUPABASE_KEY no config.txt. Nada foi feito.')
    raw_input if sys.version_info[0] < 3 else input('Enter para fechar...')
    raise SystemExit(1)

H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY}

def pega(tab, ini, fim):
    u = URL + '/rest/v1/' + tab + '?select=*'
    r = urllib.request.Request(u, headers=dict(H, Range='%d-%d' % (ini, fim),
                                               **{'Range-Unit': 'items'}))
    with urllib.request.urlopen(r, timeout=120) as f:
        return json.loads(f.read().decode('utf-8'))

def conta(tab):
    u = URL + '/rest/v1/' + tab + '?select=*&limit=1'
    r = urllib.request.Request(u, headers=dict(H, Prefer='count=exact'),
                               method='HEAD')
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            cr = f.headers.get('Content-Range') or ''
            return int(cr.split('/')[-1]) if '/' in cr else -1
    except Exception:
        return -1

carimbo = time.strftime('%Y-%m-%d_%Hh%M')
DEST = os.path.join('backups_banco', carimbo)
os.makedirs(DEST, exist_ok=True)

print('=' * 70)
print('  BACKUP DO BANCO  ->  ' + DEST)
print('=' * 70)

L = ['BACKUP DO BANCO - ' + time.strftime('%d/%m/%Y %H:%M'),
     '=' * 70, '',
     'tabela                         no banco    no arquivo   confere?', '-' * 70]
falhou = []
for tab in TUDO:
    n_banco = conta(tab)
    linhas, ini, LOTE = 0, 0, 1000
    cam = os.path.join(DEST, tab + '.jsonl')
    try:
        with open(cam, 'w', encoding='utf-8') as f:
            while True:
                parte = pega(tab, ini, ini + LOTE - 1)
                if not parte:
                    break
                for x in parte:
                    f.write(json.dumps(x, ensure_ascii=False) + '\n')
                linhas += len(parte)
                ini += LOTE
                print('   %-28s %d' % (tab, linhas), end='\r')
                if len(parte) < LOTE:
                    break
    except Exception as e:
        falhou.append((tab, str(e)[:60]))
        L.append('%-30s ERRO: %s' % (tab, str(e)[:40]))
        print('   %-28s ERRO %s' % (tab, str(e)[:40]))
        continue
    ok = 'SIM' if (n_banco < 0 or n_banco == linhas) else '*** NAO ***'
    if ok != 'SIM':
        falhou.append((tab, 'contagem nao bate'))
    L.append('%-30s %9s %13d   %s'
             % (tab, (n_banco if n_banco >= 0 else '?'), linhas, ok))
    print('   %-28s %d linhas  %s' % (tab, linhas, ok))

L += ['', 'PASTA: ' + os.path.abspath(DEST), '']
if falhou:
    L.append('*** ATENCAO: estas NAO fecharam. NAO APAGUE NADA. ***')
    for t, m in falhou:
        L.append('   %s -> %s' % (t, m))
else:
    L.append('Todas fecharam. O backup esta completo.')
L += ['', 'COMO VOLTAR ATRAS, se der erro depois de apagar:',
      '  1. abra o Supabase -> SQL Editor',
      '  2. recrie a tabela (o desenho dela esta no ARQUITETURA-DO-BANCO.md)',
      '  3. rode o RESTAURAR-DO-BACKUP.bat apontando para a pasta acima']
open(os.path.join(DEST, 'RESUMO.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('')
print('\n'.join(L[-8:]))
print('')
print('Gravado: ' + os.path.join(DEST, 'RESUMO.txt'))
try:
    input('Enter para fechar...')
except Exception:
    pass
