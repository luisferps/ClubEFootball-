"""
EQUACAO — A LEI DA FISICA DO JOGO.

Manda neste arquivo: AS-DUAS-EQUACOES-NAO-MEXER.md
Medido no eFootball em 04/08/2026: 265 medicoes, 2 cartas, 2 tecnicos,
10 proficiencias, 5 taticas, ZERO ERRO.

Esta peca NAO decide nada e NAO olha para o molde. Ela so diz como o numero nasce.
E usada nos DOIS lados: para fabricar o alvo (molde) e para fabricar o card (motor).
Foi por isso que o erro do multiplicador ficou invisivel — corrompia os dois igual.

=========================================================================
A EQUACAO 1 — O JOGO. Vale para cada um dos 26 atributos, nesta ordem:

  1. x = base do atributo (vem da carta)
  2. x = x + niveis da barra que manda nesse atributo   ·   x = MIN(99, x)
  3. m = multiplicador, lido pela PROFICIENCIA DO TECNICO
         x = x + TRUNCA( x * (m-1) )
         x = MIN(99, MAX(40, x))
  4. se for um dos atributos de boost do tecnico: x += delta (passa de 99)
  5. para cada impeto ativo que pegue o atributo: x += valor (passa de 99)

A EQUACAO 2 — O SISTEMA B = Equacao 1 + termo das habilidades.
  referencia = o valor do PASSO 2 (base+barras), sem tecnico, sem multiplicador,
               sem impeto
  ganho      = CEIL(referencia * pct/100) + fixo
  final      = resultado da Equacao 1 + ganho          SEM TRAVA DE 99

REGRA VIGENTE, RECONFIRMADA EM 28/08/2026:
  base+barras -> proficiencia com MIN(99) -> boost -> impetos.
A tentativa posterior de aplicar impetos antes da proficiencia e remover o teto foi
revogada. No teste discriminante, Messi com Finalizacao 99, Capello 89/+1 e Precisao
+4 exibiu 104 no campo; a tentativa posterior previa 107 ou mais.
=========================================================================

⚠️ AS CORRECOES A-G FORAM APLICADAS EM 04/08/2026. O arquivo anterior esta
   guardado como `equacao_v1_referencia.py` para conferencia lado a lado.
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
import json, math
import numpy as np

# ---------------------------------------------------------------- os 26 atributos
ATTRS_EF = ["offensiveAwareness","ballControl","dribbling","tightPossession","lowPass",
            "loftedPass","finishing","heading","setPieceTaking","curl","speed","acceleration",
            "kickingPower","jump","physicalContact","balance","stamina","defensiveAwareness",
            "ballWinning","trackingBack","aggression","gkAwareness","gkCatching","gkClearing",
            "gkReflexes","gkReach"]
POS = {n: i for i, n in enumerate(ATTRS_EF)}

# ---------------------------------------------------------------- as 10 barras
# cada nivel soma +1 em TODOS os atributos daquela barra. Salto(13) mora em duas.
MB = {"shooting":[6,8,9], "passing":[4,5], "dribbling":[1,2,3], "dexterity":[0,11,15],
      "lowerBodyStrength":[10,12,16], "aerialStrength":[7,13,14], "defending":[17,18,20,19],
      "gk1":[21,13], "gk2":[23,25], "gk3":[22,24]}
MBK = list(MB)

# ---------------------------------------------------------------- orcamento e custo
# pontos = 2 x (nivel maximo - 1)   ·   custo do nivel n = ceil(n/4)   ·   teto 25
ACCU = [0]; _t = 0
for _n in range(1, 26):
    _t += math.ceil(_n / 4); ACCU.append(_t)
ACCU = np.array(ACCU)

# ---------------------------------------------------------------- a tabela do tecnico
# A ORDEM CERTA (NAO-MEXER 2.8). NAO e a ordem dos 26 do sistema.
# Com a ordem errada, 41 dos 62 tecnicos recebiam o +1 no atributo errado.
AM = ["offensiveAwareness","ballControl","tightPossession","dribbling","lowPass","loftedPass",
      "finishing","setPieceTaking","curl","heading","defensiveAwareness","ballWinning",
      "trackingBack","aggression","kickingPower","speed","acceleration","balance",
      "physicalContact","jump","gkAwareness","gkCatching","gkClearing","gkReflexes",
      "gkReach","stamina"]

# =========================================================================
# MUDANCA B — a tabela MEDIDA, proficiencia 0 a 99.
# A tabela do eFHUB so vale de 72 pra cima. Abaixo ela e lixo: dizia 0,72 para
# a proficiencia 54 (o jogo da 0,960) e 0,9125 para 65 (o jogo da 1,000 EXATO).
# =========================================================================
# 27/08 — o tabm_medido.json nao existe mais. A tabela mora em
# clube.multiplicador e desce pelo regua_pacote(). Os numeros sao os mesmos:
# proficiencia 20 = 0,800 · 54 = 0,960 · 65 a 71 = 1,000 exato · 90 = 1,0365.
import fonte_unica as _FU
TABM = {int(k): float(v) for k, v in _FU.tabela_multiplicador().items()}
TABM_MIN, TABM_MAX = min(TABM), max(TABM)

def mult_de(v):
    """multiplicador tatico. Fora da faixa medida, prende nas pontas.
    Regra pratica que sai da tabela:
        72 ou mais  -> o tecnico AJUDA
        65 a 71     -> nao faz nada (1,000 exato)
        abaixo de 65-> ATRAPALHA, e cai rapido (proficiencia 20 = 0,800)"""
    v = int(round(v))
    if v in TABM: return TABM[v]
    return TABM[TABM_MIN] if v < TABM_MIN else TABM[TABM_MAX]

PISO = 40   # MUDANCA A — medido: com m ~ 0,96 os atributos de GO em 40 nao caem pra 39

def _mult(x, m):
    """Incremento truncado, com piso 40 e teto 99.

        CERTO:  x + TRUNCA( x * (m-1) )
        ERRADO: ARREDONDA_PRA_BAIXO( x * m )

    Por que: floor(74 * 0,987) = 73, e a tela deu 74. O incremento truncado
    fecha os dois lados; o floor do total so quebra quando m < 1 — que e
    exatamente a faixa onde a tabela velha tambem estava errada. Dois erros
    escondidos um atras do outro.

    ⚠️ NAO MEDIDO: o que acontece com atributo que ja entra ABAIXO de 40.
       Aqui o piso so age quando o multiplicador age (m != 1), como manda o
       passo 3 da equacao. Nenhuma medicao cobriu esse caso."""
    if m == 1.0: return x
    return min(99, max(PISO, x + int(x * (m - 1))))

def _multv(a, m):
    """o mesmo _mult, vetorizado. np.trunc corta na direcao do zero, como int()."""
    if m == 1.0: return a.astype(int)
    return np.minimum(99, np.maximum(PISO, a + np.trunc(a * (m - 1)))).astype(int)

# =========================================================================
# MUDANCA D — o jogo BLOQUEIA o nivel de barra que passaria de 99.
# Nao e so travar o atributo: ele nao deixa nem GASTAR o ponto.
#   Medido: Messi, barra do Chute — Finalizacao 80, Cobranca 83, Curva 86.
#   19 niveis (custo 55) levaram a Finalizacao a 99. O jogo recusou o 20o
#   com 7 pontos ainda sobrando.
# =========================================================================
def nivel_max_barra(base, barra):
    """nivel maximo que o jogo aceita naquela barra = 99 - o MENOR atributo dela."""
    return max(0, min(25, 99 - min(int(base[i]) for i in MB[barra])))

# =========================================================================
# MUDANCA E — o alvo util de base+barras e CEIL(99 / m).
# Com a proficiencia limitada a 99, subir base+barras alem desse ponto nao muda
# o valor final desta etapa e desperdicaria pontos de progressao.
# =========================================================================
def alvo_util(m):
    """acima disto, subir base+barras nao muda o numero apos a proficiencia."""
    if m <= 0: return 99
    return min(99, math.ceil(99 / m))

def carrega_tecnicos(path='tecnicos.json', tatica=None):
    """O Otimizador escolhe a maior proficiencia entre os estilos do tecnico.

    Empates sao equivalentes para a conta porque produzem o mesmo multiplicador.
    ``tatica`` permanece apenas para compatibilidade com chamadas antigas e nao
    muda a escolha nesta etapa do Otimizador.

    ⚠️ O clamp min(90, max(70, v)) FOI REMOVIDO: a tabela medida cobre 0 a 99.
       Era ele que fazia tecnico ruim virar neutro."""
    CO = json.load(open(path, encoding='utf-8')); out = []
    for c in CO.values():
        if not c.get('hasBoost'): continue
        sk = c['skills']
        v = max(sk.values())
        b = [POS[AM[x]] for x in c['boosts'] if 0 <= x < 26]
        out.append({'nome': c['name'], 'id': c['id'], 'tat': v, 'm': mult_de(v), 'boost': b})
    return out

# ---------------------------------------------------------------- habilidades
# ⚠️ Este bloco NAO e regra do jogo — e valoracao declarada nossa (Equacao 2).
# A habilidade nao mexe no numero da tela; ela muda comportamento em partida.
# 16/08 — SEM `encoding='utf-8'` este open MATAVA o import inteiro no
# Windows: o padrao la e cp1252, e o arquivo tem o Í de "Ímpeto de Ataque"
# (byte 0x8D na posicao 10763), que o cp1252 nao conhece. Com o import
# morto, o `patch_conta_do_motor` do gera_encaixe.py caia fora calado e a
# tela ficava SEM o CONTA-DO-MOTOR.js inteiro — a equacao de 15/08 toda.
# ⛔ Nao mudei conta nenhuma: so a forma de ler o arquivo.
# 27/08 — o HAB_EFEITOS_FINAL.json nao existe mais. As 65 habilidades e seus
# efeitos moram em clube.habilidade. Nao ha mais problema de cp1252: o dado
# chega como texto do banco, ja em utf-8.
HAB = _FU.catalogo_habilidades()
POR_ID = {int(skill_id): {'fabricavel': bool(v.get('fabricavel')),
                          'efeito': v.get('efeito') or {}}
          for skill_id, v in HAB.items()}
TEM_EFEITO = {skill_id for skill_id, v in POR_ID.items() if v['efeito']}

def buff_de(hs):
    """(pct, flat) por atributo.

    MUDANCA v5 (Luis, 05/08) — A PERDEDORA VALE METADE.
    Antes: comum vencedora do atributo valia 100%, as outras ZERO.
    Agora: vencedora 100% + CADA perdedora 50%, SEM ARREDONDAR a metade
    (5% vira 2,5%, nao 3%). Sem cascata: todas as perdedoras valem meio.
    Razao do Luis: "essa habilidade nao esta desperdicada, no jogo ela nao
    esta desperdicada de fato". RARAS continuam somando por cima, inteiras.
    O ceil final do ganho permanece (e a cadeia MEDIDA no jogo)."""
    pc_com = {}; pc_rar = {}; fl_com = {}; fl_rar = {}
    for h in hs:
        v = POR_ID.get(int(h))
        if not v or not v['efeito']: continue
        rara = not v['fabricavel']
        for i, d in v['efeito'].items():
            i = int(i)
            if 'pct' in d: (pc_rar if rara else pc_com).setdefault(i, []).append(d['pct'])
            else:          (fl_rar if rara else fl_com).setdefault(i, []).append(d['flat'])
    out = {}
    for i in set(pc_com) | set(pc_rar) | set(fl_com) | set(fl_rar):
        cs = sorted(pc_com.get(i, [0]), reverse=True)
        fs = sorted(fl_com.get(i, [0]), reverse=True)
        pct  = cs[0] + sum(cs[1:]) / 2.0 + sum(pc_rar.get(i, []))
        flat = fs[0] + sum(fs[1:]) / 2.0 + sum(fl_rar.get(i, []))
        if pct or flat: out[i] = (pct, flat)
    return out

def aplica_buff(v, pct, flat, ref=None):
    """MUDANCA F — a % le BASE+BARRAS, e o ganho NAO TRAVA em 99.

    Por que base+barras: e a unica parte que e da CARTA. Multiplicador e +1 sao
    camada do TIME; o impeto e camada EQUIPADA (o botao de ligar/desligar prova:
    Rooney 97 -> 99 -> 100 so com o botao). Se a habilidade lesse o valor
    pos-multiplicador, a MESMA carta valeria coisas diferentes conforme o tecnico
    — e um ranking de CARTAS nao pode mexer quando voce mexe no TIME.

    Por que sem trava: a trava de 99 e regra sobre o NUMERO DA TELA, e a
    habilidade nunca toca esse numero.
    Estrago medido com a trava ligada, nas 2.094 cartas jogadas:
      70,2% das cartas com pelo menos uma habilidade cortada
      18,1% de todos os pontos de habilidade engolidos
      e cortava as melhores: Verratti -58, Ruben Neves -49, Pirlo/Iniesta -45.
      A trava PUNIA a carta por ser boa."""
    r = v if ref is None else ref
    # v5: pct/flat podem vir fracionarios (perdedora vale metade) — o ceil vai
    # sobre o TOTAL para o ganho continuar INTEIRO, como o atributo do jogo.
    # Com flat inteiro e identico ao antigo: ceil(x)+f == ceil(x+f).
    return v + math.ceil(r * pct / 100 + flat)

# ---------------------------------------------------------------- a cadeia canonica
def base_barras(base, lvl):
    """PASSO 2 — base + barras, travado em 99. E a referencia da habilidade."""
    v = list(base)
    for b in MBK:
        n = lvl.get(b, 0)
        if n:
            for i in MB[b]: v[i] = min(99, v[i] + n)
    return v

def cadeia(base, lvl, m, impeto_add, boost_add=None):
    """A Equacao 1 inteira, legivel, um atributo de cada vez.
    O laco quente do motor tem uma copia inline desta conta, por velocidade."""
    boost_add = boost_add or [0] * 26
    v = base_barras(base, lvl)
    v = [_mult(x, m) for x in v]
    v = [v[i] + boost_add[i] for i in range(26)]
    return [v[i] + impeto_add[i] for i in range(26)]
