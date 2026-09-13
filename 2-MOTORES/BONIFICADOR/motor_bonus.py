# -*- coding: utf-8 -*-
"""
BONIFICADOR — v12 (09/09/2026)

O QUE MUDOU NESTA VERSAO
  1. OS DADOS DO JOGO VEM DO MODELO NOVO. Corpo, pe ruim, posicao,
     playstyles e estilos de IA saem exclusivamente de contratos v1 sobre
     clube_novo. Nao existe fallback para carta_do_motor nem para JSON antigo.
  2. GRAVA SOMENTE NO MODELO NOVO. Cada resultado apto passa pelo writer
     transacional public.gravar_build_bonificador_v6. Nao existe chamada
     produtiva ou gravacao em estruturas legadas.
  3. O BONUS DE ESTILO SEGUE A POSICAO COMPATIVEL DO JOGO.
     A funcao define o principal (1,0) e o secundario (0,5). A posicao
     escolhida decide a ativacao. Basico nao pontua. So Defensor Criativo
     e Lateral Defensivo recebem a promocao excepcional aprovada. Teto 1,5.

AS PORTAS DO BANCO
    public.bonificador_regua_v4() a receita allowlisted e seus gates
    public.bonificador_carta_v3() somente as entradas usadas pelo Bonificador
    public.bonificador_contexto_fila_v7() linhas, nomes de apresentação e selos vigentes
    public.gravar_build_bonificador_v6(jsonb) a volta transacional para linhas novas
    public.bonificador_correcao_*_v1() prepara resultados V12 sem expor nem
      substituir o resultado V9 antes do corte transacional
    public.bonificador_correcao_proxima_linha_v2(uuid) reserva o staging V12
    public.bonificador_correcao_registrar_v1(...) confirma falha sem cortar a linha

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

import os, sys, json, time, urllib.request, urllib.error, decimal, signal, threading, ssl
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
    print('  PIPELINE VIVO: consulta as linhas elegíveis do contrato canônico.')
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
                if (_os.environ.get('CLUBEF_BONIFICADOR_CORRECAO_LOTE_ID')
                        or _os.environ.get('CLUBEF_BONIFICADOR_INTEGRAL_LOTE_ID')):
                    print('  LOTE SELECIONADO SEM PENDÊNCIAS: encerrando o worker normalmente.')
                    return
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

MOTOR_BONUS = 'v12-0909-estilo-funcao-ativacao-v1'
FORMULA_BONUS = '4c6ad750fd5c8bb218220b5f330d875ea3cd8cbcb6f89bad24a394eb22322db8'
REGUA_BONUS = 'bonificador_regua_v4'
FILA_BONUS = 'bonificador_contexto_fila_v7'
WRITER_BONUS = 'gravar_build_bonificador_v6'
WRITER_CORRECAO_BONUS = 'gravar_build_bonificador_correcao_v2'
LOTE_OPERACIONAL_ID = _os.environ.get('CLUBEF_BONIFICADOR_LOTE_ID', '').strip()
LOTE_CORRECAO_ID = _os.environ.get('CLUBEF_BONIFICADOR_CORRECAO_LOTE_ID', '').strip()
LOTE_INTEGRAL_ID = _os.environ.get('CLUBEF_BONIFICADOR_INTEGRAL_LOTE_ID', '').strip()
if sum(bool(x) for x in (LOTE_OPERACIONAL_ID, LOTE_CORRECAO_ID, LOTE_INTEGRAL_ID)) > 1:
    raise RuntimeError('Selecione somente um lote do Bonificador por execução.')
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
        if nome == REGUA_BONUS:
            cur.execute('select public.bonificador_regua_v4()')
            return cur.fetchone()[0]
        if nome == 'bonificador_carta_v3':
            cur.execute('select public.bonificador_carta_v3(%s)', ((corpo or {}).get('p_card_id'),))
            return cur.fetchone()[0]
        if nome == FILA_BONUS:
            cur.execute('select * from public.bonificador_contexto_fila_v7(%s,%s)', (
                (corpo or {}).get('p_limit', 1000), (corpo or {}).get('p_offset', 0)))
            colunas = [d.name for d in cur.description]
            return [dict(zip(colunas, linha)) for linha in cur.fetchall()]
        if nome == 'bonificador_contexto_lote_integral_v1':
            cur.execute('select * from public.bonificador_contexto_lote_integral_v1(%s::uuid,%s,%s)', (
                (corpo or {}).get('p_lote_id'), (corpo or {}).get('p_limit', 100), (corpo or {}).get('p_offset', 0)))
            colunas = [d.name for d in cur.description]
            return [dict(zip(colunas, linha)) for linha in cur.fetchall()]
        if nome == 'bonificador_integral_status_v1':
            cur.execute('select public.bonificador_integral_status_v1(%s::uuid)', ((corpo or {}).get('p_lote_id'),))
            return cur.fetchone()[0]
        if nome == 'bonificador_lote_proxima_linha_v1':
            cur.execute('select public.bonificador_lote_proxima_linha_v1(%s::uuid)', (
                (corpo or {}).get('p_lote_id'),))
            resultado = cur.fetchone()[0]
            _CONEXAO_BONIFICADOR.commit()
            return resultado
        if nome == 'bonificador_lote_registrar_v1':
            cur.execute('select public.bonificador_lote_registrar_v1(%s::uuid,%s,%s,%s,%s)', (
                (corpo or {}).get('p_lote_id'), (corpo or {}).get('p_linha_id'),
                (corpo or {}).get('p_estado'), (corpo or {}).get('p_bonus_total'),
                (corpo or {}).get('p_motivo')))
            resultado = cur.fetchone()[0]
            _CONEXAO_BONIFICADOR.commit()
            return resultado
        if nome == 'bonificador_correcao_status_v1':
            cur.execute('select public.bonificador_correcao_status_v1(%s::uuid)', (
                (corpo or {}).get('p_lote_id'),))
            return cur.fetchone()[0]
        if nome == 'bonificador_correcao_proxima_linha_v2':
            cur.execute('select public.bonificador_correcao_proxima_linha_v2(%s::uuid)', (
                (corpo or {}).get('p_lote_id'),))
            resultado = cur.fetchone()[0]
            _CONEXAO_BONIFICADOR.commit()
            return resultado
        if nome == 'bonificador_correcao_registrar_v1':
            cur.execute('select public.bonificador_correcao_registrar_v1(%s::uuid,%s,%s,%s)', (
                (corpo or {}).get('p_lote_id'), (corpo or {}).get('p_linha_id'),
                (corpo or {}).get('p_estado'), (corpo or {}).get('p_motivo')))
            resultado = cur.fetchone()[0]
            _CONEXAO_BONIFICADOR.commit()
            return resultado
        if nome == WRITER_BONUS:
            cur.execute('select public.gravar_build_bonificador_v6(%s::jsonb)',
                        (json.dumps((corpo or {}).get('p_resultado')),))
            resultado = cur.fetchone()[0]
            _CONEXAO_BONIFICADOR.commit()
            return resultado
        if nome == WRITER_CORRECAO_BONUS:
            cur.execute('select public.gravar_build_bonificador_correcao_v2(%s::uuid,%s::jsonb)', (
                (corpo or {}).get('p_lote_id'), json.dumps((corpo or {}).get('p_resultado'))))
            resultado = cur.fetchone()[0]
            _CONEXAO_BONIFICADOR.commit()
            return resultado
    raise RuntimeError('contrato local não permitido: %s' % nome)


_HTTP_TRANSITORIOS = {408, 425, 429, 500, 502, 503, 504, 520, 522, 524}
_WINDOWS_REDE_TRANSITORIA = {10053, 10054, 10060, 10061}


def _erro_rpc_transitorio(erro):
    """Distingue queda de transporte de recusa permanente do contrato."""
    if isinstance(erro, urllib.error.HTTPError):
        return erro.code in _HTTP_TRANSITORIOS
    if isinstance(erro, urllib.error.URLError):
        motivo = erro.reason
        if isinstance(motivo, ssl.SSLCertVerificationError):
            return False
        if isinstance(motivo, (TimeoutError, ConnectionError)):
            return True
        if isinstance(motivo, OSError):
            if getattr(motivo, 'winerror', None) in _WINDOWS_REDE_TRANSITORIA:
                return True
        texto = str(motivo).lower()
        return any(sinal in texto for sinal in (
            'timed out', 'timeout', 'temporar', 'connection reset',
            'connection aborted', 'connection refused', '10053', '10054',
            '10060', '10061', 'host remoto', 'remote host'))
    return isinstance(erro, (TimeoutError, ConnectionError))


def rpc(nome, corpo=None, timeout=180):
    if USAR_BANCO_DIRETO:
        return _rpc_banco(nome, corpo)

    # No lote corretivo, uma falha transitória não pode virar "dados ausentes" e
    # bloquear 200 mil linhas. Zero significa repetir até a conexão voltar. Fora
    # da correção, o limite mantém um erro permanente visível ao operador.
    limite_padrao = 0 if LOTE_CORRECAO_ID else 6
    limite = _inteiro_ambiente(
        'CLUBEF_BONIFICADOR_RPC_MAX_TENTATIVAS', limite_padrao, 0)
    espera_base = _inteiro_ambiente(
        'CLUBEF_BONIFICADOR_RPC_ESPERA_SEGUNDOS', 2, 1)
    tentativa = 0

    while True:
        tentativa += 1
        try:
            req = urllib.request.Request(
                '%s/rest/v1/rpc/%s' % (URL, nome),
                data=json.dumps(corpo or {}).encode('utf-8'),
                headers=CAB, method='POST')
            with urllib.request.urlopen(req, timeout=timeout) as r:
                t = r.read().decode('utf-8')
            return json.loads(t) if t.strip() else None
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, ConnectionError) as erro:
            if not _erro_rpc_transitorio(erro):
                raise
            if limite and tentativa >= limite:
                raise
            espera = min(30, espera_base * (2 ** min(tentativa - 1, 4)))
            print(
                '   CONEXAO TRANSITORIA no %s (tentativa %d). '
                'A linha continua reservada; nova tentativa em %ds.'
                % (nome, tentativa, espera))
            time.sleep(espera)


# ============================================================== A CONTA
def nota_da_medida(valor, cortes):
    """Regra aprovada: cinco faixas -2..+2, com a borda ``valor <= corte``."""
    if valor is None or not isinstance(cortes, (list, tuple)) or len(cortes) != 4:
        return None
    if any(c is None for c in cortes):
        return None
    try:
        c1, c2, c3, c4 = (float(c) for c in cortes)
        v = float(valor)
    except (TypeError, ValueError):
        return None
    if not (c1 <= c2 <= c3 <= c4):
        return None
    if v <= c1:
        return -2
    if v <= c2:
        return -1
    if v <= c3:
        return 0
    if v <= c4:
        return 1
    return 2


def bonus_do_corpo(molde_corpo, corpo, funcao, corpo_max):
    """corpo = lista de 12 medidas na ordem do corpo_ordem. Devolve (bonus, soma, pct, detalhe)."""
    m = _por_id(molde_corpo or {}, funcao)
    if not m or not isinstance(corpo, (list, tuple)) or not corpo:
        return None
    try:
        limite = float(corpo_max)
    except (TypeError, ValueError):
        return None
    if limite <= 0:
        return None
    soma = maximo = 0.0
    pontos_por_medida = {}
    for medida, regra in m.items():
        idx = regra.get('idx')
        if not isinstance(idx, int) or isinstance(idx, bool) or idx < 0 or idx >= len(corpo):
            return None
        v = corpo[idx]
        if v is None:
            return None
        n = nota_da_medida(v, regra.get('cortes') or [])
        if n is None:
            return None
        direcao = regra.get('direcao')
        if isinstance(direcao, bool) or direcao not in (-1, 0, 1):
            return None
        try:
            peso = float(regra.get('peso'))
        except (TypeError, ValueError):
            return None
        if peso <= 0:
            return None
        if direcao == 0:
            pontos_por_medida[medida] = 0.0
            continue
        pontos = float(n * direcao) * peso
        soma += pontos
        maximo += 2.0 * peso
        pontos_por_medida[medida] = pontos
    if maximo <= 0:
        return None
    pct = max(-1.0, min(1.0, soma / maximo))
    bonus = round(max(-limite, min(limite, pct * limite)), 4)
    return bonus, round(soma, 4), round(pct, 4), pontos_por_medida


def bonus_do_corpo_writer(molde_corpo, corpo, funcao, corpo_max):
    """Converte os pontos aprovados em parcelas que fecham exatamente no total."""
    resultado = bonus_do_corpo(molde_corpo, corpo, funcao, corpo_max)
    if resultado is None:
        return None
    bonus, soma, pct, pontos_por_medida = resultado
    molde = _por_id(molde_corpo or {}, funcao) or {}
    ativas = []
    maximo = 0.0
    detalhe = {medida: 0.0 for medida in pontos_por_medida}
    for medida, pontos in pontos_por_medida.items():
        regra = molde.get(medida) or {}
        if regra.get('direcao') == 0:
            continue
        peso = float(regra.get('peso'))
        maximo += 2.0 * peso
        ativas.append((medida, pontos))
    if not ativas or maximo <= 0:
        return None
    acumulado = 0.0
    for indice, (medida, pontos) in enumerate(ativas):
        if indice == len(ativas) - 1:
            contribuicao = round(bonus - acumulado, 8)
        else:
            contribuicao = round(pontos / maximo * float(corpo_max), 8)
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
    """V12: funcao escolhe principal; a posicao escolhida decide ativacao."""
    return bonus_do_estilo_componentes(rb, est1, est2, funcao, posicao_id)[0]


def bonus_do_estilo_componentes(rb, est1, est2, funcao, posicao_id):
    """Parcelas por ataque/defesa efetivos, nunca pela ordem fisica antiga."""
    politica = rb.get('politica_estilo') or {}
    if politica.get('versao') != 'estilos-funcao-20260909-v1':
        raise RuntimeError('V12: politica aprovada de estilos ausente')
    if rb.get('politica_estilo_fingerprint') != '7ed53bbab831180cde9d247782dd133fe072acadb69bd34871c3f83f28773dc5':
        raise RuntimeError('V12: politica de estilos diverge da decisao aprovada')
    principal = _por_id(politica.get('principal_por_funcao'), funcao)
    if principal not in ('ataque', 'defesa') or posicao_id is None:
        raise RuntimeError('V12: funcao ou posicao escolhida sem definicao')
    if est1 is None or est2 is None:
        raise RuntimeError('V12: estilo ausente nao significa Basico')
    pendentes = politica.get('pendentes_ativacao') or []
    if est1 in pendentes or est2 in pendentes:
        raise RuntimeError('V12: estilo aguarda definicao de ativacao no jogo')
    if (est1 != 256 and ((int(est1) >> 6) & 3) not in (0, 2)) or (est2 != 256 and ((int(est2) >> 6) & 3) not in (1, 2)):
        raise RuntimeError('V12: slots nao representam ataque e defesa efetivos')
    liga = rb.get('liga') or {}
    for estilo in (est1, est2):
        if estilo != 256 and _por_id(liga, estilo) is None:
            raise RuntimeError('V12: estilo sem cadastro de ativacao')
    ativo_a = est1 != 256 and posicao_id in (_por_id(liga, est1) or [])
    ativo_d = est2 != 256 and posicao_id in (_por_id(liga, est2) or [])
    pontos = politica['pontos']
    a = float(pontos['principal'] if principal == 'ataque' else pontos['secundario']) if ativo_a else 0.0
    d = float(pontos['principal'] if principal == 'defesa' else pontos['secundario']) if ativo_d else 0.0
    if ativo_a and not ativo_d:
        for regra in politica['excecoes']:
            if est1 == regra['playstyle_id'] and funcao in regra['funcoes'] and posicao_id in regra['posicoes']:
                a = float(regra['valor_unico_ativo'])
    return round(min(a + d, float(pontos['teto'])), 4), round(a, 4), round(d, 4)


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
    for chave in ('corpo_soma', 'corpo_pct', 'corpo_maximo'):
        if not isinstance(linha.get(chave), (int, float)) or isinstance(linha.get(chave), bool):
            raise RuntimeError('resultado apto sem prova física numérica: %s' % chave)
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
        'corpo_soma': linha['corpo_soma'],
        'corpo_pct': linha['corpo_pct'],
        'corpo_maximo': linha['corpo_maximo'],
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


def gravar_resultados_canonicos(linhas, rpc_call, lote_operacional_id='', lote_correcao_id=''):
    """Usa o writer canônico e só então confirma o item estável do lote."""
    respostas = []
    for linha in linhas:
        payload = preparar_payload_writer(linha)
        if payload is None:
            continue
        if lote_correcao_id:
            resposta = rpc_call(WRITER_CORRECAO_BONUS, {
                'p_lote_id': lote_correcao_id, 'p_resultado': payload})
        else:
            resposta = rpc_call(WRITER_BONUS, {'p_resultado': payload})
        resposta = validar_retorno_writer(resposta, payload)
        if lote_operacional_id:
            total = payload['bonus_total']
            estado_lote = 'sem_bonus' if total == 0 else 'concluida'
            item = rpc_call('bonificador_lote_registrar_v1', {
                'p_lote_id': lote_operacional_id,
                'p_linha_id': payload['build_linha_card_id'],
                'p_estado': estado_lote,
                'p_bonus_total': total,
                'p_motivo': None,
            })
            if not isinstance(item, dict) or not item.get('ok'):
                raise RuntimeError('lote não confirmou o resultado já gravado')
        respostas.append(resposta)
        print('FILA_CONFIRMADA: linha=%d' % payload['build_linha_card_id'])
    return respostas


# ================================================================== RODA
print('=' * 70)
print('  BONIFICADOR v12 — estilo por função e posição · físico · pé ruim · IA')
print('=' * 70)

print('')
print('[1/4] baixando a receita do banco')
if LOTE_OPERACIONAL_ID and not LOTE_CORRECAO_ID:
    print('  PAREI: o lote V1 pertence ao motor/fórmula V9 e não pode ser reaproveitado.')
    print('  Use somente o lote corretivo V1 preparado para a fórmula V12.')
    pausa(); sys.exit(1)
rb = rpc(REGUA_BONUS)
if not rb or not rb.get('pode_rodar'):
    print('  PAREI: a public.%s() esta ausente ou bloqueada.' % REGUA_BONUS)
    if rb and rb.get('falta_o_que'):
        print('  Falta: %s' % ', '.join(str(x) for x in rb.get('falta_o_que') or []))
    pausa(); sys.exit(1)
for chave in ('parametro', 'molde_corpo', 'corpo_ordem', 'casa', 'liga', 'politica_estilo', 'politica_estilo_fingerprint'):
    if chave not in rb:
        print('  PAREI: contrato da regua sem a chave obrigatoria %s.' % chave)
        pausa(); sys.exit(1)
if not rb.get('liberado_para_producao'):
    print('  V12 PREPARADA: producao sera liberada na etapa de atualizacao da Maquina 2.')
    print('  Nenhuma linha foi reservada ou gravada.')
    pausa(); sys.exit(0)
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
try:
    if LOTE_INTEGRAL_ID:
        paginas = [rpc('bonificador_contexto_lote_integral_v1', {
            'p_lote_id': LOTE_INTEGRAL_ID, 'p_limit': 100, 'p_offset': 0,
        }) or []]
    elif LOTE_CORRECAO_ID:
        reservada = rpc('bonificador_correcao_proxima_linha_v2', {
            'p_lote_id': LOTE_CORRECAO_ID,
        })
        paginas = [[reservada]] if reservada else []
    elif LOTE_OPERACIONAL_ID:
        reservada = rpc('bonificador_lote_proxima_linha_v1', {
            'p_lote_id': LOTE_OPERACIONAL_ID,
        })
        paginas = [[reservada]] if reservada else []
    else:
        paginas = []
        while True:
            pagina = rpc(FILA_BONUS, {'p_limit': passo, 'p_offset': de})
            if not pagina:
                break
            paginas.append(pagina)
            de += len(pagina)
            if len(pagina) < passo:
                break
except urllib.error.HTTPError as e:
    detalhe = e.read().decode('utf-8')[:300]
    print('')
    print('  PAREI: contrato canônico do lote indisponível: %s' % detalhe)
    print('  Nao existe fallback para qualquer tabela ou contrato legado.')
    pausa(); sys.exit(1)

for lote in paginas:
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
        if str(x.get('formula_fingerprint')) != FORMULA_BONUS:
            print('')
            print('  PAREI: a fila devolveu fingerprint de fórmula diferente da V12 aprovada.')
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
    print('   %d pares...' % len(pares), end='\r')
print('   pares card x funcao ................ %d      ' % len(pares))
print('FILA_TOTAL: %d' % len(pares))

# A fila só identifica linhas marcadas. A régua já foi lida uma vez acima e
# fornece os selos usados pelo writer; não se reavalia a régua para cada linha.
for par_da_fila in pares:
    par_da_fila['contrato_versao'] = str(rb.get('contrato') or par_da_fila['contrato_versao'])
    par_da_fila['contrato_fingerprint'] = str(
        rb.get('contrato_fingerprint') or par_da_fila['contrato_fingerprint'])
    par_da_fila['formula_fingerprint'] = str(
        rb.get('formula_fingerprint') or par_da_fila['formula_fingerprint'])

if not pares:
    if LOTE_INTEGRAL_ID:
        status_lote = rpc('bonificador_integral_status_v1', {'p_lote_id': LOTE_INTEGRAL_ID}) or {}
        if (status_lote.get('existe') is not True or status_lote.get('preparado') is not True
                or any(int(status_lote.get(k) or 0) for k in ('nao_conferidas', 'bloqueadas', 'calcular_pendentes'))):
            print('  LOTE INTERROMPIDO: a conferência não confirmou todas as exceções resolvidas.')
            pausa(); sys.exit(2)
    elif LOTE_CORRECAO_ID:
        status_lote = rpc('bonificador_correcao_status_v1', {'p_lote_id': LOTE_CORRECAO_ID}) or {}
        contagens_lote = status_lote.get('contagens') or {}
        if (status_lote.get('ok') is not True
                or any(int(contagens_lote.get(k) or 0) for k in ('pendente', 'processando', 'falha'))):
            print('  LOTE INTERROMPIDO: existem pendências/falhas ou o banco não confirmou o encerramento.')
            pausa(); sys.exit(2)
    print('')
    print('  CONCLUIDO: não há exceção pendente no lote selecionado.' if LOTE_INTEGRAL_ID
          else '  CONCLUIDO: nao ha linha pendente em clube_novo.build_linha_card.')
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
        CARTA[cid] = rpc('bonificador_carta_v3', {'p_card_id': cid}) or {
            'pode_rodar': False,
            'falta_o_que': ['contrato vazio']}
    except Exception as e:
        CARTA[cid] = {
            'pode_rodar': False,
            'falta_o_que': ['falha no contrato de carta V3: %s' % str(e)[:160]]}
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
            b_corpo, c_soma, c_pct, c_maximo, detalhe = None, None, None, None, None
        else:
            b_corpo, c_soma, c_pct, detalhe = r
            # Etapa estrutural: preserva as doze parcelas e a nota vigente.
            # A aplicação seletiva da altura usa esta base, sem redistribuição.
            from altura_independente import separar_altura
            separado = separar_altura(detalhe, fun_id, aplicar_regra=False)
            if abs(float(separado['total']) - b_corpo) > 0.00000002:
                raise ValueError('Separação da altura não fecha com o físico de referência')
            molde_da_funcao = _por_id(MOLDE_CORPO, fun_id) or {}
            c_maximo = round(sum(
                2.0 * float((regra or {}).get('peso') or 0)
                for regra in molde_da_funcao.values()
                if (regra or {}).get('direcao') in (-1, 1)
            ), 4)

        b_pe = bonus_do_pe_ruim(
            par, c.get('pe_ruim_uso'), c.get('pe_ruim_precisao'))
        if b_pe is None:
            sem_pe += 1

        b_est = bonus_do_estilo(
            rb, c.get('slot1_id_jogo'), c.get('slot2_id_jogo'),
            fun_id, linha_posicao_id)
        b_est_detalhado, b_est_slot1, b_est_slot2 = bonus_do_estilo_componentes(
            rb, c.get('slot1_id_jogo'), c.get('slot2_id_jogo'),
            fun_id, linha_posicao_id)
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
        c_soma = c_pct = c_maximo = detalhe = None
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
        'corpo_soma': c_soma, 'corpo_pct': c_pct, 'corpo_maximo': c_maximo,
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
    if LOTE_CORRECAO_ID:
        for bloqueada in (x for x in saida if x.get('faltou') or not isinstance(x.get('b_total'), (int, float))):
            item = rpc('bonificador_correcao_registrar_v1', {
                'p_lote_id': LOTE_CORRECAO_ID,
                'p_linha_id': bloqueada['build_linha_card_id'],
                'p_estado': 'falha',
                'p_motivo': '; '.join(str(f) for f in bloqueada.get('faltou') or [])[:1000],
            })
            if not isinstance(item, dict) or not item.get('ok'):
                raise RuntimeError('lote corretivo não confirmou a falha da linha bloqueada')
    elif LOTE_OPERACIONAL_ID:
        for bloqueada in (x for x in saida if x.get('faltou') or not isinstance(x.get('b_total'), (int, float))):
            item = rpc('bonificador_lote_registrar_v1', {
                'p_lote_id': LOTE_OPERACIONAL_ID,
                'p_linha_id': bloqueada['build_linha_card_id'],
                'p_estado': 'falha',
                'p_bonus_total': None,
                'p_motivo': '; '.join(str(f) for f in bloqueada.get('faltou') or [])[:1000],
            })
            if not isinstance(item, dict) or not item.get('ok'):
                raise RuntimeError('lote não confirmou a falha da linha bloqueada')
    respostas = gravar_resultados_canonicos(
        gravaveis, rpc, LOTE_OPERACIONAL_ID, LOTE_CORRECAO_ID)
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
if bloqueados:
    print('  RODADA INTERROMPIDA: %d linha(s) bloqueada(s); confira as causas acima.' % bloqueados)
else:
    print('  RODADA CONFIRMADA: %d resultado(s) gravado(s) e conferido(s) no banco.' % enviados)
print('=' * 70)
PIPELINE_RESULTADO = {
    'pares': len(pares),
    'bloqueados': bloqueados,
    'enviados': enviados,
}
if bloqueados:
    pausa(); sys.exit(2)
if not _os.environ.get(_MARCADOR_RODADA):
    pausa()
