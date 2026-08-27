# -*- coding: utf-8 -*-
r"""
LIMPAR A CHAVE VELHA — as linhas de builds gravadas com carta@POSICAO

⛔ ORDEM DO LUIS, 16/08/2026 17h50:
   "Essas linhas ja existem otimizadas com algum outro nome? Se ja existir,
    pode jogar elas fora. Se nao existir, voce pode jogar elas fora, porem
    voce coloca as linhas pra ser rodadas de novo."

O QUE ACONTECEU
   O sistema mudou o jeito de nomear a linha de resultado. Antes era
   `104717@LE` — a carta mais a posicao comprada. Hoje e so `104717`.
   As linhas antigas ficaram na tabela builds com um nome que ninguem
   mais procura. Medido em 16/08: a fila de hoje tem ZERO chaves com @.

AS DUAS FAMILIAS, e elas nao tem o mesmo destino
   JA EXISTE com a chave nova ...... e copia velha do mesmo resultado.
                                     Apagar e so tirar lixo.
   NAO EXISTE com a chave nova ..... o resultado se perde ao apagar.
                                     Tem que voltar para a fila.

COMO RODAR
   1) duplo clique em LIMPAR-A-CHAVE-VELHA.bat
      -> so MEDE. Escreve o relatorio e a lista do que volta para a fila.
         NAO APAGA NADA.
   2) so depois de ler, duplo clique em APAGAR-A-CHAVE-VELHA.bat
      -> ai sim apaga, em lotes, conferindo o que o banco devolveu.

⛔ O modo que apaga se RECUSA a rodar se nao houver backup do banco de hoje.
"""
import json, os, sys, urllib.request, urllib.error, urllib.parse
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
    L.append(s); print(s, flush=True)

APAGAR = any(a.lower().startswith('apag') for a in sys.argv[1:])

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


def pega(caminho, campos=None, ordem='card_id'):
    saida, de = [], 0
    sel = ','.join(campos) if campos else '*'
    while True:
        u = '%s/rest/v1/%s?select=%s&order=%s' % (URL, caminho, sel, ordem)
        r = urllib.request.Request(u, headers=dict(
            H, **{'Range-Unit': 'items', 'Range': '%d-%d' % (de, de + 999)}))
        with urllib.request.urlopen(r, timeout=180) as f:
            p = json.loads(f.read().decode('utf-8', 'replace'))
        if not p:
            break
        saida.extend(p)
        if len(p) < 1000:
            break
        de += 1000
    return saida


P('=' * 74)
P('  LIMPAR A CHAVE VELHA  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
if APAGAR:
    P('  🔴 MODO APAGAR — este vai escrever no banco.')
else:
    P('  MODO MEDIR — nao apaga nada.')
P('=' * 74)

# ---------------------------------------------------------------- 1) le tudo
P('')
P('lendo a tabela builds...')
linhas = pega('builds', ['card_id', 'funcao', 'motor_versao', 'rodado_em'], 'card_id')
P('   builds ................. %s linhas' % '{:,}'.format(len(linhas)))

velhas, novas = [], set()
for l in linhas:
    cid = str(l.get('card_id') or '')
    fun = l.get('funcao')
    if not cid or not fun:
        continue
    if '@' in cid:
        velhas.append((cid, fun, l.get('motor_versao'), l.get('rodado_em')))
    else:
        novas.add('%s|%s' % (cid, fun))

P('   com a chave VELHA (@) .. %s' % '{:,}'.format(len(velhas)))
P('   com a chave nova ....... %s' % '{:,}'.format(len(novas)))

if not velhas:
    P('')
    P('✅ NAO HA NENHUMA LINHA COM A CHAVE VELHA. Nada a fazer.')
    sys.exit(0)

# ---------------------------------------------------------------- 2) separa
tem_par, sem_par = [], []
for cid, fun, ver, quando in velhas:
    puro = '%s|%s' % (cid.split('@')[0], fun)
    (tem_par if puro in novas else sem_par).append((cid, fun, ver, quando))

P('')
P('AS DUAS FAMILIAS')
P('   JA EXISTE com a chave nova ..... %s   -> e copia velha, so apagar'
  % '{:,}'.format(len(tem_par)))
P('   NAO EXISTE com a chave nova .... %s   -> apagar E voltar para a fila'
  % '{:,}'.format(len(sem_par)))

# ---------------------------------------------------------------- 3) da para rodar?
NA_FILA = set()
if os.path.exists('fila_v6.json'):
    try:
        F = json.load(open('fila_v6.json', encoding='utf-8'))
        if isinstance(F, dict):
            F = F.get('linhas') or F.get('fila') or []
        for x in F:
            if isinstance(x, str):
                NA_FILA.add(x)
            elif isinstance(x, dict):
                c = x.get('card_id') or x.get('id')
                f = x.get('funcao') or x.get('tipo')
                if c and f:
                    NA_FILA.add('%s|%s' % (c, f))
            elif isinstance(x, (list, tuple)) and len(x) >= 2:
                NA_FILA.add('%s|%s' % (x[0], x[1]))
    except Exception as e:
        P('   ⚠️ nao consegui ler a fila_v6.json (%s)' % str(e)[:60])

pode_rodar, nem_na_fila = [], []
for cid, fun, ver, quando in sem_par:
    puro = '%s|%s' % (cid.split('@')[0], fun)
    (pode_rodar if puro in NA_FILA else nem_na_fila).append(puro)

if sem_par:
    P('')
    P('   DAS QUE PRECISAM VOLTAR:')
    P('      esta na fila de hoje, o motor pega ... %s' % '{:,}'.format(len(pode_rodar)))
    P('      NAO esta nem na fila de hoje ......... %s' % '{:,}'.format(len(nem_na_fila)))
    if nem_na_fila:
        P('')
        P('      ⚠️ essas %s o motor NAO vai rodar mesmo devolvendo:' % '{:,}'.format(len(nem_na_fila)))
        P('         a fila de hoje nao oferece esse par carta x funcao —')
        P('         entao devolver para a fila nao faz o motor calcular.')
        P('         ⚠️ Elas saem do banco assim mesmo (ordem do Luis) e ficam')
        P('            anotadas no PARA-RODAR-DE-NOVO.txt para nao sumirem.')

# ---------------------------------------------------------------- 4) escreve
# a lista do que volta para a fila: TODA linha sem copia com a chave nova,
# com a chave JA CONVERTIDA para o formato de hoje (sem o @POSICAO).
_vistos = set()
_lista = []
for cid, fun, _v, _q in sem_par:
    k = '%s|%s' % (cid.split('@')[0], fun)
    if k not in _vistos:
        _vistos.add(k); _lista.append(k)
if _lista:
    with open('PARA-RODAR-DE-NOVO.txt', 'w', encoding='utf-8') as f:
        f.write('# as chaves NOVAS das linhas que saem sem ter copia.\n')
        f.write('# %d na fila de hoje (o motor pega) · %d fora dela\n'
                % (len(set(pode_rodar)), len(set(nem_na_fila))))
        for k in _lista:
            f.write(k + '\n')
    P('')
    P('   escrevi PARA-RODAR-DE-NOVO.txt com %s chaves' % '{:,}'.format(len(_lista)))
    P('      dessas, na fila de hoje ...... %s' % '{:,}'.format(len(set(pode_rodar))))
    P('      fora da fila de hoje ......... %s   ⚠️ devolver nao faz rodar'
      % '{:,}'.format(len(set(nem_na_fila))))

# ⛔ ORDEM DO LUIS, dita duas vezes e na segunda sem margem:
#      "Se ja existir, pode jogar fora. Se nao existir, joga fora do mesmo
#       jeito, so que antes disso voce anota quais sao e pede pro controle
#       rodar de novo."
#
#    Entao TODAS as linhas de chave velha saem. A separacao em duas familias
#    nao muda o destino delas — muda so o que acontece ANTES:
#       tem copia com a chave nova .... sai, e acabou
#       nao tem ....................... sai, mas fica anotada e vai para a fila
#
#    ⚠️ Eu tinha travado as que a fila de hoje nao oferece. Ele desfez a trava.
#       O que eu posso fazer, e faco, e ANOTAR quais sao essas — porque devolver
#       para a fila nao faz o motor rodar par que o monta_fila nao gera.
_seguras = set('%s|%s' % (c, f) for c, f, _v, _q in velhas)
_travadas = []

with open('CHAVE-VELHA-PARA-APAGAR.txt', 'w', encoding='utf-8') as f:
    f.write('# TODAS as linhas de builds com a chave velha (carta@POSICAO)\n')
    f.write('# geradas em %s\n' % datetime.now().strftime('%d/%m/%Y %H:%M'))
    f.write('# %d ja tem copia com a chave nova (saem e acabou)\n' % len(tem_par))
    f.write('# %d nao tem — saem, e as chaves novas delas estao no\n' % len(sem_par))
    f.write('#   PARA-RODAR-DE-NOVO.txt\n')
    for k in sorted(_seguras):
        f.write(k + '\n')
P('   escrevi CHAVE-VELHA-PARA-APAGAR.txt com %s chaves (TODAS)'
  % '{:,}'.format(len(_seguras)))

open('RELATORIO-CHAVE-VELHA.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')

# ---------------------------------------------------------------- 5) apagar
if not APAGAR:
    P('')
    P('=' * 74)
    P('  NADA FOI APAGADO. Leia o RELATORIO-CHAVE-VELHA.txt.')
    P('  Para apagar de verdade: APAGAR-A-CHAVE-VELHA.bat')
    P('=' * 74)
    sys.exit(0)

# ⛔ a trava do backup
hoje = datetime.now().strftime('%Y-%m-%d')
_bk = os.path.join('backups_banco')
_tem_backup = False
if os.path.isdir(_bk):
    for _d in os.listdir(_bk):
        if _d.startswith(hoje):
            _tem_backup = True
            break
if not _tem_backup:
    P('')
    P('=' * 74)
    P('  ⛔ PAREI. NAO ACHEI BACKUP DO BANCO DE HOJE (%s).' % hoje)
    P('=' * 74)
    P('  Apagar linha de resultado sem backup do dia nao se faz.')
    P('  Rode o BACKUP-DO-BANCO.bat e volte aqui.')
    sys.exit(1)

P('')
P('🔴 APAGANDO %s linhas da tabela builds — TODAS as de chave velha'
  % '{:,}'.format(len(_seguras)))

apagadas = 0
erro = None
_lote = []
for k in sorted(_seguras):
    _lote.append(k)
    if len(_lote) < 100 and k != sorted(_seguras)[-1]:
        continue
    # apaga uma a uma dentro do lote: card_id e funcao formam a chave
    for kk in _lote:
        cid, fun = kk.split('|', 1)
        u = ('%s/rest/v1/builds?card_id=eq.%s&funcao=eq.%s'
             % (URL, urllib.parse.quote(cid, safe=''), urllib.parse.quote(fun, safe='')))
        r = urllib.request.Request(u, headers=dict(H, Prefer='return=representation'),
                                   method='DELETE')
        try:
            with urllib.request.urlopen(r, timeout=90) as f:
                volta = json.loads(f.read().decode('utf-8', 'replace') or '[]')
            apagadas += len(volta) if isinstance(volta, list) else 0
        except Exception as e:
            erro = str(e)[:120]
            break
    print('   %d de %d...' % (apagadas, len(_seguras)), end='\r', flush=True)
    _lote = []
    if erro:
        break
print(' ' * 40, end='\r')

P('')
P('   o banco confirmou apagadas ... %s' % '{:,}'.format(apagadas))
if erro:
    P('   ⛔ parou com erro: %s' % erro)

# confere
depois = pega('builds', ['card_id'], 'card_id')
_sobrou = sum(1 for l in depois if '@' in str(l.get('card_id') or ''))
P('   com a chave velha AINDA no banco ... %s' % '{:,}'.format(_sobrou))
P('   (esperado: 0 — todas saem)')
P('   ' + ('✅ bate' if _sobrou == 0 else '⛔ NAO BATE — confira'))

open('RELATORIO-CHAVE-VELHA.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
P('')
P('=' * 74)
if _lista:
    P('  AGORA: duplo clique em REFAZER-O-QUE-ENVELHECEU-2.bat')
    P('  para devolver as %s para a fila. Depois, o motor.' % '{:,}'.format(len(_lista)))
P('  O relatorio ficou em RELATORIO-CHAVE-VELHA.txt')
P('=' * 74)
