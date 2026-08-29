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
import os, time, threading, json
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
    funcao  = p.get('funcao')
    if not card_id or not funcao:
        return erro('faltou card_id ou funcao')

    try:
        r = regua()
    except Exception:
        return erro('nao sei agora: a regua nao esta carregada', 503)

    if funcao not in r.molde:
        return erro('funcao desconhecida')

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

    fixas    = set(c.get('habilidades_fixas') or [])
    possivel = set(c.get('habilidades_possiveis') or [])
    escolhidas = list(p.get('habilidades_escolhidas') or [])
    fora = [h for h in escolhidas if h not in possivel]
    if fora:
        return erro('esta carta nao aceita: %s' % ', '.join(fora[:3]))
    vagas_hab = 5 if possivel else 0
    if len(escolhidas) > vagas_hab:
        return erro('a carta tem %d vagas de habilidade' % vagas_hab)
    habs = sorted(fixas | set(escolhidas))

    impetos = [int(i['impeto_id']) for i in (c.get('impetos_nativos') or [])
               if i.get('impeto_id') is not None]
    extra = p.get('impeto_escolhido')
    if extra is not None:
        if int(c.get('vagas_livres') or 0) < 1:
            return erro('esta carta nao tem vaga de impeto livre')
        if int(extra) not in r.imp:
            return erro('impeto desconhecido')
        impetos.append(int(extra))

    tid  = p.get('tecnico_id')
    prof = p.get('proficiencia')
    if tid is not None:
        tid = int(tid)
        if tid not in r.tec:
            return erro('tecnico desconhecido')
        if prof is None:
            prof = r.tec[tid].get('proficiencia')
        if prof is None:
            return erro('falta a proficiencia do tecnico')

    estado = {'barras': barras, 'impetos': impetos, 'habilidades': habs,
              'tecnico_id': tid, 'proficiencia': prof}
    carta = {'atributos': c.get('atributos'), 'orcamento': c.get('orcamento')}

    try:
        r2 = AV.avalia(estado, carta, funcao, r)
    except (AV.InsumoFaltando, ReguaIncompleta) as e:
        return erro('nao da para calcular: %s' % e, 409)

    return jsonify({
        'ok': True,
        'nota': round(r2['b1'], CASAS),
        'valores': r2['valores'],
        'ganho_por_etapa': r2['ganho_por_etapa'],
        'versao_molde': r2['versao_molde'],
        'usou': {'habilidades': habs, 'impetos': len(impetos),
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
    card_id, funcao = p.get('card_id'), p.get('funcao')
    if not card_id or not funcao:
        return erro('faltou card_id ou funcao')

    try:
        r = regua()
    except Exception:
        return erro('nao sei agora: a regua nao esta carregada', 503)
    if funcao not in r.molde:
        return erro('funcao desconhecida')

    try:
        c = banco.carta_para_simular(card_id)
    except banco.BancoIndisponivel:
        return erro('nao sei agora: o banco nao respondeu', 503)
    if not c:
        return erro('carta nao encontrada', 404)
    if not c.get('pronto_motor_otimizacao'):
        return erro('esta carta ainda esta incompleta para a conta; falta insumo', 409)

    fixas      = set(c.get('habilidades_fixas') or [])
    possivel   = set(c.get('habilidades_possiveis') or [])
    escolhidas = list(p.get('habilidades_escolhidas') or [])
    fora = [h for h in escolhidas if h not in possivel]
    if fora:
        return erro('esta carta nao aceita: %s' % ', '.join(fora[:3]))
    if len(escolhidas) > (5 if possivel else 0):
        return erro('a carta tem %d vagas de habilidade' % (5 if possivel else 0))
    habs = sorted(fixas | set(escolhidas))

    impetos = [int(i['impeto_id']) for i in (c.get('impetos_nativos') or [])
               if i.get('impeto_id') is not None]
    extra = p.get('impeto_escolhido')
    if extra is not None:
        if int(c.get('vagas_livres') or 0) < 1:
            return erro('esta carta nao tem vaga de impeto livre')
        if int(extra) not in r.imp:
            return erro('impeto desconhecido')
        impetos.append(int(extra))

    tid, prof = p.get('tecnico_id'), p.get('proficiencia')
    m = 1.0
    boosts = []
    if tid is not None:
        tid = int(tid)
        t = r.tec.get(tid)
        if t is None:
            return erro('tecnico desconhecido')
        if prof is None:
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
    for i in impetos:
        for k, d in (r.imp.get(i) or {}).items():
            impeto_add[int(k)] += int(d)
    boost_add = [0] * len(base)
    for i in boosts:
        boost_add[int(i)] += 1

    try:
        buff = AV.buff_de(habs, r)
    except AV.InsumoFaltando as e:
        return erro('nao da para calcular: %s' % e, 409)

    mol = r.molde[funcao]
    arows = [(i, mol[i][0], mol[i][1]) for i in sorted(mol)]

    o = Otimizador(r, base, c.get('orcamento'), arows,
                   impeto_add, boost_add, buff, m)
    lvl, _ = o.melhor()
    lvl = o.sobra_para_o_maior_peso(lvl)

    estado = {'barras': {k: v for k, v in lvl.items() if v}, 'impetos': impetos,
              'habilidades': habs, 'tecnico_id': tid, 'proficiencia': prof, 'buff': buff}
    carta = {'atributos': base, 'orcamento': c.get('orcamento')}
    try:
        r2 = AV.avalia(estado, carta, funcao, r)
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
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT') or 8080))
