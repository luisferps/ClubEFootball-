# -*- coding: utf-8 -*-
"""
SERVIDOR — o app do AVALIAR mais as rotas que a TELA usa.

Importa o app ja provado e soma rotas por cima. E este que o Start Command sobe.

POR QUE ESTAS ROTAS FALAM DIFERENTE DO /avaliar:
a tela NAO guarda o tecnico_id nem o id do impeto — ela guarda os BOOSTS (os 2
atributos do +1), o nome do tecnico (de onde tira o multiplicador) e o NOME do
impeto ("Forca +1"). Medido no motor-e-ficha-base.js. Entao estas rotas aceitam o
estado do jeito que a tela tem, sem obrigar a tela a saber de id nenhum.

Provado em 25/08: 8 de 8 builds do motor reproduzidas por este caminho.

O QUE SAI: nota · os 26 valores · as barras.
O QUE NUNCA SAI: alvo · peso · degraus · punicao · molde · pool.
"""

import math
from flask import request, jsonify

from app import (app, regua, banco, erro, _passou_no_limite, CASAS,
                 AV, ReguaIncompleta)
from otimizador import Otimizador


def _abre(p):
    """As conferencias que toda rota faz. Devolve (erro, regua, carta)."""
    card_id, funcao_id = p.get('card_id'), p.get('funcao_id')
    if not card_id or funcao_id is None:
        return erro('faltou card_id ou funcao_id'), None, None
    try:
        funcao_id = int(funcao_id)
    except (TypeError, ValueError):
        return erro('funcao_id invalido'), None, None
    p['funcao_id'] = funcao_id
    try:
        r = regua()
    except Exception:
        return erro('nao sei agora: a regua nao esta carregada', 503), None, None
    if funcao_id not in r.molde:
        return erro('funcao_id desconhecida'), None, None
    try:
        c = banco.carta_para_simular(card_id)
    except banco.BancoIndisponivel:
        return erro('nao sei agora: o banco nao respondeu', 503), None, None
    if not c:
        return erro('carta nao encontrada', 404), None, None
    if not c.get('pronto_motor_otimizacao'):
        return erro('esta carta ainda esta incompleta para a conta; falta insumo', 409), None, None
    return None, r, c


def _le_estado(p, c, r):
    """Traduz o que a tela mandou para o que a conta precisa."""
    fixas = {int(x) for x in (c.get('habilidades_fixas') or [])}

    # ⛔ 25/08 — O POOL E POR FUNCAO, NAO POR CARTA.
    #    Esta linha recusava as builds que o proprio motor fez. Medido: das 4
    #    builds gravadas que tentei reproduzir, as 4 voltaram HTTP 400 "esta
    #    carta nao aceita", citando habilidades que o motor tinha posto.
    #    A causa: `habilidades_possiveis` vinha de clube.carta_habilidade
    #    (relacao='espaco'), que e uma lista POR CARTA. Mas o pool que o motor
    #    usa e POR FUNCAO — prova: numa carta so ele varia de 22 a 30 conforme
    #    a funcao (card 89130772077328, 8 tamanhos distintos em 10 funcoes).
    #    Sao coisas diferentes, e comparar as duas nao provava nada.
    #    A medida que vale: das 6.000 habilidades usadas em builds nao marcadas,
    #    6.000 de 6.000 estao no pool da funcao. ZERO fora. O motor esta certo.
    #    Por isso o pool vem agora por (card_id, funcao), com o pool da carta
    #    como rede de seguranca se o banco ainda nao tiver a linha da funcao.
    #    E isto esclarece a outra ponta: `habilidades_possiveis` (relacao
    #    'espaco') nao e a lista de candidatas — sao as VAGAS que a carta tem.
    #    Sao os dois numeros de que a conta precisa, e eram um so.
    vagas = 5
    pool_funcao = banco.pool_da_funcao(p.get('card_id'), p.get('funcao_id'))
    if pool_funcao is None:
        return erro('pool canônico recusado para esta carta e função', 409), None
    possivel = set(pool_funcao)

    try:
        escolhidas = [int(x) for x in (p.get('skill_ids') or [])]
    except (TypeError, ValueError):
        return erro('skill_ids invalidos'), None
    fora = [h for h in escolhidas if h not in possivel]
    if fora:
        return erro('esta carta nao aceita skill_id: %s' % ', '.join(str(x) for x in fora[:3])), None

    # ⛔ 25/08 — AS VAGAS SAO DA CARTA, NAO SAO 5 SEMPRE.
    #    Estava escrito `5 if possivel else 0`. O numero 5 cravado e o achado
    #    critico n.1 da auditoria dos motores: "o motor sempre monta 5
    #    habilidades, mas a regra do sistema e de 0 a 5 por carta", e toda carta
    #    com menos de 5 vagas recebia build com 5 e NOTA INFLADA, sem erro e sem
    #    aviso. Agora a conta usa as vagas que a carta realmente tem.
    if len(escolhidas) > vagas:
        return erro('a carta tem %d vaga(s) de habilidade' % vagas), None
    habs = sorted(fixas | set(escolhidas))

    if p.get('impeto_escolhido') is not None or p.get('impeto_nome') is not None:
        return erro('consumidor de ímpetos continua desligado', 409), None
    impetos = []

    boosts, m, prof = [], 1.0, None
    tid = p.get('tecnico_id')
    if tid is not None:
        t = r.tec.get(int(tid))
        if t is None:
            return erro('tecnico desconhecido'), None
        boosts = list(t.get('boosts') or [])
        prof = t.get('proficiencia')

    if prof is not None:
        mm = r.mult.get(int(round(float(prof))))
        if mm is None:
            return erro('proficiencia fora da tabela de multiplicador'), None
        m = float(mm)
    elif boosts:
        return erro('o tecnico foi escolhido mas nao veio proficiencia nem multiplicador'), None

    base = c.get('atributos')
    if not base:
        return erro('a carta nao tem os 26 atributos', 409), None
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
        return erro('nao da para calcular: %s' % e, 409), None

    return None, {'habs': habs, 'impetos': impetos, 'boosts': boosts, 'm': m,
                  'prof': prof, 'base': base, 'impeto_add': impeto_add,
                  'boost_add': boost_add, 'buff': buff}


def _avalia_com_m(estado, carta, funcao, r, d):
    """A cadeia do avaliador com o multiplicador ja resolvido:
    base+barras -> proficiencia -> boosts -> impetos -> habilidade."""
    base = carta['atributos']
    ref = AV.base_barras(base, estado.get('barras') or {}, r)
    v = [AV._mult(ref[i], d['m']) for i in range(len(ref))]
    v = [v[i] + d['boost_add'][i] for i in range(len(v))]
    v = [v[i] + d['impeto_add'][i] for i in range(len(v))]
    for i, (pct, flat) in d['buff'].items():
        i = int(i)
        v[i] = v[i] + math.ceil(ref[i] * pct / 100.0 + flat)
    r.molde_completo(funcao)
    mol = r.molde[funcao]
    arows = [(i, mol[i][0], mol[i][1]) for i in sorted(mol)]
    return {'b1': AV.nota_de(v, arows, r), 'valores': v, 'versao_molde': r.versao_molde}


@app.post('/nota')
def nota_da_tela():
    """A nota do estado que a tela montou — com as barras que o usuario pos."""
    ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
    if not _passou_no_limite(ip):
        return erro('muitas contas em pouco tempo; espere um minuto', 429)
    p = request.get_json(silent=True) or {}
    e, r, c = _abre(p)
    if e: return e
    e, d = _le_estado(p, c, r)
    if e: return e
    barras = {k: int(v) for k, v in (p.get('barras') or {}).items() if v}
    for b in barras:
        if b not in r.barra:
            return erro('barra desconhecida: %s' % b)
    if any(n < 0 or n > 25 for n in barras.values()):
        return erro('nivel de barra fora de 0 a 25')
    try:
        r2 = _avalia_com_m({'barras': barras},
                           {'atributos': d['base'], 'orcamento': c.get('orcamento')},
                           p['funcao_id'], r, d)
    except (AV.InsumoFaltando, ReguaIncompleta) as ex:
        return erro('nao da para calcular: %s' % ex, 409)
    return jsonify({'ok': True, 'nota': round(r2['b1'], CASAS),
                    'valores': r2['valores'], 'versao_molde': r2['versao_molde']})


@app.post('/otimizar')
def otimizar():
    """A melhor distribuicao de barras para o cenario que o usuario montou.

    O usuario escolhe impeto, tecnico e habilidades; ISSO FICA FIXO; e o servidor
    acha onde por cada ponto de barra. Mesma programacao dinamica do motor —
    provado: 8 de 8 builds com as barras identicas as que o motor escolheu.
    """
    ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '?').split(',')[0].strip()
    if not _passou_no_limite(ip):
        return erro('muitas contas em pouco tempo; espere um minuto', 429)
    p = request.get_json(silent=True) or {}
    e, r, c = _abre(p)
    if e: return e
    e, d = _le_estado(p, c, r)
    if e: return e
    mol = r.molde[p['funcao_id']]
    arows = [(i, mol[i][0], mol[i][1]) for i in sorted(mol)]
    o = Otimizador(r, d['base'], c.get('orcamento'), arows,
                   d['impeto_add'], d['boost_add'], d['buff'], d['m'])
    lvl, _ = o.melhor()
    lvl = o.sobra_para_o_maior_peso(lvl)
    barras = {k: v for k, v in lvl.items() if v}
    try:
        r2 = _avalia_com_m({'barras': barras},
                           {'atributos': d['base'], 'orcamento': c.get('orcamento')},
                           p['funcao_id'], r, d)
    except (AV.InsumoFaltando, ReguaIncompleta) as ex:
        return erro('nao da para calcular: %s' % ex, 409)
    return jsonify({'ok': True, 'barras': barras, 'nota': round(r2['b1'], CASAS),
                    'valores': r2['valores'], 'gasto': o.gasto(lvl),
                    'orcamento': c.get('orcamento'), 'versao_molde': r2['versao_molde']})


# ------------------------------------------------------------------- CORS
# A tela roda em outro endereco (Netlify, ou o arquivo local) e o navegador so
# deixa ela falar com este servico se ele autorizar. ORIGENS_LIBERADAS e uma
# lista separada por virgula nas variaveis do Railway; vazio = qualquer origem
# (util enquanto o Luis testa com o arquivo local, onde a origem e "null").
import os as _os
_ORIGENS = [o.strip() for o in (_os.environ.get('ORIGENS_LIBERADAS') or '').split(',') if o.strip()]


@app.after_request
def _libera_origem(resp):
    origem = request.headers.get('Origin')
    if origem and (not _ORIGENS or origem in _ORIGENS):
        resp.headers['Access-Control-Allow-Origin'] = origem
        resp.headers['Vary'] = 'Origin'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Chave-Admin'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Max-Age'] = '86400'
    return resp


@app.route('/<path:qualquer>', methods=['OPTIONS'])
def _preflight(qualquer):
    return ('', 204)
