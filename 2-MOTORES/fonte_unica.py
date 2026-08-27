# -*- coding: utf-8 -*-
"""
FONTE ÚNICA — v2 (27/08/2026): agora é o BANCO, não o arquivo.

O QUE MUDOU
  Antes:  dados/base_unica.json  (um arquivo que alguém tinha que baixar)
  Agora:  o Supabase, por três portas:
            public.fila_do_motor()    quem rodar
            public.carta_do_motor(id) a carta
            public.regua_pacote()     molde, técnicos, habilidades, ímpetos
            public.regua_bonus()      bloqueios, corpo, os dois estilos

⛔ O MOTOR NÃO MUDA. Este módulo devolve exatamente o mesmo formato que o
   roda_lote_v6.py já esperava. Trocar o arquivo por este é a mudança inteira.

A CHAVE sai do config.txt na hora de rodar. Nunca é gravada nem impressa aqui.

CACHE: a carta é buscada uma vez e fica guardada em memória durante a rodada.
       O `carimbo()` devolve a hora da última extração, então o motor recarrega
       sozinho quando entra carga nova.
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
if _CASA and _os.path.abspath(_os.getcwd()) != _os.path.abspath(_CASA):
    _os.chdir(_CASA)

import json, time, urllib.request, urllib.error

# ------------------------------------------------------------------ ligacao
cfg = {}
if _os.path.exists('config.txt'):
    for linha in open('config.txt', encoding='utf-8'):
        linha = linha.strip()
        if linha and not linha.startswith('#') and '=' in linha:
            k, v = linha.split('=', 1)
            cfg[k.strip()] = v.strip()
URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')
CAB = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}


def _rpc(nome, corpo=None, timeout=180, tentativas=4):
    erro = None
    for t in range(tentativas):
        try:
            req = urllib.request.Request(
                '%s/rest/v1/rpc/%s' % (URL, nome),
                data=json.dumps(corpo or {}).encode('utf-8'),
                headers=CAB, method='POST')
            with urllib.request.urlopen(req, timeout=timeout) as r:
                t2 = r.read().decode('utf-8')
            return json.loads(t2) if t2.strip() else None
        except Exception as e:
            erro = e
            time.sleep(1.5 * (t + 1))
    raise SystemExit('\n  PARE. O banco nao respondeu em %s: %s\n' % (nome, erro))


def existe():
    """Ha fonte? Aqui: ha chave e o banco responde."""
    if not URL or not KEY or 'COLE_AQUI' in KEY:
        return False
    try:
        return bool(_rpc('estado_da_fila'))
    except SystemExit:
        return False


# ------------------------------------------------------------------ a carta
_CACHE = {}

def _traduz(j):
    """Do formato do banco para o formato que o motor ja espera."""
    if not j:
        return None
    cid = str(j.get('card_id'))
    imp = []
    for k in ('impeto_s1', 'impeto_s2_cond'):
        v = j.get(k)
        if v:
            imp.append(v)
    return {
        'id':      cid,
        'nome':    j.get('nome'),
        'nm':      j.get('nome'),
        'pos':     j.get('posicao'),
        'np':      j.get('posicao'),
        'orc':     j.get('orcamento') or 0,
        'base':    j.get('atributos'),
        'ovr':     j.get('overall'),
        'modelo':  j.get('slot1_nome'),
        'modelo2': j.get('slot2_nome'),          # <<< o segundo slot de 2027
        'corpo':   j.get('corpo'),
        'pe_ruim': [j.get('pe_ruim_uso'), j.get('pe_ruim_precisao')],
        'com':     j.get('estilos_ia') or [],
        'raras':   j.get('habilidades_fixas') or [],
        'falta':   j.get('habilidades_possiveis') or [],
        'pool_cheio': not (j.get('habilidades_possiveis')),
        'impeto_nomes': imp,
        'impeto_condicional': j.get('impeto_s2_cond'),
        'fab':     None,
        'sl':      (1 if j.get('vaga_s1') else 0) + (1 if j.get('vaga_s2') else 0),
        'visto_na_casca': True,
        'level_cap': j.get('level_cap'),
        'cap_estimado': j.get('cap_estimado'),
    }


def carta(card_id):
    """Uma carta, do banco. Guarda em memoria."""
    cid = str(card_id).split('@')[0]
    if cid not in _CACHE:
        _CACHE[cid] = _traduz(_rpc('carta_do_motor', {'p_card_id': cid}))
    return _CACHE[cid]


def carrega_base(ids=None):
    """{id_base: card} — o mesmo formato de antes.

    Sem `ids`, traz a fila inteira. Com `ids`, so essas (bem mais rapido).
    """
    if ids is None:
        fila = _rpc('proxima_da_fila', {'p_limite': 1000000}) or []
        ids = sorted({str(x.get('card_id')) for x in fila})

    # 27/08 — EM LOTE. Antes era uma chamada HTTP por carta: 20.845 idas ao
    # banco, e isso DUAS vezes (um carregamento por processo). Levava horas so
    # para comecar. Agora vai de 500 em 500 pelo cartas_do_motor.
    base = {}
    ids = [str(c) for c in ids]
    LOTE = 500
    for i in range(0, len(ids), LOTE):
        pedaco = ids[i:i + LOTE]
        linhas = _rpc('cartas_do_motor', {'p_ids': pedaco})
        if linhas is None:
            for cid in pedaco:                    # o banco recusou o lote: uma a uma
                c = carta(cid)
                if c:
                    base[str(cid).split('@')[0]] = c
        else:
            for j in linhas:
                c = _traduz(j)
                if c:
                    base[str(c['id']).split('@')[0]] = c
                    _CACHE[str(c['id'])] = c
        print('   base: %d/%d cartas' % (min(i + LOTE, len(ids)), len(ids)), flush=True)
    return base


# ------------------------------------------------------------------ insumos
_INSUMOS = None

def carrega_tudo():
    """Todos os insumos, do banco, no formato que o motor espera."""
    global _INSUMOS
    if _INSUMOS is not None:
        return _INSUMOS
    rp = _rpc('regua_pacote') or {}
    rb = _rpc('regua_bonus') or {}

    molde = []
    for funcao, m in (rp.get('molde') or {}).items():
        for attr_idx, par in m.items():
            molde.append({'funcao': funcao, 'attr': int(attr_idx),
                          'alvo': par[0], 'peso': par[1]})

    tecnicos = {}
    for tid, t in (rp.get('tecnico') or {}).items():
        tecnicos[str(tid)] = {'nome': t.get('nome'),
                              'boosts': t.get('boosts') or [],
                              'proficiencias': t.get('proficiencias') or {}}

    _INSUMOS = {
        'molde': molde,
        'tecnicos_catalogo': tecnicos,
        'habilidades': rp.get('habilidade') or {},
        'bloqueio': rb.get('bloqueio') or {},
        'parametro': rp.get('parametro') or {},
        'atributo': rp.get('atributo') or {},
        'barra': rp.get('barra') or {},
        'custo_nivel': rp.get('custo_nivel') or {},
        'multiplicador': rp.get('multiplicador') or {},
        'fabricavel': rp.get('fabricavel') or [],
        'ordem_boost': rp.get('ordem_boost') or {},
        'impeto': rp.get('impeto') or {},
        'impeto_nome': rp.get('impeto_nome') or {},
        'versao_molde': rp.get('versao_molde'),
        # a regra dos dois estilos, aprovada em 26/08
        'estilo_casa': rb.get('casa') or {},
        'estilo_liga': rb.get('liga') or {},
        'posicao_slot': rb.get('posicao_slot') or {},
        'bonus_parametro': rb.get('parametro') or {},
        'molde_corpo': rb.get('molde_corpo') or {},
        'corpo_ordem': rb.get('corpo_ordem') or {},
        'sa_familia': rb.get('sa_familia') or {},
        'regra_funcao': rb.get('regra_funcao') or {},
        'posicao_sigla': rb.get('posicao_sigla') or {},
    }
    return _INSUMOS


def carimbo():
    """Muda quando entra carga nova — o motor recarrega sozinho."""
    try:
        e = _rpc('estado_da_fila') or {}
        return int(e.get('na_fila', 0)) * 1000 + int(e.get('ja_rodadas', 0))
    except Exception:
        return None


# ------------------------------------------------------------------ a fila
def proxima_fila(limite=200):
    """O proximo lote: [{card_id, funcao_codigo, overall, posicao}]"""
    return _rpc('proxima_da_fila', {'p_limite': limite}) or []


def gravar(linhas):
    """A volta. Grava na clube.build E TIRA a linha da fila, no mesmo comando."""
    if not linhas:
        return 0
    total = 0
    for i in range(0, len(linhas), 200):
        total += int(_rpc('gravar_build', {'p_linhas': linhas[i:i+200]}) or 0)
    return total


def estado():
    return _rpc('estado_da_fila') or {}


# ------------------------------------------------------- insumos que eram arquivo
# Ate 27/08 o equacao.py abria tabm_medido.json e HAB_EFEITOS_FINAL.json, e o
# motor.py abria CAT_dom.json. Esses tres arquivos nao existem mais: o dado mora
# no banco (clube.multiplicador, clube.habilidade, clube.impeto_fabricavel) e
# desce pelo mesmo regua_pacote() de sempre. A conta nao mudou - so a porta.

def tabela_multiplicador():
    """{ponto: multiplicador} - o que era tabm_medido.json."""
    t = carrega_tudo().get('multiplicador') or {}
    if not t:
        raise SystemExit('PAROU: clube.multiplicador veio vazio do banco.')
    return t


def catalogo_habilidades():
    """{nome: {arquivo, tipo, efeito}} - o que era HAB_EFEITOS_FINAL.json.

    No banco a chave JA E o nome exibido, entao 'arquivo' e a propria chave.
    """
    h = carrega_tudo().get('habilidades') or {}
    if not h:
        raise SystemExit('PAROU: clube.habilidade veio vazia do banco.')
    return {k: {'arquivo': k, 'codigo': v.get('codigo'), 'tipo': v.get('tipo'),
                'efeito': v.get('efeito') or {}}
            for k, v in h.items()}


def habilidades_de_goleiro():
    """As 6 habilidades que so entram em funcao de GOLEIRO.

    Ordem do Luis, 08/08, vendo o Sneijder MC armador com 'Repos. baixa do GO'.
    Antes vinha de k.lower().startswith('gk') na chave do JSON. Agora vem do
    campo codigo de clube.habilidade, que e a mesma chave canonica.
    """
    return {k for k, v in catalogo_habilidades().items()
            if str(v.get('codigo') or '').lower().startswith('gk')}


def catalogo_fabricaveis():
    """[[nome, 0|1, [[attr_idx, valor], ...]], ...] - o que era CAT_dom.json.

    O 2o campo e o slot: 0 = livre, 1 = condicional (clube.impeto_fabricavel.condicional).
    """
    c = carrega_tudo().get('fabricavel') or []
    if not c:
        raise SystemExit('PAROU: clube.impeto_fabricavel veio vazio do banco.')
    return [[x[0], int(x[1]), [[int(a), b] for a, b in (x[2] or [])]] for x in c]


def carrega_tecnicos_do_banco(tatica=None):
    """A lista de tecnicos no formato que o motor espera - o que era tecnicos.json.

    Vem de clube.tecnico (id, nome, boosts, extras.proficiencias). O 'hasBoost'
    do arquivo virou o teste que ja existia: so entra quem tem pelo menos um
    boost valido (indice de atributo entre 0 e 25). Boost [-1,-1] = sem boost.

    A conta e a mesma de equacao.carrega_tecnicos: se a tatica nao for dita,
    usa o MAIOR das proficiencias - de proposito, porque o Luis ainda nao cravou
    a tatica.
    """
    import equacao as _EQ
    cat = carrega_tudo().get('tecnicos_catalogo') or {}
    if not cat:
        raise SystemExit('PAROU: clube.tecnico veio vazia do banco.')
    out = []
    for tid, c in cat.items():
        boosts = [int(x) for x in (c.get('boosts') or [])]
        b = [_EQ.POS[_EQ.AM[x]] for x in boosts if 0 <= x < 26]
        if not b:
            continue                      # era o hasBoost do arquivo
        sk = {k: float(v) for k, v in (c.get('proficiencias') or {}).items()}
        if not sk:
            continue
        v = sk.get(tatica) if (tatica and tatica in sk) else max(sk.values())
        out.append({'nome': c.get('nome'), 'id': int(tid), 'tat': v,
                    'm': _EQ.mult_de(v), 'boost': b})
    return out


def peso_da_ordem():
    """{card_id: [vagas_de_impeto, orcamento]} das cartas que estao na fila.

    So serve para a ORDEM: carta com vaga de impeto livre + pool de habilidade
    roda um DP inteiro por candidato e chega a levar 4.953 s. Essas vao para o
    fim. Nao muda resultado nenhum.
    """
    return _rpc('peso_da_ordem') or {}
