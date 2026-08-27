# -*- coding: utf-8 -*-
"""
A FILA DE COLETA — passo 5 da reforma, primeira metade. 16/08/2026

O QUE FALTAVA:
  O sistema tinha o MAPA do que falta, mas nao tinha a FILA — a lista, por
  campo, de quais cartas perguntar a qual fonte, em que ordem. Sem isso o
  motor de atualizacao (o braco que busca) nao tem o que seguir.

O QUE ESTE PROGRAMA FAZ:
  1. Descobre TODOS os campos que a base realmente tem — nao le lista
     escrita a mao. Campo novo aparece sozinho.
  2. Para cada campo, decide o estado de cada carta pelas quatro regras:
     valor · zerado · nao se aplica · NAO SEI.
  3. Para cada "NAO SEI", diz QUEM perguntar, na ordem de precedencia.
  4. Separa em duas filas: a que roda sozinha e a que so anda com o
     navegador aberto.
  5. Guarda desde quando cada campo esta em "nao sei", para o prazo.

⛔ NAO coleta nada. NAO escreve no banco. NAO mexe em nota nenhuma.
   So le, decide e grava a fila.

⛔ A REGRA QUE NASCEU DO ERRO DE 16/08:
   A regua dos quatro estados foi montada com uma LISTA ESCRITA A MAO de 25
   campos. A base tinha mais. Idade, lesao, forma, condicao, wfu, wfa e
   capdesc ficaram de fora, e por isso a tela imprimiu "null anos" por dias
   sem nenhum relatorio apontar. Aqui a lista sai da BASE, e campo sem regra
   declarada NAO E IGNORADO — ele aparece em vermelho e o programa cobra.
"""
import json, os, sys, io, collections
from datetime import datetime, timedelta

# ⛔ 18/08 — A REGRA DA BOX MORA EM ClubEfootball\programas\regras_do_card.py,
#    E SO LA. "Esse e o problema de ter tanto arquivo" (Luis, 18/08). Este
#    programa NAO tem copia da resposta para "isto e box?" — ele pergunta.
#    ⛔ E mora no ClubEfootball, nao na raiz: a raiz e legado e vai deixar de
#       existir. Coisa nova vai no ClubEfootball (regra do Luis, 17/08).
import sys as _sys, os as _os
_AQUI = _os.path.dirname(_os.path.abspath(__file__))
for _d in (_AQUI,
           _os.path.join(_os.getcwd(), 'ClubEfootball', 'programas'),
           _os.path.join(_os.path.dirname(_AQUI), 'programas'),
           _os.path.join(_AQUI, 'ClubEfootball', 'programas')):
    if _os.path.isdir(_d) and _d not in _sys.path:
        _sys.path.insert(0, _d)
import regras_do_card as REGRA


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def P(*a):
    print(*a, flush=True)


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

PRAZO_DIAS = 2      # ordem do Luis: "nao sei" ha mais de dois dias e vermelho

# ============================================================================
#  AS FONTES — como cada uma anda
# ============================================================================
# ⛔ 16/08 03h20 — CORRIGIDO CONTRA A FONTE, nao suposto.
#    Eu tinha posto efHub, efscout e efootballdb como "roda sozinha". Errado.
#    Esta escrito no COLETAR-EFHUB-PELO-CONSOLE.md (10/08) e repetido dentro do
#    coletar_so_os_furados.py (14/08):
#
#      "A API do efHub devolve 403 fora do Chrome logado."
#      "O efScout entrega o banco inteiro num .bin — nao da para pedir por id."
#
#    Quem roda sozinho de verdade e SO o efootballdb. E ele responde box, data
#    e vaga NUMA VISITA SO.
FONTES = {
    'efootballdb': ('sozinha',   'a UNICA que responde fora do navegador. Uma visita traz box, data e vaga'),
    'efhub':       ('navegador', '⛔ 403 fora do Chrome desde 10/08. So pelo Console (F12)'),
    'efscout':     ('lote',      'nao atende por carta: entrega o banco inteiro num .bin'),
    'efootbase':   ('navegador', 'SO anda com o navegador aberto, colando o script'),
    'tela':        ('resgate',   'o HTML antigo — unica fonte de idade e estilo da IA'),
    'jogo':        ('luis',      'so o Luis, olhando o videogame'),
    'derivado':    ('local',     'sai de outro campo, aqui dentro. Nao se pede a ninguem'),
}

# ============================================================================
#  QUEM RESPONDE CADA CAMPO — a ordem de precedencia
# ============================================================================
#  MEDIDO onde deu para medir: a coluna `fonte_de_cada_campo` da base diz quem
#  ja respondeu de fato, carta por carta. Onde ela nao diz, esta DECLARADO e
#  marcado como tal — para ninguem confundir suposicao com medicao.
#
#  ('regra do vazio', [fontes em ordem], 'medido'|'declarado', 'observacao')
CAMPOS = {
    # --- identidade: se falta, e buraco grave -------------------------------
    'nome':     ('nao_sei',       ['efhub'],                'medido',    None),
    'ovr':      ('nao_sei',       ['efhub'],                'medido',    None),
    'pos':      ('nao_sei',       ['efhub'],                'medido',    None),
    'np':       ('nao_sei',       ['efhub'],                'medido',    None),
    'sec':      ('nao_se_aplica', ['efhub'],                'declarado', 'carta sem posicao secundaria existe'),
    'modelo':   ('nao_sei',       ['efhub'],                'medido',    None),
    'altura':   ('nao_sei',       ['efhub'],                'medido',    None),
    'peso':     ('nao_sei',       ['efhub'],                'medido',    None),
    'pe':       ('nao_sei',       ['efhub'],                'medido',    None),

    # --- numeros do jogo ----------------------------------------------------
    'max_ovr':  ('nao_sei',       ['efhub'],                'medido',    None),
    'tier':     ('nao_sei',       ['efhub', 'efootbase'],   'declarado', 'a regra de S+/S nao sai do OVR — nao e derivavel'),
    'levelCap': ('nao_sei',       ['efhub', 'efootbase'],   'declarado', 'ate que nivel a carta sobe'),
    'orc':      ('zerado',        ['efhub'],                'medido',    'orcamento 0 e legitimo: carta que nao evolui'),
    'base':     ('nao_sei',       ['efhub'],                'medido',    None),
    'votos':    ('nao_se_aplica', ['efhub'],                'declarado', 'nem toda carta tem voto'),

    # --- habilidade ---------------------------------------------------------
    'fab':      ('nao_se_aplica', ['efhub'],                'medido',    'carta sem habilidade de fabrica existe'),
    'falta':    ('nao_sei',       ['derivado'],             'medido',    'sai do pool da funcao — falta_por_card.json'),
    'raras':    ('nao_se_aplica', ['derivado'],             'medido',    '71% da base nao tem rara, e isso e resposta'),

    # --- impeto -------------------------------------------------------------
    'impeto':   ('nao_sei',       ['efootbase', 'efhub', 'efscout', 'jogo'], 'medido', 'a situacao ja esta calculada em impeto_situacao'),
    'nm':       ('nao_sei',       ['efootbase', 'efscout', 'jogo'], 'medido', 'os nomes do impeto de fabrica'),
    'nx':       ('nao_sei',       ['efootbase'],            'declarado', 'o teto de cada atributo de impeto'),
    'nmn':      ('nao_sei',       ['derivado'],             'declarado', 'o nome calculado, sai do nm contra o CAT'),
    'sl':       ('nao_sei',       ['efhub', 'efootbase'],   'medido',    'as vagas de impeto'),
    # ⛔ o efootballdb responde box, data e vaga NUMA VISITA SO, e sem navegador.
    #    Por isso ele vem primeiro nos tres — e a unica coleta que anda sozinha.
    'vaga':     ('nao_sei',       ['efootballdb', 'efootbase', 'efscout'], 'medido', 'a ficha do efootballdb traz os tres boosters'),
    'vagas_livres': ('nao_sei',   ['derivado'],             'declarado', 'sai do sl menos o que ja esta usado'),

    # --- data e box ---------------------------------------------------------
    # ⛔ 18/08 — QUEM RESPONDE BOX E O efHUB, NAO O efootballdb.
    #    O `variation_details.name` do efootballdb e a etiqueta da carta, nao a
    #    box. Pedir box a ele so repoe o erro: 598 prateleiras de um card so.
    #    O efHub LISTA as box e as cartas de cada uma; o vigia le essa lista.
    'box':      ('nao_sei',       [REGRA.DONO_DO_CAMPO['box']], 'medido', 'a lista de box do efHub (/api/public/packs)'),
    'etiqueta_do_card': ('nao_se_aplica', [REGRA.DONO_DO_CAMPO['etiqueta_do_card']], 'medido', 'variation_details.name — o tipo do card e a partida que ele comemora'),
    'dt':       ('nao_sei',       ['efootballdb', 'efootbase', 'efhub'], 'medido', 'variation_details.release_date'),

    # --- corpo e pe ruim ----------------------------------------------------
    'corpo':    ('nao_sei',       ['efhub'],                'medido',    'as 12 medidas'),
    'pe_ruim':  ('nao_sei',       ['efhub'],                'medido',    None),

    # --- os que so existiam dentro do HTML ----------------------------------
    #     ⚠️ achados em 16/08. Nenhum tinha regra ate hoje. A chave do estilo de
    #     jogo da IA e `com` — no banco a coluna se chama estilo_ia, mas na base
    #     e no HTML a chave e `com`. Quem procurasse por "estilo_ia" na base nao
    #     acharia nada e concluiria que o campo nao existe. (Eu conclui, as 02h25.)
    # ⛔ 16/08 09h — MEDIDO NA FONTE, pelo Chrome: a ficha do efHub responde
    #    `comSkills` (o estilo de jogo da IA), `age`, `injuryResistance`,
    #    `weakFootUsage`, `weakFootAccuracy`, `form`, `condition`, `levelCap` e
    #    `playerModel`. Eu tinha escrito que estes campos NAO TINHAM FONTE.
    #    Tinham. A porta e o navegador — /api/public/players/<nosso_id> devolve
    #    200 de dentro de uma aba do efhub.com, e o id dele E o nosso id.
    'com':      ('nao_sei',       ['tela', 'efhub', 'efootbase'], 'medido', 'comSkills na ficha do efHub'),
    'age':      ('nao_sei',       ['tela', 'efhub', 'efootbase'], 'declarado', '⚠️ a tela imprimia "null anos"'),
    'inj':      ('nao_sei',       ['tela', 'efhub'],        'declarado', '⚠️ resistencia a lesao'),
    # ⚠️ forma, cond e capdesc NAO estao entre os 8 campos que o resgate tira do
    #    HTML — os 136 que existem vieram do efHub, pelo cards.json. Por isso a
    #    ordem aqui comeca no efHub, nao na tela.
    'forma':    ('nao_sei',       ['efhub'],                'medido',    None),
    'cond':     ('nao_sei',       ['efhub'],                'medido',    None),
    'wfu':      ('nao_sei',       ['tela', 'efhub'],        'declarado', 'uso do pe ruim'),
    'wfa':      ('nao_sei',       ['tela', 'efhub'],        'declarado', 'precisao do pe ruim'),
    'capdesc':  ('nao_se_aplica', ['efhub'],                'medido',    'a descricao do teto, so texto'),
    # ⛔ 18/08 — E CARIMBO NOSSO, NAO DADO DA CARTA.
    #    `visto_na_casca` marca se a carta ja apareceu no HTML antigo, no
    #    resgate da tela. Nao existe fonte a quem pedir isso: ou a carta estava
    #    la, ou nao estava. Sem esta linha o programa PARAVA a rodada inteira —
    #    e parou, em 17/08 23:34, no passo 5h.
    'visto_na_casca': ('nao_se_aplica', ['derivado'],        'medido',
                       'carimbo do resgate da tela: a carta estava no HTML antigo. Nao se pede a ninguem'),
    'mst':      ('nao_se_aplica', ['tela', 'efhub'],        'declarado', 'mestre / familiaridade'),
    'mx':       ('nao_sei',       ['tela', 'efhub'],        'declarado', 'o maximo de cada atributo'),
    'maxOvr':   ('nao_sei',       ['tela', 'efhub'],        'declarado', 'a nota maxima — o efHub ja da em max_ovr'),

    # --- os que sao conta nossa, nao dado de fora ---------------------------
    'id':             ('nao_sei',       ['derivado'], 'medido',    'a chave'),
    'boostId':        ('nao_se_aplica', ['efhub'],    'medido',    'carta sem impeto nao tem'),
    'boostId2':       ('nao_se_aplica', ['efhub'],    'medido',    'carta com um impeto so nao tem o segundo'),
    'origem_ficha':   ('nao_se_aplica', ['derivado'], 'declarado', 'de qual coleta a ficha veio'),
    'impeto_nativo':  ('nao_se_aplica', ['derivado'], 'declarado', None),
    'fonte_de_cada_campo': ('nao_se_aplica', ['derivado'], 'medido', 'o carimbo de origem — e conta nossa'),

    # ⛔ 18/08 — OS CINCO QUE PARAVAM A RODADA. Mesmo caso do `visto_na_casca`:
    #    campo que nasceu na base depois e nunca teve regra. Sem a linha aqui o
    #    programa PARA — e para com razao, porque campo sem regra some da conta
    #    de pendencia sem ninguem ver.
    #    Nenhum destes cinco se pede a fonte nenhuma:
    'estado_de_cada_campo': ('nao_se_aplica', ['derivado'], 'medido',
                             'a marca dos quatro estados — e a conta que ESTE programa gera'),
    'nota_maxima_tela':     ('nao_se_aplica', ['tela'], 'medido',
                             'a nota maxima que a TELA mostrava. Nao e o max_ovr do efHub — os dois discordam em 2.444 cards e cada um tem dono'),
    # os tres `_bruto` sao o texto CRU do efHub, guardado ao lado do numero
    # convertido para dar para conferir a conversao. Quem falta e o campo
    # convertido (`lesao`, `wfu`, `wfa`), que ja tem regra propria acima.
    'lesao_bruto':            ('nao_se_aplica', ['efhub'], 'medido', 'o texto cru da lesao, para conferir a conversao'),
    'pe_ruim_uso_bruto':      ('nao_se_aplica', ['efhub'], 'medido', 'o texto cru do uso do pe ruim'),
    'pe_ruim_precisao_bruto': ('nao_se_aplica', ['efhub'], 'medido', 'o texto cru da precisao do pe ruim'),
}

# campos calculados a partir do impeto: nao se pede a ninguem
for k in ('impeto_quantos', 'impeto_tem', 'impeto_nomes',
          'impeto_condicional', 'impeto_efeito', 'impeto_soma', 'impeto_situacao',
          'impeto_de_onde'):
    CAMPOS[k] = ('nao_sei', ['derivado'], 'medido', 'calculado a partir do impeto')

# ⛔ vazio aqui e a BOA noticia: nenhum codigo de impeto ficou sem traducao.
#    Marcar como "nao sei" inventaria 3.658 pendencias que nao existem.
CAMPOS['impeto_orfao'] = ('nao_se_aplica', ['derivado'], 'medido',
                          'os codigos de impeto que o catalogo nao conhece. Vazio = nenhum')

# ============================================================================
#  QUEM NASCE DE QUEM — o campo derivado HERDA o estado do pai
# ============================================================================
#  ⛔ 16/08: sem isto o programa dizia que 6.459 cartas estavam sem
#     `impeto_nativo`. Nao estavam: carta que o jogo nao da impeto nao TEM
#     impeto nativo, e isso e resposta, nao buraco. Contar campo derivado como
#     falta e inventar 100 mil pendencias que ninguem pode resolver — porque
#     nao ha a quem pedir.
DERIVA_DE = {
    'impeto_orfao': 'impeto', 'impeto_quantos': 'impeto', 'impeto_tem': 'impeto',
    'impeto_nomes': 'impeto', 'impeto_condicional': 'impeto', 'impeto_efeito': 'impeto',
    'impeto_soma': 'impeto', 'impeto_situacao': 'impeto', 'impeto_de_onde': 'impeto',
    'impeto_nativo': 'impeto', 'nm': 'impeto', 'nx': 'impeto', 'nmn': 'impeto',
    'boostId': 'impeto', 'boostId2': 'impeto', 'vagas_livres': 'sl',
}

IMPETO_SITUACAO = {
    'tem ímpeto':             'valor',
    'sem ímpeto e sem vaga':  'nao_se_aplica',
    'vaga livre — A COLETAR': 'nao_sei',
}
FONTE_VAZIA = {'nao preenchido', 'nenhuma', '', None}
FONTE_CONFERIDA = 'CONFERIDO'


def vazio(v):
    return v is None or v == '' or v == [] or v == {}


P('=' * 78)
P('  A FILA DE COLETA  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')
P('  O que perguntar, a quem, e em que ordem. Passo 5 da reforma.')
P('')
P('  ⛔ NAO coleta nada. NAO escreve no banco. So le e grava a fila.')
P('')

# --------------------------------------------------------------- a base
CAM = os.path.join('dados', 'base_unica.json')
if not os.path.exists(CAM):
    P('⛔ nao achei o %s. Nada foi feito.' % CAM)
    sys.exit(1)
B = json.load(open(CAM, encoding='utf-8'))
cards = B['cards']
P('  base lida ................. %d cartas' % len(cards))

# ------------------------------------------ o resgate da tela, se ja existe
CAM_TELA = os.path.join('dados', 'metadados_da_tela.json')
TELA = {}
if os.path.exists(CAM_TELA):
    try:
        TELA = (json.load(open(CAM_TELA, encoding='utf-8')) or {}).get('dados') or {}
        P('  resgate da tela ........... %d cartas (idade, estilo da IA, pe ruim...)' % len(TELA))
    except Exception:
        TELA = {}
else:
    P('  resgate da tela ........... ⚠️ NAO EXISTE — rode antes o RESGATAR-DA-TELA.bat')
    P('                              sem ele, idade e estilo da IA contam como falta')
    P('                              em todas as 6.469, e nao e verdade.')

# ============================================================================
#  O QUE JA FOI PERGUNTADO — para nao perguntar duas vezes a mesma fonte
# ============================================================================
#  ⛔ 16/08 09h15: o braco visitou 350 cartas, o efootballdb respondeu "nao
#     tenho" em todas, e nada registrava isso. Na fila seguinte as mesmas 350
#     voltavam para o comeco. Para sempre.
#
#     "Nao tem" e RESPOSTA. Vira `nao se aplica`, sai da pendencia, e a fonte
#     que respondeu NAO e perguntada de novo. As outras da ordem continuam
#     valendo — quem respondeu foi ela, nao o mundo.
CAM_JA = os.path.join('dados', 'ja_perguntei.json')
JA = {}
if os.path.exists(CAM_JA):
    try:
        JA = (json.load(open(CAM_JA, encoding='utf-8')) or {}).get('perguntas') or {}
        _n = sum(1 for c in JA.values() for _ in c)
        P('  ja perguntei .............. %d cartas · %d respostas guardadas' % (len(JA), _n))
    except Exception:
        JA = {}


# ⛔ 16/08 10h30 — DUAS COISAS DIFERENTES, E EU TINHA JUNTADO AS DUAS:
#
#   "nao tem" ............... a fonte ACHOU a carta e disse que ela nao tem esse
#                             campo. Isso e fato SOBRE A CARTA. Fecha o campo.
#   "nao existe nesta fonte"  a fonte nem conhece a carta. Isso e fato SOBRE A
#                             FONTE. NAO fecha nada — a proxima da fila tem de
#                             ser perguntada.
#
#   Na primeira versao as duas fechavam o campo. Eram 139 linhas que iam sair da
#   pendencia sem ninguem nunca ter respondido sobre elas.
def alguem_disse_que_nao_tem(cid, campo):
    """Alguma fonte achou a carta e disse que ela NAO TEM esse campo?"""
    r = (JA.get(cid) or {}).get(campo)
    return bool(r) and r.get('resposta') == 'nao tem'


def fonte_nao_atende(cid, campo, fonte):
    """Aquela fonte nem conhece essa carta — pular ela e ir para a proxima."""
    r = (JA.get(cid) or {}).get(campo)
    return bool(r) and r.get('fonte') == fonte and (
        r.get('resposta') in ('nao tem', 'nao existe nesta fonte'))


# ==================================================== 1) OS CAMPOS QUE EXISTEM
# ⛔ Descobertos da base, nao de lista escrita a mao.
existentes = collections.Counter()
for c in cards:
    for k in c:
        existentes[k] += 1
for cid, v in TELA.items():
    for k in v:
        existentes[k] += 1

sem_regra = [k for k in existentes if k not in CAMPOS]

P('')
P('-' * 78)
P('  1) OS CAMPOS QUE A BASE TEM — descobertos nela, nao numa lista minha')
P('')
P('  campos achados ............ %d' % len(existentes))
P('  com regra declarada ....... %d' % (len(existentes) - len(sem_regra)))
if sem_regra:
    P('  ⛔ SEM REGRA .............. %d  <<< ESTES NAO ESTAO SENDO CONTADOS' % len(sem_regra))
    P('')
    for k in sorted(sem_regra):
        P('       %-24s aparece em %d cartas' % (k, existentes[k]))
    P('')
    P('  ⛔ PAREI. Campo sem regra e campo que some da lista de pendencia sem')
    P('     ninguem ver — foi exatamente assim que 6.333 cartas ficaram sem')
    P('     idade por dias. Declare a regra de cada um em CAMPOS e rode de novo.')
    sys.exit(1)
P('  ✅ todo campo da base tem regra. Nenhum esta invisivel.')

# ====================================================== 2) O ESTADO E A FILA
P('')
P('-' * 78)
P('  2) O ESTADO DE CADA CAMPO, E QUEM PERGUNTAR')
P('')

conta = collections.defaultdict(collections.Counter)
fila = collections.defaultdict(list)     # campo -> [card_id]

ORDEM_DOS_CAMPOS = ([k for k in CAMPOS if k not in DERIVA_DE] +
                    [k for k in CAMPOS if k in DERIVA_DE])   # o pai antes do filho

for c in cards:
    cid = str(c.get('id'))
    fontes = c.get('fonte_de_cada_campo') or {}
    t = TELA.get(cid) or {}
    estado_desta_carta = {}
    for campo in ORDEM_DOS_CAMPOS:
        regra_vazio, quem, _prova, _obs = CAMPOS[campo]
        if campo == 'impeto':
            st = IMPETO_SITUACAO.get(c.get('impeto_situacao')) or 'nao_sei'
        else:
            v = c.get(campo)
            if vazio(v) and campo in t:
                v = t.get(campo)          # o resgate da tela preenche
            if not vazio(v):
                st = 'zerado' if v == 0 or v == 0.0 else 'valor'
            else:
                # 1) campo derivado HERDA do pai. Carta que o jogo nao da impeto
                #    nao TEM impeto nativo — e resposta, nao buraco.
                pai = DERIVA_DE.get(campo)
                if pai and estado_desta_carta.get(pai) in ('nao_se_aplica', 'zerado'):
                    st = 'nao_se_aplica'
                # 2) ⛔ ALGUEM JA PERGUNTOU E A FONTE DISSE "NAO TENHO".
                #    Isto vem ANTES de tudo o mais, porque e a evidencia mais
                #    forte que existe: alguem foi la e perguntou.
                #    ⚠️ Na primeira versao esta checagem estava por ultimo, e a
                #    regra 3 (o "nao preenchido" da base) disparava antes. As
                #    cartas ja respondidas continuavam voltando para a fila.
                elif alguem_disse_que_nao_tem(cid, campo):
                    st = 'nao_se_aplica'
                # 3) alguem foi perguntado e veio vazio -> ninguem puxou
                elif campo in fontes and fontes.get(campo) in FONTE_VAZIA:
                    st = 'nao_sei'
                # 4) o pai esta em "nao sei" -> o filho tambem
                elif pai and estado_desta_carta.get(pai) == 'nao_sei':
                    st = 'nao_sei'
                # 5) vale a regra declarada do campo
                else:
                    st = regra_vazio
        # ⛔ 18/08 (noite) — O MAXIMO IGUAL A BASE NAO E RESPOSTA, E BURACO.
        #    Ordem do Luis, olhando a box recente: "os cards continuam como se
        #    nao tivesse progressao, sendo que tem."
        #    Medido na base de 18/08: 1.007 cartas com `mx` identico ao `base`.
        #    Dessas, 816 sao legitimas — levelCap 0 ou 1, carta que nao evolui.
        #    As outras 191 sobem ate o nivel 27, 32, 35 — e estao gravadas como
        #    se o maximo delas fosse a base. Eden Hazard, Mbappe, Bellingham,
        #    Diego Costa, Michael Olise: todos medidos sem a evolucao.
        #    O estado nao via nada porque o campo ESTA preenchido. Resposta
        #    errada parece resposta boa — mesmo defeito do levelCap de manha.
        if campo in ('mx', 'maxOvr') and st == 'valor' \
                and c.get('levelCap') not in (0, 1, None):
            _bs, _mx = c.get('base'), c.get('mx')
            if campo == 'mx':
                _mesmo = bool(_bs) and bool(_mx) and list(_bs) == list(_mx)
            else:
                try:
                    _mesmo = abs(float(c.get('maxOvr') or 0) - float(c.get('ovr') or 0)) < 0.01
                except Exception:
                    _mesmo = False
            if _mesmo:
                st = 'nao_sei'
        estado_desta_carta[campo] = st
        conta[campo][st] += 1
        if st == 'nao_sei':
            fila[campo].append(cid)

# ------------------------------------------------------------- o relatorio
P('  %-16s %8s %8s %8s %9s   %s' % ('campo', 'valor', 'zerado', 'n/aplica', 'NAO SEI', 'quem perguntar'))
P('  ' + '-' * 74)
ordem = sorted(CAMPOS, key=lambda k: -conta[k].get('nao_sei', 0))
total_nao_sei = 0
for campo in ordem:
    d = conta[campo]
    ns = d.get('nao_sei', 0)
    total_nao_sei += ns
    if ns == 0:
        continue
    quem = [f for f in CAMPOS[campo][1] if not (f == 'tela' and TELA)] or CAMPOS[campo][1]
    P('  %-16s %8d %8d %8d %9d   %s' % (
        campo, d.get('valor', 0), d.get('zerado', 0), d.get('nao_se_aplica', 0), ns,
        ' > '.join(quem)))
P('  ' + '-' * 74)
P('  %-16s %36s %9d' % ('TOTAL', '', total_nao_sei))

# ============================================ 3) AS DUAS FILAS
P('')
P('-' * 78)
P('  3) AS DUAS FILAS — o que roda sozinho e o que precisa de voce')
P('')

# ⛔ 16/08 09h — UMA FONTE JA GASTA NAO PODE CONTINUAR MANDANDO NA FILA.
#    O resgate da tela ja rodou e varreu as 22 cascas. O que sobrou em "nao sei"
#    e justamente o que ele NAO achou — insistir nela e mandar o Luis repetir uma
#    coisa que nao vai mudar nada. Entao, depois que o resgate roda, a `tela` sai
#    da vez e quem assume e a proxima fonte da ordem.
def primeira_util(campo):
    ids = fila.get(campo) or []
    for f in CAMPOS[campo][1]:
        if f == 'tela' and TELA:
            continue          # ja foi ate o fim: nao tem mais o que tirar dali
        # se essa fonte ja respondeu "nao tenho" para TODAS as cartas que
        # sobraram neste campo, ela esta gasta: quem assume e a proxima.
        if ids and all(fonte_nao_atende(c, campo, f) for c in ids):
            continue          # essa fonte ja se pronunciou sobre todas: passa a vez
        return f
    return CAMPOS[campo][1][0]


por_fonte = collections.defaultdict(lambda: collections.defaultdict(list))
for campo, ids in fila.items():
    por_fonte[primeira_util(campo)][campo] = ids

# ⛔ 16/08 03h10: o rotulo do grupo "tela" dizia "JA ESTA NA PASTA — e so rodar
#    o resgate". Depois que o resgate JA RODOU, isso vira mentira: o que sobrou
#    aqui e justamente o que ele NAO achou, e nao ha a quem pedir. Mandar rodar
#    de novo uma coisa que nao vai mudar nada e pior que nao dizer nada.
rotulo_tela = 'JA ESTA NA PASTA — e so rodar o RESGATAR-DA-TELA.bat'
for como_rotulo, titulo in (('sozinha',   'RODA SOZINHA — sem ninguem olhando'),
                            ('navegador', 'SO COM O NAVEGADOR ABERTO — precisa de voce'),
                            ('resgate',   rotulo_tela),
                            ('luis',      'SO VOCE, OLHANDO O VIDEOGAME'),
                            ('local',     'NAO SE PEDE A NINGUEM — sai de outro campo')):
    linhas = []
    for fonte, campos in sorted(por_fonte.items()):
        if FONTES.get(fonte, ('?', ''))[0] != como_rotulo:
            continue
        for campo, ids in sorted(campos.items(), key=lambda x: -len(x[1])):
            if ids:
                linhas.append((fonte, campo, len(ids)))
    if not linhas:
        continue
    P('  %s' % titulo)
    for fonte, campo, n in sorted(linhas, key=lambda x: -x[2]):
        P('     %-14s %-16s %6d cartas' % (fonte, campo, n))
    tot = sum(n for _, _, n in linhas)
    # ⛔ o total acima e de PARES carta+campo. Uma ficha do efHub responde varios
    #    campos de uma vez, entao o que conta para o corte diario e quantas
    #    CARTAS DISTINTAS precisam ser buscadas — nao quantos buracos existem.
    # ⛔ 16/08 10h40: aqui eu contava os ids da fila como se fossem cartas. 73%
    #    deles sao `carta@posicao` — a mesma carta varias vezes. O braco ja
    #    juntava; a fila nao, e por isso ela prometia 5.017 visitas onde o braco
    #    fazia 2.402. Numero na tela que ninguem mediu, de novo.
    linhas_ids = set()
    for fonte, campos in por_fonte.items():
        if FONTES.get(fonte, ('?', ''))[0] != como_rotulo:
            continue
        for campo, ids in campos.items():
            linhas_ids.update(ids)
    distintas = {c.split('@')[0] for c in linhas_ids}
    P('     %-31s %6d pares carta+campo' % ('', tot))
    P('     %-31s %6d linhas da fila' % ('', len(linhas_ids)))
    P('     %-31s %6d CARTAS de verdade  <<< e isto que se visita' % ('', len(distintas)))
    if como_rotulo == 'sozinha':
        # 0,15s de pausa + ~0,30s de resposta = ~0,45s por carta. MEDIDO no braco,
        # nao chutado — a versao anterior dizia 3s por carta e inflava 6 vezes.
        P('     uma visita por carta, ~0,45s cada — da mais ou menos %d minutos'
          % max(1, int(len(distintas) * 0.45 / 60) + 1))
    if como_rotulo == 'navegador':
        dias = (len(distintas) + 2099) // 2100
        P('     ⚠️  o efHub corta em ~2.100 fichas/dia — sao ~%d sessao(oes) de Console' % dias)
    P('')

# ================================================ 4) O PRAZO
P('-' * 78)
P('  4) O PRAZO — ha quanto tempo cada coisa esta em "nao sei"')
P('')

CAM_PRAZO = os.path.join('dados', 'desde_quando_nao_sei.json')
antes = {}
if os.path.exists(CAM_PRAZO):
    try:
        antes = (json.load(open(CAM_PRAZO, encoding='utf-8')) or {}).get('desde') or {}
    except Exception:
        antes = {}

hoje = datetime.now()
agora_txt = hoje.strftime('%Y-%m-%d %H:%M')
desde = {}
vencidos = collections.Counter()
novos = 0
for campo, ids in fila.items():
    d = antes.get(campo) or {}
    novo = {}
    for cid in ids:
        quando = d.get(cid)
        if not quando:
            quando = agora_txt
            novos += 1
        novo[cid] = quando
        try:
            dt = datetime.strptime(quando, '%Y-%m-%d %H:%M')
            if hoje - dt > timedelta(days=PRAZO_DIAS):
                vencidos[campo] += 1
        except Exception:
            pass
    desde[campo] = novo

if not antes:
    P('  primeira vez que isto roda — o relogio comeca a contar AGORA.')
    P('  %d pares carta+campo marcados as %s' % (novos, agora_txt))
    P('  Da proxima vez este bloco mostra o que passou de %d dias.' % PRAZO_DIAS)
else:
    P('  pares novos desde a ultima vez .... %d' % novos)
    if vencidos:
        P('')
        P('  ⛔ EM "NAO SEI" HA MAIS DE %d DIAS:' % PRAZO_DIAS)
        for campo, n in vencidos.most_common():
            P('     %-18s %6d cartas' % (campo, n))
    else:
        P('  ✅ nada passou de %d dias.' % PRAZO_DIAS)

# ================================================================ GRAVAR
# ============================================================================
#  RESPOSTA SUSPEITA — a que parece boa e nao e. 18/08/2026
# ============================================================================
#  ORDEM DO LUIS, 18/08, e ele achou isto olhando a tela:
#    "O eFootball lanca a carta, o pessoal do efHub coloca ela no banco deles,
#     so que na primeira vez eles nao colocam a evolucao dela — as barrinhas,
#     o nivel que ela pode chegar. A gente consulta, ve 1/1, e imagina que e
#     carta sem evolucao. So que nao e. E como a gente ja consultou uma vez,
#     fecha a questao e nunca mais olha. No dia seguinte eles atualizam, e a
#     gente fica com o banco defasado."
#
#  ⛔ POR QUE ISTO NAO SE CONSERTAVA SOZINHO — e o ponto fino:
#     A fila so repergunta o que esta `nao_sei`. O efHub NAO deixou em branco:
#     ele RESPONDEU "nivel 1". Resposta errada entra como `valor`, sai da fila,
#     e ninguem volta la nunca mais. Resposta errada parece resposta boa.
#
#  MEDIDO EM 18/08 — quem estava marcado como "nao evolui":
#     Kylian Mbappe 96 · Vitinha 96 · Declan Rice 96 · Virgil van Dijk 95
#     Frenkie de Jong 95 · Raphinha 95 · Jules Kounde 95 · Gavi 94 · Dani Olmo 94
#     todos de box de 13/08, com orcamento 0. Carta de New Season Campaign nao
#     e carta congelada — isso e impossivel.
#
#  ⛔ ISTO NAO MEXE NOS QUATRO ESTADOS. A conta de `nao_sei` continua igual e a
#     conferencia do fim continua batendo. Isto e uma lista A MAIS, que o vigia
#     le junto: cartas cuja resposta merece ser perguntada de novo.
DIAS_DE_DESCONFIANCA = 30    # depois disso, aceita-se que ela e POTW mesmo
suspeitas = []
try:
    _hoje = datetime.now().date()
    for _c in (B.get('cards') if isinstance(B, dict) else B) or []:
        _cid = str(_c.get('id') or '')
        if not _cid or '@' in _cid:
            continue
        # ⛔ carta sem nome e registro fantasma (ficha do efHub que entrou sem
        #    carta). Nao se pergunta progressao de quem nao tem nome nem nota.
        #    Sem este corte a lista ia de 19 para 195, quase tudo fantasma.
        if not _c.get('nome'):
            continue
        # ⛔ 18/08, 2a versao — NIVEL ZERO TAMBEM. Achado com o Luis olhando a
        #    tela: as 11 cartas da box `Summer Transfer 17 Aug '26`, de 5 dias,
        #    estavam com levelCap = ZERO, nao 1 — e a regra so olhava o 1.
        #    Elliot Anderson 86, Morgan Rogers 86, Denzel Dumfries 85: box de 5
        #    dias, orcamento 0, e o sistema aceitou "nao evolui" como resposta.
        #    O proprio Luis ja tinha dito a regra: "carta que nao evolui e a que
        #    tem nivel maximo UM OU ZERO". Os dois numeros dizem a mesma coisa,
        #    entao os dois sao suspeitos na box recente.
        #    Medido: a lista vai de 19 para 53 cartas.
        if _c.get('levelCap') not in (0, 1):
            continue
        _d = _c.get('dt')
        _idade = None
        if _d:
            try:
                _y, _m, _dd = [int(x) for x in str(_d)[:10].split('-')]
                _idade = (_hoje - datetime(_y, _m, _dd).date()).days
            except Exception:
                _idade = None
        # sem data de box tambem entra: nao saber a idade nao e prova de nada
        if _idade is None or _idade <= DIAS_DE_DESCONFIANCA:
            suspeitas.append({'card': _cid, 'nome': _c.get('nome'),
                              'ovr': _c.get('ovr'), 'box': _c.get('box'),
                              'dias_de_box': _idade, 'campo': 'levelCap',
                              'respondeu': _c.get('levelCap'),
                              'por_que': ('nivel 1 em carta de box recente: o efHub '
                                          'costuma publicar a progressao dias depois')})
except Exception as _e:
    P('  (nao consegui montar a lista de respostas suspeitas: %s)' % str(_e)[:90])

# ⛔ 18/08 (noite) — A SEGUNDA DESCONFIANCA: EVOLUI, MAS O MAXIMO E A BASE.
#    Estas nao dependem de box recente nem de prazo: a carta sobe ate o nivel
#    32 e o maximo gravado e igual ao basico. Isso nao e uma carta congelada,
#    e uma coleta que nunca aconteceu. Entram na pilha do vigia junto com os
#    furos, com prioridade pelo OVR.
try:
    _ja = {str(x.get('card')) for x in suspeitas}
    _semprog = []
    for _c in (B.get('cards') if isinstance(B, dict) else B) or []:
        _cid = str(_c.get('id') or '')
        if not _cid or '@' in _cid or not _c.get('nome') or _cid in _ja:
            continue
        if _c.get('levelCap') in (0, 1, None):
            continue
        _bs, _mx = _c.get('base'), _c.get('mx')
        if not _bs or not _mx or list(_bs) != list(_mx):
            continue
        _semprog.append({'card': _cid, 'nome': _c.get('nome'), 'ovr': _c.get('ovr'),
                         'box': _c.get('box'), 'dias_de_box': None, 'campo': 'mx',
                         'respondeu': 'maximo igual ao basico',
                         'por_que': ('a carta sobe ate o nivel %s e o maximo gravado e '
                                     'igual ao basico — a evolucao nunca foi coletada'
                                     % _c.get('levelCap'))})
    _semprog.sort(key=lambda x: -(x.get('ovr') or 0))
    if _semprog:
        suspeitas.extend(_semprog)
        P('')
        P('  EVOLUI MAS O MAXIMO E A BASE ... %d cartas' % len(_semprog))
        for _x in _semprog[:5]:
            P('       %-24s ovr %s' % (str(_x.get('nome'))[:24], _x.get('ovr')))
except Exception as _e:
    P('  (nao consegui montar a lista do maximo igual a base: %s)' % str(_e)[:90])



saida = {
    'o_que_e': 'a fila de coleta: o que perguntar, a quem, em que ordem',
    'gerado_por': 'fila_de_coleta.py',
    'gerado_em': hoje.isoformat(),
    'prazo_dias': PRAZO_DIAS,
    'regra': ('os campos saem da BASE, nao de lista escrita a mao. Campo sem regra '
              'declarada faz o programa PARAR — campo invisivel e campo que some da '
              'pendencia sem ninguem ver.'),
    'fontes': {k: {'como_anda': v[0], 'observacao': v[1]} for k, v in FONTES.items()},
    'por_campo': {
        campo: {
            # ⛔ 16/08 09h50 — A TELA MOSTRAVA UMA COISA E O ARQUIVO GUARDAVA OUTRA.
            #    Aqui estava gravada a ordem CRUA, com a `tela` na frente. Mas a
            #    `tela` ja foi esgotada pelo resgate, e a tela do programa ja
            #    mostrava a proxima fonte. Quem lia o arquivo (o gerador da coleta
            #    do efHub) via `tela` como primeira e PULAVA o campo — sumiram
            #    idade, estilo de jogo da IA, lesao, pe ruim, maximo e nota maxima
            #    da coleta, que sao justamente os melhores.
            #    Agora o arquivo guarda o mesmo que a tela mostra. A ordem crua
            #    fica ao lado, com outro nome, para nao se perder.
            'quem_perguntar': ([f for f in CAMPOS[campo][1] if not (f == 'tela' and TELA)]
                               or CAMPOS[campo][1]),
            'ordem_completa': CAMPOS[campo][1],
            'fontes_ja_esgotadas': ['tela'] if TELA else [],
            'a_ordem_e': CAMPOS[campo][2],
            'observacao': CAMPOS[campo][3],
            'regra_do_vazio': CAMPOS[campo][0],
            'valor': conta[campo].get('valor', 0),
            'zerado': conta[campo].get('zerado', 0),
            'nao_se_aplica': conta[campo].get('nao_se_aplica', 0),
            'nao_sei': conta[campo].get('nao_sei', 0),
            'cartas_a_perguntar': fila.get(campo, []),
        } for campo in CAMPOS},
    'total_nao_sei': total_nao_sei,
    'usou_o_resgate_da_tela': bool(TELA),
    # ⛔ NAO entra na conta dos quatro estados. E lista A MAIS, para o vigia.
    'respostas_suspeitas': suspeitas,
}
if suspeitas:
    P('')
    P('  ⚠️ RESPOSTAS SUSPEITAS — %d cartas' % len(suspeitas))
    P('     nivel maximo 0 ou 1 em carta de box com menos de %d dias.' % DIAS_DE_DESCONFIANCA)
    P('     Elas voltam para o vigia mesmo tendo resposta. As mais fortes:')
    for _x in sorted(suspeitas, key=lambda x: -(x.get('ovr') or 0))[:8]:
        P('        %-24s ovr %-4s nivel %-2s %s' % (str(_x['nome'])[:24], _x['ovr'],
                                                    _x.get('respondeu'),
                                                    str(_x.get('box'))[:34]))

dest = os.path.join(CASA, 'dados', 'fila_de_coleta.json')
os.makedirs(os.path.dirname(dest), exist_ok=True)
with open(dest, 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False)

with open(CAM_PRAZO, 'w', encoding='utf-8') as f:
    json.dump({'o_que_e': 'desde quando cada carta esta em "nao sei" em cada campo',
               'gerado_em': hoje.isoformat(), 'desde': desde}, f, ensure_ascii=False)

P('')
P('  gravei .................... dados/fila_de_coleta.json')
P('  gravei .................... dados/desde_quando_nao_sei.json')

# --------------------------------------------------------- CONFERENCIA
V = json.load(open(dest, encoding='utf-8'))
soma = sum(v['nao_sei'] for v in V['por_campo'].values())
listas = sum(len(v['cartas_a_perguntar']) for v in V['por_campo'].values())
P('')
P('  CONFERENCIA — lendo o arquivo de volta do disco')
if soma != total_nao_sei or listas != total_nao_sei:
    P('  ⛔ contei %d, a soma do arquivo deu %d e as listas somam %d.' % (total_nao_sei, soma, listas))
    sys.exit(1)
P('  ✅ %d "nao sei" contados, %d na soma, %d nas listas — bate' % (total_nao_sei, soma, listas))
P('')
P('  PRONTO E CONFERIDO.')
