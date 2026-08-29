# -*- coding: utf-8 -*-
"""
BONIFICADOR — v8 (28/08/2026)

O QUE MUDOU NESTA VERSAO
  1. OS DADOS DO JOGO VEM DO MODELO NOVO. Corpo, pe ruim, posicao,
     playstyles e estilos de IA saem exclusivamente de contratos v1 sobre
     clube_novo. Nao existe fallback para carta_do_motor nem para JSON antigo.
  2. GRAVA NO BANCO. O resultado vai para as colunas b_* da clube.build, que e
     de onde a tela le (public.casa_tela). Acabou o bonus.jsonl e a tabela
     public.bonus.
  3. O BONUS DE ESTILO E POR FUNCAO, NAO POR POSICAO.  <-- a correcao de fundo
     Antes: o estilo ligava na POSICAO, entao Defensor criativo montado como
     Zagueiro de combate ganhava o mesmo 1,0 que um destruidor legitimo.
     Agora: 1,0 so na funcao que e a CASA daquele estilo. O impostor zera.
  4. OS DOIS SLOTS DE 2027. +0,5 quando o segundo slot tambem ativa naquela
     posicao — repetido ou nao. Teto 1,5.
     Cascata: se o slot recomendado da posicao esta Basico, o outro slot assume
     com 1,0 cheio.

AS PORTAS DO BANCO
    public.bonificador_regua_v1() a receita allowlisted e seus gates
    public.bonificador_carta_v1() somente as entradas usadas pelo Bonificador
    public.bonificador_pares_v1() os pares card x funcao ja rodados
    public.gravar_bonus(json)     a volta

A CHAVE sai do config.txt na hora de rodar. Nunca e gravada nem impressa aqui.
"""

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
        _sys.path.append(_CASA)
if _MEU_LUGAR in _sys.path:
    _sys.path.remove(_MEU_LUGAR)
_sys.path.insert(0, _MEU_LUGAR)

import os, sys, json, time, urllib.request, urllib.error

MOTOR_BONUS = 'v8-2808-clube-novo-contrato-v1'
LOTE = 200
NAOSEI = 'NAO-SEI.txt'


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


# ===================================================== A LIGACAO COM O BANCO
cfg = {}
if os.path.exists('config.txt'):
    for linha in open('config.txt', encoding='utf-8'):
        linha = linha.strip()
        if linha and not linha.startswith('#') and '=' in linha:
            k, v = linha.split('=', 1)
            cfg[k.strip()] = v.strip()
URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')

if not URL or not KEY or 'COLE_AQUI' in KEY:
    print('')
    print('  PAREI: sem config.txt com a chave do Supabase.')
    print('  Esta versao do motor le e grava NO BANCO — sem a chave nao ha o que fazer.')
    pausa(); sys.exit(1)

CAB = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
       'Content-Type': 'application/json'}


def rpc(nome, corpo=None, timeout=180):
    req = urllib.request.Request(
        '%s/rest/v1/rpc/%s' % (URL, nome),
        data=json.dumps(corpo or {}).encode('utf-8'),
        headers=CAB, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        t = r.read().decode('utf-8')
    return json.loads(t) if t.strip() else None


# ============================================================== A CONTA
def nota_da_medida(valor, cortes):
    """os 4 degraus do molde do fisico -> 0..1"""
    if valor is None:
        return None
    n = 0
    for c in cortes:
        if c is None:
            continue
        if valor >= c:
            n += 1
    return n / 4.0


def bonus_do_corpo(molde_corpo, corpo, funcao, corpo_max):
    """corpo = lista de 12 medidas na ordem do corpo_ordem. Devolve (bonus, soma, pct, detalhe)."""
    m = (molde_corpo or {}).get(funcao)
    if not m or not corpo:
        return None
    soma = peso_total = 0.0
    detalhe = {}
    for medida, regra in m.items():
        idx = regra.get('idx')
        if idx is None or idx >= len(corpo):
            continue
        v = corpo[idx]
        if v is None:
            continue
        n = nota_da_medida(v, regra.get('cortes') or [])
        if n is None:
            continue
        if (regra.get('direcao') or '') == '-':
            n = 1.0 - n
        p = float(regra.get('peso') or 0)
        soma += n * p
        peso_total += p
        detalhe[medida] = round(n, 3)
    if peso_total <= 0:
        return None
    pct = soma / peso_total
    bonus = round((pct * 2 - 1) * float(corpo_max), 4)
    return bonus, round(soma, 4), round(pct, 4), detalhe


def bonus_do_pe_ruim(par, uso, prec):
    """par = os parametros. uso e precisao vao de 0 a 3."""
    teto = float(par.get('pe_ruim_teto') or 1.0)
    f = [float(par.get('pe_ruim_frequencia_%d' % i) or 0) for i in range(4)]
    q = [float(par.get('pe_ruim_precisao_%d' % i) or 0) for i in range(4)]
    try:
        u, p = int(uso), int(prec)
    except Exception:
        return None
    if not (0 <= u < 4) or not (0 <= p < 4):
        return None
    return round(f[u] * q[p] * teto, 4)


def _por_id(mapa, chave):
    """Chaves de objeto JSON chegam como texto; ids da carta chegam numericos."""
    if chave is None or not isinstance(mapa, dict):
        return None
    return mapa.get(str(chave), mapa.get(chave))


def bonus_do_estilo(rb, est1, est2, funcao, posicao_id):
    """
    ⛔ A REGRA DOS DOIS ESTILOS — aprovada pelo Luis em 26/08.

      1,0  na funcao que e a CASA do estilo do slot que MANDA na posicao
      +0,5 se o outro slot tambem ATIVA naquela posicao (repetido ou nao)
      teto 1,5

    CASCATA: se o slot que manda esta Basico, o OUTRO assume com 1,0 cheio.

    POR QUE POR FUNCAO E NAO POR POSICAO: antes o estilo ligava na posicao, e
    entao Defensor criativo montado como Zagueiro de combate ganhava o mesmo
    1,0 que um destruidor legitimo. O sistema nao avisava que a ficha estava
    errada. Agora o impostor zera e o dono da funcao sobe sozinho.
    """
    casa = rb.get('casa') or {}
    liga = rb.get('liga') or {}
    par  = rb.get('parametro') or {}
    pri  = float(par.get('estilo_ativo') or 1.0)
    sec  = float(par.get('estilo_ativo_secundario') or 0.5)
    teto = pri + sec

    slot_manda = _por_id(rb.get('posicao_slot') or {}, posicao_id) or 'ofensivo'
    # slot 1 = ofensivo (o legado) · slot 2 = defensivo (o novo de 2027)
    dono, outro = (est1, est2) if slot_manda == 'ofensivo' else (est2, est1)

    # CASCATA: o slot que manda esta vazio -> o outro assume inteiro
    if not dono:
        dono, outro = outro, None

    b = 0.0
    if dono and _por_id(_por_id(casa, dono) or {}, posicao_id) == funcao:
        b += pri
    if outro and posicao_id in (_por_id(liga, outro) or []):
        b += sec
    return round(min(b, teto), 4)


def bonus_do_estilo_ia(par, lista):
    if not lista:
        return 0.0
    pt = float(par.get('estilo_ia_ponto') or 1.0)
    teto = float(par.get('estilo_ia_teto') or 4)
    return round(pt * min(len(lista), teto) / teto, 4)


# ================================================================== RODA
print('=' * 70)
print('  BONIFICADOR v8  —  corpo · pe ruim · estilo (por funcao) · IA')
print('=' * 70)

print('')
print('[1/4] baixando a receita do banco')
rb = rpc('bonificador_regua_v1')
if not rb or not rb.get('pode_rodar'):
    print('  PAREI: a public.bonificador_regua_v1() esta ausente ou bloqueada.')
    if rb and rb.get('falta_o_que'):
        print('  Falta: %s' % ', '.join(str(x) for x in rb.get('falta_o_que') or []))
    pausa(); sys.exit(1)
for chave in ('parametro', 'molde_corpo', 'corpo_ordem', 'casa', 'liga', 'posicao_slot'):
    if chave not in rb:
        print('  PAREI: contrato da regua sem a chave obrigatoria %s.' % chave)
        pausa(); sys.exit(1)
par = rb.get('parametro') or {}
CORPO_MAX = float(par.get('bonus_corpo_max') or 1.5)

# o corpo vem como lista na ordem do corpo_ordem; monto o indice de cada medida
ORD = rb.get('corpo_ordem') or {}
IDX = {}
for pos, d in ORD.items():
    try:
        IDX[(d or {}).get('nosso')] = int(pos)
    except Exception:
        pass
MOLDE_CORPO = rb.get('molde_corpo') or {}
for fun, m in MOLDE_CORPO.items():
    for medida, regra in m.items():
        regra['idx'] = IDX.get(medida)

print('   funcoes com molde do fisico ........ %d' % len(MOLDE_CORPO))
print('   estilos com casa ................... %d' % len(rb.get('casa') or {}))
print('   estilos que ligam .................. %d' % len(rb.get('liga') or {}))
print('   estilo_ativo %.2f · secundario %.2f · teto %.2f'
      % (float(par.get('estilo_ativo') or 1), float(par.get('estilo_ativo_secundario') or 0.5),
         float(par.get('estilo_ativo') or 1) + float(par.get('estilo_ativo_secundario') or 0.5)))

print('')
print('[2/4] baixando os pares card x funcao ja rodados')
pares, passo, de = [], 1000, 0
while True:
    lote = rpc('bonificador_pares_v1', {'p_limit': passo, 'p_offset': de})
    if not lote:
        break
    pares.extend((x['card_id'], x['funcao_codigo']) for x in lote)
    de += passo
    print('   %d pares...' % len(pares), end='\r')
    if len(lote) < passo:
        break
print('   pares card x funcao ................ %d      ' % len(pares))

if not pares:
    print('')
    print('  Nao ha build nenhuma na clube.build. Rode o motor otimizador antes.')
    pausa(); sys.exit(1)

cards = sorted({c for c, _ in pares})
print('   cards distintos .................... %d' % len(cards))

print('')
print('[3/4] calculando')
CARTA = {}
saida = []
sem_corpo = sem_pe = sem_estilo = sem_ia = 0
for i, cid in enumerate(cards):
    if i % 200 == 0:
        print('   %d/%d cards...' % (i, len(cards)), end='\r')
    try:
        CARTA[cid] = rpc('bonificador_carta_v1', {'p_card_id': cid}) or {
            'pode_rodar': False,
            'falta_o_que': ['contrato vazio']}
    except Exception as e:
        CARTA[cid] = {
            'pode_rodar': False,
            'falta_o_que': ['falha no contrato v1: %s' % str(e)[:160]]}
print('   %d/%d cards            ' % (len(cards), len(cards)))

for cid, fun in pares:
    c = CARTA.get(cid) or {}
    falhas_contrato = list(c.get('falta_o_que') or [])
    contrato_ok = bool(c.get('pode_rodar'))

    if contrato_ok:
        r = bonus_do_corpo(MOLDE_CORPO, c.get('corpo'), fun, CORPO_MAX)
        if r is None:
            sem_corpo += 1
            b_corpo, c_soma, c_pct, detalhe = None, None, None, None
        else:
            b_corpo, c_soma, c_pct, detalhe = r

        b_pe = bonus_do_pe_ruim(
            par, c.get('pe_ruim_uso'), c.get('pe_ruim_precisao'))
        if b_pe is None:
            sem_pe += 1

        b_est = bonus_do_estilo(
            rb, c.get('slot1_id_jogo'), c.get('slot2_id_jogo'),
            fun, c.get('posicao_id'))
        if b_est is None:
            sem_estilo += 1

        ia = c.get('estilos_ia')
        if ia is None:
            sem_ia += 1
            b_ia = None
        else:
            b_ia = bonus_do_estilo_ia(par, ia)
    else:
        b_corpo = b_pe = b_est = b_ia = None
        c_soma = c_pct = detalhe = None
        sem_corpo += 1
        sem_pe += 1
        sem_estilo += 1
        sem_ia += 1

    faltou = list(falhas_contrato)
    faltou.extend(n for n, v in (
        ('corpo', b_corpo), ('pe ruim', b_pe), ('estilo', b_est),
        ('estilo da IA', b_ia)) if not isinstance(v, (int, float)))
    faltou = list(dict.fromkeys(faltou))
    componentes = (b_corpo, b_pe, b_est, b_ia)
    b_total = (round(sum(componentes), 4)
               if not faltou and all(isinstance(x, (int, float)) for x in componentes)
               else None)

    saida.append({
        'card_id': cid, 'funcao_codigo': fun,
        'b_corpo': b_corpo, 'b_pe_ruim': b_pe, 'b_estilo': b_est, 'b_ia': b_ia,
        'b_total': b_total,
        # ⛔ 15/08 ORDEM DO LUIS: "se ele nao sabe, ele vai querer colocar zero,
        #    e um numero inventado". O que faltou fica ESCRITO, com nome.
        'faltou': faltou,
        'corpo_soma': c_soma, 'corpo_pct': c_pct,
        'detalhe': detalhe, 'motor_bonus': MOTOR_BONUS})

print('   %d pares calculados' % len(saida))
com_est = sum(1 for x in saida if x['b_estilo'])
com_meio = sum(1 for x in saida if x['b_estilo'] and x['b_estilo'] > float(par.get('estilo_ativo') or 1))
print('   com bonus de estilo ................ %d' % com_est)
print('   com o +0,5 do segundo slot ......... %d' % com_meio)

# --------------------------------------- 3b) A LISTA DOS "NAO SEI"
print('')
print('[3b] a lista dos NAO SEI')
falta_por_tipo, falta_por_card = {}, {}
for x in saida:
    for f in x['faltou']:
        falta_por_tipo.setdefault(f, set()).add(x['card_id'])
        falta_por_card.setdefault(x['card_id'], set()).add(f)
try:
    with open(NAOSEI, 'w', encoding='utf-8') as f:
        f.write('=' * 74 + '\n')
        f.write('  NAO SEI — tudo que o Bonificador nao conseguiu puxar\n')
        f.write('  gerado em %s\n' % time.strftime('%d/%m/%Y %H:%M'))
        f.write('=' * 74 + '\n\n')
        f.write('REGRA (ordem do Luis, 15/08): quando o dado nao existe, o motor\n')
        f.write('NAO poe zero. Poe NAO SEI, e o card aparece nesta lista.\n\n')
        f.write('  %d pares card x funcao ao todo\n' % len(saida))
        f.write('  %d pares com pelo menos um NAO SEI\n'
                % sum(1 for x in saida if x['faltou']))
        f.write('  %d cards distintos afetados\n\n' % len(falta_por_card))
        for tipo in sorted(falta_por_tipo, key=lambda k: -len(falta_por_tipo[k])):
            npar = sum(1 for x in saida if tipo in x['faltou'])
            f.write('  %-16s %6d cards  %6d pares\n'
                    % (tipo, len(falta_por_tipo[tipo]), npar))
        f.write('\n')
        f.write('DE ONDE CADA UM VEM AGORA (contratos v1, 28/08):\n')
        f.write('  corpo .......... clube_novo.carta_corpo_jogo + corpo_ordem\n')
        f.write('  pe ruim ........ clube_novo.carta_jogo + clube_novo.pe\n')
        f.write('  estilo ......... clube_novo.playstyle por id_jogo + regra reindexada\n')
        f.write('  estilo da IA ... clube_novo.carta_estilo_ia_jogo por bit\n')
    print('   escrito em %s' % NAOSEI)
except Exception as e:
    print('   nao consegui escrever o %s (%s)' % (NAOSEI, e))

# --------------------------------------------------------- 4) A VOLTA
print('')
print('[4/4] gravando no banco')
enviados = 0
gravaveis = [x for x in saida if not x['faltou'] and isinstance(x['b_total'], (int, float))]
bloqueados = len(saida) - len(gravaveis)
print('   pares aptos ........................ %d' % len(gravaveis))
print('   pares bloqueados (sem fallback) .... %d' % bloqueados)
for i in range(0, len(gravaveis), LOTE):
    lote = [{'card_id': x['card_id'], 'funcao_codigo': x['funcao_codigo'],
             'b_corpo': x['b_corpo'], 'b_pe_ruim': x['b_pe_ruim'],
             'b_estilo': x['b_estilo'], 'b_ia': x['b_ia'], 'b_total': x['b_total']}
            for x in gravaveis[i:i + LOTE]]
    try:
        n = rpc('gravar_bonus', {'p_linhas': lote})
        enviados += int(n or 0)
        print('   %d/%d gravados...' % (enviados, len(gravaveis)), end='\r')
    except urllib.error.HTTPError as e:
        print('')
        print('   ERRO no lote %d: %s' % (i // LOTE, e.read().decode('utf-8')[:300]))
        pausa(); sys.exit(1)

print('   %d linhas gravadas na clube.build          ' % enviados)
print('')
print('=' * 70)
print('  PRONTO. A tela le da public.casa_tela, que le da clube.build.')
print('  Confira: select * from clube.auditoria_completa() where status = \'FALHA\';')
print('=' * 70)
pausa()
