# -*- coding: utf-8 -*-
"""
BONIFICADOR — v9 (31/08/2026)

O QUE MUDOU NESTA VERSAO
  1. OS DADOS DO JOGO VEM DO MODELO NOVO. Corpo, pe ruim, posicao,
     playstyles e estilos de IA saem exclusivamente de contratos v1 sobre
     clube_novo. Nao existe fallback para carta_do_motor nem para JSON antigo.
  2. GRAVA SOMENTE NO MODELO NOVO. Cada resultado apto passa pelo writer
     transacional public.gravar_build_bonificador_v4. Nao existe chamada
     produtiva ou gravacao em estruturas legadas.
  3. O BONUS DE ESTILO E POR FUNCAO, NAO POR POSICAO.  <-- a correcao de fundo
     Antes: o estilo ligava na POSICAO, entao Defensor criativo montado como
     Zagueiro de combate ganhava o mesmo 1,0 que um destruidor legitimo.
     Agora: 1,0 so na funcao que e a CASA daquele estilo. O impostor zera.
  4. OS DOIS SLOTS DE 2027. +0,5 quando o segundo slot tambem ativa naquela
     posicao — repetido ou nao. Teto 1,5.
     Cascata: se o slot recomendado da posicao esta Basico, o outro slot assume
     com 1,0 cheio.

AS PORTAS DO BANCO
    public.bonificador_regua_v2() a receita allowlisted e seus gates
    public.bonificador_carta_v2() somente as entradas usadas pelo Bonificador
    public.bonificador_contexto_fila_v4() linhas e selos vigentes
    public.gravar_build_bonificador_v4(jsonb) a volta transacional

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

import os, sys, json, time, urllib.request, urllib.error, decimal, signal, threading
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


# ========================================================= PIPELINE VIVO
# O estado da fila vive somente no banco. Este laço não cria checkpoint, cache ou
# arquivo de controle: cada rodada relê os pares já confirmados pelo Otimizador.
_MARCADOR_RODADA = '_CLUBEF_BONIFICADOR_RODADA_INTERNA'


def _inteiro_ambiente(nome, padrao, minimo=0):
    bruto = _os.environ.get(nome, str(padrao))
    try:
        valor = int(bruto)
    except (TypeError, ValueError):
        raise RuntimeError('%s precisa ser inteiro, recebeu %r' % (nome, bruto))
    if valor < minimo:
        raise RuntimeError('%s precisa ser maior ou igual a %d' % (nome, minimo))
    return valor


def _executar_pipeline_vivo():
    """Roda uma rodada por vez e volta ao banco sem carregar estado local."""
    import runpy

    espera = _inteiro_ambiente('CLUBEF_BONIFICADOR_INTERVALO_SEGUNDOS', 5, 1)
    # Somente para teste offline/diagnóstico controlado; 0 significa operação contínua.
    max_rodadas = _inteiro_ambiente('CLUBEF_BONIFICADOR_MAX_RODADAS', 0, 0)
    rodada = 0
    parar = threading.Event()
    arquivo_parada = _os.environ.get('CLUBEF_BONIFICADOR_STOP_FILE', '')

    def parada_solicitada():
        return parar.is_set() or bool(arquivo_parada and _os.path.exists(arquivo_parada))

    def solicitar_parada(_sinal, _quadro):
        if not parar.is_set():
            print('\n  PARADA SOLICITADA: termino a rodada já em andamento e não inicio outra.')
        parar.set()

    sinais = [signal.SIGINT]
    if hasattr(signal, 'SIGBREAK'):
        sinais.append(signal.SIGBREAK)
    anteriores = {sinal: signal.getsignal(sinal) for sinal in sinais}
    for sinal in sinais:
        signal.signal(sinal, solicitar_parada)
    print('  PIPELINE VIVO: consulta linhas confirmadas pelo Otimizador continuamente.')
    print('  Quando não houver linha apta, espera %ds. Ctrl+C para parar normalmente.' % espera)
    try:
        while not parada_solicitada():
            rodada += 1
            _os.environ[_MARCADOR_RODADA] = str(rodada)
            resultado = None
            try:
                resultado = runpy.run_path(__file__, run_name='__main__').get('PIPELINE_RESULTADO')
            except SystemExit as erro:
                codigo = 0 if erro.code is None else erro.code
                if codigo != 0:
                    raise
            finally:
                _os.environ.pop(_MARCADOR_RODADA, None)

            if max_rodadas and rodada >= max_rodadas:
                print('  PARADA DE TESTE: limite de %d rodada(s) atingido.' % max_rodadas)
                return

            if parada_solicitada():
                break

            confirmou = int((resultado or {}).get('enviados') or 0)
            if confirmou == 0:
                print('  AGUARDANDO NOVAS LINHAS: nenhuma linha apta confirmada nesta rodada; '
                      'nova consulta em %ds. Ctrl+C para parar.' % espera)
                for _ in range(espera * 10):
                    if parada_solicitada():
                        break
                    time.sleep(0.1)
            else:
                print('  CONTINUANDO: %d resultado(s) confirmado(s); consultando novas linhas.' % confirmou)
    except KeyboardInterrupt:
        solicitar_parada(None, None)
    finally:
        for sinal, anterior in anteriores.items():
            signal.signal(sinal, anterior)
    print('  PARADA NORMAL: Bonificador interrompido pelo operador. '
          'Resultados já confirmados permanecem no banco.')


if __name__ == '__main__' and not _os.environ.get(_MARCADOR_RODADA):
    _executar_pipeline_vivo()
    raise SystemExit(0)

MOTOR_BONUS = 'v9-3108-clube-novo-writer-v1'
WRITER_BONUS = 'gravar_build_bonificador_v4'
LOTE = 200
NAOSEI = 'NAO-SEI.txt'


def pausa(msg='Enter para fechar...'):
    try:
        if _os.environ.get('CLUBEF_BONIFICADOR_INTERATIVO') == '1' and sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


# ===================================================== A LIGACAO COM O BANCO
cfg = {}
CONFIG_BONIFICADOR = _os.environ.get('CLUBEF_BONIFICADOR_CONFIG', 'config.txt')
if os.path.exists(CONFIG_BONIFICADOR):
    for linha in open(CONFIG_BONIFICADOR, encoding='utf-8'):
        linha = linha.strip()
        if linha and not linha.startswith('#') and '=' in linha:
            k, v = linha.split('=', 1)
            cfg[k.strip()] = v.strip()
URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')
DB_URL = cfg.get('BONIFICADOR_DATABASE_URL', '')
USAR_BANCO_DIRETO = bool(DB_URL and _os.environ.get('CLUBEF_BONIFICADOR_USAR_BANCO_DIRETO') == '1')

if not DB_URL and (not URL or not KEY or 'COLE_AQUI' in KEY):
    print('')
    print('  PAREI: sem config.txt com a chave do Supabase.')
    print('  Esta versao do motor le e grava NO BANCO — sem a chave nao ha o que fazer.')
    pausa(); sys.exit(1)

CAB = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
       'Content-Type': 'application/json'}
_CONEXAO_BONIFICADOR = None


def _rpc_banco(nome, corpo):
    """Acesso local restrito aos contratos; não abre tabela nem schema ao motor."""
    global _CONEXAO_BONIFICADOR
    import psycopg
    if _CONEXAO_BONIFICADOR is None or _CONEXAO_BONIFICADOR.closed:
        _CONEXAO_BONIFICADOR = psycopg.connect(DB_URL, connect_timeout=15)
    with _CONEXAO_BONIFICADOR.cursor() as cur:
        if nome == 'bonificador_regua_v2':
            cur.execute('select public.bonificador_regua_v2()')
            return cur.fetchone()[0]
        if nome == 'bonificador_carta_v2':
            cur.execute('select public.bonificador_carta_v2(%s)', ((corpo or {}).get('p_card_id'),))
            return cur.fetchone()[0]
        if nome == 'bonificador_contexto_fila_v4':
            cur.execute('select * from public.bonificador_contexto_fila_v4(%s,%s)', (
                (corpo or {}).get('p_limit', 1000), (corpo or {}).get('p_offset', 0)))
            colunas = [d.name for d in cur.description]
            return [dict(zip(colunas, linha)) for linha in cur.fetchall()]
        if nome == WRITER_BONUS:
            cur.execute('select public.gravar_build_bonificador_v4(%s::jsonb)',
                        (json.dumps((corpo or {}).get('p_resultado')),))
            resultado = cur.fetchone()[0]
            _CONEXAO_BONIFICADOR.commit()
            return resultado
    raise RuntimeError('contrato local não permitido: %s' % nome)


def rpc(nome, corpo=None, timeout=180):
    if USAR_BANCO_DIRETO:
        return _rpc_banco(nome, corpo)
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
    m = _por_id(molde_corpo or {}, funcao)
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


def bonus_do_corpo_writer(molde_corpo, corpo, funcao, corpo_max):
    """Mantém o total histórico e converte suas notas em contribuições reais."""
    resultado = bonus_do_corpo(molde_corpo, corpo, funcao, corpo_max)
    if resultado is None:
        return None
    bonus, soma, pct, notas = resultado
    molde = _por_id(molde_corpo or {}, funcao) or {}
    medidas = [(medida, float((molde.get(medida) or {}).get('peso') or 0), nota)
               for medida, nota in notas.items()]
    peso_total = sum(peso for _, peso, _ in medidas)
    if not medidas or peso_total <= 0:
        return None
    detalhe = {}
    acumulado = 0.0
    for indice, (medida, peso, nota) in enumerate(medidas):
        if indice == len(medidas) - 1:
            contribuicao = round(bonus - acumulado, 8)
        else:
            contribuicao = round(
                (2 * nota - 1) * peso / peso_total * float(corpo_max), 8)
            acumulado = round(acumulado + contribuicao, 8)
        detalhe[medida] = contribuicao
    return bonus, soma, pct, detalhe


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


def bonus_do_estilo_componentes(rb, est1, est2, funcao, posicao_id):
    """Expõe por slot físico as mesmas parcelas já somadas pela fórmula v8."""
    casa = rb.get('casa') or {}
    liga = rb.get('liga') or {}
    par = rb.get('parametro') or {}
    pri = float(par.get('estilo_ativo') or 1.0)
    sec = float(par.get('estilo_ativo_secundario') or 0.5)
    teto = pri + sec
    slot_manda = _por_id(rb.get('posicao_slot') or {}, posicao_id) or 'ofensivo'
    if slot_manda == 'ofensivo':
        dono, outro, slot_dono, slot_outro = est1, est2, 1, 2
    else:
        dono, outro, slot_dono, slot_outro = est2, est1, 2, 1
    if not dono:
        dono, outro = outro, None
        slot_dono, slot_outro = slot_outro, slot_dono
    por_slot = {1: 0.0, 2: 0.0}
    if dono and _por_id(_por_id(casa, dono) or {}, posicao_id) == funcao:
        por_slot[slot_dono] += pri
    if outro and posicao_id in (_por_id(liga, outro) or []):
        por_slot[slot_outro] += sec
    total = round(min(por_slot[1] + por_slot[2], teto), 4)
    return total, round(por_slot[1], 4), round(por_slot[2], 4)


def bonus_do_estilo_ia(par, lista):
    if not lista:
        return 0.0
    pt = float(par.get('estilo_ia_ponto') or 1.0)
    teto = float(par.get('estilo_ia_teto') or 4)
    return round(pt * min(len(lista), teto) / teto, 4)


def preparar_payload_writer(linha):
    """Monta o envelope exato do writer ou bloqueia antes de qualquer RPC."""
    if linha.get('faltou'):
        return None
    textos = ('card_id', 'carta_versao', 'carta_fingerprint',
              'contrato_versao', 'contrato_fingerprint',
              'formula_fingerprint', 'motor_bonus')
    ids = ('build_linha_card_id', 'funcao_id', 'posicao_id')
    for chave in textos:
        if not isinstance(linha.get(chave), str) or not linha[chave].strip():
            raise RuntimeError('resultado sem selo obrigatorio: %s' % chave)
    for chave in ids:
        if not isinstance(linha.get(chave), int) or isinstance(linha.get(chave), bool):
            raise RuntimeError('resultado sem identidade numerica: %s' % chave)
    parcelas = {
        'bonus_pe': linha.get('b_pe_ruim'),
        'bonus_fisico_total': linha.get('b_corpo'),
        # A formula v8 nao possui uma parcela posicional separada.
        'bonus_posicao': 0.0,
        'bonus_playstyle_1': linha.get('b_estilo_slot1'),
        'bonus_playstyle_2': linha.get('b_estilo_slot2'),
        'bonus_ia': linha.get('b_ia'),
    }
    if any(not isinstance(v, (int, float)) or isinstance(v, bool)
           for v in parcelas.values()):
        raise RuntimeError('resultado apto possui parcela nao numerica')
    detalhe_fisico = linha.get('detalhe')
    if not isinstance(detalhe_fisico, dict) or not detalhe_fisico:
        raise RuntimeError('resultado apto nao detalha as contribuicoes fisicas')
    try:
        soma_detalhe = sum(
            (decimal.Decimal(str(v)) for v in detalhe_fisico.values()
             if not isinstance(v, bool)), decimal.Decimal('0'))
    except (decimal.InvalidOperation, ValueError, TypeError):
        raise RuntimeError('detalhe fisico possui contribuicao nao numerica')
    if len(detalhe_fisico) != sum(
            1 for v in detalhe_fisico.values()
            if isinstance(v, (int, float)) and not isinstance(v, bool)):
        raise RuntimeError('detalhe fisico possui contribuicao nao numerica')
    if soma_detalhe != decimal.Decimal(str(parcelas['bonus_fisico_total'])):
        raise RuntimeError('detalhe fisico diverge do bonus_fisico_total')
    total = round(sum(parcelas.values()), 4)
    if total != linha.get('b_total'):
        raise RuntimeError('resultado bloqueado: total diverge das parcelas do writer')
    if round(parcelas['bonus_playstyle_1'] + parcelas['bonus_playstyle_2'], 4) != linha.get('b_estilo'):
        raise RuntimeError('resultado bloqueado: decomposicao dos playstyles diverge da formula v8')
    return {
        'build_linha_card_id': linha['build_linha_card_id'],
        'card_id': linha['card_id'],
        'funcao_id': linha['funcao_id'],
        'posicao_id': linha['posicao_id'],
        'carta_versao': linha['carta_versao'],
        'carta_fingerprint': linha['carta_fingerprint'],
        'contrato_versao': linha['contrato_versao'],
        'contrato_fingerprint': linha['contrato_fingerprint'],
        'formula_fingerprint': linha['formula_fingerprint'],
        'motor_versao': linha['motor_bonus'],
        'bonus_pe': parcelas['bonus_pe'],
        'bonus_fisico_total': parcelas['bonus_fisico_total'],
        'bonus_fisico_detalhe': detalhe_fisico,
        'bonus_posicao': parcelas['bonus_posicao'],
        'bonus_playstyle_1': parcelas['bonus_playstyle_1'],
        'bonus_playstyle_2': parcelas['bonus_playstyle_2'],
        'bonus_ia': parcelas['bonus_ia'],
        'bonus_outros': {},
        'bonus_total': total,
    }


def validar_retorno_writer(resposta, payload):
    if not isinstance(resposta, dict):
        raise RuntimeError('writer novo nao devolveu o readback JSON esperado')
    if resposta.get('readback') != 'ok':
        raise RuntimeError('writer novo nao confirmou o readback transacional')
    if resposta.get('build_linha_card_id') != payload['build_linha_card_id']:
        raise RuntimeError('writer novo devolveu outra identidade de linha')
    if resposta.get('carta_versao') != payload['carta_versao'] or resposta.get('carta_fingerprint') != payload['carta_fingerprint']:
        raise RuntimeError('writer novo devolveu selos de carta divergentes')
    if not isinstance(resposta.get('build_bonificador_id'), int):
        raise RuntimeError('writer novo nao devolveu build_bonificador_id valido')
    fingerprint = resposta.get('resultado_fingerprint')
    if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(c not in '0123456789abcdef' for c in fingerprint.lower()):
        raise RuntimeError('writer novo nao devolveu resultado_fingerprint SHA-256 valido')
    gravado = resposta.get('gravado') is True
    idempotente = resposta.get('idempotente') is True
    if gravado == idempotente:
        raise RuntimeError('writer novo devolveu estado gravado/idempotente incoerente')
    return resposta


def gravar_resultados_canonicos(linhas, rpc_call):
    """Usa exclusivamente o writer público controlado, uma transação por resultado."""
    respostas = []
    for linha in linhas:
        payload = preparar_payload_writer(linha)
        if payload is None:
            continue
        resposta = rpc_call(WRITER_BONUS, {'p_resultado': payload})
        respostas.append(validar_retorno_writer(resposta, payload))
        print('FILA_CONFIRMADA: linha=%d' % payload['build_linha_card_id'])
    return respostas


# ================================================================== RODA
print('=' * 70)
print('  BONIFICADOR v9  —  corpo · pe ruim · estilo (por funcao) · IA')
print('=' * 70)

print('')
print('[1/4] baixando a receita do banco')
rb = rpc('bonificador_regua_v2')
if not rb or not rb.get('pode_rodar'):
    print('  PAREI: a public.bonificador_regua_v2() esta ausente ou bloqueada.')
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
print('[2/4] baixando as linhas pendentes e os selos vigentes')
pares, passo, de = [], 1000, 0
while True:
    try:
        lote = rpc('bonificador_contexto_fila_v4',
                   {'p_limit': passo, 'p_offset': de})
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode('utf-8')[:300]
        print('')
        print('  PAREI: contrato canônico da fila V4 indisponível: %s' % detalhe)
        print('  Nao existe fallback para qualquer tabela ou contrato legado.')
        pausa(); sys.exit(1)
    if not lote:
        break
    for x in lote:
        exigidos = ('build_linha_card_id', 'card_id', 'funcao_id',
                    'funcao_codigo', 'posicao_id', 'carta_versao',
                    'carta_fingerprint', 'contrato_versao',
                    'contrato_fingerprint', 'formula_fingerprint')
        ausentes = [k for k in exigidos if x.get(k) is None]
        if ausentes:
            print('')
            print('  PAREI: contexto do writer nao devolve identidade/selos: %s.'
                  % ', '.join(ausentes))
            pausa(); sys.exit(1)
        pares.append({
            'build_linha_card_id': int(x['build_linha_card_id']),
            'card_id': str(x['card_id']),
            'funcao_id': int(x['funcao_id']),
            'funcao_codigo': str(x['funcao_codigo']),
            'posicao_id': int(x['posicao_id']),
            'carta_versao': str(x['carta_versao']),
            'carta_fingerprint': str(x['carta_fingerprint']),
            'contrato_versao': str(x['contrato_versao']),
            'contrato_fingerprint': str(x['contrato_fingerprint']),
            'formula_fingerprint': str(x['formula_fingerprint']),
        })
    de += passo
    print('   %d pares...' % len(pares), end='\r')
    if len(lote) < passo:
        break
print('   pares card x funcao ................ %d      ' % len(pares))
print('FILA_TOTAL: %d' % len(pares))

# A fila só identifica linhas marcadas. A régua já foi lida uma vez acima e
# fornece os selos usados pelo writer; não se reavalia a régua para cada linha.
for par_da_fila in pares:
    par_da_fila['contrato_versao'] = str(rb.get('contrato') or par_da_fila['contrato_versao'])
    par_da_fila['contrato_fingerprint'] = str(
        rb.get('contrato_fingerprint') or par_da_fila['contrato_fingerprint'])

if not pares:
    print('')
    print('  CONCLUIDO: nao ha linha pendente em clube_novo.build_linha_card.')
    print('  Nenhuma gravacao era necessaria nesta rodada.')
    if not _os.environ.get(_MARCADOR_RODADA):
        pausa()
    sys.exit(0)

cards = sorted({x['card_id'] for x in pares})
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
        CARTA[cid] = rpc('bonificador_carta_v2', {'p_card_id': cid}) or {
            'pode_rodar': False,
            'falta_o_que': ['contrato vazio']}
    except Exception as e:
        CARTA[cid] = {
            'pode_rodar': False,
            'falta_o_que': ['falha no contrato v1: %s' % str(e)[:160]]}
print('   %d/%d cards            ' % (len(cards), len(cards)))

for contexto in pares:
    linha_id = contexto['build_linha_card_id']
    cid = contexto['card_id']
    fun_id = contexto['funcao_id']
    fun_codigo = contexto['funcao_codigo']
    linha_posicao_id = contexto['posicao_id']
    print('FILA_LINHA: linha=%d card=%s funcao=%d posicao=%d'
          % (linha_id, cid, fun_id, linha_posicao_id))
    c = CARTA.get(cid) or {}
    falhas_contrato = list(c.get('falta_o_que') or [])
    if str(c.get('card_id') or '') != str(cid):
        falhas_contrato.append('contrato devolveu outro card_id')
    for selo in ('carta_versao', 'carta_fingerprint'):
        if not isinstance(c.get(selo), str) or not c.get(selo).strip():
            falhas_contrato.append('contrato sem %s' % selo)
    if c.get('carta_versao') != contexto.get('carta_versao'):
        falhas_contrato.append('versao da carta divergiu da linha canônica')
    else:
        # A carta é a fonte física. O fingerprint da linha identifica a build;
        # o fingerprint do contrato de carta sela o insumo do Bonificador.
        contexto['carta_fingerprint'] = str(c.get('carta_fingerprint') or '')
    falhas_contrato = list(dict.fromkeys(falhas_contrato))
    contrato_ok = bool(c.get('pode_rodar')) and not falhas_contrato

    if contrato_ok:
        r = bonus_do_corpo_writer(
            MOLDE_CORPO, c.get('corpo'), fun_id, CORPO_MAX)
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
            fun_id, c.get('posicao_id'))
        b_est_detalhado, b_est_slot1, b_est_slot2 = bonus_do_estilo_componentes(
            rb, c.get('slot1_id_jogo'), c.get('slot2_id_jogo'),
            fun_id, c.get('posicao_id'))
        if b_est != b_est_detalhado:
            falhas_contrato.append('decomposicao dos playstyles diverge da formula v8')
        if b_est is None:
            sem_estilo += 1

        ia = c.get('estilos_ia')
        if ia is None:
            sem_ia += 1
            b_ia = None
        else:
            b_ia = bonus_do_estilo_ia(par, ia)
    else:
        b_corpo = b_pe = b_est = b_est_slot1 = b_est_slot2 = b_ia = None
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
        'build_linha_card_id': linha_id,
        'card_id': cid, 'funcao_id': fun_id, 'funcao_codigo': fun_codigo,
        'posicao_id': linha_posicao_id,
        'b_corpo': b_corpo, 'b_pe_ruim': b_pe, 'b_estilo': b_est, 'b_ia': b_ia,
        'b_estilo_slot1': b_est_slot1, 'b_estilo_slot2': b_est_slot2,
        'b_total': b_total,
        # ⛔ 15/08 ORDEM DO LUIS: "se ele nao sabe, ele vai querer colocar zero,
        #    e um numero inventado". O que faltou fica ESCRITO, com nome.
        'faltou': faltou,
        'corpo_soma': c_soma, 'corpo_pct': c_pct,
        'detalhe': detalhe, 'motor_bonus': MOTOR_BONUS,
        'carta_versao': contexto.get('carta_versao'),
        'carta_fingerprint': contexto.get('carta_fingerprint'),
        'contrato_versao': contexto.get('contrato_versao'),
        'contrato_fingerprint': contexto.get('contrato_fingerprint'),
        'formula_fingerprint': contexto.get('formula_fingerprint')})
    print('FILA_RESULTADO: ' + json.dumps({
        'linha_id': linha_id, 'card_id': cid, 'funcao_id': fun_id,
        'estado': 'bloqueada' if faltou else 'apta',
        'b_corpo': b_corpo, 'b_pe_ruim': b_pe, 'b_estilo': b_est,
        'b_ia': b_ia, 'b_total': b_total, 'faltou': faltou,
    }, ensure_ascii=False, separators=(',', ':')))
    print('FILA_CALCULADA: linha=%d estado=%s' % (
        linha_id, 'bloqueada' if faltou else 'apta'))

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
try:
    respostas = gravar_resultados_canonicos(gravaveis, rpc)
    enviados = len(respostas)
except urllib.error.HTTPError as e:
    print('')
    print('   ERRO no writer clube_novo: %s' % e.read().decode('utf-8')[:300])
    pausa(); sys.exit(1)
except Exception as e:
    print('')
    print('   PAREI: retorno do writer novo recusado: %s' % str(e)[:300])
    pausa(); sys.exit(1)
if enviados != len(gravaveis):
    print('')
    print('   PAREI: nem todo resultado apto recebeu readback do writer novo.')
    pausa(); sys.exit(1)

print('   %d resultados confirmados em clube_novo.build_bonificador' % enviados)
print('')
print('=' * 70)
print('  PRONTO. O writer novo confirmou identidade, selos e readback transacional.')
print('  Nenhuma chamada produtiva foi feita para o writer legado.')
print('=' * 70)
PIPELINE_RESULTADO = {
    'pares': len(pares),
    'bloqueados': bloqueados,
    'enviados': enviados,
}
if not _os.environ.get(_MARCADOR_RODADA):
    pausa()
