# -*- coding: utf-8 -*-
r"""
SUBIR O QUE A TELA LE — os quatro insumos que nao tinham tabela.

ORDEM DO LUIS, 17/08/2026:
    "O encaixe e so uma interface. Ele e o que vai fazer as consultas do banco
     e colocar na tela. Ele nao tem que ficar carregando um outro banco de
     dados duplicado dentro dele. E por isso que da errado."

O QUE SOBE

    regra.json               ->  insumo_regra_funcao   (2 linhas: REGRA e SA_FAMILIA)
    meu_time.json            ->  meu_time              (114 cartas)
    campanhas_efhub.json     ->  campanha              (fonte 'efhub-home')
    efscout_campanhas.json   ->  campanha              (fonte 'efscout')
                             ->  insumo_player_type    (137 cartas)

⛔ RODE ANTES o sql/26-o-que-a-tela-le.sql no SQL Editor do Supabase.
   Sem as tabelas, o banco recusa e este programa avisa qual faltou.

⛔ NAO APAGA NADA. Tudo e upsert por chave. Rodar duas vezes nao duplica.

⛔ ARQUIVO QUE NAO EXISTE NAO ZERA TABELA. Se o meu_time.json sumir da pasta,
   a tabela `meu_time` fica como esta — nao vira zero. Apagar exige ordem.

A CHAVE sai do config.txt na hora de rodar. Nunca e impressa nem gravada aqui.
"""
import json, os, sys, io, time, urllib.request, urllib.error

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
    print('PAREI: nao achei o config.txt nem aqui nem nas pastas de cima.')
    sys.exit(1)
os.chdir(CASA)

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

LOTE = 200
AGORA = time.strftime('%Y-%m-%dT%H:%M:%S')


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
if not URL or not KEY or 'COLE_AQUI' in KEY:
    P('O config.txt esta sem a URL ou a chave do Supabase.')
    pausa(); sys.exit(1)

CAB = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
       'Content-Type': 'application/json'}


def le(p, padrao):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return padrao


def manda(tabela, linhas, chave):
    """Upsert em lotes. Devolve (ok, falha)."""
    if not linhas:
        P('   nada a subir'); return 0, 0
    ok = falha = 0
    for i in range(0, len(linhas), LOTE):
        lote = linhas[i:i + LOTE]
        req = urllib.request.Request(
            '%s/rest/v1/%s?on_conflict=%s' % (URL, tabela, chave),
            data=json.dumps(lote, ensure_ascii=False).encode('utf-8'),
            headers=dict(CAB, **{'Prefer': 'resolution=merge-duplicates,return=minimal'}),
            method='POST')
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                r.read()
            ok += len(lote)
        except urllib.error.HTTPError as e:
            det = ''
            try:
                det = e.read().decode('utf-8', 'ignore')[:220]
            except Exception:
                pass
            falha += len(lote)
            P('   ⛔ HTTP %s  %s' % (e.code, det))
            if 'does not exist' in det or 'schema cache' in det:
                P('      -> falta rodar o sql/26-o-que-a-tela-le.sql no Supabase.')
            break
        except Exception as e:
            falha += len(lote)
            P('   ⛔ %s' % str(e)[:200])
            break
    return ok, falha


resumo = []
P('=' * 74)
P('  SUBIR O QUE A TELA LE')
P('=' * 74)

# --------------------------------------------------------------- 1. A REGRA
P('')
P('[1/4] A REGRA DA FUNCAO   regra.json -> insumo_regra_funcao')
R = le('regra.json', {}) or {}
linhas = []
for chave, o_que in (('REGRA', 'posicao -> as funcoes que ela pode ocupar'),
                     ('SA_FAMILIA', 'estilo de jogo -> familia do segundo atacante')):
    if R.get(chave):
        linhas.append({'chave': chave, 'valor': R[chave], 'o_que_e': o_que,
                       'vem_de': 'regra.json', 'atualizado_em': AGORA})
if not linhas:
    P('   ⛔ nao achei o regra.json (ou ele esta vazio). A tabela fica como esta.')
else:
    P('   REGRA: %d posicoes · SA_FAMILIA: %d estilos'
      % (len(R.get('REGRA') or {}), len(R.get('SA_FAMILIA') or {})))
    resumo.append(('insumo_regra_funcao',) + manda('insumo_regra_funcao', linhas, 'chave'))

# ------------------------------------------------------------ 2. O MEU TIME
P('')
P('[2/4] O MEU TIME   meu_time.json -> meu_time')
M = le('meu_time.json', {}) or {}
ids = [str(x) for x in (M.get('ids') or [])]
nomes = {str(k): v for k, v in (M.get('nomes') or {}).items()}
fonte = (M.get('fonte') or '')[:200]
if not ids:
    P('   ⛔ nao achei o meu_time.json (ou ele esta sem ids). A tabela fica como esta.')
else:
    # ⚠️ id sem nome NAO fica de fora: o id e que manda, o nome e rotulo.
    linhas = [{'card_id': i, 'nome': nomes.get(i), 'fonte': fonte,
               'atualizado_em': AGORA} for i in dict.fromkeys(ids)]
    sem_nome = sum(1 for x in linhas if not x['nome'])
    P('   %d cartas · %d sem nome no arquivo (sobem assim mesmo, o id manda)'
      % (len(linhas), sem_nome))
    resumo.append(('meu_time',) + manda('meu_time', linhas, 'card_id'))

# ----------------------------------------------------------- 3. AS CAMPANHAS
P('')
P('[3/4] AS CAMPANHAS   campanhas_efhub.json + efscout_campanhas.json -> campanha')
linhas = []

E = le('campanhas_efhub.json', {}) or {}
ordem = {n: i for i, n in enumerate(E.get('ordem') or [])}
quando = E.get('quando')
for nome, cartas in (E.get('campanhas') or {}).items():
    linhas.append({'fonte': 'efhub-home', 'nome': nome,
                   'ids': [str(x) for x in (cartas or [])],
                   'ordem': ordem.get(nome), 'quando': quando,
                   'atualizado_em': AGORA})

S = le('efscout_campanhas.json', {}) or {}
for nome, cartas in (S.get('campanhas') or {}).items():
    linhas.append({'fonte': 'efscout', 'nome': nome,
                   'ids': [str(x) for x in (cartas or [])],
                   'ordem': None, 'quando': None,
                   'atualizado_em': AGORA})

if not linhas:
    P('   ⛔ nao achei campanha nenhuma. A tabela fica como esta.')
else:
    ef = sum(1 for x in linhas if x['fonte'] == 'efhub-home')
    P('   %d do efHub · %d do efscout' % (ef, len(linhas) - ef))
    # ⚠️ as duas fontes listam a MESMA box com conteudo que pode divergir.
    #    Por isso a chave e (fonte, nome): as duas ficam, e da para medir depois.
    nomes_ef = {x['nome'] for x in linhas if x['fonte'] == 'efhub-home'}
    nomes_es = {x['nome'] for x in linhas if x['fonte'] == 'efscout'}
    P('   box que as DUAS listam: %d (ficam as duas, para poder comparar)'
      % len(nomes_ef & nomes_es))
    resumo.append(('campanha',) + manda('campanha', linhas, 'fonte,nome'))

# ------------------------------------------------------- 4. O TIPO DA CARTA
P('')
P('[4/4] O TIPO DA CARTA   efscout_campanhas.json -> insumo_player_type')
PT = (S.get('player_type') or {})
if not PT:
    P('   ⛔ nao achei o player_type. A tabela fica como esta.')
else:
    linhas = []
    for cid, tipo in PT.items():
        try:
            linhas.append({'card_id': str(cid), 'tipo': int(tipo),
                           'atualizado_em': AGORA})
        except Exception:
            pass
    P('   %d cartas com tipo' % len(linhas))
    resumo.append(('insumo_player_type',) + manda('insumo_player_type', linhas, 'card_id'))

# ---------------------------------------------------------------------------
P('')
P('=' * 74)
P('  RESUMO')
P('=' * 74)
falhou = 0
for tab, ok, falha in resumo:
    P('  %-24s %5d linhas   %s' % (tab, ok, ('%d FALHARAM' % falha) if falha else 'ok'))
    falhou += falha
P('')
if falhou:
    P('  ⛔ Alguma coisa nao subiu. Leia o erro acima — quase sempre e a tabela')
    P('     que ainda nao existe. Rode o sql/26-o-que-a-tela-le.sql e tente de novo.')
else:
    P('  Pronto. A tela agora tem no banco tudo o que ela le.')
P('=' * 74)
pausa()
sys.exit(1 if falhou else 0)
