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
    card_id, funcao = p.get('card_id'), p.get('funcao')
    if not card_id or not funcao:
        return erro('faltou card_id ou funcao'), None, None
    try:
        r = regua()
    except Exception:
        return erro('nao sei agora: a regua nao esta carregada', 503), None, None
    if funcao not in r.molde:
        return erro('funcao desconhecida'), None, None
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
    fixas      = set(c.get('habilidades_fixas') or [])

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
    vagas    = len(c.get('habilidades_possiveis') or [])
    possivel = set(c.get('habilidades_possiveis') or [])
    try:
        pool_funcao = banco.pool_da_funcao(p.get('card_id'), p.get('funcao'))
    except Exception:
        pool_funcao = None
    if pool_funcao:
        possivel = set(pool_funcao)

    escolhidas = list(p.get('habilidades_escolhidas') or [])
    fora = [h for h in escolhidas if h not in possivel]
    if fora:
        return erro('esta carta nao aceita: %s' % ', '.join(fora[:3])), None

    # ⛔ 25/08 — AS VAGAS SAO DA CARTA, NAO SAO 5 SEMPRE.
    #    Estava escrito `5 if possivel else 0`. O numero 5 cravado e o achado
    #    critico n.1 da auditoria dos motores: "o motor sempre monta 5
    #    habilidades, mas a regra do sistema e de 0 a 5 por carta", e toda carta
    #    com menos de 5 vagas recebia build com 5 e NOTA INFLADA, sem erro e sem
    #    aviso. Agora a conta usa as vagas que a carta realmente tem.
    if len(escolhidas) > vagas:
        return erro('a carta tem %d vaga(s) de habilidade' % vagas), None
    habs = sorted(fixas | set(escolhidas))

    impetos = [int(i['impeto_id']) for i in (c.get('impetos_nativos') or [])
               if i.get('impeto_id') is not None]
    extra = p.get('impeto_escolhido')
    if extra is None and p.get('impeto_nome'):
        # a tela guarda o impeto por NOME ("Forca +1"), nunca por id
        extra = (getattr(r, 'imp_nome', None) or {}).get(str(p['impeto_nome']).strip())
        if extra is None:
            return erro('impeto desconhecido: %s' % p['impeto_nome']), None
    if extra is not None:
        if int(c.get('vagas_livres') or 0) < 1:
            return erro('esta carta nao tem vaga de impeto livre'), None
        if int(extra) not in r.imp:
            return erro('impeto desconhecido'), None
        impetos.append(int(extra))

    boosts, m, prof = [], 1.0, p.get('proficiencia')
    tid = p.get('tecnico_id')
    if tid is not None:
        t = r.tec.get(int(tid))
        if t is None:
            return erro('tecnico desconhecido'), None
        boosts = list(t.get('boosts') or [])
        if prof is None:
            prof = t.get('proficiencia')
    else:
        for b in (p.get('boosts_attr') or []):
            b = int(b)
            if not (0 <= b < len(c.get('atributos') or [])):
                return erro('boost fora dos 26 atributos'), None
            boosts.append(b)

    if p.get('multiplicador') is not None:
        try:
            m = float(p['multiplicador'])
        except (TypeError, ValueError):
            return erro('multiplicador invalido'), None
        if not (0.5 <= m <= 1.5):
            return erro('multiplicador fora da faixa'), None
    elif prof is not None:
        mm = r.mult.get(int(round(float(prof))))
        if mm is None:
            return erro('proficiencia fora da tabela de multiplicador'), None
        m = float(mm)
    elif boosts:
        return erro('o tecnico foi escolhido mas nao veio proficiencia nem multiplicador'), None

    base = c.get('atributos')
    if not base:
        return erro('a carta nao tem os 26 atributos', 409), None
    add = [0] * len(base)
    for i in impetos:
        for k, d in (r.imp.get(i) or {}).items():
            add[int(k)] += int(d)
    for i in boosts:
        add[int(i)] += 1

    try:
        buff = AV.buff_de(habs, r)
    except AV.InsumoFaltando as e:
        return erro('nao da para calcular: %s' % e, 409), None

    return None, {'habs': habs, 'impetos': impetos, 'boosts': boosts, 'm': m,
                  'prof': prof, 'base': base, 'add': add, 'buff': buff}


def _avalia_com_m(estado, carta, funcao, r, d):
    """A cadeia do avaliador com o multiplicador ja resolvido:
    base+barras -> multiplicador -> +1 do tecnico -> impetos -> habilidade."""
    base = carta['atributos']
    ref = AV.base_barras(base, estado.get('barras') or {}, r)
    v = [AV._mult(x, d['m']) for x in ref]
    for i in d['boosts']:
        v[int(i)] = v[int(i)] + 1
    for i in d['impetos']:
        for k, dd in (r.imp.get(i) or {}).items():
            v[int(k)] = v[int(k)] + int(dd)
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
                           p['funcao'], r, d)
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
    mol = r.molde[p['funcao']]
    arows = [(i, mol[i][0], mol[i][1]) for i in sorted(mol)]
    o = Otimizador(r, d['base'], c.get('orcamento'), arows, d['add'], d['buff'], d['m'])
    lvl, _ = o.melhor()
    lvl = o.sobra_para_o_maior_peso(lvl)
    barras = {k: v for k, v in lvl.items() if v}
    try:
        r2 = _avalia_com_m({'barras': barras},
                           {'atributos': d['base'], 'orcamento': c.get('orcamento')},
                           p['funcao'], r, d)
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
