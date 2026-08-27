# -*- coding: utf-8 -*-
r"""
A VOLTA AUTOMATICA — passo 7 da reforma. 16/08/2026

⛔ O DEFEITO QUE ISTO EXISTE PARA MATAR
   O "refazer" e feito na mao, e ja falhou: em 16/08 descobriu-se que 325 linhas
   estavam com pontuacao velha havia dias porque alguem limpou UM dos tres
   lugares que o motor considera "ja feito". Ninguem percebeu.

   O plano do Luis: "se o insumo e mais novo que o produto, a linha volta para a
   fila SOZINHA. Se a receita mudou, tudo que foi feito com a receita velha volta."

O QUE ESTE PROGRAMA FAZ — e o que NAO faz
   FAZ .... pergunta ao banco o que a tabela `builds` guarda, compara com a
            `cards_base`, e escreve PRECISA-REFAZER.txt no formato
            `card_id|funcao`, que e o que o REFAZER-DE-VERDADE.bat consome.
   NAO FAZ  nao mexe na fila, nao mexe no feitos.txt, nao mexe no linhas.jsonl,
            nao escreve no banco. Quem tira as linhas da frente e o
            REFAZER-DE-VERDADE.bat, que ja e provado desde 16/08.

⚠️ A ARMADILHA QUE ESTE PROGRAMA SE RECUSA A CAIR
   O `subir_base.py` grava `atualizado_em = agora` em TODAS as 6.469 linhas a
   cada vez que roda. Se a comparacao fosse so "carta mais nova que a linha",
   depois de qualquer SUBIR-BASE o programa mandaria refazer as 11 mil linhas —
   e nao mudou nada. Por isso ele PARA e avisa quando a resposta e "refaz quase
   tudo": um numero grande demais nao e trabalho, e sintoma.

⛔ SO LE. Pode rodar com o motor rodando.
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
    L.append(s); print(s, flush=True)

# quanto da base inteira ja e "demais" — acima disto o programa se recusa
TETO_DE_SUSPEITA = 0.60

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
    """Baixa uma tabela inteira, de mil em mil."""
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


# ===========================================================================
#  O MARCO — o ponto zero da volta automatica. 16/08/2026 16h20
# ===========================================================================
# ⛔ POR QUE ISTO PRECISOU EXISTIR
#    A hora da carta (`cards_base.atualizado_em`) so passou a significar "foi
#    aqui que este dado mudou" a partir de 16/08 16h. Antes disso o
#    subir_base.py carimbava as 6.469 a cada upload — e a ultima rodada com o
#    defeito, as 15h56, deixou TODAS as cartas com a mesma hora.
#
#    Com isso, "a carta e mais nova que a linha" ficou verdadeiro para 10.595
#    das 11.133 linhas. Nao porque mudaram: porque foram todas carimbadas
#    juntas. Um carimbo em massa NAO E PROVA de que o dado mudou.
#
#    O marco separa as duas coisas: hora ATE o marco = nao sei, nao conta.
#    Hora DEPOIS do marco = mudou de verdade, e conta.
#
#    ⚠️ Ele nao apaga historia: as linhas de antes do marco continuam sendo o
#    que sao. Ele so impede que o carimbo em massa seja lido como novidade.
MARCO_ARQ = 'MARCO-DA-VOLTA.txt'
MARCAR = any(a.lower().startswith('marc') for a in sys.argv[1:])

P('=' * 74)
P('  A VOLTA AUTOMATICA — o que precisa refazer  ·  ' 
  + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 74)

# ---------------------------------------------------- 1) o que a builds guarda
try:
    r = urllib.request.Request(URL + '/rest/v1/builds?select=*&limit=1', headers=H)
    with urllib.request.urlopen(r, timeout=90) as f:
        amostra = json.loads(f.read().decode('utf-8', 'replace'))
except Exception as e:
    P('⛔ nao consegui falar com o banco: %s' % str(e)[:120])
    sys.exit(1)
if not amostra:
    P('⛔ a tabela builds voltou vazia. Nada a refazer.')
    sys.exit(0)

COL = sorted(amostra[0].keys())
P('')
P('a tabela builds tem %d colunas' % len(COL))

# ⛔ 16/08 16h15 — ESTA LISTA JA FICOU PARA TRAS UMA VEZ, NO MESMO DIA.
#    A primeira versao procurava por 'atualizado_em', 'quando', 'criado_em',
#    'gerado_em', 'updated_at', 'created_at' — e disse "NAO EXISTE".
#    A builds tem `rodado_em` E `atualizado`. Os dois estavam ali o tempo todo.
#    Foi lista escrita a mao de novo, a terceira vez em 24 horas.
#
#    Por isso agora ela nao so procura o nome: ela CONFERE O VALOR. Uma coluna
#    so serve se o que tem dentro parece data. Nome nao prova nada.
CANDIDATAS = ['rodado_em', 'atualizado_em', 'atualizado', 'quando',
              'criado_em', 'gerado_em', 'updated_at', 'created_at']


def parece_data(v):
    s = str(v or '')
    return len(s) >= 10 and s[:2] == '20' and '-' in s


COL_HORA = None
_amostra_hora = None
for c in CANDIDATAS:
    if c not in COL:
        continue
    _v = amostra[0].get(c)
    if _v is None or parece_data(_v):
        COL_HORA = c
        _amostra_hora = _v
        break
COL_VER = 'motor_versao' if 'motor_versao' in COL else None

P('   coluna de hora ......... %s%s'
  % (COL_HORA or '⛔ NAO EXISTE',
     ('   exemplo: %s' % _amostra_hora) if _amostra_hora else ''))
P('   coluna de versao ....... %s' % (COL_VER or '⛔ NAO EXISTE'))

# ---------------------------------------------------- 2) baixa os dois lados
P('')
P('lendo o banco...')
campos_b = ['card_id', 'funcao'] + [c for c in (COL_HORA, COL_VER) if c]
linhas = pega('builds', campos_b, 'card_id')
P('   builds ................. %s linhas' % '{:,}'.format(len(linhas)))

cards = pega('cards_base', ['card_id', 'atualizado_em'], 'card_id')
QUANDO_A_CARTA = {str(c['card_id']): c.get('atualizado_em') for c in cards}
P('   cards_base ............. %s cartas' % '{:,}'.format(len(cards)))

# a versao vigente do motor, perguntada — nao escrita a mao
# ⛔ 16/08 16h25 — POR QUE ISTO NAO LIA ANTES, e a licao e a mesma do dia:
#    eu pedia a tabela ordenada por `id`. A motor_versao NAO TEM coluna id — a
#    chave dela e (motor, versao). O PostgREST recusava, a excecao era engolida
#    pelo `except`, e o programa dizia "nao consegui ler" sem dizer por que.
#    Um erro engolido e um erro que ninguem conserta.
VIGENTE = None
_por_que_nao = None
if COL_VER:
    try:
        v = pega('motor_versao', None, 'motor')
        otim = [x for x in v if str(x.get('motor') or '').lower().startswith('otimiz')]
        if not otim:
            _por_que_nao = 'nao achei nenhuma linha com motor="otimizacao"'
        else:
            # ⚠️ prefiro a marcada como vigente; se houver mais de uma (o
            #    subir_versoes marca toda versao nova como vigente e nao
            #    desmarca a anterior), fico com a MAIOR. Empate nao decide sozinho.
            vig = [x for x in otim if x.get('vigente')]
            alvo = vig or otim
            try:
                alvo = sorted(alvo, key=lambda x: int(x.get('versao') or 0))
            except Exception:
                pass
            VIGENTE = str(alvo[-1].get('versao') or '')
            if len(vig) > 1:
                _por_que_nao = ('⚠️ %d versoes marcadas como vigentes ao mesmo tempo — '
                                'fiquei com a maior (%s)' % (len(vig), VIGENTE))
    except Exception as e:
        _por_que_nao = str(e)[:90]
    P('   versao vigente do motor  %s' % (VIGENTE or 'nao consegui ler'))
    if _por_que_nao:
        P('      %s' % _por_que_nao)

# ---------------------------------------------------- 2b) o marco
if MARCAR:
    _agora = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    with open(MARCO_ARQ, 'w', encoding='utf-8') as _f:
        _f.write(_agora + '\n')
        _f.write('O ponto zero da volta automatica.\n')
        _f.write('Carimbo de carta ATE esta hora nao vale como prova de mudanca:\n')
        _f.write('ate 16/08 16h o subir_base carimbava todas as cartas a cada upload.\n')
        _f.write('Daqui pra frente, hora nova na carta = dado mudou de verdade.\n')
    P('')
    P('=' * 74)
    P('  MARCO GRAVADO: %s' % _agora)
    P('=' * 74)
    P('')
    P('  A partir de agora a volta automatica so conta como "envelheceu" a')
    P('  linha cuja carta mudou DEPOIS desta hora.')
    P('')
    P('  ⚠️ Isto NAO conserta as linhas de hoje para tras. Elas ficam como')
    P('     estao — e a foto de agora, que o conferir provou estar coerente:')
    P('     o banco e a pasta concordam em tudo.')
    P('')
    P('  Rode o A-VOLTA-AUTOMATICA.bat de novo para ver o resultado.')
    sys.exit(0)

MARCO = None
if os.path.exists(MARCO_ARQ):
    try:
        MARCO = open(MARCO_ARQ, encoding='utf-8').readline().strip()
    except Exception:
        MARCO = None
P('   marco (o ponto zero) ... %s' % (MARCO or 'NAO EXISTE'))

# ---------------------------------------------------- 3) a conta
por_hora, por_receita, sem_carta, antes_do_marco = [], [], [], 0
for l in linhas:
    cid = str(l.get('card_id'))
    fun = l.get('funcao')
    if not cid or not fun:
        continue
    chave = '%s|%s' % (cid, fun)
    qc = QUANDO_A_CARTA.get(cid)
    if qc is None:
        sem_carta.append(chave)
        continue
    if COL_HORA and l.get(COL_HORA) and str(qc) > str(l[COL_HORA]):
        # ⛔ carimbo ate o marco nao e prova: foi carimbo em massa, nao mudanca
        if MARCO and str(qc)[:19] <= str(MARCO)[:19]:
            antes_do_marco += 1
        else:
            por_hora.append(chave)
    if COL_VER and VIGENTE and str(l.get(COL_VER) or '') != VIGENTE:
        por_receita.append(chave)

todas = []
vistas = set()
for k in por_receita + por_hora:
    if k not in vistas:
        vistas.add(k); todas.append(k)

# ===========================================================================
#  ⛔ SEM COMPARACAO NAO EXISTE "ZERO" — 16/08/2026 16h15
# ===========================================================================
#    Na primeira rodada de verdade este programa respondeu "PRECISA REFAZER: 0
#    de 11.133" — e era MENTIRA. A tabela builds nao tem coluna de hora, e a
#    versao vigente do motor nao pode ser lida. Ele nao comparou NADA e disse
#    zero, que e a resposta mais perigosa que existe: parece boa noticia.
#
#    E exatamente a doenca do dia inteiro — "nao achei" virando "nao tem".
#    Um programa que nao conseguiu medir tem que dizer QUE NAO CONSEGUIU.
_pode_hora = bool(COL_HORA) and any(l.get(COL_HORA) for l in linhas)
_pode_receita = bool(COL_VER) and bool(VIGENTE)
if not _pode_hora and not _pode_receita:
    P('')
    P('=' * 74)
    P('  ⛔ PAREI. NAO DA PARA RESPONDER — e isso nao e zero.')
    P('=' * 74)
    P('')
    P('  Para saber o que envelheceu preciso de UMA destas duas:')
    P('')
    P('     a hora em que a linha foi calculada .... %s'
      % ('tem: ' + COL_HORA if _pode_hora else '⛔ a tabela builds NAO TEM'))
    P('     a versao do motor que a fez ............ %s'
      % ('tem' if _pode_receita else
         ('a coluna %s existe, mas nao consigo ler qual e a VIGENTE' % COL_VER
          if COL_VER else '⛔ nao existe')))
    P('')
    P('  Sem nenhuma das duas eu nao comparei nada. Responder "0 precisam')
    P('  refazer" seria dizer que esta tudo certo por nao ter olhado —')
    P('  o mesmo erro que deixou 325 linhas com pontuacao velha em 16/08.')
    P('')
    P('  ⛔ NAO ESCREVI o PRECISA-REFAZER.txt. Um arquivo vazio seria lido')
    P('     amanha como "nada a fazer".')
    P('')
    P('  O CONSERTO, e e o passo 7:')
    P('     1. a tabela builds precisa de uma coluna de hora')
    P('     2. quem escreve a linha precisa carimbar essa hora')
    P('     3. o que ja existe fica sem hora — e isso e "nao sei quando",')
    P('        que e pendencia, nao ordem de refazer 11 mil linhas')
    P('')
    P('  As %d colunas que a builds tem hoje:' % len(COL))
    for _i in range(0, len(COL), 4):
        P('     ' + '  '.join('%-24s' % c for c in COL[_i:_i + 4]))
    open('RELATORIO-A-VOLTA.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    P('')
    P('  O relatorio ficou em RELATORIO-A-VOLTA.txt')
    sys.exit(1)

P('')
P('COMO EU CONSEGUI MEDIR')
P('   pela hora da carta contra a hora da linha ... %s'
  % ('sim' if _pode_hora else 'NAO — a builds nao tem coluna de hora'))
P('   pela versao do motor ........................ %s'
  % ('sim' if _pode_receita else 'NAO — nao sei qual versao e a vigente'))

P('')
P('O QUE ENVELHECEU')
P('   a carta mudou depois da linha .... %s' % '{:,}'.format(len(por_hora)))
P('   a linha saiu de receita velha .... %s' % '{:,}'.format(len(por_receita)))
P('   linha sem carta na base .......... %s   (nao entra: nao ha o que refazer)'
  % '{:,}'.format(len(sem_carta)))
if antes_do_marco:
    P('   carimbo ATE o marco, nao conta ... %s   (carimbo em massa, nao mudanca)'
      % '{:,}'.format(antes_do_marco))
P('   -----')
P('   PRECISA REFAZER .................. %s de %s'
  % ('{:,}'.format(len(todas)), '{:,}'.format(len(linhas))))

# ---------------------------------------------------- 4) a trava
fatia = (len(todas) / float(len(linhas))) if linhas else 0
if fatia > TETO_DE_SUSPEITA:
    P('')
    P('=' * 74)
    P('  ⛔ PAREI. ISSO E %d%% DE TUDO — e sintoma, nao trabalho.' % round(fatia * 100))
    P('=' * 74)
    P('')
    P('  A causa quase certa: o subir_base.py grava `atualizado_em = agora` em')
    P('  TODAS as cartas a cada vez que roda. Depois de um SUBIR-BASE, toda')
    P('  carta fica "mais nova" que toda linha, mesmo sem nada ter mudado.')
    P('')
    P('  Refazer %s linhas assim seria horas de motor para chegar no' % '{:,}'.format(len(todas)))
    P('  mesmo numero. NAO escrevi a lista.')
    P('')
    if not MARCO:
        P('  O CONSERTO E UM CLIQUE: falta o MARCO, o ponto zero.')
        P('')
        P('    O subir_base ja foi consertado (16/08 16h): campo vazio nao sobe')
        P('    e so sobe quem mudou. Mas as cartas ficaram todas com o carimbo')
        P('    da ultima rodada com defeito, as 15h56 — e por isso todas')
        P('    parecem mais novas que todas as linhas.')
        P('')
        P('    Duplo clique em  MARCAR-O-PONTO-ZERO.bat  e rode isto de novo.')
        P('    Dali pra frente, hora nova na carta = dado mudou de verdade.')
    else:
        P('  O marco existe (%s) e mesmo assim deu %d%%.' % (MARCO, round(fatia * 100)))
        P('  Entao a causa e outra, e vale investigar antes de refazer.')
    P('')
    open('RELATORIO-A-VOLTA.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    P('  O relatorio ficou em RELATORIO-A-VOLTA.txt')
    sys.exit(1)

# ===========================================================================
#  ⛔ ENVELHECEU E NAO DA PARA REFAZER E OUTRA COISA — 16/08/2026 17h45
# ===========================================================================
#    Medido: das 489 que sobraram depois da primeira rodada, ZERO estavam na
#    fila_v6.json. Sao linhas de resultado para pares carta x funcao que o
#    sistema NAO PRODUZ MAIS — sobra do motor 5, de 07/08.
#
#    Se elas forem para o PRECISA-REFAZER, acontece isto: o REFAZER poe na
#    frente da fila, o monta_fila reconstroi a fila e as descarta, o motor nao
#    roda nenhuma, e na proxima vez este programa acha as mesmas 489.
#    ⛔ UM LACO INFINITO QUE PARECE TRABALHO.
#
#    Entao a lista e partida em duas, e a segunda NAO e ordem de refazer:
#      PRECISA-REFAZER.txt ......... esta na fila. Da para refazer.
#      SOBRAS-DO-MOTOR-VELHO.txt ... nao esta. Nao ha o que refazer.
#
#    O que fazer com as sobras e DECISAO DO LUIS, e envolve APAGAR linha do
#    banco — a classe de operacao mais perigosa que existe aqui. Este programa
#    so aponta.
NA_FILA = set()
_cam_fila = 'fila_v6.json'
if os.path.exists(_cam_fila):
    try:
        _F = json.load(open(_cam_fila, encoding='utf-8'))
        if isinstance(_F, dict):
            _F = _F.get('linhas') or _F.get('fila') or []
        for _x in _F:
            if isinstance(_x, str):
                NA_FILA.add(_x)
            elif isinstance(_x, dict):
                _c = _x.get('card_id') or _x.get('id') or _x.get('card')
                _f = _x.get('funcao') or _x.get('tipo')
                if _c and _f:
                    NA_FILA.add('%s|%s' % (_c, _f))
            elif isinstance(_x, (list, tuple)) and len(_x) >= 2:
                NA_FILA.add('%s|%s' % (_x[0], _x[1]))
    except Exception as _e:
        P('   ⚠️ nao consegui ler a fila_v6.json (%s) — nao separo as sobras'
          % str(_e)[:60])
        NA_FILA = None

if NA_FILA:
    da_para = [k for k in todas if k in NA_FILA]
    sobras = [k for k in todas if k not in NA_FILA]
else:
    da_para, sobras = todas, []

P('')
P('DA PARA REFAZER?')
P('   esta na fila, o motor pega ....... %s' % '{:,}'.format(len(da_para)))
P('   NAO esta na fila — e SOBRA ....... %s' % '{:,}'.format(len(sobras)))

# ---------------------------------------------------- 5) as listas
SAI = 'PRECISA-REFAZER.txt'
with open(SAI, 'w', encoding='utf-8') as f:
    for k in da_para:
        f.write(k + '\n')

if sobras:
    import collections as _co
    _porf = _co.Counter(k.split('|', 1)[1] for k in sobras)
    with open('SOBRAS-DO-MOTOR-VELHO.txt', 'w', encoding='utf-8') as f:
        f.write('SOBRAS DO MOTOR VELHO — %s\n' % datetime.now().strftime('%d/%m/%Y %H:%M'))
        f.write('\n')
        f.write('Linhas na tabela builds feitas por uma versao do motor que nao vale\n')
        f.write('mais, E que NAO estao na fila de hoje. O sistema nao produz mais\n')
        f.write('esses pares carta x funcao — entao NAO HA O QUE REFAZER.\n')
        f.write('\n')
        f.write('⛔ NAO rode o REFAZER com esta lista. Ele poe na frente da fila, o\n')
        f.write('   monta_fila descarta, o motor nao roda nenhuma, e amanha elas\n')
        f.write('   aparecem de novo. Um laco que parece trabalho.\n')
        f.write('\n')
        f.write('O que fazer com elas e decisao do Luis, e envolve APAGAR linha do\n')
        f.write('banco. Este programa so aponta.\n')
        f.write('\n')
        f.write('por funcao:\n')
        for _f, _n in _porf.most_common():
            f.write('   %-34s %d\n' % (_f, _n))
        f.write('\n')
        f.write('as chaves:\n')
        for k in sobras:
            f.write(k + '\n')
    P('')
    P('   escrevi SOBRAS-DO-MOTOR-VELHO.txt com %s chaves' % '{:,}'.format(len(sobras)))
    P('   por funcao: ' + ' · '.join('%s %d' % (f, n) for f, n in
                                     sorted(_porf.items(), key=lambda x: -x[1])[:5]))

P('')
if da_para:
    P('  O QUE FAZER AGORA')
    P('     duplo clique em REFAZER-O-QUE-ENVELHECEU.bat')
    P('     ⛔ com o motor PARADO. Depois, COMECAR-TUDO.bat.')
else:
    P('  ✅ NAO HA NADA PARA REFAZER.')
    if sobras:
        P('     As %s que envelheceram sao SOBRA: nao estao na fila e o sistema'
          % '{:,}'.format(len(sobras)))
        P('     nao produz mais esses pares. Leia o SOBRAS-DO-MOTOR-VELHO.txt.')
        P('     ⛔ Nao adianta rodar o REFAZER com elas.')

open('RELATORIO-A-VOLTA.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
P('')
P('=' * 74)
P('  Nada foi escrito no banco, na fila nem no feitos.txt.')
P('=' * 74)
