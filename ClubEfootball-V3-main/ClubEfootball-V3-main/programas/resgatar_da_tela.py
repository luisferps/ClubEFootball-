# -*- coding: utf-8 -*-
"""
RESGATAR DA TELA — 16/08/2026

O PROBLEMA, medido em 16/08 02h45:

  Oito campos do sistema NAO EXISTEM em nenhum arquivo de dado, em nenhuma
  tabela do banco e em nenhum programa de coleta. Eles existem SO DENTRO DO
  HTML JA GERADO, e sao copiados de uma geracao para a proxima:

      com     os estilos de jogo da IA
      age     a idade
      inj     a lesao
      wfa     a precisao do pe ruim
      wfu     o uso do pe ruim
      mst     o mestre / familiaridade
      mx      o maximo
      maxOvr  a pontuacao maxima da tela

  O gera_encaixe.py declara isso na propria cabecalho:
      "HTML antigo (v164 / v171) ... o que so existe na tela"
  e, na hora de montar cada card, faz  m.get('com')  onde m e o registro lido
  do HTML anterior.

  Medido na casca encaixe_B_v171_datas_tela.html: 491 cards, e o estilo de
  jogo da IA de 435 deles. 6.469 - 435 = 6.034 sem estilo. E exatamente o
  numero que os relatorios vinham dando ha semanas, e ninguem sabia de onde
  saia: saia de um arquivo de saida.

  ⛔ Se esse HTML se perder, ou se alguem gerar a tela a partir de uma casca
     limpa, esses oito campos somem e NAO HA DE ONDE TIRAR DE VOLTA.

O QUE ESTE PROGRAMA FAZ:

  Le todos os HTML que tem `const D`, tira os oito campos de cada card, e
  grava  dados/metadados_da_tela.json  — um arquivo de DADO, com a origem de
  cada valor e a data do arquivo de onde veio.

  NAO escreve no banco. NAO mexe em HTML nenhum. NAO mexe no cards.json nem
  no base_unica.json. So LE e grava um arquivo novo.

  Quando o mesmo card aparece em mais de um HTML, vale o do arquivo MAIS
  NOVO que tiver o campo preenchido — e fica registrado de qual arquivo veio.
"""
import json, os, sys, io, glob, collections
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CAMPOS = ['com', 'age', 'inj', 'wfa', 'wfu', 'mst', 'mx', 'maxOvr']

ROTULO = {
    'com':    'estilos de jogo da IA',
    'age':    'idade',
    'inj':    'lesao',
    'wfa':    'pe ruim — precisao',
    'wfu':    'pe ruim — uso',
    'mst':    'mestre / familiaridade',
    'mx':     'maximo',
    'maxOvr': 'pontuacao maxima da tela',
}


def P(*a):
    print(*a)
    sys.stdout.flush()


# ---------------------------------------------------------------- onde estou
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

P('=' * 74)
P('  RESGATAR DA TELA  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 74)
P('')
P('  Oito campos do sistema so existem dentro do HTML ja gerado.')
P('  Este programa tira eles de la e grava num arquivo de dado.')
P('')
P('  NAO escreve no banco. NAO mexe em HTML. So le.')
P('')
P('  pasta ..................... %s' % CASA)


# ------------------------------------------------------- achar os HTML
CANDIDATOS = []
for padrao in ('encaixe/*.html', '*.html', '../*.html', '../../*.html'):
    for p in glob.glob(os.path.join(CASA, padrao)):
        rp = os.path.realpath(p)
        if rp not in CANDIDATOS:
            CANDIDATOS.append(rp)

P('  arquivos .html achados .... %d' % len(CANDIDATOS))


TETO_MB = 200      # arquivo maior que isto nao e tela nossa; nao vale abrir


def tira_o_D(caminho):
    """Devolve a lista do `const D` do HTML, ou None.

    ⛔ 16/08: a primeira versao decodificava o arquivo inteiro para texto antes
       de procurar. Com 125 arquivos, um deles de 38 MB, isso levava minutos.
       Agora a procura e feita nos BYTES, que e muito mais rapido, e so o
       pedaco que interessa vira texto.
    """
    try:
        tam = os.path.getsize(caminho)
    except OSError:
        return None
    if tam < 5000 or tam > TETO_MB * 1024 * 1024:
        return None
    try:
        with open(caminho, 'rb') as f:
            b = f.read()
    except Exception:
        return None
    i = b.find(b'const D=')
    if i < 0:
        i = b.find(b'const D =')
    if i < 0:
        return None
    jb = b.find(b'[', i)
    if jb < 0:
        return None
    s = b[jb:].decode('utf-8', 'replace')
    j = 0
    prof = 0
    k = j
    dentro_de_texto = False
    escapa = False
    n = len(s)
    while k < n:
        ch = s[k]
        if dentro_de_texto:
            if escapa:
                escapa = False
            elif ch == '\\':
                escapa = True
            elif ch == '"':
                dentro_de_texto = False
        else:
            if ch == '"':
                dentro_de_texto = True
            elif ch == '[':
                prof += 1
            elif ch == ']':
                prof -= 1
                if prof == 0:
                    break
        k += 1
    if prof != 0:
        return None
    try:
        return json.loads(s[j:k + 1])
    except Exception:
        return None


# ============================================================================
#  ⛔ QUEM E FONTE E QUEM E COPIA — a distincao mais importante deste programa
# ============================================================================
#  As CASCAS (encaixe_B_v164, encaixe_B_v171) sao as unicas que trouxeram esses
#  campos de fora. Tudo o mais e SAIDA que este sistema gerou, e o gerador
#  escreve `'com': m.get('com') or []` em TODO card — entao na saida todo card
#  tem o campo, vazio ou nao. Usar a saida como fonte faz card que NUNCA foi
#  coletado passar por "conferido, nao tem".
#
#  ⚠️ Esse aviso ja estava escrito dentro do motor_bonus.py desde 15/08, e eu
#     ignorei na primeira versao deste programa: ordenei tudo por data e deixei
#     a saida (que e a mais nova) mandar na casca. E o mesmo erro que a reforma
#     inteira existe para matar, cometido dentro do conserto dele.
#
#  Entao: a CASCA manda sempre. A saida so preenche o que a casca nao tem, e
#  fica marcada como copia propagada.
def e_casca(caminho):
    n = os.path.basename(caminho).lower()
    return n.startswith('encaixe_b_')


cascas, saidas = [], []
P('')
P('  lendo (so os que tem `const D` dentro contam):')
for n, c in enumerate(CANDIDATOS, 1):
    nome = os.path.basename(c)
    if len(nome) > 44:
        nome = nome[:41] + '...'
    print('   %4d/%d  %-46s' % (n, len(CANDIDATOS), nome), end='\r', flush=True)
    D = tira_o_D(c)
    if not D:
        continue
    (cascas if e_casca(c) else saidas).append((os.path.getmtime(c), c, D))
print(' ' * 70, end='\r')

if not cascas and not saidas:
    P('')
    P('  ⛔ nenhum HTML com `const D` foi encontrado. Nada foi gravado.')
    sys.exit(1)

cascas.sort(key=lambda t: -t[0])
saidas.sort(key=lambda t: -t[0])
lidos = cascas + saidas          # a casca primeiro, SEMPRE

P('')
P('  AS FONTES — a casca manda; a saida so preenche o que faltar')
P('')
P('  %-42s %10s %9s %8s' % ('arquivo', 'quando', 'registros', 'o que e'))
P('  ' + '-' * 72)
for grupo, rotulo in ((cascas, 'FONTE'), (saidas, 'copia')):
    for mt, c, D in grupo:
        nome = os.path.relpath(c, CASA)
        if len(nome) > 42:
            nome = '...' + nome[-39:]
        P('  %-42s %10s %9d %8s' % (
            nome, datetime.fromtimestamp(mt).strftime('%d/%m %H:%M'), len(D), rotulo))
if not cascas:
    P('')
    P('  ⛔ NENHUMA CASCA ORIGINAL FOI ENCONTRADA (encaixe_B_v164 / v171).')
    P('     Sem elas nao da para saber quem foi conferido e quem nunca foi')
    P('     coletado. Nao vou gravar em cima do que existe.')
    sys.exit(1)


# ------------------------------------------------------------------ o resgate
def vazio(v):
    return v is None or v == '' or v == [] or v == {}


dados = {}      # card -> {campo: valor}
origem = {}     # card -> {campo: {arquivo, quando, tipo}}
visto_na_casca = set()   # quem APARECE numa casca — com ou sem o campo preenchido

for mt, caminho, D in lidos:
    nome = os.path.relpath(caminho, CASA)
    quando = datetime.fromtimestamp(mt).strftime('%Y-%m-%d %H:%M')
    tipo = 'fonte' if e_casca(caminho) else 'copia propagada da saida'
    for r in D:
        if not isinstance(r, dict):
            continue
        cid = str(r.get('id') or '').split('@')[0]
        if not cid or cid == 'None':
            continue
        if tipo == 'fonte':
            visto_na_casca.add(cid)
        d = dados.setdefault(cid, {})
        o = origem.setdefault(cid, {})
        for campo in CAMPOS:
            if campo in d:
                continue            # a casca ja mandou, ou um arquivo mais novo
            v = r.get(campo)
            if vazio(v):
                continue
            d[campo] = v
            o[campo] = {'arquivo': nome, 'quando': quando, 'tipo': tipo}

# limpar card que nao trouxe nada
dados = {k: v for k, v in dados.items() if v}
origem = {k: v for k, v in origem.items() if v}

P('')
P('  O QUE FOI RESGATADO')
P('')
P('  %-26s %9s %12s %10s' % ('campo', 'cards', 'da FONTE', 'da copia'))
P('  ' + '-' * 62)
conta = {}
conta_fonte = {}
for campo in CAMPOS:
    n = sum(1 for v in dados.values() if campo in v)
    nf = sum(1 for c, o in origem.items() if o.get(campo, {}).get('tipo') == 'fonte')
    conta[campo] = n
    conta_fonte[campo] = nf
    P('  %-26s %9d %12d %10d' % (ROTULO[campo], n, nf, n - nf))
P('  ' + '-' * 62)
P('  %-26s %9d' % ('cards distintos', len(dados)))
P('')
P('  cards que aparecem numa CASCA ... %d' % len(visto_na_casca))
P('     ⛔ so para estes da para dizer "conferido, nao tem". Para o resto,')
P('        campo vazio e NAO SEI — ninguem puxou.')

# quantos estilos por card
qt = collections.Counter()
for cid, v in dados.items():
    qt[len(v.get('com') or [])] += 1
if qt:
    P('')
    P('  estilos de jogo da IA por card:')
    for n in sorted(qt):
        P('     %d estilo(s) .......... %d cards' % (n, qt[n]))


# ---------------------------------------------------------------- quanto falta
CAM_BASE = os.path.join('dados', 'base_unica.json')
total_base = None
if os.path.exists(CAM_BASE):
    try:
        B = json.load(open(CAM_BASE, encoding='utf-8'))
        total_base = len(B.get('cards') or [])
    except Exception:
        total_base = None

if total_base:
    P('')
    P('  CONTRA A BASE INTEIRA — %d cards' % total_base)
    P('')
    for campo in CAMPOS:
        falta = total_base - conta[campo]
        P('  %-26s tem %5d  ·  falta %5d' % (ROTULO[campo], conta[campo], falta))


# ------------------------------------------------------------------- gravar
destino = os.path.join(CASA, 'dados', 'metadados_da_tela.json')
os.makedirs(os.path.dirname(destino), exist_ok=True)

saida = {
    'o_que_e': ('os campos que so existiam dentro do HTML ja gerado, tirados de la '
                'e postos num arquivo de dado. Estilo de jogo da IA, idade, lesao, '
                'pe ruim (uso e precisao), mestre, maximo e pontuacao maxima da tela.'),
    'por_que_existe': ('em 16/08/2026 foi medido que estes oito campos nao estavam '
                       'em nenhum arquivo de dado, em nenhuma tabela do banco e em '
                       'nenhum programa de coleta — so no HTML de saida, copiado de '
                       'uma geracao para a proxima. O produto tinha virado a fonte.'),
    'gerado_por': 'resgatar_da_tela.py',
    'gerado_em': datetime.now().isoformat(),
    'regra': ('a CASCA (encaixe_B_v164 / v171) manda sempre — e a unica que trouxe '
              'esses campos de fora. A saida gerada so preenche o que a casca nao '
              'tem, e fica marcada como copia propagada. Usar a saida como fonte '
              'faria card nunca coletado passar por "conferido, nao tem".'),
    'arquivos_lidos': [
        {'arquivo': os.path.relpath(c, CASA),
         'quando': datetime.fromtimestamp(mt).strftime('%Y-%m-%d %H:%M'),
         'registros': len(D),
         'tipo': 'fonte' if e_casca(c) else 'copia propagada da saida'}
        for mt, c, D in lidos],
    'quantos_por_campo': {ROTULO[k]: conta[k] for k in CAMPOS},
    'quantos_por_campo_da_fonte': {ROTULO[k]: conta_fonte[k] for k in CAMPOS},
    'cards_distintos': len(dados),
    'cards_vistos_numa_casca': sorted(visto_na_casca),
    'o_que_e_visto_numa_casca': ('so para estes cards um campo vazio significa '
                                 '"conferido, nao tem". Para os outros, vazio e NAO SEI.'),
    'total_na_base': total_base,
    'dados': dados,
    'de_onde_veio_cada_valor': origem,
}

antes = None
if os.path.exists(destino):
    antes = destino + '.ANTES-' + datetime.now().strftime('%Y%m%d-%H%M%S')
    try:
        os.replace(destino, antes)
    except Exception:
        antes = None

with open(destino, 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False)

P('')
P('  gravei ................... dados/metadados_da_tela.json')
if antes:
    P('  o anterior virou ......... %s' % os.path.basename(antes))


# ------------------------------------------------------------- CONFERENCIA
P('')
P('  CONFERENCIA — lendo o arquivo de volta do disco')
V = json.load(open(destino, encoding='utf-8'))
volta = V.get('dados') or {}
erro = 0
if len(volta) != len(dados):
    P('  ⛔ gravei %d cards e li %d de volta.' % (len(dados), len(volta)))
    erro = 1
for campo in CAMPOS:
    n = sum(1 for v in volta.values() if campo in v)
    if n != conta[campo]:
        P('  ⛔ %s: contei %d, li de volta %d' % (ROTULO[campo], conta[campo], n))
        erro = 1
if erro:
    P('')
    P('  PAREI. O arquivo nao bate com o que foi contado.')
    sys.exit(1)

P('  ✅ os %d cards e os %d campos vieram de volta iguais' % (len(volta), len(CAMPOS)))
P('')
P('  ⛔ O QUE ISTO NAO RESOLVE:')
P('     o dado agora existe fora do HTML, mas continua sem FONTE — ninguem')
P('     coleta estilo de jogo da IA nem idade. Isso e o passo 5 da reforma.')
P('     ⚠️  Ate la, NAO APAGUE nenhum .html da pasta encaixe.')
P('')
P('  PRONTO E CONFERIDO.')
