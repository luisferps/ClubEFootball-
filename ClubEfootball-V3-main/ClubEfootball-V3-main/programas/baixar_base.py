# -*- coding: utf-8 -*-
"""
BAIXAR A BASE UNICA DO SUPABASE — o banco manda de volta para a pasta.

⛔ POR QUE ESTE ARQUIVO FOI REESCRITO EM 16/08/2026, 17h30

   Ordem do Luis: "a base da transformacao e ler os dados de UM LUGAR UNICO,
   que e o banco de dados. Nao esquece disso nunca."

   Este e o programa que faz isso valer. So que ele estava com DOIS defeitos,
   os dois da mesma familia — lista escrita a mao que ficou para tras:

   1. TRAZIA 41 COLUNAS DE 89. Tudo que nao estava na lista era jogado fora
      em silencio. Medido em 16/08 14h26, perguntando ao banco:

         estilo_ia ............. 2.744 cartas no banco    -> jogado fora
         pe_ruim_precisao ...... 2.760                     -> jogado fora
         lesao ................. 2.706                     -> jogado fora
         maximo ................ 2.785                     -> jogado fora
         nota_maxima_tela ...... 2.785                     -> jogado fora
         mestre ................ 1.798                     -> jogado fora
         estado_de_cada_campo .. 6.469                     -> jogado fora
         a ficha inteira do impeto (9 colunas)             -> jogada fora

   2. APAGAVA O QUE NAO VEM DO BANCO. Ele so preservava os `tecnicos`. O
      dados/base_unica.json tem 24 nos no topo — molde, habilidades, bloqueio,
      corpo_chaves, nomes_habilidade, tecnicos_catalogo — e OS MOTORES LEEM
      TODOS ELES. Baixar apagava seis.

   AGORA ELE PERGUNTA AO BANCO quais colunas existem e traz TODAS. Coluna que
   ele nao conhece entra com o nome que o banco usa e sai ANUNCIADA na tela —
   nunca sumindo calada. E preserva todo no do topo que nao seja `cards`.

REGRA DA CASA: se o banco e a pasta divergirem, O BANCO GANHA.

SEGURANCA
   - backup datado antes de escrever (backups_base\\)
   - se o banco vier com menos cartas do que a pasta ja tem, ele PARA.
     Para forcar mesmo assim:  BAIXAR-BASE.bat forcar
   - troca atomica do arquivo: nao existe base pela metade

A chave sai do config.txt, lido na hora. Este arquivo nao guarda chave nenhuma.

COMO RODAR
    duplo clique em BAIXAR-BASE.bat
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
import json
import os
import sys
import io
import time
import urllib.request
import urllib.error

# ⛔ 16/08 15h30 — O `_MEU_STDOUT` NAO E ENFEITE, E O CONSERTO DE UM TOMBO.
#    O primeiro BAIXAR-BASE de verdade morreu aqui, com
#    "ValueError: I/O operation on closed file", e o motivo e sutil:
#
#      1. este arquivo embrulha o sys.stdout num TextIOWrapper
#      2. o backup_base.py, ao ser importado, embrulha DE NOVO e troca o
#         sys.stdout pelo dele
#      3. o nosso embrulho fica sem ninguem apontando para ele, o coletor de
#         lixo do Python o destroi — e ao morrer ele FECHA o buffer que os
#         dois estavam usando
#      4. o proximo print de qualquer um dos dois estoura
#
#    Guardar o embrulho numa variavel do modulo mantem ele vivo e o buffer
#    aberto. E a mesma familia do "o produto virou a fonte": alguem some com
#    a coisa que outro ainda estava usando.
_MEU_STDOUT = None
try:
    _MEU_STDOUT = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                   errors='replace', line_buffering=True)
    sys.stdout = _MEU_STDOUT
except Exception:
    pass


def diz(msg=''):
    """Um print que NUNCA derruba o programa. Se a saida morreu, segue calado —
    perder uma mensagem e ruim; perder a base por causa dela e inaceitavel.

    ⚠️ O `msg=''` tem dono: sem ele, `diz()` sem argumento (a linha em branco
    do relatorio) estourava com TypeError DEPOIS da base ja gravada. Aconteceu
    em 16/08 15h28. Um print de linha vazia nao pode derrubar nada."""
    try:
        print(msg, flush=True)
    except Exception:
        try:
            sys.stderr.write(str(msg) + '\n')
        except Exception:
            pass

os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

FORCAR = any(a.lower().startswith('forc') for a in sys.argv[1:])
SO_CONFERIR = any(a.lower().startswith('confer') for a in sys.argv[1:])


def pausa(msg='Enter para fechar...'):
    """Nao trava quando o .bat chama sem teclado (o ALIMENTAR-TUDO chama assim)."""
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


BASE = os.path.join('dados', 'base_unica.json')
TABELA = 'cards_base'
PAGINA = 1000        # o PostgREST limita a resposta; puxo de mil em mil

if not os.path.exists('config.txt'):
    print('Falta o config.txt (com SUPABASE_URL e SUPABASE_KEY).')
    pausa()
    sys.exit(1)

cfg = {}
for linha in open('config.txt', encoding='utf-8'):
    linha = linha.strip()
    if linha and not linha.startswith('#') and '=' in linha:
        k, v = linha.split('=', 1)
        cfg[k.strip()] = v.strip()

URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')
if not URL or not KEY or 'COLE_AQUI' in KEY:
    print('O config.txt esta sem a URL ou a chave do Supabase.')
    pausa()
    sys.exit(1)


def pagina(de, ate):
    """Uma pagina da tabela. `Range` e como o PostgREST pagina."""
    req = urllib.request.Request(
        '%s/rest/v1/%s?select=*&order=card_id' % (URL, TABELA),
        headers={'apikey': KEY,
                 'Authorization': 'Bearer ' + KEY,
                 'Range-Unit': 'items',
                 'Range': '%d-%d' % (de, ate)})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode('utf-8'))


# ---------------------------------------------------------------------------
# A VOLTA: coluna do banco -> chave do JSON que o motor entende.
# Onde o nome e igual nos dois lados nao precisa estar aqui: o programa passa
# direto. Isto e so a lista dos que MUDAM DE NOME.
# ---------------------------------------------------------------------------
DE_VOLTA = {
    'card_id': 'id', 'posicao': 'pos', 'posicao_nativa': 'np',
    'posicoes_sec': 'sec', 'estilo_de_jogo': 'modelo', 'orcamento': 'orc',
    'level_cap': 'levelCap', 'atributos_base': 'base',
    'impeto_efeito': 'nm', 'impeto_nomes': 'nmn',
    'impeto_delta_condicional': 'nx',
    'impeto_nomes_decompostos': 'impeto_nomes',
    'impeto_efeito_legivel': 'impeto_efeito',
    'vagas_impeto': 'sl', 'vaga_detalhe': 'vaga',
    'hab_nativas': 'fab', 'hab_faltantes': 'falta', 'hab_raras': 'raras',
    'data_lancamento': 'dt', 'boost_id': 'boostId', 'boost_id2': 'boostId2',
    # ⛔ 18/08 — a etiqueta do card (o TIPO do card e a partida que ele
    #    comemora). Sai do campo `box`, onde nunca devia ter estado. `box` desce
    #    com o proprio nome, entao nao precisa de linha aqui.
    'etiqueta_do_card': 'etiqueta_do_card',
    'idade': 'age', 'pe_ruim_uso': 'wfu', 'cap_desbloq': 'capdesc',
    # ⛔ 16/08 17h35: esta faltava. Sem ela o banco descia `condicao` e a pasta
    #    ficava com `cond` — o MESMO campo em duas chaves, e o conferir
    #    acusava "so a pasta tem cond, 136 cartas". Era eu que tinha perdido.
    'condicao': 'cond',
    # os oito que so existiam dentro do HTML (achados em 16/08)
    'estilo_ia': 'com', 'maximo': 'mx', 'mestre': 'mst',
    'pontuacao_maxima_da_casca': 'maxOvr',
    # ⛔ 16/08 15h20 — `nota_maxima_tela` NAO desce como `maxOvr`, e nao e
    #    detalhe. Medido: os dois numeros DISCORDAM em 2.444 de 2.785 cards
    #    (33185: a pasta diz 82,51 e o banco diz 81,0).
    #
    #    A causa: a coluna tem DOIS DONOS escrevendo coisas diferentes.
    #      entrar_com_o_efhub.py  ->  nota_maxima_tela = overallRating do efHub
    #      metadados_da_tela.json ->  maxOvr           = o que a TELA mostrava
    #
    #    Sao duas medidas, nao uma repetida. Se descesse como `maxOvr`, o
    #    numero do efHub apagaria o da tela em 2.444 cards e ninguem veria.
    #    Por isso ele desce com o nome do banco, ao lado. Item 22 do
    #    CONSERTOS-PENDENTES: falta o Luis decidir qual e a de verdade.
}

# ---------------------------------------------------------------------------
# OS GEMEOS — duas colunas para a MESMA coisa, achadas em 16/08 14h26
# ---------------------------------------------------------------------------
# ⛔ Nao apago nenhuma: a regra da casa e ACRESCENTA ANTES DE TIRAR. Aqui eu
#    so escolho, por carta, a que tem resposta — preferindo a mais cheia.
#    (ganhadora, perdedora, chave no arquivo, o que e)
GEMEOS = [
    ('lesao',            'resist_lesao', 'inj', 'resistencia a lesao'),
    ('pe_ruim_precisao', 'pe_ruim_prec', 'wfa', 'precisao do pe ruim'),
]

# ---------------------------------------------------------------------------
# O QUE NAO DESCE — cada linha com o motivo escrito
# ---------------------------------------------------------------------------
IGNORAR = {
    'atualizado_em':         'carimbo de hora do banco, nao e dado da carta',
    'metadado_tela_de_onde': 'procedencia do resgate da tela',
}
# ⛔ 19/08 — `visto_na_casca` NAO ENTRA AQUI. NUNCA. Ja entrou duas vezes.
#    Ele parece procedencia, mas nao e: o motor_bonus PARA sem ele. Sem esse
#    campo nao da para separar "conferi e a carta NAO tem estilo de IA" de
#    "nunca perguntei" — e os dois viram bonus diferente. Descartar ele aqui
#    quebra a corrente inteira do ATUALIZAR-O-ENCAIXE-AGORA, e o aviso que
#    aparece manda rodar o BAIXAR-BASE, que e justamente quem estava jogando
#    fora. Se voce esta lendo isto pensando em por ele de volta: nao ponha.

# ---------------------------------------------------------------------------
# O QUE E OBRIGATORIO DESCER — a trava que impede o defeito acima de voltar
# ---------------------------------------------------------------------------
# Se o banco TEM a coluna e ela nao chegou no arquivo, este programa para e
# diz o nome. Nada de descobrir isso tres programas depois, no meio da corrente.
OBRIGATORIAS = {
    'visto_na_casca': 'o motor_bonus para sem ele',
}
# as 26 colunas atr_* sao o atributos_base explodido; o motor le a LISTA
PREFIXO_IGNORADO = ('atr_',)


def deve_ignorar(coluna):
    if coluna in IGNORAR:
        return True
    return coluna.startswith(PREFIXO_IGNORADO)


print('=' * 70)
print('  BAIXAR A BASE UNICA <- Supabase, tabela %s' % TABELA)
print('=' * 70)
if SO_CONFERIR:
    print('  MODO CONFERIR — baixa, compara e NAO ESCREVE NADA.')
    print('  Serve para ver quem esta na frente antes de virar a chave.')
else:
    print('Regra: se o banco e a pasta divergirem, O BANCO GANHA.')
print('-' * 70)

linhas = []
de = 0
while True:
    try:
        pedaco = pagina(de, de + PAGINA - 1)
    except urllib.error.HTTPError as erro:
        det = ''
        try:
            det = erro.read().decode('utf-8', 'ignore')[:300]
        except Exception:
            pass
        print('O banco recusou: HTTP %s %s' % (erro.code, det))
        print('Se disser que a tabela nao existe, rode antes o sql/20-cards-base.sql.')
        pausa()
        sys.exit(1)
    except Exception as erro:
        print('Nao consegui falar com o banco: %s' % erro)
        pausa()
        sys.exit(1)

    if not pedaco:
        break
    linhas.extend(pedaco)
    print('   baixados %d cards...' % len(linhas))
    if len(pedaco) < PAGINA:
        break
    de += PAGINA

if not linhas:
    print()
    print('A tabela %s esta VAZIA. Nao vou apagar a base boa da pasta.' % TABELA)
    print('Rode o SUBIR-BASE.bat primeiro, ou confira a tabela no painel.')
    pausa()
    sys.exit(1)

# ---- as colunas que o banco realmente tem, perguntadas a ele ---------------
COLUNAS = sorted(linhas[0].keys())
GEMEA_PERDEDORA = set(g[1] for g in GEMEOS)
GEMEA_GANHADORA = set(g[0] for g in GEMEOS)

novas = [c for c in COLUNAS
         if c not in DE_VOLTA and not deve_ignorar(c)
         and c not in GEMEA_PERDEDORA and c not in GEMEA_GANHADORA]
ignoradas = [c for c in COLUNAS if deve_ignorar(c)]

print('-' * 70)
print('  colunas no banco .......... %d' % len(COLUNAS))
print('  com nome trocado .......... %d' % len([c for c in DE_VOLTA if c in COLUNAS]))
print('  descem com o nome do banco  %d' % len(novas))
print('  nao descem ................ %d   (%d sao atr_*, o atributos_base explodido)'
      % (len(ignoradas), len([c for c in ignoradas if c.startswith('atr_')])))
for c in sorted(IGNORAR):
    if c in COLUNAS:
        print('     %-24s %s' % (c, IGNORAR[c]))
if novas:
    print('  ⚠️ colunas que eu nao conhecia — descem com o nome do banco:')
    for c in novas:
        print('     %s' % c)


def card_do_banco(linha):
    c = {}
    for coluna, valor in linha.items():
        if deve_ignorar(coluna):
            continue
        if coluna in GEMEA_PERDEDORA or coluna in GEMEA_GANHADORA:
            continue
        if valor is None:
            continue
        c[DE_VOLTA.get(coluna, coluna)] = valor
    # os gemeos: a que tem resposta ganha, preferindo a mais cheia
    for ganha, perde, chave, _oque in GEMEOS:
        v = linha.get(ganha)
        if v is None:
            v = linha.get(perde)
        if v is not None:
            c[chave] = v
    # max_ovr volta como texto no PostgREST (numeric). O motor espera numero.
    if isinstance(c.get('max_ovr'), str):
        try:
            c['max_ovr'] = float(c['max_ovr'])
        except Exception:
            c.pop('max_ovr', None)
    return c


# ---- o que NAO vem do banco e nao pode ser perdido -------------------------
# ⛔ 16/08: aqui morava o segundo defeito. O programa preservava so os
#    `tecnicos` e apagava molde, habilidades, bloqueio, corpo_chaves,
#    nomes_habilidade e tecnicos_catalogo — que OS MOTORES LEEM.
#    Agora preserva TODO no do topo que nao seja `cards`.
antiga = {}
if os.path.exists(BASE):
    try:
        with open(BASE, 'r', encoding='utf-8') as f:
            antiga = json.load(f)
    except Exception as erro:
        print('   (nao consegui ler a base anterior: %s)' % erro)
        antiga = {}

quantas_antes = len(antiga.get('cards') or [])
if quantas_antes and len(linhas) < quantas_antes and not FORCAR:
    print()
    print('=' * 70)
    print('  ⛔ PAREI. O banco tem MENOS cartas do que a pasta.')
    print('     no banco ... %d' % len(linhas))
    print('     na pasta ... %d' % quantas_antes)
    print()
    print('  Baixar assim apagaria %d cartas. Confira a tabela antes.' % (quantas_antes - len(linhas)))
    print('  Se for de proposito:   BAIXAR-BASE.bat forcar')
    print('=' * 70)
    pausa()
    sys.exit(1)

preservados = [k for k in antiga if k not in
               ('cards', 'gerado_por', 'o_que_e', 'total_cards', 'baixado_em')]

# ===========================================================================
#  MODO CONFERIR — quem esta na frente, campo por campo E valor por valor
# ===========================================================================
if SO_CONFERIR:
    novos = [card_do_banco(l) for l in linhas]
    do_banco = {str(c.get('id')): c for c in novos}
    da_pasta = {str(c.get('id')): c for c in (antiga.get('cards') or [])}

    def cheio(v):
        return not (v is None or v == '' or v == [] or v == {})

    so_banco, so_pasta, difere = {}, {}, {}
    exemplo = {}
    for cid, p in da_pasta.items():
        b = do_banco.get(cid)
        if b is None:
            continue
        for k in set(p) | set(b):
            tb, tp = cheio(b.get(k)), cheio(p.get(k))
            if tb and not tp:
                so_banco[k] = so_banco.get(k, 0) + 1
            elif tp and not tb:
                so_pasta[k] = so_pasta.get(k, 0) + 1
            elif tb and tp and b.get(k) != p.get(k):
                difere[k] = difere.get(k, 0) + 1
                if k not in exemplo:
                    exemplo[k] = (cid, p.get(k), b.get(k))

    print()
    print('=' * 70)
    print('  QUEM ESTA NA FRENTE')
    print('=' * 70)
    print('  cartas no banco ... %s' % '{:,}'.format(len(do_banco)))
    print('  cartas na pasta ... %s' % '{:,}'.format(len(da_pasta)))
    fora = [c for c in da_pasta if c not in do_banco]
    if fora:
        print('  ⛔ na pasta e NAO no banco: %d   (baixar apagaria)' % len(fora))
        print('     %s' % ', '.join(fora[:8]))

    print()
    print('  1) SO O BANCO TEM  — o que voce GANHA ao baixar')
    if so_banco:
        for k in sorted(so_banco, key=lambda x: -so_banco[x]):
            print('     %-24s %s cartas' % (k, '{:,}'.format(so_banco[k])))
    else:
        print('     nenhum')

    print()
    print('  2) SO A PASTA TEM  — o que voce PERDE ao baixar')
    if so_pasta:
        for k in sorted(so_pasta, key=lambda x: -so_pasta[x]):
            print('     ⛔ %-22s %s cartas' % (k, '{:,}'.format(so_pasta[k])))
        print()
        print('     Rode o SUBIR-BASE.bat ANTES de baixar, ou estes campos somem.')
    else:
        print('     ✅ nenhum. Baixar nao perde campo nenhum.')

    print()
    print('  3) OS DOIS TEM, COM VALOR DIFERENTE — o banco sobrescreve')
    if difere:
        for k in sorted(difere, key=lambda x: -difere[x])[:25]:
            cid, vp, vb = exemplo[k]
            sp = json.dumps(vp, ensure_ascii=False)[:34]
            sb = json.dumps(vb, ensure_ascii=False)[:34]
            print('     %-22s %6s cartas   %s: pasta %s -> banco %s'
                  % (k, '{:,}'.format(difere[k]), cid, sp, sb))
        print()
        print('     Se a pasta rodou o unificador depois do ultimo SUBIR-BASE,')
        print('     a pasta e que esta na frente e baixar VOLTA ATRAS.')
    else:
        print('     ✅ nenhum. Os dois concordam em tudo que ambos tem.')

    print()
    print('=' * 70)
    print('  NADA FOI ESCRITO. A base da pasta esta intacta.')
    print('=' * 70)
    pausa()
    sys.exit(0)

# ---- backup ANTES de escrever ---------------------------------------------
# ⛔ A COPIA PROPRIA VEM PRIMEIRO, e nao depende de programa nenhum.
#    Antes o backup era delegado ao backup_base.py; quando ele estourou, o
#    proprio aviso de erro estourou junto e o programa morreu. Agora a copia
#    que garante o retorno e feita aqui, com shutil, sem importar ninguem.
import shutil
copia = None
if os.path.exists(BASE):
    try:
        copia = BASE + '.ANTES-DE-BAIXAR-' + time.strftime('%Y%m%d-%H%M%S')
        shutil.copy2(BASE, copia)
        diz('   copia de seguranca ... %s' % os.path.basename(copia))
    except Exception as erro:
        diz('   ⛔ PAREI: nao consegui copiar a base antes de trocar (%s)' % erro)
        pausa()
        sys.exit(1)

# o backup datado da pasta e um extra. Se falhar, nao para nada.
try:
    import backup_base
    backup_base.uma_rodada()
except Exception as erro:
    diz('   (o backup_base.py nao rodou: %s — a copia acima ja garante a volta)'
        % str(erro)[:80])

cards = [card_do_banco(l) for l in linhas]

# ---- A TRAVA DAS OBRIGATORIAS — antes de escrever, nao depois --------------
# ⛔ 19/08 — o `visto_na_casca` ja foi descartado aqui duas vezes, e as duas o
#    erro so apareceu tres programas adiante, no motor_bonus, com uma mensagem
#    mandando rodar justamente este programa. Agora ele para AQUI, com o nome
#    do campo, e nao chega a sobrescrever a base boa da pasta.
_faltou = []
for _col, _porque in OBRIGATORIAS.items():
    _tem_no_banco = any((l.get(_col) not in (None, '', [], {})) for l in linhas)
    _nome = DE_VOLTA.get(_col, _col)
    _chegou = sum(1 for c in cards if c.get(_nome) not in (None, '', [], {}))
    if _tem_no_banco and not _chegou:
        _faltou.append((_col, _porque))
if _faltou:
    print()
    print('=' * 70)
    print('  PAREI ANTES DE ESCREVER — campo obrigatorio nao desceu')
    print('=' * 70)
    for _col, _porque in _faltou:
        print('   %-24s %s' % (_col, _porque))
    print()
    print('   O banco TEM esse campo, mas ele nao chegou no arquivo.')
    print('   Quase sempre a causa e ele ter entrado no IGNORAR la em cima.')
    print('   A base da pasta NAO foi tocada — o que estava bom continua bom.')
    print()
    pausa()
    sys.exit(1)

saida = {
    'gerado_por': 'baixar_base.py',
    'o_que_e': 'Base unica baixada da tabela cards_base do Supabase. O BANCO GANHA.',
    'baixado_em': time.strftime('%Y-%m-%d %H:%M:%S'),
    'total_cards': len(cards),
}
for k in preservados:
    saida[k] = antiga[k]
saida['cards'] = cards

os.makedirs(os.path.dirname(BASE), exist_ok=True)
temporario = BASE + '.tmp'
with open(temporario, 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False)
os.replace(temporario, BASE)   # troca atomica: nao existe arquivo pela metade

# ---- a conferencia: o que entrou, campo por campo --------------------------
def conta_campos(lista):
    d = {}
    for c in lista:
        for k, v in c.items():
            if v is None or v == '' or v == [] or v == {}:
                continue
            d[k] = d.get(k, 0) + 1
    return d

depois = conta_campos(cards)
antes = conta_campos(antiga.get('cards') or [])

diz('-' * 70)
diz('Gravado: %s' % BASE)
diz('   %d cards vindos do banco' % len(cards))
diz('   %d campos por card' % len(depois))
diz('   nos do topo preservados: %s' % (', '.join(preservados) or 'nenhum'))

ganhou = [(k, antes.get(k, 0), depois[k]) for k in depois if depois[k] > antes.get(k, 0)]
perdeu = [(k, antes[k], depois.get(k, 0)) for k in antes if depois.get(k, 0) < antes[k]]

if ganhou:
    diz()
    diz('   O QUE O BANCO TROUXE A MAIS')
    for k, a, d in sorted(ganhou, key=lambda x: -(x[2] - x[1]))[:20]:
        diz('      %-22s %8s -> %8s' % (k, '{:,}'.format(a), '{:,}'.format(d)))
if perdeu:
    diz()
    diz('   ⛔ O QUE A PASTA TINHA E O BANCO NAO TEM')
    for k, a, d in sorted(perdeu, key=lambda x: -(x[1] - x[2]))[:20]:
        diz('      %-22s %8s -> %8s' % (k, '{:,}'.format(a), '{:,}'.format(d)))
    diz()
    diz('   Isto nao e sempre erro — pode ser campo que o SUBIR-BASE ainda')
    diz('   nao manda. A base anterior esta em backups_base\\.')
else:
    diz()
    diz('   ✅ nenhum campo perdeu carta na descida.')

diz()
diz('Backup da versao anterior: pasta backups_base\\')
pausa()
