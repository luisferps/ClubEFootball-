# -*- coding: utf-8 -*-
"""
SUBIR OS METADADOS DA TELA — 16/08/2026

Pega o dados/metadados_da_tela.json (o que o RESGATAR-DA-TELA.bat tirou de
dentro dos HTML) e poe no banco, no cards_base, com a origem de cada valor.

⛔ NAO apaga nada. NAO muda pontuacao nenhuma. So preenche colunas novas.
⛔ Onde a palavra da casca antiga nao tem traducao EXATA, o numero fica em
   branco e a palavra e guardada como estava. Traduzir no chute e inventar.
"""
import json, os, sys, io, urllib.request, urllib.error
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
    P('NAO ACHEI SUPABASE_URL / SUPABASE_KEY no config.txt. Nada foi feito.')
    sys.exit(1)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}


def conta(u):
    try:
        r = urllib.request.Request(URL + '/rest/v1/' + u,
                                   headers=dict(H, Prefer='count=exact'), method='HEAD')
        with urllib.request.urlopen(r, timeout=90) as f:
            cr = f.headers.get('Content-Range') or ''
            return int(cr.split('/')[-1]) if '/' in cr else -1
    except Exception:
        return -1


def sobe(tabela, linhas, conflito, lote_tam=200):
    """Sobe e devolve (quantas mandei, quantas o SERVIDOR disse que gravou).

    ⛔ 16/08 03h05: o Supabase devolveu HTTP 400 na primeira tentativa. O motivo:
       o PostgREST exige que TODAS as linhas de um mesmo lote tenham EXATAMENTE
       as mesmas colunas ("All object keys must match"). As minhas variam — uma
       carta tem idade e nao tem estilo de IA, outra o contrario.

       ⚠️ A saida FACIL seria completar todas as linhas com null nas colunas que
          faltam. Isso SOBRESCREVERIA com vazio o que ja esta no banco — as 435
          linhas de estilo_ia que o motor de bonus gravou as 02h25 morreriam.
          Apagar dado bom para caber num lote e exatamente o que esta reforma
          existe para impedir.

       O certo: separar as linhas por CONJUNTO DE COLUNAS e mandar cada grupo no
       seu proprio lote. Cada carta so escreve nas colunas que ela realmente tem.
    """
    grupos = {}
    for lin in linhas:
        grupos.setdefault(tuple(sorted(lin.keys())), []).append(lin)

    P('  colunas diferentes ........ %d grupos (o PostgREST exige lote uniforme)' % len(grupos))
    mandei = gravou = 0
    feitos = 0
    for chaves, grupo in sorted(grupos.items(), key=lambda x: -len(x[1])):
        for i in range(0, len(grupo), lote_tam):
            lote = grupo[i:i + lote_tam]
            u = URL + '/rest/v1/' + tabela + '?on_conflict=' + conflito
            d = json.dumps(lote, ensure_ascii=False).encode('utf-8')
            r = urllib.request.Request(u, data=d, headers=dict(
                H, Prefer='resolution=merge-duplicates,return=representation'), method='POST')
            try:
                with urllib.request.urlopen(r, timeout=180) as f:
                    corpo = f.read().decode('utf-8', 'replace')
            except urllib.error.HTTPError as e:
                # ⛔ sempre mostrar o que o servidor disse. Esconder a mensagem
                #    fez esta noite perder uma rodada inteira.
                msg = e.read().decode('utf-8', 'replace')[:400]
                P('')
                P('  ⛔ o banco recusou (HTTP %s):' % e.code)
                P('     %s' % msg)
                P('')
                P('     colunas deste lote: %s' % ', '.join(chaves))
                raise SystemExit(1)
            try:
                volta = json.loads(corpo)
                g = len(volta) if isinstance(volta, list) else 0
            except Exception:
                g = 0
            mandei += len(lote)
            gravou += g
            feitos += len(lote)
            print('   %d de %d...' % (feitos, len(linhas)), end='\r', flush=True)
    print(' ' * 40, end='\r')
    return mandei, gravou


# ============================================================================
#  AS TRADUCOES — so as que batem EXATO. Saem do codigo da tela, nao de palpite.
# ============================================================================
#  gera_encaixe.py, linhas 1856-1857:
#     const PR_ROT_F=["Quase nunca","Raramente","Ocasionalmente","Regularmente"]
#     const PR_ROT_Q=["Baixa","Média","Alta","Muito alta"]
PR_ROT_F = ['Quase nunca', 'Raramente', 'Ocasionalmente', 'Regularmente']
PR_ROT_Q = ['Baixa', 'Média', 'Alta', 'Muito alta']
# ⛔ Para LESAO nao existe tabela nenhuma no codigo. Fica sem numero.
TABELA_DE = {'wfu': PR_ROT_F, 'wfa': PR_ROT_Q, 'inj': None}


def para_numero(campo, v):
    """Devolve (numero_ou_None, palavra_ou_None). So traduz o que bate exato."""
    if v is None or v == '':
        return None, None
    if isinstance(v, bool):
        return None, str(v)
    if isinstance(v, (int, float)):
        return int(v), None
    tab = TABELA_DE.get(campo)
    if tab and v in tab:
        return tab.index(v), v
    return None, str(v)          # palavra sem traducao: guarda a palavra


P('=' * 74)
P('  SUBIR OS METADADOS DA TELA  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 74)
P('')

CAM = os.path.join('dados', 'metadados_da_tela.json')
if not os.path.exists(CAM):
    P('⛔ nao achei o %s.' % CAM)
    P('   Rode antes o RESGATAR-DA-TELA.bat. Nada foi feito.')
    sys.exit(1)

M = json.load(open(CAM, encoding='utf-8'))
D = M.get('dados') or {}
O = M.get('de_onde_veio_cada_valor') or {}
VISTOS = set(M.get('cards_vistos_numa_casca') or [])
P('  arquivo lido .............. %d cartas' % len(D))
P('  vistas numa casca ......... %d' % len(VISTOS))
P('  gerado em ................. %s' % (M.get('gerado_em') or '?')[:16])

# --------------------------------------------------- as colunas existem?
teste = conta('cards_base?select=card_id&visto_na_casca=not.is.null')
try:
    r = urllib.request.Request(URL + '/rest/v1/cards_base?select=idade,lesao_bruto,'
                               'pe_ruim_uso_bruto,maximo,visto_na_casca,'
                               'metadado_tela_de_onde&limit=1', headers=H)
    urllib.request.urlopen(r, timeout=60).read()
except urllib.error.HTTPError as e:
    P('')
    P('  ⛔ as colunas novas ainda nao existem no banco.')
    P('     Abra o CRIAR-METADADOS-NO-SUPABASE.html e siga os 4 passos.')
    P('     (%s)' % e.read().decode('utf-8', 'replace')[:160])
    sys.exit(1)
except Exception as e:
    P('  ⛔ nao consegui falar com o banco: %s' % str(e)[:80])
    sys.exit(1)

# ------------------------------------------------------------- montar
linhas = []
sem_traducao = {}
conta_campo = {}
for cid, v in D.items():
    o = O.get(cid) or {}
    so_da_fonte = {k for k, d in o.items() if (d or {}).get('tipo') == 'fonte'}

    lin = {'card_id': cid,
           'visto_na_casca': cid in VISTOS,
           'metadado_tela_de_onde': o or None}

    # ⛔ o estilo de jogo da IA so entra QUANDO VEIO DE CASCA. A copia
    #    propagada nao serve: nela todo card tem o campo, vazio ou nao, e
    #    isso faria carta nunca coletada passar por "conferido, nao tem".
    #    E a mesma disciplina que o motor_bonus.py ja aplica desde 15/08.
    if 'com' in v and 'com' in so_da_fonte:
        lin['estilo_ia'] = v['com']

    if v.get('age') is not None:
        lin['idade'] = int(v['age'])
    if v.get('mst') is not None:
        lin['mestre'] = str(v['mst'])
    if v.get('mx') is not None:
        lin['maximo'] = v['mx']
    if v.get('maxOvr') is not None:
        try:
            lin['nota_maxima_tela'] = float(v['maxOvr'])
        except Exception:
            pass

    for campo, (col_n, col_b) in (('inj', ('lesao', 'lesao_bruto')),
                                  ('wfu', ('pe_ruim_uso', 'pe_ruim_uso_bruto')),
                                  ('wfa', ('pe_ruim_precisao', 'pe_ruim_precisao_bruto'))):
        if campo not in v:
            continue
        n, palavra = para_numero(campo, v[campo])
        if n is not None:
            lin[col_n] = n
        if palavra is not None:
            lin[col_b] = palavra
            if n is None:
                sem_traducao.setdefault(campo, {})
                sem_traducao[campo][palavra] = sem_traducao[campo].get(palavra, 0) + 1

    for k in lin:
        if k != 'card_id':
            conta_campo[k] = conta_campo.get(k, 0) + 1
    linhas.append(lin)

P('')
P('  O QUE VAI SUBIR')
P('')
for k in sorted(conta_campo, key=lambda x: -conta_campo[x]):
    P('     %-24s %6d cartas' % (k, conta_campo[k]))

if sem_traducao:
    P('')
    P('  ⚠️  PALAVRAS QUE NENHUMA TABELA TRADUZ — sobem como palavra, sem numero')
    P('')
    for campo, d in sorted(sem_traducao.items()):
        for palavra, n in sorted(d.items(), key=lambda x: -x[1]):
            P('     %-18s %-20s %6d cartas' % (campo, palavra, n))
    P('')
    P('     Cada uma dessas e UMA conferida no jogo, uma vez so. Depois vira')
    P('     traducao e nunca mais se pergunta. ⛔ Nao chutei nenhuma.')

# ------------------------------------------------------------- antes
antes_idade = conta('cards_base?select=card_id&idade=not.is.null')
antes_ia = conta('cards_base?select=card_id&estilo_ia=not.is.null')
P('')
P('  no banco ANTES ............ idade: %s · estilo_ia: %s' % (antes_idade, antes_ia))

# ------------------------------------------------------------- subir
P('')
P('  subindo %d cartas...' % len(linhas))
mandei, gravou = sobe('cards_base', linhas, 'card_id')
P('  mandei .................... %d' % mandei)
P('  o BANCO gravou ............ %d' % gravou)
if gravou != mandei:
    P('')
    P('  ⛔ o banco gravou menos do que eu mandei. PAREI.')
    sys.exit(1)

# --------------------------------------------------------- CONFERENCIA
P('')
P('  CONFERENCIA — lendo de volta do banco')
depois = {
    'idade':            conta('cards_base?select=card_id&idade=not.is.null'),
    'estilo_ia':        conta('cards_base?select=card_id&estilo_ia=not.is.null'),
    'lesao_bruto':      conta('cards_base?select=card_id&lesao_bruto=not.is.null'),
    'pe_ruim_uso_bruto': conta('cards_base?select=card_id&pe_ruim_uso_bruto=not.is.null'),
    'maximo':           conta('cards_base?select=card_id&maximo=not.is.null'),
    'visto_na_casca':   conta('cards_base?select=card_id&visto_na_casca=is.true'),
}
erro = 0
for k, n in depois.items():
    esp = conta_campo.get(k, 0)
    if k == 'visto_na_casca':
        esp = len(VISTOS)
    marca = '✅' if n >= esp else '⛔'
    if n < esp:
        erro = 1
    P('     %-20s %6d   (subi %d) %s' % (k, n, esp, marca))

if erro:
    P('')
    P('  ⛔ alguma coluna ficou com menos do que subiu. PAREI.')
    sys.exit(1)

P('')
P('  ✅ PRONTO E CONFERIDO.')
P('')
P('     Os oito campos deixaram de morar so dentro de um HTML.')
P('     Agora o BACKUP-DO-BANCO.bat leva eles junto.')
P('')
P('  ⚠️  O que isto ainda NAO resolve: ninguem COLETA esses campos. A fonte')
P('     continua sendo 22 arquivos parados na pasta Downloads. Enquanto o')
P('     motor de atualizacao nao nascer, nao apague nada que comece com')
P('     encaixe_B_ ali.')
