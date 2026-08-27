# -*- coding: utf-8 -*-
"""
MOTOR DO ENCAIXE — RODADA v6  ·  versao com ENTRADA QUENTE (07/08/2026)

  1. Roda a fila_v6.json inteira: card por card, funcao por funcao.
  2. QUANDO ACABA, NAO FECHA. Fica olhando o fila_EXTRA.json.
     Card novo que voce jogar la dentro entra na fila e roda, sem parar o motor.
     Da tambem pra jogar card novo la ENQUANTO ele roda a fila principal —
     ele pega assim que terminar o que esta na mao.
  3. Nada roda duas vezes: feitos.txt guarda card+funcao ja resolvidos.
  4. Se cair, recomeca exatamente onde parou.

⛔ NAO MEXE NA FORMULA. Mesmo motor, mesmas travas, mesmo molde.
⛔ NAO GRAVA NO SUPABASE. O envio continua sendo o ENVIAR.bat.

Para fechar de vez: feche a janela, ou crie um arquivo chamado PARAR.txt na pasta.
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
import json, os, re, sys, time, collections, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))


# ===========================================================================
#  DE QUAIS ATRIBUTOS E ESSE IMPETO — lido do catalogo, nao adivinhado
# ===========================================================================
#  ⛔ 18/08. Serve para o bloco do IMPETO CONDICIONAL saber QUAIS posicoes do
#     `nm` pertencem ao impeto condicional quando a carta tem mais de um.
#     Antes isso era adivinhado pelo valor ("valor 1 = condicional"), e o
#     palpite deu degrau inventado em 56 cartas — Messi, Neuer, Haaland, Kane.
#
#     O nome vem com o nivel colado ("Chute +1"); o catalogo tem os dois
#     idiomas e todos os niveis, entao a busca ignora o nivel e tenta os dois
#     nomes. Nome que o catalogo nao conhece devolve lista VAZIA — e quem
#     chama trata isso como "nao sei", nunca como "pode subir tudo".
_CAT_ATS = None


def _atributos_do_impeto(nome):
    global _CAT_ATS
    if _CAT_ATS is None:
        _CAT_ATS = {}
        try:
            import fonte_unica as _FUc
            for x in _FUc.catalogo_fabricaveis():
                if not (isinstance(x, list) and len(x) == 3):
                    continue
                base = re.sub(r'\s*\+\d+\s*$', '', str(x[0])).strip().lower()
                ats = sorted({int(p[0]) for p in (x[2] or [])
                              if isinstance(p, (list, tuple)) and len(p) == 2})
                if base and ats:
                    _CAT_ATS.setdefault(base, ats)
        except Exception:
            _CAT_ATS = {}
    if not nome:
        return []
    return _CAT_ATS.get(re.sub(r'\s*\+\d+\s*$', '', str(nome)).strip().lower(), [])

# Quantas linhas por arquivo de saida. 1 = uma linha por gravacao (o padrao).
# Nao existe mais "lote de calculo": o pool entrega em fluxo, linha a linha.
GRAVA_A_CADA = 1
TELA_A_CADA  = 1        # de quantas em quantas linhas a tela se move

try:    NUCLEOS = int(os.environ.get('NUCLEOS', '0'))
except ValueError: NUCLEOS = 0
if NUCLEOS <= 0:
    # ⚠️ os.cpu_count() devolve o numero LOGICO. Com hyperthreading, uma maquina de
    # 2 nucleos fisicos reporta 4. O trabalho aqui e CPU puro (o DP das barras), e
    # thread irma nao tem unidade de calculo propria — pedir 4 numa maquina de 2
    # fisicos so faz os processos disputarem o mesmo nucleo.
    # Metade do logico e a aproximacao do fisico. Na maquina do Luis: 4 -> 2.
    NUCLEOS = max(1, (os.cpu_count() or 2) // 2)

CORTE9_LIGADO = True
CORTE11_LIGADO = os.environ.get('CORTE11', '1') != '0'   # grupos de efeito identico
# ⚠️ 08/08/2026 — O CORTE 9 EXISTE e a linha abaixo NAO e morta.
#   motor.py de 37.702 bytes, linha 437:  if globals().get('CORTE9', True) ...
#   E a PODA POR DOMINANCIA (05/08 noite): assinatura que e >= outra em TODO atributo
#   com peso domina, e a dominada nunca pode ser a unica dona do otimo. Chance zero:
#   nao perde o otimo, so corta dominado.
#   POR QUE PRECISA: a regra da metade acabou com a colisao de assinaturas do CORTE 8,
#   e o lote pulou de ~80 s para mais de 900 s. Sem CORTE 9 a rodada foi medida em 29 h.
#   ⛔ O motor.py de 35.222 bytes (o que estava no GitHub e na pasta) NAO TEM o CORTE 9.
#      Conferir sempre: motor.py tem que ter o CORTE 9 (era 37.702 bytes; com o CORTE 11 passou de 39.700).
#   ⚠️ NAO CONFUNDIR com TETO_PUN = 9 do regua.py — aquele e a punicao que para no 9o
#      ponto, constante, sem liga/desliga. Coincidencia infeliz de numero.
D, SAIDA, FILA = 'dados/', 'saida_v6/', 'fila_v6.json'
LINHAS  = 'saida_v6/linhas.jsonl'   # uma linha de resultado por linha do arquivo
EFHUB   = 'cards_efhub.json'   # o que o alimentador trouxe — NUNCA escreve no cards.json
EXTRA   = 'fila_EXTRA.json'
FEITOS  = 'feitos.txt'
PARAR   = 'PARAR.txt'
ESPERA  = 60          # segundos entre uma olhada e outra no fila_EXTRA.json

def agora(): return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def hms(s):
    s = int(max(0, s)); return '%02d:%02d:%02d' % (s // 3600, s % 3600 // 60, s % 60)

_W = {}

# ============================================================================
#  DENTRO DE UMA RODADA, SO O cards.json PODE CRESCER. TODO O RESTO E CONGELADO.
#
#  recarrega ... dados/cards.json e cards_efhub.json — semantica de ACRESCIMO:
#                card novo entra; card que ja rodou nao e recalculado, entao mudar
#                nao retroage.
#  CONGELADOS .. falta_por_card.json · raras_por_card.json · molde.json ·
#                tecnicos.json · HAB_EFEITOS_FINAL.json
#
#  POR QUE: o `falta` nao e dado do card, e o ESPACO DE BUSCA do motor. Duas linhas
#  da mesma rodada com pools diferentes NAO sao comparaveis — Musiala mediu 57,7 com
#  pool 5 e -135,5 com pool 0. Se o arquivo mudasse no meio, o lote 3 e o lote 90
#  seriam pontuados sob regras diferentes e o ranking misturaria os dois, sem ninguem
#  ver, porque as duas notas saem com cara de normal. O `raras` idem: entra na conta
#  pela regra da metade (sum(pc_rar) no equacao.py).
#
#  O mtime dos cinco congelados vai gravado EM CADA LINHA (campo `insumos`), para que
#  "sera que mudou no meio?" seja uma consulta, nao uma suspeita.
# ============================================================================

CONGELADOS = [D + 'falta_por_card.json', D + 'raras_por_card.json', D + 'molde.json',
              'tecnicos.json', 'HAB_EFEITOS_FINAL.json']

# efHub manda nestes campos; `falta` e `raras` sao derivacao local e NAO vem dele.
EFHUB_MANDA = ('base', 'max_ovr', 'orc', 'dt', 'sl', 'fab', 'pos', 'np', 'sec',
               'modelo', 'altura', 'peso', 'pe', 'ovr', 'nome', 'levelCap',
               'boostId', 'boostId2')


# ============================================================================
#  O CARIMBO DAS REGRAS (ordem do Luis, 09/08)
#  "se mudar alguma coisa, a gente tem que separar o que ja foi rodado do que nao
#   foi, porque o que foi rodado errado tem que voltar pra fila com a regra certa."
#
#  Cada linha sai com este carimbo. O REVISAR-FILA.bat compara o carimbo da linha
#  com o carimbo de agora e devolve para a PONTA da fila tudo que esta defasado,
#  dizendo O QUE mudou. Assim nao existe mais linha velha com regra nova no mesmo
#  ranking, e ninguem precisa lembrar de nada.
#
#  ⚠️ MUDOU A LOGICA DO CODIGO (nao um arquivo)? Suba o VERSAO_REGRAS. E o unico
#     jeito de o sistema saber que a conta de ontem nao vale mais.
# ============================================================================
VERSAO_REGRAS = 6      # 6 = tabela de posicao + super substituto + 3 degraus do
                       #     condicional + trava da data com lista de conferidos

ARQUIVOS_DE_REGRA = [
    D + 'molde.json', D + 'falta_por_card.json', D + 'raras_por_card.json',
    'tecnicos.json', 'HAB_EFEITOS_FINAL.json',
    'habilidades_por_posicao.json', 'impeto_conferido_no_jogo.json',
    'ids_sem_vaga_pela_data.json',
]


def _carimbo_das_regras():
    c = {'v': VERSAO_REGRAS, 'pool': POOL,
         'fonte': 'base_unica' if FONTE_UNICA else 'cards.json+efhub',
         'corte10': bool(CORTE10), 'corte11': bool(CORTE11_LIGADO),
         'corte9': bool(CORTE9_LIGADO), 'margem': 'sem corte (1e18)'}
    for p_ in ARQUIVOS_DE_REGRA:
        try:    c[os.path.basename(p_)] = int(os.path.getmtime(p_))
        except Exception: c[os.path.basename(p_)] = None
    return c


def _carimbo_dos_insumos():
    c = {}
    for p in CONGELADOS:
        try:    c[os.path.basename(p)] = int(os.path.getmtime(p))
        except Exception: c[os.path.basename(p)] = None
    return c


# ============================================================================
#  FONTE UNICA  (Luis, 14/08/2026)
#  "O motor tem que procurar num lugar so."
#
#  Com o arquivo FONTE-UNICA.txt na pasta, o motor para de montar o card lendo
#  cards.json + cards_efhub.json e passa a ler dados/base_unica.json — que E o
#  resultado desse mesmo merge, ja feito pelo unificar_base.py obedecendo o
#  precedencia.json, a trava da data e o CONFERIDO.json.
#
#  Sem o arquivo, nada muda: o motor se comporta exatamente como antes.
#  Para ver a diferenca ANTES de ligar, rode o PROVAR-FONTE-UNICA.bat.
# ============================================================================
# ⛔ 27/08 — SEM INTERRUPTOR. A fonte e o BANCO, sempre. Nao existe mais
#    FONTE-UNICA.txt nem GRAVA-DIRETO.txt: o motor le e grava no banco e ponto.
FONTE_UNICA = True

try:
    import grava_direto as _gd
except Exception:
    class _gd:                      # sem o modulo, tudo segue como antes
        LIGADO = False
        junta = staticmethod(lambda *a, **k: None)
        descarrega = staticmethod(lambda: None)
        resumo = staticmethod(lambda: 'grava direto: modulo ausente')


def _mtime_das_fontes():
    """O carimbo que diz 'a fonte mudou, recarrega'."""
    if FONTE_UNICA:
        import fonte_unica as _fu
        return (_fu.carimbo() or 0, 0)
    return (os.path.getmtime(D + 'cards.json'),
            os.path.getmtime(EFHUB) if os.path.exists(EFHUB) else 0)


def _recarrega_cards_da_base():
    """A fonte unica: dados/base_unica.json e mais nada."""
    import fonte_unica
    _W['BASE'] = fonte_unica.carrega_base()
    _W['mtime'] = _mtime_das_fontes()


def _insumos_da_base():
    """MOLDE, TECNICOS, HABILIDADES e BLOQUEIO — todos do mesmo arquivo.

    Ordem do Luis, 14/08/2026: "o motor tem que procurar num lugar so".
    Antes: o motor abria dados/molde.json, tecnicos.json, HAB_EFEITOS_FINAL.json
    e habilidades_por_posicao.json, cada um por fora. Agora sai tudo da base.

    Se a base estiver velha (sem os insumos dentro), ele PARA e avisa — nao cai
    de volta nos arquivos calado, que era como o defeito do "Dominio aereo"
    passou dias sem ninguem ver.
    """
    import fonte_unica
    b = fonte_unica.carrega_tudo()
    faltam = [k for k in ('molde', 'tecnicos_catalogo', 'habilidades', 'bloqueio')
              if not b.get(k)]
    if faltam:
        raise SystemExit(
            '\n  PARE. A fonte unica esta ligada mas a base nao tem os insumos: %s\n'
            '  A base e velha. Rode o UNIFICAR-BASE.bat e comece de novo.\n'
            % ', '.join(faltam))
    return b


def _recarrega_cards():
    """Rele SO as duas fontes de card. O alimentador acrescenta card com o motor
    rodando, e o processo filho carregou a versao antiga no arranque — sem isto, card
    novo daria 'nao esta no cards.json' e cada filho vive a rodada inteira.

    NAO rele falta_por_card nem raras_por_card: sao congelados (ver o bloco acima)."""
    if FONTE_UNICA:
        return _recarrega_cards_da_base()
    base = {}
    for c in json.load(open(D + 'cards.json', encoding='utf-8')):
        b = str(c['id']).split('@')[0]
        if b not in base or (c.get('orc') or 0) > (base[b].get('orc') or 0):
            base[b] = c

    # cards_efhub.json — o que o alimentador trouxe. Precedencia POR CAMPO.
    if os.path.exists(EFHUB):
        try:
            for c in json.load(open(EFHUB, encoding='utf-8')):
                b = str(c['id']).split('@')[0]
                if b in base:
                    for k in EFHUB_MANDA:
                        if c.get(k) is not None:
                            base[b][k] = c[k]
                else:
                    base[b] = c
        except Exception:
            pass

    _W['BASE'] = base
    _W['mtime'] = _mtime_das_fontes()


def _carrega_no_processo():
    from equacao import carrega_tecnicos
    import motor as M
    # 🔴 MEDIDO EM 08/08 18:03 — A MARGEM DO MOTOR **NAO** E EXATA. NAO DESLIGUE O 1e18.
    #   Paul Scholes / Volante de construcao:
    #       sem corte (1e18) .... b1 124,90  ·  4953,3 s
    #       margem do motor ..... b1  69,40  ·    51,2 s   -> PERDEU 55,50 PONTOS
    #   Por que: a MARG do motor limita so o que o TECNICO pode virar (2 atributos,
    #   +1 em cada). Foi deduzida ANTES do pool de habilidades existir. Com a
    #   habilidade entrando depois, o impeto cortado por estar "55 abaixo" volta a
    #   ganhar. O teto e invalido — era o aviso da sessao que criou o corte.
    #   Ordem do Luis: "vai entregar a melhor combinacao possivel". Logo SEM CORTE.
    M.MARG_OVERRIDE = 1e18
    M.TABELA_DP = 'regua'
    M.CORTE9 = CORTE9_LIGADO
    M.CORTE11 = CORTE11_LIGADO
    MOLDE = collections.defaultdict(list)
    if FONTE_UNICA:
        _b = _insumos_da_base()
        for r in _b['molde']:
            MOLDE[r['funcao']].append([r['attr'], r['peso'], r['alvo'], 0, 0, 0])
        _W['INSUMOS_BASE'] = _b
    else:
        for r in json.load(open(D + 'molde.json', encoding='utf-8')):
            MOLDE[r['funcao']].append([r['attr'], r['peso'], r['alvo'], 0, 0, 0])
    _W['M'] = M
    _W['MOLDE'] = MOLDE
    _W['TECS'] = carrega_tecnicos('tecnicos.json')
    _W['RARAS'] = json.load(open(D + 'raras_por_card.json', encoding='utf-8'))
    _W['FALTA'] = json.load(open(D + 'falta_por_card.json', encoding='utf-8'))
    _W['INSUMOS'] = _carimbo_dos_insumos()
    _W['REGRAS'] = _carimbo_das_regras()
    _recarrega_cards()
    _W['COMUNS'] = _comuns_do_jogo(_W['BASE'])
    _W['FILA'] = _fila_incid()

# ====================== A REGRA DO POOL (Luis, 08/08) ======================
# "Nao se faz escolha por quantidade de incidencia na comunidade. Faz escolha pelo
#  motor, no qual e o que da mais pontos. Quando ha um empate, olha-se o que a
#  comunidade escolhe. Essa e a regra."
#
# Logo o pool NAO e a lista da comunidade. O pool e o que o JOGO permite:
#   as 44 habilidades COMUNS menos as que o card ja tem.
# As 17 raras nao entram: sao inerentes ao card, nunca se adicionam.
# A incidencia da comunidade entra so como DESEMPATE, e disso o proprio motor
# cuida — pelo parametro fila_incid de build_completo2().
#
# O que estava errado: a lista da comunidade fazia papel de filtro de
# elegibilidade. Card com 9 nativas recebia 2 candidatas em vez de 35, e o motor
# levava as 2 sem escolher nada (motor.py: `if len(cand) <= 5: combos=[cand]`).
POOL = os.environ.get('POOL', 'regra')     # regra | uniao | atual | novo
CORTE10 = os.environ.get('CORTE10', '1') != '0'   # dominancia entre habilidades


def _comuns_do_jogo(base):
    """as habilidades COMUNS (adicionaveis) do jogo.

    Fonte: HAB_EFEITOS_FINAL.json, campo `tipo`.

    ⛔ 08/08: o 'Puxada e tapa' estava marcado comum na tabela e ELE E RARA (ordem do
    Luis). Corrigido NA PROPRIA TABELA (tapTrick.tipo = 'rara'), que e a fonte que o
    equacao.py tambem le para decidir competir x somar. Agora: 44 COMUNS e 18 RARAS,
    e nao precisa de excecao nenhuma aqui."""
    try:
        import fonte_unica as _FUh
        H = _FUh.catalogo_habilidades()
        c = {v['arquivo'] for v in H.values() if v.get('tipo') == 'comum'}
        if c: return c
    except Exception as e:
        print('nao consegui ler HAB_EFEITOS_FINAL: %s — caio no vocabulario da base' % e)
    fab = set(); rar = set()
    for x in base.values():
        fab |= set(x.get('fab') or []); rar |= set(x.get('raras') or [])
    return fab - rar


# ⛔ 08/08 (Luis, vendo o Sneijder MC armador com "Repos. baixa do GO" adicionada):
# "tem algumas habilidades que nao podem ser utilizadas para outras posicoes".
# As 6 habilidades de goleiro da tabela (chave gk* no HAB_EFEITOS_FINAL.json) so
# entram em funcao de GOLEIRO. Nao e cosmetico: a `gkLowPunt` mexe no atributo 4
# (+2%), que tem peso em funcao de meio — o motor estava comprando ponto com uma
# habilidade que o jogo nao deixa por num jogador de linha.
def _habs_de_goleiro():
    try:
        import fonte_unica as _FUg
        return _FUg.habilidades_de_goleiro()
    except Exception as e:
        raise SystemExit('PAROU: nao consegui a lista de habilidades de goleiro '
                         'do banco (%s). Sem ela o motor poe habilidade de GO '
                         'em jogador de linha.' % e)


def _habs_so_de_linha(base):
    """as habilidades que NUNCA aparecem de fabrica num goleiro — evidencia da
    propria base, nao chute: 39 delas, de '360 graus' a 'Xerifao'.

    MEDIDO 08/08: nas duas funcoes de goleiro, dessas 39 SO a 'Fortaleza aerea'
    mexe em atributo com peso — e ela e RARA, nunca se adiciona. Logo tirar as 39
    do pool de goleiro custa ZERO ponto e ainda encurta o pool. O que ela conserta
    e a tela: o motor estava enfiando '360 graus' e 'Passe em profundidade' no
    Neuer e no Vozinha, que o jogo nao deixa."""
    gk, li = set(), set()
    for c in base.values():
        p = str(c.get('np') or c.get('pos') or '')
        alvo = gk if p in ('GK', 'GO', 'Goleiro') else li
        for h in (c.get('fab') or []) + (c.get('raras') or []):
            alvo.add(h)
    return li - gk


# ================ TABELA DE POSICAO (ordem do Luis, 09/08) ================
# habilidades_por_posicao.json: habilidade -> grupos de posicao onde ela NAO pode
# entrar. E a "Tabela Definitiva" que o Luis passou, 37 habilidades. O arquivo e a
# fonte — para mudar uma regra, mexe no JSON, nao no codigo.
def _bloqueio_por_funcao():
    """{funcao: set(habilidades proibidas)}"""
    try:
        J = (_W.get('INSUMOS_BASE') or {}).get('bloqueio') if FONTE_UNICA else None
        if not J:
            J = json.load(open('habilidades_por_posicao.json', encoding='utf-8'))
    except Exception as e:
        print('nao consegui ler habilidades_por_posicao.json (%s) — sem bloqueio' % e)
        return {}
    G = J.get('_posicoes') or {}
    out = collections.defaultdict(set)
    for hab, grupos in (J.get('bloqueios') or {}).items():
        for g in grupos:
            for f in G.get(g, []):
                out[f].add(hab)
    return out


def _pool_de(c, bid, funcao=None):
    if POOL == 'regra':
        tem = set(c.get('fab') or []) | set(c.get('raras') or [])
        p = _W['COMUNS'] - tem
        if funcao:
            # 1) a tabela do Luis (explicita, manda)
            p = p - _W.setdefault('BLOQ', _bloqueio_por_funcao()).get(funcao, set())
            # 2) e a inferencia da base para goleiro: habilidade que nunca aparece
            #    de fabrica em goleiro nao entra em goleiro. Medido: custo ZERO ponto.
            if 'Goleiro' in funcao:
                p = p - _W.setdefault('SO_LINHA', _habs_so_de_linha(_W['BASE']))
            else:
                p = p - _W.setdefault('GK_HABS', _habs_de_goleiro())
        return sorted(p)
    a = set(c.get('falta') or []); n = set(_W['FALTA'].get(bid) or [])
    if POOL == 'atual': return sorted(a)
    if POOL == 'novo':  return sorted(n)
    return sorted(a | n)


def _fila_incid():
    """a tabela FILA (incidencia por funcao) da casca do encaixe — o DESEMPATE."""
    for p in ('encaixe/encaixe_B_v171_datas_tela.html',
              'encaixe_B_v171_datas_tela.html'):
        if os.path.exists(p):
            try:
                s = open(p, encoding='utf-8', errors='replace').read()
                i = s.find('const FILA=') + 11; j = s.find('};', i)
                F = json.loads(s[i:j + 1])
                return {k: {h: v for h, v in (F.get(k) or [])} for k in F}
            except Exception as e:
                print('nao consegui ler a FILA de %s: %s' % (p, e))
    return {}

def trabalha(r):
    """UMA linha card x funcao. Devolve o resultado COM A CADEIA INTEIRA."""
    t0 = time.time()
    if not _W: _carrega_no_processo()
    M = _W['M']
    bid = str(r['card_id']).split('@')[0]
    c0 = _W['BASE'].get(bid)
    if not c0:
        # pode ser card que o alimentador acrescentou depois deste processo nascer
        try:
            atual = _mtime_das_fontes()
            if atual != _W.get('mtime'):
                _recarrega_cards()
                c0 = _W['BASE'].get(bid)
        except Exception:
            pass
    if not c0:
        return {'ERRO': 'card %s nao esta no cards.json' % bid, 'n': r.get('n')}
    c = dict(c0)
    c['arows'] = [x[:] for x in _W['MOLDE'][r['funcao']]]
    c['raras'] = _W['RARAS'].get(bid, [])
    c['falta'] = _pool_de(c, bid, r['funcao'])
    c['pool_cheio'] = list(c['falta'])   # guardado para a lista "De fora" da ficha

    # ===== HABILIDADE VETADA SAI DO POOL ANTES DA BUSCA (Luis, 10/08) =====
    # "nao e mais esperto gravar as duas melhores builds e so substituir caso isso
    #  ocorra? Ja pensou refazer um card de 80 minutos so por causa disso?"
    # Ele esta certo, e da para fazer melhor: se ela NUNCA pode ser a escolha, o
    # unico resultado que interessa e o melhor SEM ela. Procurar com ela dentro e
    # refazer depois e fazer o trabalho duas vezes — num card de 80 min, vira 160.
    #
    # E EXATAMENTE EQUIVALENTE: se o otimo nao usava a vetada, tirar do pool nao
    # muda nada; se usava, o que queremos e justamente o otimo sem ela.
    # De brinde o pool encolhe, entao a busca fica MAIS RAPIDA.
    #
    #   Super substituto ....... 09/08. So vale entrando do banco.
    #   Especialista em penalti  10/08. "nao pode vir como adicional".
    # Elas continuam indo para a lista de SUGESTAO, mais abaixo.
    VETADAS = ['Super substituto', 'Especialista em pênalti']
    _forcar_sug = [h for h in VETADAS if h in c['falta']]
    if _forcar_sug:
        c['falta'] = [h for h in c['falta'] if h not in VETADAS]

    # ============== CORTE 10 — DOMINANCIA ENTRE HABILIDADES ==============
    # ✅ CHANCE ZERO. Escrito FORA do motor de proposito: o motor monta o cand com
    #    `cand = [h for h in c.get('falta') if util(h)]` (motor.py linha 374), entao
    #    tirar a dominada do `falta` encolhe o cand igual — sem tocar no congelado.
    #
    # A prova e a mesma do CORTE 9 (motor.py 413-424), no nivel da HABILIDADE:
    #   1. buff maior nunca abaixa atributo (o ganho e crescente em pct e em flat)
    #   2. a regua e crescente em cada atributo
    #   3. habilidade NAO gasta orcamento — sao 5 vagas, sempre as 5
    # Logo, se A >= B em TODO atributo com peso, trocar B por A nunca baixa a nota.
    # A regra da metade nao quebra: se A >= B componente a componente, o multiset de
    # cada atributo fica >= componente a componente, e `maior + resto/2` e monotono.
    #
    # REGRA: B sai se tiver 5 ou mais dominadores. Qualquer conjunto de 5 que
    # contenha B tem no maximo 4 dominadores dele dentro -> sobra um FORA -> a troca
    # existe -> B nunca e o unico dono do otimo.
    #
    # ⛔ REMOVE UM POR VEZ e recalcula. Se removesse todos de uma vez, 6 habilidades
    #    IDENTICAS teriam 5 dominadores cada e sairiam todas — perdendo a opcao.
    #
    # Medido em 7.090 linhas simuladas: cand mediana 23 -> 20, combinacoes 2,3x
    # menos, projecao da rodada 56 h -> 24,7 h.
    if CORTE10 and c['falta']:
        try:
            pes = sorted({r[0] for r in c['arows'] if r[1]})
            _EF = {n: v['efeito'] for n, v in M.POR_NOME.items()}

            def _vet(h):
                e = _EF.get(h) or {}
                out = []
                for i in pes:
                    d = e.get(str(i)) or e.get(i) or {}
                    out.append(d.get('pct', 0)); out.append(d.get('flat', 0))
                return tuple(out)

            uteis = [h for h in c['falta'] if any(_vet(h))]
            if len(uteis) > 5:
                V = {h: _vet(h) for h in uteis}
                vivos = list(uteis)
                while True:
                    fora = None
                    for b_ in vivos:
                        n = 0
                        for a_ in vivos:
                            if a_ != b_ and all(x >= y for x, y in zip(V[a_], V[b_])):
                                n += 1
                                if n >= 5: break
                        if n >= 5:
                            fora = b_; break
                    if fora is None: break
                    vivos.remove(fora)
                mortos = set(uteis) - set(vivos)
                if mortos:
                    c['falta'] = [h for h in c['falta'] if h not in mortos]
        except Exception:
            pass

    # REGRA 08/08 (Luis): carta que NAO EVOLUI (POTW / levelCap 1 -> orc 0) nao
    # adiciona habilidade nenhuma. Sem ponto de progressao nao ha o que gastar:
    # nela so o TECNICO mexe. Antes o motor enfiava 5 habilidades que o jogo nao
    # deixa comprar, e a nota saia inflada.
    if not (c.get('orc') or 0):
        c['falta'] = []
    try:
        b = M.build_completo2(dict(c), _W['TECS'],
                              (_W.get('FILA') or {}).get(r['funcao']))
    except Exception as e:
        return {'ERRO': '%s / %s: %s' % (c.get('nome'), r['funcao'], e), 'n': r.get('n')}
    if not b:
        return {'ERRO': '%s / %s: build vazia' % (c.get('nome'), r['funcao']), 'n': r.get('n')}

    # ===== IMPETO CONDICIONAL: as TRES notas (+1, +2, +3) =====
    # REGRA DO LUIS (05/08): "pra fins de ranking usa o impeto condicional sempre no
    # nivel 1 dele". Degraus lidos do videogame em 31/07:
    #     1 a 7 jogadores da condicao -> +1   (o ranking usa este, SEMPRE)
    #     8 a 10                      -> +2
    #     11 a 23                     -> +3
    # ⛔ O botao da tela NAO pode somar por fora: o condicional mexe em ATRIBUTO,
    #    entao trocar o degrau obriga a REFAZER as quatro escolhas do motor.
    #    Por isso aqui roda de novo, inteiro, para +2 e para +3.
    # Ordem do Luis (09/08): "sim, 1, 2 e 3" — o degrau do meio entra agora.
    #
    # ==========================================================================
    # ⛔ MUDOU EM 18/08 — NAO VOLTAR AO PALPITE
    # ==========================================================================
    #   Estava assim:
    #       _pos = [k for k, x in enumerate(_nm) if x and int(x[1]) == 1]
    #   com o comentario: "o condicional e gravado em nivel 1; impeto normal vem
    #   em +2/+3/+4/+5; logo entrada do `nm` com valor 1 = condicional".
    #
    #   ISSO E PALPITE, E ESTA ERRADO. Existe impeto FIXO entregue em nivel 1.
    #   Medido em 18/08 nas 12.368 linhas: 56 cartas ganharam degrau 2 e 3 sem
    #   ser condicionais — e a fonte dizia, com todas as letras, que NAO eram:
    #       Messi 90       Fisica +1 · Accuracy +4        fonte: [false, false]
    #       Neuer 88       Passe +1 · Defesaca +3         fonte: [false, false]
    #       De Bruyne 87   Agilidade +1 · Precisao +3     fonte: [false, false]
    #       Haaland 87     Vigor Fisico +1 · Chute +3     fonte: [false, false]
    #       Kane 87        Conducao Tecnica +1 · Chute +3 fonte: [false, false]
    #   (o ACHADO-1608-I ja tinha avisado disso, e o palpite continuou aqui)
    #
    #   Ordem do Luis, 18/08: "isso nao e um conserto pontual, tem que deixar o
    #   sistema funcionar assim, senao daqui a pouco tem o mesmo problema."
    #
    #   AGORA A PERGUNTA E FEITA A FONTE, nao ao numero:
    #       `impeto_condicional` e uma lista de sim/nao, uma por impeto da carta.
    #       Sem sim nenhum -> NAO EXISTE DEGRAU. `cond` fica vazio, e pronto.
    #   E quais posicoes do `nm` subir sai dos ATRIBUTOS do impeto condicional,
    #   lidos do catalogo (CAT_dom.json, que desce do banco) — nao do valor.
    # ==========================================================================
    cond = {}
    try:
        _nm = c.get('nm') or []
        _flags = c.get('impeto_condicional')
        _tem_cond = isinstance(_flags, list) and any(bool(x) for x in _flags)
        _pos = []
        if _tem_cond:
            _nomes = c.get('impeto_nomes') or []
            _alvo = set()
            for _i, _f in enumerate(_flags):
                if not _f or _i >= len(_nomes):
                    continue
                for _a in _atributos_do_impeto(_nomes[_i]):
                    _alvo.add(int(_a))
            if _alvo:
                # so sobem os atributos DO impeto condicional
                _pos = [k for k, x in enumerate(_nm)
                        if x and int(x[0]) in _alvo]
            elif len([1 for _f in _flags if _f]) == len(_flags) or len(_nomes) <= 1:
                # o catalogo nao conhece o nome, mas a carta so tem impeto
                # condicional: entao todo o `nm` e dele. Nao ha o que confundir.
                _pos = [k for k, x in enumerate(_nm) if x]
            else:
                # carta com dois impetos e catalogo sem o nome do condicional:
                # nao da pra separar qual atributo e de qual. NAO CHUTA.
                _pos = []
        if _pos:
            for _grau in (2, 3):
                _nmk = [(list(x) if x else x) for x in _nm]
                for k in _pos:
                    _nmk[k][1] = _grau
                _ck = dict(c); _ck['nm'] = _nmk
                _bk = M.build_completo2(dict(_ck), _W['TECS'],
                                        (_W.get('FILA') or {}).get(r['funcao']))
                if _bk:
                    cond[str(_grau)] = {
                        'b1': round(_bk['nota'], 4), 'barras': _bk.get('lvl'),
                        'vals': _bk.get('vals'), 'impeto': _bk.get('fab'),
                        'tecnico': _bk.get('tecnico'), 'tecnico_id': _bk.get('tecnico_id'),
                        'boost_tecnico': _bk.get('boost'),
                        'habilidades': _bk.get('habilidades', []),
                        'sobra': _bk.get('sobra'),
                    }
    except Exception as e:
        cond = {'ERRO': str(e)}

    # ===== "DE FORA" — as que da pra selecionar e NAO MUDAM A NOTA =====
    # Ordem do Luis (08/08): a caixa de habilidades tem tres listas — nativas,
    # adicionadas e "de fora", com SO as que pode selecionar e nao vai alterar nada
    # na nota. "Seja porque valem zero, seja porque valem doze, tanto faz."
    # TETO 5. Quais cinco? As mais INCIDENTES na comunidade — regra dele: pontos
    # decidem, e quando a nota nao muda a comunidade desempata.
    #
    # DE GRACA: e a mesma assinatura de efeito que o CORTE 8 do motor usa para
    # deduplicar. Nao roda DP nenhum. Medido: ~0,005 s por linha (~36 s em 8.144).
    neutras = []
    try:
        esc = list(b.get('habilidades') or [])
        pes = {r[0] for r in c['arows'] if r[1]}
        fixas = list(c.get('fab') or []) + list(c.get('raras') or [])

        def _sig(hs):
            bf = M.buff_de(hs)
            return tuple(sorted((i, p, f) for i, (p, f) in bf.items() if i in pes))

        base = _sig(fixas + esc)
        for cand in (c.get('pool_cheio') or c.get('falta') or []):
            if cand in esc or cand in neutras:
                continue
            for h in esc:
                if _sig(fixas + [x for x in esc if x != h] + [cand]) == base:
                    neutras.append(cand); break
        _inc = (_W.get('FILA') or {}).get(r['funcao']) or {}
        neutras.sort(key=lambda h: (-_inc.get(h, 0), h))
        if _forcar_sug:
            neutras = list(_forcar_sug) + [h for h in neutras if h not in _forcar_sug]
        neutras = neutras[:5]
    except Exception:
        neutras = []

    # ===== QUANTO A VETADA VALERIA (Luis, 10/08) =====
    # "se voce vetar o super substituto e o especialista em penalti, como que a gente
    #  vai saber que elas podem ser boas?"
    # Sem isso, a vetada iria para a sugestao SEMPRE — viraria ruido, nao informacao.
    # Aqui a gente mede, de graca: pega a build campea e troca cada uma das 5
    # escolhidas pela vetada, MANTENDO barras, impeto e tecnico. A melhor troca vira
    # o ganho dela. Nao roda DP nenhum — sao 5 contas de nota por vetada.
    # O numero e um PISO: com as barras reotimizadas ela poderia render um pouco
    # mais. Se ja der positivo aqui, e porque ela e boa de verdade.
    vetada_vale = {}
    try:
        if _forcar_sug and b.get('lvl') is not None:
            _fix = list(c.get('fab') or []) + list(c.get('raras') or [])
            _esc = list(b.get('habilidades') or [])
            _m = b.get('m') or 1.0
            _add = b.get('add')
            _n0 = b.get('nota')

            def _nota_com(hs):
                _bf = M.buff_de(hs)
                _cd = M.Card(dict(c), m=_m, bf=(_bf or None))
                return M.notaDe(_cd.vals_finais(b['lvl'], _add), _cd.arows)

            _base = _nota_com(_fix + _esc)
            for _v in _forcar_sug:
                _melhor, _troca = None, None
                for _h in _esc:
                    _cand = [x for x in _esc if x != _h] + [_v]
                    _d = _nota_com(_fix + _cand) - _base
                    if _melhor is None or _d > _melhor:
                        _melhor, _troca = _d, _h
                if _melhor is not None:
                    vetada_vale[_v] = {'ganho': round(float(_melhor), 2),
                                       'no_lugar_de': _troca,
                                       'seria_escolhida': bool(_melhor > 1e-9)}
    except Exception as _e:
        vetada_vale = {'ERRO': str(_e)}

    # a sugestao so mostra a vetada quando ela REALMENTE valeria a pena
    try:
        for _v in list(_forcar_sug or []):
            _info = vetada_vale.get(_v) or {}
            if not _info.get('seria_escolhida'):
                neutras = [h for h in neutras if h != _v]
    except Exception:
        pass

    # ===== TECNICO: os outros que dao a MESMA nota (Luis, 08/08) =====
    # "pode ter algum outro que tambem seja otimizado, so nao apareceu na tela."
    #
    # O tecnico entra na conta por DUAS coisas so: o multiplicador `m` e a lista de
    # atributos que ele boosta (+1 em cada). Logo dois tecnicos dao nota IDENTICA se:
    #   1. tem o MESMO m, e
    #   2. a diferenca entre os conjuntos de boost cai SO em atributo que a funcao
    #      NAO pesa — porque a nota le apenas os atributos com peso.
    #
    # ⛔ A primeira versao disto exigia o MESMO conjunto de boost (o caso de diferenca
    #    vazia). Medido em 114 linhas: ZERO empates — estreito demais, inutil na tela.
    #    Nao voltar para aquilo.
    #
    # Por que nao aceito "o atributo esta em 99, o +1 se perde": nao da para provar
    # pelo vals_tela, que ja vem COM o +1 do tecnico escolhido — 99 ali pode ser 98+1
    # (o boost contou) ou 99 travado (nao contou). Sem distinguir, seria chute.
    tecnicos_iguais = []
    try:
        pes_t = {r[0] for r in c['arows'] if r[1]}

        def _idx(x):
            if isinstance(x, int): return x
            try: return M.POS[x]
            except Exception: return None

        _bo = {_idx(x) for x in (b.get('boost') or [])}
        _bo.discard(None)
        _m = b.get('m')
        for t in _W['TECS']:
            # ⛔ 14/08: casa por ID. Antes casava por nome e havia 5 Mourinhos.
            _mesmo = (t.get('id') == b.get('tecnico_id')) if b.get('tecnico_id') \
                     else (t['nome'] == b.get('tecnico'))
            if _mesmo or t['m'] != _m:
                continue
            outro = {_idx(x) for x in (t.get('boost') or [])}
            outro.discard(None)
            if not ((_bo ^ outro) & pes_t):      # a diferenca so cai onde peso = 0
                tecnicos_iguais.append(t['nome'])
        tecnicos_iguais = sorted(set(tecnicos_iguais))[:5]
    except Exception:
        tecnicos_iguais = []

    arows = c['arows']
    alvo = {a[0]: a[2] for a in arows}
    peso = {a[0]: a[1] for a in arows}
    v_carta = b.get('vals_carta') or []
    v_tela  = b.get('vals_tela') or []
    v_final = b.get('vals') or []
    base    = c.get('base') or []
    if isinstance(base, str): base = json.loads(base)

    cadeia = []
    for i in range(len(v_final)):
        e0 = base[i] if i < len(base) else None
        e1 = v_carta[i] if i < len(v_carta) else None
        e2 = v_tela[i]  if i < len(v_tela)  else None
        e3 = v_final[i]
        al = alvo.get(i)
        cadeia.append({'attr': i, 'peso': peso.get(i, 0), 'alvo': al,
                       'base': e0, 'com_barras': e1, 'na_tela': e2, 'final': e3,
                       'vs_alvo': (None if al is None else round(e3 - al, 2))})

    return {
        'n': r.get('n'), 'card_id': bid, 'nome': c.get('nome'),
        'funcao': r['funcao'], 'origem': r.get('origem'), 'estilo': r.get('estilo'),
        'tier': r.get('tier'), 'ovr': r.get('ovr'), 'orc': c.get('orc'),
        'box': r.get('box'),   # de qual campanha o card veio (so os da home)
        'b1': round(b['nota'], 4),
        'barras': b.get('lvl'), 'vals': v_final,
        'impeto': b.get('fab'), 'tecnico': b.get('tecnico'),
        # ⛔ 14/08: a linha passou a guardar o ID do tecnico.
        # Sao 1.664 tecnicos e 1.528 nomes: 5 "Jose Mourinho" diferentes,
        # 4 "F. Beckenbauer". So o nome nao diz qual entrou na build.
        'tecnico_id': b.get('tecnico_id'),
        'habilidades': b.get('habilidades', []),
        'neutras': neutras,
        'vetada_vale': vetada_vale,           # quanto a vetada valeria, e no lugar de quem
        'tecnicos_iguais': tecnicos_iguais,   # outro tecnico, mesma nota exata
        # as tres notas do impeto condicional: a oficial (nivel 1) e o b1 acima;
        # cond['2'] e cond['3'] sao os degraus, cada um com a build INTEIRA.
        'cond': cond,
        'pool': POOL, 'n_pool': len(c['falta']),
        'cadeia': cadeia,
        'vals_carta': v_carta, 'vals_tela': v_tela,
        'buff': {str(k): v for k, v in (b.get('buff') or {}).items()},
        'boost_tecnico': b.get('boost'), 'add': b.get('add'),
        'sobra': b.get('sobra'), 'pool_disponivel': c['falta'],
        'segundos': round(time.time() - t0, 2), 'quando': agora(),
        'insumos': _W['INSUMOS'],
        'regras': _W['REGRAS'],        # o carimbo — ver REVISAR-FILA.bat
    }

# ------------------------------------------------------------------ feitos

def chave(r): return '%s|%s' % (str(r['card_id']).split('@')[0], r['funcao'])


def carrega_feitos():
    """Reconstroi o que ja foi resolvido, olhando a saida de verdade."""
    feitos = set()
    if os.path.exists(LINHAS):
        with open(LINHAS, encoding='utf-8') as f:
            for l in f:
                l = l.strip()
                if not l: continue
                try:
                    x = json.loads(l)
                    if x.get('card_id') and x.get('funcao'):
                        feitos.add('%s|%s' % (x['card_id'], x['funcao']))
                except Exception:
                    pass                      # linha cortada no meio de uma queda
    if os.path.isdir(SAIDA):                  # lotes das rodadas antigas
        for f in sorted(os.listdir(SAIDA)):
            if not f.endswith('.json'): continue
            try:
                for x in json.load(open(SAIDA + f, encoding='utf-8')):
                    if x.get('card_id') and x.get('funcao'):
                        feitos.add('%s|%s' % (x['card_id'], x['funcao']))
            except Exception:
                pass
    if os.path.exists(FEITOS):
        with open(FEITOS, encoding='utf-8') as f:
            for l in f:
                l = l.strip()
                if l: feitos.add(l)
    return feitos


def le_extra():
    if not os.path.exists(EXTRA): return []
    try:
        d = json.load(open(EXTRA, encoding='utf-8'))
        return d if isinstance(d, list) else []
    except Exception:
        return []   # arquivo sendo escrito neste instante — olha de novo depois


# ⛔ 18/08 — O MOTOR AVISA QUE ESTA VIVO.
#    ORDEM DO LUIS: "voce nao tem que esperar coletar tudo pra rodar o motor.
#    Voce coleta, poe o motor pra rodar, VOLTA e coleta mais ENQUANTO ele esta
#    rodando, e alimenta ele de novo."
#    Para os dois andarem juntos, a rodada precisa saber se o motor ja esta de
#    pe — senao abriria um segundo. Este carimbo responde isso: o motor escreve
#    a hora a cada linha. Carimbo velho (mais de 15 min) = motor morreu.
VIVO = 'MOTOR-VIVO.txt'


def carimba_vivo(quantas=0, faltam=0):
    try:
        with open(VIVO, 'w', encoding='utf-8', newline='') as f:
            f.write('%s\n%d prontas nesta sessao\n%d na fila\n'
                    % (agora(), quantas, faltam))
    except Exception:
        pass


def apaga_o_vivo():
    try:
        if os.path.exists(VIVO):
            os.remove(VIVO)
    except Exception:
        pass

# ------------------------------------------------------------------ main

def main():
    import multiprocessing as mp
    os.makedirs(SAIDA, exist_ok=True)
    if os.path.exists(PARAR): os.remove(PARAR)

    # ⛔ 27/08 — A FILA VEM DO BANCO, nao do fila_v6.json.
    #    Ordem: prioridade 0 = as que JA RODARAM antes (para conferir a migracao
    #    e parar cedo se divergir), depois lancamento, depois overall desc.
    import fonte_unica as _fu
    _lote = _fu.proxima_fila(1000000)
    fila = [{'n': i + 1, 'card_id': str(x['card_id']), 'funcao': x['funcao_codigo']}
            for i, x in enumerate(_lote)]
    feitos = set()          # quem ja rodou nao volta: ele sai da fila ao gravar
    n_proc = NUCLEOS

    print('=' * 70)
    print('  MOTOR DO ENCAIXE — RODADA v6  ·  linha por linha · entrada quente')
    print('=' * 70)
    print('inicio ............ %s' % agora())
    print('fila principal .... %d linhas (do banco, ja na ordem)' % len(fila))
    print('ja resolvidas ..... %d' % len(feitos))
    from regua import TETO_PUN
    import motor as _M
    _tam = os.path.getsize(os.path.join(os.path.dirname(os.path.abspath(_M.__file__)), 'motor.py'))
    _fonte = open(_M.__file__, encoding='utf-8', errors='replace').read()
    _tem9 = 'CORTE9' in _fonte
    _tem11 = '_combos_por_grupo' in _fonte
    print('pool .............. %s%s' % (POOL.upper(), ' + CORTE10' if CORTE10 else ' (CORTE10 DESLIGADO)'))
    print('travas ............ CORTE11 %s · CORTE8 %s · CORTE9 %s · TETO_PUN %d · TABELA_DP regua'
          % ('LIGADO' if (_tem11 and CORTE11_LIGADO) else ('DESLIGADO' if _tem11 else 'NAO EXISTE NESTE motor.py'),
             'LIGADO' if getattr(_M, 'CORTE8', True) else 'DESLIGADO',
             'LIGADO' if (_tem9 and CORTE9_LIGADO) else 'NAO EXISTE NESTE motor.py',
             TETO_PUN))
    print('motor.py .......... %d bytes %s' % (_tam, 'OK' if _tem9 else
          '⛔ SEM O CORTE 9 — tem que ter o CORTE 9 (era 37.702 bytes; com o CORTE 11 passou de 39.700)'))
    if not _tem9:
        print()
        print('⛔ PARANDO. Este motor.py nao tem a poda por dominancia (CORTE 9).')
        print('   Sem ela a rodada custa 29 h em vez de bem menos, e o lote pula de')
        print('   ~80 s para mais de 900 s. Troque o motor.py antes de rodar.')
        return
    print('nucleos ........... %d processos · %d logicos (~%d fisicos)'
          % (n_proc, os.cpu_count() or 1, max(1, (os.cpu_count() or 2) // 2)))
    print('gravacao .......... 1 linha por vez, em %s' % LINHAS)
    print('entrada quente .... jogue card novo em %s a qualquer hora' % EXTRA)
    print('para fechar ....... feche a janela, ou crie o arquivo PARAR.txt')
    print('fonte ............. o BANCO (clube.carta_jogo + as reguas)')
    print('volta ............. o BANCO (clube.build) — a linha sai da fila ao gravar')
    print('=' * 70, flush=True)

    pool = mp.Pool(processes=n_proc) if n_proc > 1 else None
    log  = open('log_v6.txt', 'a', encoding='utf-8')
    # marca no ARQUIVO onde esta rodada comecou — o VIGIA.bat usa isto para nao
    # misturar os numeros de uma rodada com os da anterior.
    log.write('\ninicio ............ %s\n' % agora()); log.flush()
    fh   = open(FEITOS, 'a', encoding='utf-8')
    out  = open(LINHAS, 'a', encoding='utf-8')
    t_ini = time.time()
    cont = {'ok': 0, 'erro': 0, 'quente': 0}

    def roda(pendentes, total, etiqueta, base=0):
        """Processa em FLUXO: grava cada linha assim que ela sai."""
        it = (trabalha(r) for r in pendentes) if pool is None else \
             pool.imap_unordered(trabalha, pendentes, chunksize=1)
        for x in it:
            if os.path.exists(PARAR):
                print('[%s] PARAR.txt encontrado. Fechando.' % agora(), flush=True)
                return False
            if not x:
                continue
            if 'ERRO' in x:
                cont['erro'] += 1
                msg = '[%s] ERRO linha %s · %s' % (agora(), x.get('n'), x['ERRO'])
                print('   ' + msg, flush=True); log.write(msg + '\n'); log.flush()
                continue

            out.write(json.dumps(x, ensure_ascii=False) + '\n'); out.flush()
            # ⛔ 14/08 — O MOTOR GRAVA DIRETO NA TABELA `builds`.
            # Ordem do Luis: "o motor gerar OUTRA TABELA com as otimizacoes".
            # O arquivo continua sendo escrito de proposito: o carrega_feitos()
            # le dele, e ele e a rede de seguranca se a internet cair.
            # Sem o GRAVA-DIRETO.txt na pasta, esta chamada nao faz nada.
            # ⛔ 27/08 — A VOLTA E O BANCO. gravar_build() grava na clube.build
            #    E TIRA a linha da fila, no mesmo comando. Sem interruptor.
            try:
                _fu.gravar([{
                    'card_id': x['card_id'], 'funcao_codigo': x['funcao'],
                    'b1': x.get('b1'), 'barras': x.get('barras'),
                    'impeto': x.get('impeto'), 'tecnico_id': x.get('tecnico_id'),
                    'tecnico_nome': x.get('tecnico'), 'habilidades': x.get('habilidades'),
                    'vals': x.get('vals'), 'falta_pool': x.get('falta_pool'),
                    'sobra': x.get('sobra'), 'receita_versao': x.get('receita_versao'),
                    'motor_versao': 'v6'}])
            except Exception as _e:
                print('   [banco] %s' % _e, flush=True)
            fh.write('%s|%s\n' % (x['card_id'], x['funcao'])); fh.flush()
            feitos.add('%s|%s' % (x['card_id'], x['funcao']))
            cont['ok'] += 1
            # ⛔ o carimbo de vida, a cada linha. E por ele que a rodada sabe
            #    que o motor esta de pe e NAO precisa abrir outro.
            carimba_vivo(cont['ok'], max(0, total - (cont['ok'] + cont['erro'] - base)))
            if etiqueta == 'quente': cont['quente'] += 1

            n = cont['ok'] + cont['erro'] - base
            if n % TELA_A_CADA == 0:
                dec = time.time() - t_ini
                media = dec / max(1, n)
                linha = ('[%s] %5d/%-5d %5.1f%% · %-24s %-26s b1 %9.2f · %4.1fs'
                         '  | decorrido %s · media %.1f s/linha · falta ~%s%s'
                         % (agora(), n, total, 100.0 * n / max(1, total),
                            (x.get('nome') or '')[:24], (x.get('funcao') or '')[:26],
                            x.get('b1') or 0, x.get('segundos') or 0,
                            hms(dec), media, hms(media * max(0, total - n)),
                            ('  · ERROS %d' % cont['erro']) if cont['erro'] else ''))
                print(linha, flush=True)
                log.write(linha + '\n'); log.flush()
        return True

    try:
        # ---------- 1) a fila principal ----------
        pend = [r for r in fila if chave(r) not in feitos]

        # ===== AS MONSTRO VAO PRO FIM DA FILA (ordem do Luis, 08/08) =====
        # "nao tem como pular essa linha e jogar pro final? pra rodar as outras".
        # Medido no linhas.jsonl: as linhas caras sao SEMPRE as que tem VAGA DE
        # IMPETO LIVRE junto com pool de habilidade. Sem corte de margem, todo
        # impeto candidato sobrevive e cada um roda um DP inteiro.
        #    com vaga de impeto + pool: 696 s a 4.953 s
        #    sem vaga de impeto       : mediana ~120 s, pior 304 s
        # Isto NAO muda resultado nenhum — so a ORDEM. As monstro rodam depois,
        # e nada e descartado. Para desligar: MONSTRO_NO_FIM=0.
        if os.environ.get('MONSTRO_NO_FIM', '1') != '0':
            _sl = {}
            try:
                for _c in json.load(open(D + 'cards.json', encoding='utf-8')):
                    _b = str(_c['id']).split('@')[0]
                    _v = sum(_c.get('sl') or [])
                    _o = _c.get('orc') or 0
                    if _b not in _sl or (_v, _o) > _sl[_b]:
                        _sl[_b] = (_v, _o)
            except Exception as _e:
                print('nao consegui ler o sl para ordenar (%s) — fila na ordem normal' % _e)
            def _monstro(_r):
                v, o = _sl.get(str(_r['card_id']).split('@')[0], (0, 0))
                return 1 if (v > 0 and o > 0) else 0
            pend.sort(key=_monstro)             # estavel: nao mexe no resto da ordem
            _n = sum(1 for _r in pend if _monstro(_r))
            print('ordem ............. %d linhas leves primeiro · %d MONSTRO no fim'
                  % (len(pend) - _n, _n), flush=True)

        # ===== A PONTA DA FILA (ordem do Luis, 08/08) =====
        # "carta que voce consertou, coloca na ponta da fila". O fila_PRIORIDADE.json
        # guarda chaves card_id|funcao — elas passam na frente de tudo, inclusive do
        # desempate leve/monstro acima.
        try:
            if os.path.exists('fila_PRIORIDADE.json'):
                # 09/08: a prioridade passou a ser uma LISTA ORDENADA, nao um saco.
                # Quem vem primeiro NO ARQUIVO roda primeiro. Assim da pra por uma
                # box nova na frente das consertadas sem perder as consertadas.
                _lista = json.load(open('fila_PRIORIDADE.json', encoding='utf-8'))
                _rank = {}
                for _i, _k in enumerate(_lista):
                    if _k not in _rank:
                        _rank[_k] = _i
                if _rank:
                    pend.sort(key=lambda _r: _rank.get(chave(_r), 10 ** 9))
                    _np = sum(1 for _r in pend if chave(_r) in _rank)
                    print('prioridade ........ %d linhas na PONTA da fila (na ordem do arquivo)'
                          % _np, flush=True)
        except Exception as _e:
            print('nao consegui ler o fila_PRIORIDADE.json (%s)' % _e, flush=True)

        print('[%s] fila principal: %d linhas a rodar' % (agora(), len(pend)), flush=True)
        seguiu = roda(pend, len(pend), 'principal')

        # ---------- 2) entrada quente ----------
        if seguiu:
            print()
            print('[%s] fila principal terminada. ENTRADA QUENTE LIGADA.' % agora(), flush=True)
            print('            jogue os cards novos em %s — eu pego sozinho.' % EXTRA, flush=True)
            vazio = 0
            while not os.path.exists(PARAR):
                # ⛔ 18/08 — LINHA COM `refazer` ENTRA MESMO JA TENDO RESULTADO.
                #    Antes, para refazer uma linha era preciso ARRANCAR ela do
                #    linhas.jsonl (o refazer_de_verdade fazia isso) — e isso
                #    exige o motor PARADO. Era a unica razao pela qual coletar e
                #    rodar nao podiam acontecer ao mesmo tempo.
                #    Com a marca `refazer`, quem quer uma linha nova so joga ela
                #    no fila_EXTRA. O motor recalcula e grava por cima. Ninguem
                #    precisa parar nada.
                _ex = le_extra()
                novos = [r for r in _ex if r.get('refazer') or chave(r) not in feitos]
                _refaz = sum(1 for r in novos if r.get('refazer'))
                if not novos:
                    vazio += 1
                    if vazio % 10 == 1:
                        print('[%s] esperando card novo em %s ...' % (agora(), EXTRA), flush=True)
                    time.sleep(ESPERA)
                    continue
                vazio = 0
                print('[%s] CHEGOU TRABALHO: %d linhas (%d sao REFAZER). Rodando.'
                      % (agora(), len(novos), _refaz), flush=True)
                base = cont['ok'] + cont['erro']
                if not roda(novos, len(novos), 'quente', base):
                    break
    finally:
        if pool is not None: pool.terminate(); pool.join()
        out.close(); fh.close(); log.close()
        apaga_o_vivo()

    print()
    print('[%s] TERMINOU. %d linhas gravadas · %d quentes · %d erros'
          % (agora(), cont['ok'], cont['quente'], cont['erro']))
    try:
        _gd.descarrega()
        print(_gd.resumo(), flush=True)
    except Exception as _e:
        print('   [grava_direto] %s' % _e, flush=True)
    print('resultado em %s · log em log_v6.txt' % LINHAS)

if __name__ == '__main__':
    import multiprocessing as mp
    mp.freeze_support(); main()
