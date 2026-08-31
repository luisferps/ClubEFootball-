# -*- coding: utf-8 -*-
"""
AVALIAR — o servico que da a nota.

A metade do motor que pode ficar online. Recebe o estado que o usuario montou na
ficha e devolve A NOTA DO PROPRIO MOTOR. A regua (alvo, peso, degraus, punicao,
molde) fica AQUI DENTRO e nunca vai para o navegador.

Ordem do Luis, 25/08:
  "A gente nao pode abrir mao de que a nota que sai la, quando ele mexer no
   jogador dele, seja exatamente a nota que o nosso motor daria."
  "Se ele fica disponivel na internet de um jeito que alguem possa copiar,
   a gente cria os proprios concorrentes."

O QUE SAI DAQUI:  nota (b1) · os 26 valores · o ganho por etapa · a versao do molde
O QUE NUNCA SAI:  alvo · peso · degraus · formula da punicao · molde · o pool

Banco fora do ar = "nao sei agora". NUNCA uma conta local de emergencia.
"""
import os, time, threading, json, copy
from flask import Flask, request, jsonify

import banco
from otimizador import Otimizador
from monta_regua import da_rpc
from regua_do_banco import ReguaIncompleta
import avaliador as AV

app = Flask(__name__)

TATICA        = os.environ.get('TATICA_DO_TIME') or None
TTL_REGUA     = int(os.environ.get('TTL_REGUA_SEGUNDOS') or 900)
LIMITE_MINUTO = int(os.environ.get('LIMITE_POR_MINUTO') or 60)
CASAS         = int(os.environ.get('CASAS_DA_NOTA') or 1)

_lock   = threading.Lock()
_regua  = None
_quando = 0.0
_batidas = {}


def regua(forcar=False):
    """A regua vem do banco e fica em memoria por TTL_REGUA. Se o banco cair, o
    servico segue com a regua que ja tem — mas NUNCA nasce sem ela."""
    global _regua, _quando
    with _lock:
        velha = (time.time() - _quando) > TTL_REGUA
        if _regua is None or forcar or velha:
            try:
                nova = da_rpc(banco.pacote_da_regua(), TATICA)
                _regua, _quando = nova, time.time()
            except Exception:
                if _regua is None:
                    raise
        return _regua


def _passou_no_limite(ip):
    agora = int(time.time() // 60)
    with _lock:
        for k in [k for k in _batidas if k[1] != agora]:
            _batidas.pop(k, None)
        n = _batidas.get((ip, agora), 0) + 1
        _batidas[(ip, agora)] = n
    return n <= LIMITE_MINUTO


def erro(msg, codigo=400):
    return jsonify({'ok': False, 'erro': msg}), codigo


def _impetos_da_linha(carta, pedido, regua_atual):
    if pedido.get('impeto_nome') is not None or pedido.get('impeto_escolhido') is not None:
        raise ValueError('impeto deve ser informado por codigo e nivel, nunca por nome')
    equipados = carta.get('impetos_equipados') or []
    condicionais = [x for x in equipados if x.get('condicional')]
    if len(condicionais) > 1:
        raise ValueError('a carta possui mais de um impeto condicional')
    codigos = [int(x['codigo_impeto']) for x in equipados]
    if any(codigo not in regua_atual.imp_meta for codigo in codigos):
        raise ValueError('receita de impeto equipada ausente')
    codigo_pedido = pedido.get('impeto_condicional_codigo')
    nivel_pedido = pedido.get('impeto_condicional_nivel')
    if not condicionais:
        if codigo_pedido is not None or nivel_pedido is not None:
            raise ValueError('a carta nao possui impeto condicional')
        return codigos,None,None
    codigo = int(condicionais[0]['codigo_impeto'])
    maximo = int(condicionais[0].get('nivel_maximo') or 0)
    if codigo_pedido is None or nivel_pedido is None:
        raise ValueError('codigo e nivel do impeto condicional sao obrigatorios')
    if int(codigo_pedido) != codigo:
        raise ValueError('impeto condicional nao pertence a carta')
    nivel = int(nivel_pedido)
    if not 1 <= nivel <= maximo:
        raise ValueError('nivel do impeto condicional fora da faixa fisica')
    return codigos,codigo,nivel


def _regua_da_linha(regua_atual, codigo_condicional, nivel_condicional):
    """Adapta o catálogo antes da fórmula; a rotina matemática fica intocada."""
    if codigo_condicional is None:
        return regua_atual
    meta = regua_atual.imp_meta[int(codigo_condicional)]
    adaptada = copy.copy(regua_atual)
    adaptada.imp = dict(regua_atual.imp)
    adaptada.imp[int(codigo_condicional)] = {
        int(indice): int(nivel_condicional) for indice in meta.get('efeitos') or {}
    }
    return adaptada


@app.get('/saude')
def saude():
    try:
        r = regua()
        return jsonify({'ok': True, 'versao_molde': r.versao_molde,
                        'funcoes': len(r.molde), 'regua_carregada_ha_s': int(time.time() - _quando)})
    except Exception as e:
        return erro('a regua nao carregou: %s' % e, 503)


@app.post('/recarregar')
def recarregar():
    if request.headers.get('X-Chave-Admin') != (os.environ.get('CHAVE_ADMIN') or '\0'):
        return erro('nao autorizado', 401)
    try:
        r = regua(forcar=True)
        return jsonify({'ok': True, 'versao_molde': r.versao_molde})
    except Exception as e:
        return erro(str(e), 503)


@app.post('/avaliar')
def avaliar():
    ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
    if not _passou_no_limite(ip):
        return erro('muitas contas em pouco tempo; espere um minuto', 429)

    p = request.get_json(silent=True) or {}
    card_id = p.get('card_id')
    funcao_id = p.get('funcao_id')
    if not card_id or funcao_id is None:
        return erro('faltou card_id ou funcao_id')
    try:
        funcao_id = int(funcao_id)
    except (TypeError, ValueError):
        return erro('funcao_id invalido')

    try:
        r = regua()
    except Exception:
        return erro('nao sei agora: a regua nao esta carregada', 503)

    if funcao_id not in r.molde:
        return erro('funcao_id desconhecida')

    try:
        c = banco.carta_para_simular(card_id)
    except banco.BancoIndisponivel:
        return erro('nao sei agora: o banco nao respondeu', 503)
    if not c:
        return erro('carta nao encontrada', 404)
    if not c.get('pronto_motor_otimizacao'):
        return erro('esta carta ainda esta incompleta para a conta; falta insumo', 409)

    # ---- o que o usuario mandou, conferido contra o que a carta permite ----
    barras = {k: int(v) for k, v in (p.get('barras') or {}).items() if v}
    for b in barras:
        if b not in r.barra:
            return erro('barra desconhecida: %s' % b)
    if any(n < 0 or n > 25 for n in barras.values()):
        return erro('nivel de barra fora de 0 a 25')

    fixas = {int(x) for x in (c.get('habilidades_fixas') or [])}
    possivel = banco.pool_da_funcao(card_id, funcao_id)
    if possivel is None:
        return erro('pool canônico recusado para esta carta e função', 409)
    possivel = set(possivel)
    try:
        escolhidas = [int(x) for x in (p.get('skill_ids') or [])]
    except (TypeError, ValueError):
        return erro('skill_ids invalidos')
    fora = [h for h in escolhidas if h not in possivel]
    if fora:
        return erro('esta carta nao aceita skill_id: %s' % ', '.join(str(x) for x in fora[:3]))
    vagas_hab = 5 if possivel else 0
    if len(escolhidas) > vagas_hab:
        return erro('a carta tem %d vagas de habilidade' % vagas_hab)
    habs = sorted(fixas | set(escolhidas))

    try:
        impetos,impeto_condicional_codigo,impeto_condicional_nivel = _impetos_da_linha(c,p,r)
    except (TypeError,ValueError) as e:
        return erro(str(e),409)
    r_linha = _regua_da_linha(r,impeto_condicional_codigo,impeto_condicional_nivel)

    tid  = p.get('tecnico_id')
    prof = None
    if tid is not None:
        tid = int(tid)
        if tid not in r.tec:
            return erro('tecnico desconhecido')
        prof = r.tec[tid].get('proficiencia')
        if prof is None:
            return erro('falta a proficiencia do tecnico')

    estado = {'barras': barras, 'impetos': impetos,
              'impeto_condicional_codigo': impeto_condicional_codigo,
              'impeto_condicional_nivel': impeto_condicional_nivel,'habilidades': habs,
              'tecnico_id': tid, 'proficiencia': prof}
    carta = {'atributos': c.get('atributos'), 'orcamento': c.get('orcamento')}

    try:
        r2 = AV.avalia(estado, carta, funcao_id, r_linha)
    except (AV.InsumoFaltando, ReguaIncompleta) as e:
        return erro('nao da para calcular: %s' % e, 409)

    return jsonify({
        'ok': True,
        'nota': round(r2['b1'], CASAS),
        'valores': r2['valores'],
        'ganho_por_etapa': r2['ganho_por_etapa'],
        'versao_molde': r2['versao_molde'],
        'usou': {'skill_ids': habs, 'impeto_ids': impetos,
                 'impeto_condicional_codigo': impeto_condicional_codigo,
                 'impeto_condicional_nivel': impeto_condicional_nivel,
                 'barras_gastas': sum(r.custo[n] for n in barras.values() if n),
                 'orcamento': carta['orcamento']},
    })


@app.post('/otimizar')
def otimizar():
    """A melhor distribuicao de barras para o cenario que o usuario montou.

    O usuario escolhe impeto, tecnico e habilidades; ISSO FICA FIXO; e o servidor
    acha onde por cada ponto de barra. Mesma programacao dinamica do motor —
    provado: 8 de 8 builds com as barras identicas as que o motor escolheu.

    Devolve as barras e a nota. NUNCA o alvo, o peso ou o molde.
    """
    ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
    if not _passou_no_limite(ip):
        return erro('muitas contas em pouco tempo; espere um minuto', 429)

    p = request.get_json(silent=True) or {}
    card_id, funcao_id = p.get('card_id'), p.get('funcao_id')
    if not card_id or funcao_id is None:
        return erro('faltou card_id ou funcao_id')
    try:
        funcao_id = int(funcao_id)
    except (TypeError, ValueError):
        return erro('funcao_id invalido')

    try:
        r = regua()
    except Exception:
        return erro('nao sei agora: a regua nao esta carregada', 503)
    if funcao_id not in r.molde:
        return erro('funcao_id desconhecida')

    try:
        c = banco.carta_para_simular(card_id)
    except banco.BancoIndisponivel:
        return erro('nao sei agora: o banco nao respondeu', 503)
    if not c:
        return erro('carta nao encontrada', 404)
    if not c.get('pronto_motor_otimizacao'):
        return erro('esta carta ainda esta incompleta para a conta; falta insumo', 409)

    fixas = {int(x) for x in (c.get('habilidades_fixas') or [])}
    pool = banco.pool_da_funcao(card_id, funcao_id)
    if pool is None:
        return erro('pool canônico recusado para esta carta e função', 409)
    possivel = set(pool)
    try:
        escolhidas = [int(x) for x in (p.get('skill_ids') or [])]
    except (TypeError, ValueError):
        return erro('skill_ids invalidos')
    fora = [h for h in escolhidas if h not in possivel]
    if fora:
        return erro('esta carta nao aceita skill_id: %s' % ', '.join(str(x) for x in fora[:3]))
    if len(escolhidas) > (5 if possivel else 0):
        return erro('a carta tem %d vagas de habilidade' % (5 if possivel else 0))
    habs = sorted(fixas | set(escolhidas))

    try:
        impetos,impeto_condicional_codigo,impeto_condicional_nivel = _impetos_da_linha(c,p,r)
    except (TypeError,ValueError) as e:
        return erro(str(e),409)
    r_linha = _regua_da_linha(r,impeto_condicional_codigo,impeto_condicional_nivel)

    tid, prof = p.get('tecnico_id'), None
    m = 1.0
    boosts = []
    if tid is not None:
        tid = int(tid)
        t = r.tec.get(tid)
        if t is None:
            return erro('tecnico desconhecido')
        prof = t.get('proficiencia')
        if prof is None:
            return erro('falta a proficiencia do tecnico')
        mm = r.mult.get(int(round(float(prof))))
        if mm is None:
            return erro('proficiencia fora da tabela de multiplicador')
        m = float(mm)
        boosts = list(t.get('boosts') or [])

    base = c.get('atributos')
    if not base:
        return erro('a carta nao tem os 26 atributos', 409)

    impeto_add = [0] * len(base)
    for codigo in impetos:
        for k,d in (r_linha.imp.get(codigo) or {}).items():
            impeto_add[int(k)] += int(d)
    boost_add = [0] * len(base)
    for i in boosts:
        boost_add[int(i)] += 1

    try:
        buff = AV.buff_de(habs, r)
    except AV.InsumoFaltando as e:
        return erro('nao da para calcular: %s' % e, 409)

    mol = r.molde[funcao_id]
    arows = [(i, mol[i][0], mol[i][1]) for i in sorted(mol)]

    o = Otimizador(r_linha, base, c.get('orcamento'), arows,
                   impeto_add, boost_add, buff, m)
    lvl, _ = o.melhor()
    lvl = o.sobra_para_o_maior_peso(lvl)

    estado = {'barras': {k: v for k, v in lvl.items() if v}, 'impetos': impetos,
              'impeto_condicional_codigo': impeto_condicional_codigo,
              'impeto_condicional_nivel': impeto_condicional_nivel,
              'habilidades': habs, 'tecnico_id': tid, 'proficiencia': prof, 'buff': buff}
    carta = {'atributos': base, 'orcamento': c.get('orcamento')}
    try:
        r2 = AV.avalia(estado, carta, funcao_id, r_linha)
    except (AV.InsumoFaltando, ReguaIncompleta) as e:
        return erro('nao da para calcular: %s' % e, 409)

    return jsonify({
        'ok': True,
        'barras': {k: v for k, v in lvl.items() if v},
        'nota': round(r2['b1'], CASAS),
        'valores': r2['valores'],
        'gasto': o.gasto(lvl),
        'orcamento': c.get('orcamento'),
        'versao_molde': r2['versao_molde'],
        'usou': {'skill_ids': habs,'impeto_ids': impetos,
                 'impeto_condicional_codigo': impeto_condicional_codigo,
                 'impeto_condicional_nivel': impeto_condicional_nivel,
                 'tecnico_id': tid},
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT') or 8080))
