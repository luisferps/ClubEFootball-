# -*- coding: utf-8 -*-
r"""
SUBIR O QUE SO EXISTIA NA MAQUINA — os quatro insumos sem fonte externa.

ORDEM DO LUIS, 17/08/2026:
    "Eu acho que o mais importante agora e colocar isso aqui no banco de dados
     tambem. Porque, em suma, se sumir nao e tanto ferrado."

O QUE SOBE, e por que estes quatro

    dados/falta_por_card.json ........ 2.420 cartas · o espaco de habilidades
    dados/raras_por_card.json ........... 707 cartas · as habilidades raras
    impeto_conferido_no_jogo.json ....... 291 cartas · O LUIS OLHOU NO JOGO
    CONFERIDO.json ........................ 6 cartas · com o "como" de cada uma

    Todo o resto o sistema recoleta: efHub, efScout, efootballdb. Estes quatro
    nao tem fonte externa nenhuma. As 291 sao o caso grave — e o Luis abrindo
    carta por carta dentro do eFootball e anotando. Perdeu, perdeu.

⚠️ AS REGRAS ESCRITAS VAO JUNTO. Os arquivos nao tem so dado: tem as chaves
   `_regra`, `_como_usar`, `ordem_do_luis`, `_aviso`, que explicam POR QUE
   cada coisa e assim. Perder o dado e ruim; perder o porque e pior, porque
   ai alguem "conserta" o que estava certo.

⛔ NAO APAGA NADA. Tudo e upsert por (arquivo, chave).
⛔ ARQUIVO QUE NAO EXISTE NAO ZERA NADA. Se um deles sumir da pasta, o que ja
   esta no banco FICA. Apagar exige ordem, e ordem nao se supoe.

⛔ RODE ANTES o ClubEfootball\sql\29-o-que-so-existia-na-maquina.sql

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

LOTE = 300
AGORA = time.strftime('%Y-%m-%dT%H:%M:%S')

# (o arquivo na pasta, o nome que ele tem no banco, onde estao os registros)
#   o terceiro campo e a chave interna onde mora o dicionario de cartas —
#   None quer dizer "o arquivo inteiro ja e o dicionario".
FONTES = [
    (os.path.join('dados', 'falta_por_card.json'), 'falta_por_card',        None),
    (os.path.join('dados', 'raras_por_card.json'), 'raras_por_card',        None),
    ('impeto_conferido_no_jogo.json',              'impeto_conferido_no_jogo', 'conferidos'),
    ('CONFERIDO.json',                             'CONFERIDO',             'conferidos'),
]


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
CAB = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
       'Content-Type': 'application/json'}


def manda(linhas):
    ok = falha = 0
    for i in range(0, len(linhas), LOTE):
        lote = linhas[i:i + LOTE]
        req = urllib.request.Request(
            '%s/rest/v1/insumo_local?on_conflict=arquivo,chave' % URL,
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
            P('      ⛔ HTTP %s  %s' % (e.code, det))
            if 'does not exist' in det or 'schema cache' in det:
                P('         -> falta rodar o sql\\29-o-que-so-existia-na-maquina.sql')
            break
        except Exception as e:
            falha += len(lote)
            P('      ⛔ %s' % str(e)[:200])
            break
    return ok, falha


P('=' * 74)
P('  SUBIR O QUE SO EXISTIA NA MAQUINA')
P('=' * 74)
P('')
P('  Estes quatro nao tem fonte externa. Se a maquina sumir, some com eles.')

resumo = []
faltou_arquivo = []

for caminho, nome, dentro in FONTES:
    P('')
    P('-' * 74)
    P('  %s' % caminho)
    P('-' * 74)
    if not os.path.exists(caminho):
        P('   ⛔ nao esta na pasta. O que ja estiver no banco FICA como esta.')
        faltou_arquivo.append(caminho)
        continue
    try:
        d = json.load(open(caminho, encoding='utf-8'))
    except Exception as e:
        P('   ⛔ nao consegui ler: %s' % e)
        faltou_arquivo.append(caminho)
        continue

    # as notas ficam no topo (_regra, _como_usar, ordem_do_luis...);
    # os registros de carta ficam dentro de `conferidos` quando `dentro` diz.
    registros = d.get(dentro) if dentro else d
    if not isinstance(registros, dict):
        P('   ⛔ formato inesperado: esperava um dicionario.')
        faltou_arquivo.append(caminho)
        continue

    linhas = [{'arquivo': nome, 'chave': str(k), 'valor': v,
               'atualizado_em': AGORA} for k, v in registros.items()]
    n_cartas = len(linhas)

    # ⚠️ AS REGRAS ESCRITAS VAO JUNTO — e sao elas que impedem alguem de
    #    "consertar" no futuro o que estava certo de proposito.
    n_notas = 0
    if dentro:
        for k, v in d.items():
            if k == dentro:
                continue
            linhas.append({'arquivo': nome, 'chave': str(k), 'valor': v,
                           'atualizado_em': AGORA})
            n_notas += 1

    P('   %s cartas · %d notas (as regras escritas)'
      % ('{:,}'.format(n_cartas).replace(',', '.'), n_notas))
    ok, falha = manda(linhas)
    P('   subiram %d · falharam %d' % (ok, falha))
    resumo.append((nome, n_cartas, n_notas, ok, falha))

P('')
P('=' * 74)
P('  RESUMO')
P('=' * 74)
total_falha = 0
for nome, c, n, ok, falha in resumo:
    P('  %-26s %5d cartas · %2d notas · %5d subiram%s'
      % (nome, c, n, ok, ('  ⛔ %d FALHARAM' % falha) if falha else ''))
    total_falha += falha
if faltou_arquivo:
    P('')
    P('  ⚠️ nao estavam na pasta: %s' % ', '.join(faltou_arquivo))
    P('     O que ja estava no banco continua la — nada foi apagado.')
P('')
if total_falha:
    P('  ⛔ Alguma coisa nao subiu. Leia o erro acima e rode de novo.')
else:
    P('  ✅ Pronto. Agora eles existem em dois lugares.')
P('=' * 74)
pausa()
sys.exit(1 if total_falha else 0)
