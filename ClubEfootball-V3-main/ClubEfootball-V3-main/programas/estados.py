# -*- coding: utf-8 -*-
r"""
OS QUATRO ESTADOS DE CADA DADO — 16/08/2026

A ORDEM DO LUIS, 16/08 de madrugada, palavra dele:
  "Voce tem que colocar em todos os dados que a gente for coletar: quando nao tem, ele
   vai pro motor como valor zero, porque nao tem. So que voce tem que colocar QUE NAO
   TEM — nao que ele E zero."

OS QUATRO ESTADOS
  valor          puxou e veio um numero           o motor usa o numero      nao e pendencia
  zerado         puxou, o campo existe, e 0       o motor usa zero          nao e pendencia
  nao_se_aplica  conferiu: o campo NAO existe     o motor nao usa nada      nao e pendencia
  nao_sei        ninguem puxou ainda              zero, MARCADO             E PENDENCIA

======================================================================================
 O QUE MUDOU EM 16/08 A TARDE — A REGUA PASSOU A SE MONTAR SOZINHA
======================================================================================
  Ate hoje a lista de campos aqui embaixo era ESCRITA A MAO. Media 24 campos.
  A base tem 32 campos de dado. Os 8 que sobravam nao apareciam como buraco em lugar
  nenhum — nem no relatorio, nem no mapa da cascata, nem no NAO-SEI.txt.
  Foi por isso que a tela imprimiu "null anos" por dias sem ninguem ver: ninguem
  estava contando a idade.

  Agora o programa PERGUNTA A BASE quais campos existem. Campo novo entra sozinho na
  proxima coleta, e o relatorio avisa que entrou. Campo que sumiu da base tambem e
  avisado — e isso separa DOIS defeitos que antes viravam o mesmo numero:

     campo que existe e ninguem puxou ....... N buracos de coleta
     campo que NAO CHEGA na base ............ 1 conserto de esteira

  O estilo de jogo da IA era o segundo e vinha contado como o primeiro: 6.469 "nao sei"
  de um campo que o motor nunca pode usar, porque a chave nao existe em carta nenhuma.

O QUE ESTE PROGRAMA FAZ
  1. le o dados/base_unica.json
  2. descobre TODOS os campos que a base tem
  3. decide o estado de CADA CAMPO de CADA CARTA
  4. grava dados/estado_de_cada_campo.json  (arquivo NOVO, nao mexe no base_unica)
  5. sobe para a coluna estado_de_cada_campo da cards_base
  6. escreve RELATORIO-DOS-ESTADOS.txt e imprime o resumo curto

⛔ NAO MEXE no dados/base_unica.json. NAO mexe em pontuacao nenhuma. So acrescenta.
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

LINHAS = []
def P(*a):
    s = ' '.join(str(x) for x in a)
    LINHAS.append(s)
    print(s, flush=True)

def SO_NO_ARQUIVO(*a):
    LINHAS.append(' '.join(str(x) for x in a))

SO_CONTAR = (len(sys.argv) > 1 and sys.argv[1].lower().startswith('cont'))

# ============================================================================
# A REGRA — o que um campo VAZIO quer dizer, campo por campo
# ============================================================================
#   'fonte'   a chave dentro do fonte_de_cada_campo (se houver)
#   'vazio'   o que um valor vazio quer dizer quando A FONTE RESPONDEU:
#                'zerado'         -> zero de verdade
#                'nao_se_aplica'  -> o campo nao existe para essa carta
#                'nao_sei'        -> a fonte respondeu mas nao trouxe este campo
#
# ⛔ Na duvida, 'nao_sei'. Marcar como "nao se aplica" o que na verdade e buraco de
#    coleta e o pior erro possivel: some da lista de pendencia para sempre.
#
# ⚠️ Esta lista NAO precisa mais estar completa. Campo que a base tem e que nao esta
#    aqui entra sozinho com a regra segura ('nao_sei' quando vazio) e e ANUNCIADO no
#    relatorio. O que esta escrito aqui e so o que foge do padrao.
CAMPOS = {
    'nome':     {'fonte': None,      'vazio': 'nao_sei'},
    'ovr':      {'fonte': None,      'vazio': 'nao_sei'},
    'max_ovr':  {'fonte': None,      'vazio': 'nao_sei'},
    'pos':      {'fonte': None,      'vazio': 'nao_sei'},
    'np':       {'fonte': None,      'vazio': 'nao_sei'},
    'sec':      {'fonte': None,      'vazio': 'nao_se_aplica'},   # carta sem posicao secundaria existe
    'modelo':   {'fonte': 'modelo',  'vazio': 'nao_sei'},
    'orc':      {'fonte': 'orc',     'vazio': 'zerado'},          # orcamento 0 e legitimo: carta que nao evolui
    'levelCap': {'fonte': None,      'vazio': 'nao_sei'},
    'tier':     {'fonte': None,      'vazio': 'nao_sei'},
    'altura':   {'fonte': None,      'vazio': 'nao_sei'},
    'peso':     {'fonte': None,      'vazio': 'nao_sei'},
    'pe':       {'fonte': None,      'vazio': 'nao_sei'},
    'base':     {'fonte': 'base',    'vazio': 'nao_sei'},
    'fab':      {'fonte': 'fab',     'vazio': 'nao_se_aplica'},   # carta sem habilidade de fabrica existe
    'falta':    {'fonte': 'falta',   'vazio': 'nao_sei'},
    'raras':    {'fonte': None,      'vazio': 'nao_se_aplica'},   # 71% da base nao tem rara — e resposta
    'corpo':    {'fonte': 'corpo',   'vazio': 'nao_sei'},
    'pe_ruim':  {'fonte': 'pe_ruim', 'vazio': 'nao_sei'},
    'box':      {'fonte': 'box',     'vazio': 'nao_sei'},
    'dt':       {'fonte': None,      'vazio': 'nao_sei'},
    'vaga':     {'fonte': 'vaga',    'vazio': 'nao_sei'},
    'sl':       {'fonte': 'sl',      'vazio': 'nao_sei'},

    # ⚠️ 16/08 — O NOME DESTE CAMPO JA ERROU DUAS VEZES. Medido nos dois arquivos:
    #    'estilo_ia'  e o nome da COLUNA NO BANCO      -> 0 cartas na base
    #    'com'        e o nome da chave no HTML/resgate -> 0 cartas na base
    #    Nenhum dos dois chega ao dados/base_unica.json. Quem procurou por um so
    #    dos nomes concluiu coisa errada. Vale 'com', que e como o resto do
    #    sistema chama (fila_de_coleta.py, resgatar_da_tela.py, o gerador).
    # ⚠️ fonte 'com': o efHub responder com lista vazia e RESPOSTA — a carta nao
    #    tem estilo de jogo da IA. Vira nao_se_aplica, nao pendencia.
    'com':      {'fonte': 'com',     'vazio': 'nao_se_aplica'},
    'mst':      {'fonte': None,      'vazio': 'nao_sei'},
    'mx':       {'fonte': None,      'vazio': 'nao_sei'},
    'maxOvr':   {'fonte': None,      'vazio': 'nao_sei'},
}

# Onde o dado esta guardado quando o campo NAO CHEGA na base. Serve para o
# relatorio dizer "existe e nao chegou" em vez de "ninguem coletou".
ONDE_ESTA_GUARDADO = os.path.join('dados', 'metadados_da_tela.json')

# ============================================================================
# O QUE NAO E DADO DE CARTA — e por que
# ============================================================================
# ⛔ Esta lista existe para ser LIDA, nao para esconder campo. Cada linha tem o motivo.
#    Campo que nao estiver aqui NEM no CAMPOS entra na regua sozinho.
NAO_E_DADO = {
    'id':                    'a chave da carta',
    'fonte_de_cada_campo':   'diz de onde veio cada campo — e metadado, nao dado',
    'origem_ficha':          'de qual ficha a carta foi lida — metadado',
    'nm':                    'a soma do impeto por atributo — DERIVADO do impeto',
    'nx':                    'o teto do condicional — DERIVADO do impeto',
    'nmn':                   'o nome do impeto com o nivel — DERIVADO do impeto',
    'impeto_orfao':          'DERIVADO do impeto',
    'impeto_quantos':        'DERIVADO do impeto',
    'impeto_tem':            'DERIVADO do impeto',
    'impeto_nomes':          'DERIVADO do impeto',
    'impeto_condicional':    'DERIVADO do impeto',
    'impeto_efeito':         'DERIVADO do impeto',
    'impeto_soma':           'DERIVADO do impeto',
    'impeto_situacao':       'e o proprio estado do impeto — vira o campo impeto',
    'impeto_de_onde':        'DERIVADO do impeto',
    'impeto_nativo':         'DERIVADO do impeto',
    'vagas_livres':          'DERIVADO do impeto',
    'boostId':               'o id cru do impeto na ficha — o impeto ja tem estado proprio',
    'boostId2':              'o id cru do impeto na ficha — o impeto ja tem estado proprio',
}

# O IMPETO tem regra propria: a base JA RESPONDE no campo impeto_situacao.
IMPETO_SITUACAO = {
    'tem ímpeto':             'valor',
    'sem ímpeto e sem vaga':  'nao_se_aplica',   # carta velha: o jogo nao da. NAO e falta.
    'vaga livre — A COLETAR': 'nao_sei',         # ESTA sim e falta de verdade
}

FONTE_VAZIA = {'nao preenchido', 'nenhuma', '', None}
FONTE_CONFERIDA = 'CONFERIDO'


def esta_vazio(v):
    return v is None or v == '' or v == [] or v == {}


def estado_do_campo(card, campo, regra):
    """Devolve (estado, conferido)."""
    fontes = card.get('fonte_de_cada_campo') or {}
    fonte = fontes.get(regra['fonte']) if regra['fonte'] else None
    conferido = (fonte == FONTE_CONFERIDA)
    v = card.get(campo)

    # 1) tem valor de verdade
    if not esta_vazio(v):
        # zero explicito e ZERADO, nao "tem valor" — sao coisas diferentes
        if v == 0 or v == 0.0:
            return 'zerado', conferido
        return 'valor', conferido

    # 2) vazio. Quem respondeu?
    if regra['fonte'] is not None:
        if fonte in FONTE_VAZIA:
            return 'nao_sei', conferido          # ninguem puxou
        return regra['vazio'], conferido         # a fonte respondeu e veio vazio
    # 3) campo sem fonte declarada: vale a regra do campo
    return regra['vazio'], conferido


# ============================================================================
P('=' * 74)
P('  OS QUATRO ESTADOS DE CADA DADO  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
if SO_CONTAR:
    P('  MODO CONTAR — nao escreve nada, so mostra a conta')
P('=' * 74)

CAM = os.path.join('dados', 'base_unica.json')
if not os.path.exists(CAM):
    P('⛔ nao achei o %s. Nada foi feito.' % CAM)
    sys.exit(1)
B = json.load(open(CAM, encoding='utf-8'))
cards = B['cards']
P('')
P('base lida ................. %d registros' % len(cards))

# ============================================================================
# A REGUA SE MONTA — perguntando a base quais campos existem
# ============================================================================
existe_na_base = {}
for c in cards:
    for k in c:
        existe_na_base[k] = existe_na_base.get(k, 0) + 1

A_MAO = set(CAMPOS)
NASCERAM = sorted(k for k in existe_na_base if k not in CAMPOS and k not in NAO_E_DADO)
SUMIRAM = sorted(k for k in CAMPOS if k not in existe_na_base)

for k in NASCERAM:
    CAMPOS[k] = {'fonte': None, 'vazio': 'nao_sei', 'nasceu': 'achado na base em ' +
                 datetime.now().strftime('%d/%m/%Y')}

P('campos que a base tem ..... %d' % len(existe_na_base))
P('   dado de carta .......... %d   -> a regua mede todos' % len(CAMPOS))
P('   nao e dado de carta .... %d   -> chave, metadado e derivado do impeto' % len(NAO_E_DADO))
P('a regua escrita a mao tinha %d campos' % len(A_MAO))

# ---------------------------------------------------------------- a conta
estados = {}          # card_id -> {campo: estado}
conta = {}            # campo -> {estado: n}
conferidos = 0
for c in cards:
    cid = str(c['id'])
    e = {}
    for campo, regra in CAMPOS.items():
        st, conf = estado_do_campo(c, campo, regra)
        e[campo] = st
        if conf:
            e[campo + '__conferido'] = True
            conferidos += 1
        conta.setdefault(campo, {})[st] = conta.setdefault(campo, {}).get(st, 0) + 1
    # o impeto, pela situacao que a base ja calculou
    sit = c.get('impeto_situacao')
    st = IMPETO_SITUACAO.get(sit)
    if st is None:
        st = 'nao_sei'
    e['impeto'] = st
    conta.setdefault('impeto', {})[st] = conta.setdefault('impeto', {}).get(st, 0) + 1
    estados[cid] = e

# ---------------------------------------------------------------- o que a regua ganhou
if NASCERAM:
    P('')
    P('🆕 ENTRARAM NA REGUA AGORA — %d campos que a base tinha e ninguem media' % len(NASCERAM))
    P('')
    P('  %-12s %8s %10s' % ('campo', 'tem', 'NAO SEI'))
    P('  ' + '-' * 34)
    for k in NASCERAM:
        P('  %-12s %8s %10s' % (k, '{:,}'.format(existe_na_base[k]),
                                '{:,}'.format(conta.get(k, {}).get('nao_sei', 0))))
else:
    P('')
    P('nenhum campo novo — a regua ja cobria tudo que a base tem.')

# ---------------------------------------------------------------- o que nao chega
NAO_CHEGA = [k for k in SUMIRAM if k != 'impeto']

# quem ja tem o dado guardado fora da base
GUARDADO = {}
if os.path.exists(ONDE_ESTA_GUARDADO):
    try:
        _m = json.load(open(ONDE_ESTA_GUARDADO, encoding='utf-8')).get('dados') or {}
        for _x in _m.values():
            for _k, _v in _x.items():
                if not esta_vazio(_v):
                    GUARDADO[_k] = GUARDADO.get(_k, 0) + 1
    except Exception:
        GUARDADO = {}

if NAO_CHEGA:
    P('')
    P('🔴 CAMPOS QUE NAO CHEGAM NA BASE — %d' % len(NAO_CHEGA))
    P('   A chave nao existe em NENHUMA das %d cartas do dados/base_unica.json,' % len(cards))
    P('   que e o arquivo de onde os DOIS MOTORES leem. Coletar mais nao resolve.')
    P('')
    P('  %-10s %10s %14s' % ('campo', 'na base', 'ja resgatado'))
    P('  ' + '-' * 38)
    for k in NAO_CHEGA:
        P('  %-10s %10s %14s' % (k, '0', '{:,}'.format(GUARDADO.get(k, 0))))
    _tem = sum(GUARDADO.get(k, 0) for k in NAO_CHEGA)
    if _tem:
        P('')
        P('   ⛔ %s valores JA ESTAO no %s e nao entram na base.'
          % ('{:,}'.format(_tem), ONDE_ESTA_GUARDADO))
        P('      Nao e falta de coleta: e o unificar_base.py que nao le esse arquivo.')

# ---------------------------------------------------------------- a tabela
SO_NO_ARQUIVO('')
SO_NO_ARQUIVO('A CONTA — quantos de cada estado, por campo')
SO_NO_ARQUIVO('')
SO_NO_ARQUIVO('  %-12s %9s %9s %14s %10s %8s'
              % ('campo', 'valor', 'zerado', 'nao se aplica', 'NAO SEI', 'novo?'))
SO_NO_ARQUIVO('  ' + '-' * 68)
ordem = sorted(conta, key=lambda k: -conta[k].get('nao_sei', 0))
pendencia_total = 0
pendencia_real = 0
for campo in ordem:
    d = conta[campo]
    ns = d.get('nao_sei', 0)
    pendencia_total += ns
    if campo not in NAO_CHEGA:
        pendencia_real += ns
    SO_NO_ARQUIVO('  %-12s %9s %9s %14s %10s %8s'
                  % (campo, '{:,}'.format(d.get('valor', 0)), '{:,}'.format(d.get('zerado', 0)),
                     '{:,}'.format(d.get('nao_se_aplica', 0)), '{:,}'.format(ns),
                     'novo' if campo in NASCERAM else ('NAO CHEGA' if campo in NAO_CHEGA else '')))
SO_NO_ARQUIVO('  ' + '-' * 68)

P('')
P('A CONTA')
P('   pendencia de coleta de verdade ... %s' % '{:,}'.format(pendencia_real))
if NAO_CHEGA:
    P('   campo que nao chega na base ...... %s   (%s, e 1 conserto so)'
      % ('{:,}'.format(pendencia_total - pendencia_real), ', '.join(NAO_CHEGA)))
P('   somando os dois .................. %s' % '{:,}'.format(pendencia_total))
P('   conferido no jogo (inviolavel) ... %d campos' % conferidos)
P('')
P('   a tabela campo a campo esta no RELATORIO-DOS-ESTADOS.txt')

# ---------------------------------------------------------------- o impeto
SO_NO_ARQUIVO('')
SO_NO_ARQUIVO('O IMPETO — o caso que provou a necessidade disto tudo')
d = conta.get('impeto', {})
SO_NO_ARQUIVO('   tem impeto ....................... %s   -> valor          (nao e falta)' % '{:,}'.format(d.get('valor', 0)))
SO_NO_ARQUIVO('   sem impeto e sem vaga ............ %s   -> nao se aplica  (nao e falta)' % '{:,}'.format(d.get('nao_se_aplica', 0)))
SO_NO_ARQUIVO('   vaga livre, a coletar ............ %s   -> NAO SEI        (falta de verdade)' % '{:,}'.format(d.get('nao_sei', 0)))

if SO_CONTAR:
    open('RELATORIO-DOS-ESTADOS.txt', 'w', encoding='utf-8').write('\n'.join(LINHAS) + '\n')
    P('')
    P('=' * 74)
    P('  MODO CONTAR. Nada foi escrito no banco.')
    P('=' * 74)
    sys.exit(0)

# ---------------------------------------------------------------- o arquivo
SAI = os.path.join('dados', 'estado_de_cada_campo.json')
P('')
P('GRAVANDO')
if os.path.exists(SAI):
    import shutil
    b = SAI + '.ANTES-DE-' + datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy2(SAI, b)
    P('   backup ............ %s' % os.path.basename(b))
json.dump({'o_que_e': 'o estado de cada campo de cada carta — valor, zerado, nao_se_aplica, nao_sei',
           'gerado_em': datetime.now().isoformat(),
           'regra': 'claude/REGRA-1608-OS-QUATRO-ESTADOS-DE-CADA-DADO.md',
           'a_regua_se_monta_sozinha': True,
           'campos_medidos': sorted(CAMPOS) + ['impeto'],
           'campos_que_nasceram_hoje': NASCERAM,
           'campos_que_nao_chegam_na_base': NAO_CHEGA,
           'nao_e_dado_de_carta': NAO_E_DADO,
           'estados': estados},
          open(SAI, 'w', encoding='utf-8'), ensure_ascii=False)
P('   %s ... %.1f MB' % (SAI, os.path.getsize(SAI) / 1048576.0))

# ---------------------------------------------------------------- o banco
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
    P('   ⛔ nao achei a chave no config.txt. O arquivo foi gravado, o banco nao.')
    open('RELATORIO-DOS-ESTADOS.txt', 'w', encoding='utf-8').write('\n'.join(LINHAS) + '\n')
    sys.exit(1)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}

linhas = [{'card_id': cid, 'estado_de_cada_campo': e} for cid, e in estados.items()]
enviadas = 0
try:
    for i in range(0, len(linhas), 300):
        lote = linhas[i:i + 300]
        u = URL + '/rest/v1/cards_base?on_conflict=card_id'
        d = json.dumps(lote, ensure_ascii=False).encode('utf-8')
        r = urllib.request.Request(u, data=d, headers=dict(
            H, Prefer='resolution=merge-duplicates,return=minimal'), method='POST')
        with urllib.request.urlopen(r, timeout=180):
            enviadas += len(lote)
        print('   subindo ........... %d de %d' % (enviadas, len(linhas)), end='\r', flush=True)
    P('   subidas ........... %d de %d cartas       ' % (enviadas, len(linhas)))
except urllib.error.HTTPError as e:
    P('')
    P('   ⛔ ERRO %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]))
    P('   A coluna estado_de_cada_campo existe? Rode antes o CRIAR-ESTADOS-NO-SUPABASE.html')
    P('   O arquivo da pasta FOI gravado — so o banco que nao recebeu.')
    open('RELATORIO-DOS-ESTADOS.txt', 'w', encoding='utf-8').write('\n'.join(LINHAS) + '\n')
    sys.exit(1)

# ---------------------------------------------------------------- conferencia
P('')
P('CONFERENCIA — lendo de volta do banco')
try:
    r = urllib.request.Request(
        URL + '/rest/v1/cards_base?select=card_id&estado_de_cada_campo=not.is.null&limit=1',
        headers=dict(H, Prefer='count=exact'), method='HEAD')
    with urllib.request.urlopen(r, timeout=90) as f:
        cr = f.headers.get('Content-Range') or ''
        n = int(cr.split('/')[-1]) if '/' in cr else -1
    P('   cartas com estado no banco ... %s de %d' % ('{:,}'.format(n), len(linhas)))
    P('   ✅ bate' if n == len(linhas) else '   ⛔ NAO BATE')
except Exception as e:
    P('   nao consegui reler: %s' % e)

open('RELATORIO-DOS-ESTADOS.txt', 'w', encoding='utf-8').write('\n'.join(LINHAS) + '\n')

P('')
P('=' * 74)
P('  PRONTO. A regua agora se monta a partir da base — campo novo entra sozinho.')
P('  A tabela campo a campo: RELATORIO-DOS-ESTADOS.txt')
P('  Para so ver a conta, sem escrever:  ESTADOS.bat contar')
P('=' * 74)
