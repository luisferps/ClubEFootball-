# -*- coding: utf-8 -*-
"""
FONTE ÚNICA — contrato versionado do Otimizador.

O QUE MUDOU
  Antes:  dados/base_unica.json  (um arquivo que alguém tinha que baixar)
  Agora:  o Supabase, somente pelas portas ``public.otimizador_*_v1``.

⛔ A FÓRMULA NÃO MUDA. Este módulo troca somente endereços e identidades de
   entrada. Cálculo, pesos e ordem continuam fora daqui.

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

import hashlib, json, time, urllib.request, urllib.error

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
        pacote = _rpc('otimizador_regua_v1') or {}
        return pacote.get('contrato') == 'otimizador_regua_v1'
    except SystemExit:
        return False


# ------------------------------------------------------------------ a carta
_CACHE = {}

def _traduz(j):
    """Contrato v1 -> estrutura interna, sempre por IDs/códigos físicos."""
    if not j:
        return None
    cid = str(j.get('card_id'))
    ap = j.get('apresentacao') or {}
    esc = j.get('escalares') or {}
    gate = j.get('gate') or {}
    atributos = sorted(j.get('atributos') or [], key=lambda x: int(x['indice_otimizador']))
    corpo = sorted(j.get('corpo') or [], key=lambda x: int(x['pos']))
    habilidades = j.get('habilidades') or []
    impetos = sorted(j.get('impetos') or [], key=lambda x: int(x['slot']))
    pes = {x.get('campo'): x for x in (j.get('pes') or [])}
    playstyles = sorted(j.get('playstyles') or [], key=lambda x: int(x['slot_fisico']))

    nativas = [int(x['skill_id']) for x in habilidades if bool(x.get('fabricavel'))]
    raras = [int(x['skill_id']) for x in habilidades if not bool(x.get('fabricavel'))]
    vagas = {int(x['slot']): bool(x.get('vaga')) for x in impetos}

    return {
        'id':      cid,
        'nome':    ap.get('nome'),                 # somente apresentação
        'nm':      [],                             # consumidor de Ímpetos desligado
        'posicao_id': j.get('posicao_principal_id'),
        'pos':     j.get('posicao_principal_id'),
        'np':      j.get('posicao_principal_id'),
        'posicao_nome': ap.get('posicao'),         # somente apresentação
        'orc':     esc.get('orcamento') or 0,
        'base':    [x.get('valor') for x in atributos],
        'ovr':     esc.get('overall'),
        'modelo':  playstyles[0].get('playstyle_id') if len(playstyles) > 0 else None,
        'modelo2': playstyles[1].get('playstyle_id') if len(playstyles) > 1 else None,
        'corpo':   [x.get('valor') for x in corpo],
        'pe_ruim': [(pes.get('pe_ruim_uso') or {}).get('valor'),
                    (pes.get('pe_ruim_precisao') or {}).get('valor')],
        'com':     [int(x['bit_estilo_ia']) for x in (j.get('estilos_ia') or [])],
        'fab':     nativas,
        'raras':   raras,
        'falta':   [],
        'pool_cheio': False,
        'impetos': impetos,
        'impeto_furado': [],
        'sl':      [1 if vagas.get(1) else 0, 1 if vagas.get(2) else 0],
        'gate':    gate,
        'dimensoes_ids': j.get('dimensoes') or {},
        'cardinalidades': j.get('cardinalidades') or {},
        'visto_na_casca': True,
        'level_cap': esc.get('level_cap'),
        'cap_estimado': esc.get('cap_estimado'),
    }

def carta(card_id):
    """Uma carta, do banco. Guarda em memoria."""
    cid = str(card_id).split('@')[0]
    if cid not in _CACHE:
        _CACHE[cid] = _traduz(_rpc('otimizador_carta_v1', {'p_card_id': cid}))
    return _CACHE[cid]


def carrega_base(ids=None):
    """{id_base: card} — o mesmo formato de antes.

    Sem `ids`, traz a fila inteira. Com `ids`, so essas (bem mais rapido).
    """
    if ids is None:
        fila = _rpc('otimizador_proxima_fila_v1', {'p_limite': 1000000}) or []
        ids = sorted({str(x.get('card_id')) for x in fila})

    # 27/08 — EM LOTE. Antes era uma chamada HTTP por carta: 20.845 idas ao
    # banco, e isso DUAS vezes (um carregamento por processo). Levava horas so
    # para comecar. Agora vai de 500 em 500 pelo cartas_do_motor.
    base = {}
    ids = [str(c) for c in ids]
    LOTE = 500
    for i in range(0, len(ids), LOTE):
        pedaco = ids[i:i + LOTE]
        linhas = _rpc('otimizador_cartas_v1', {'p_ids': pedaco})
        if linhas is None:
            raise SystemExit('PAROU: otimizador_cartas_v1 nao devolveu o lote; sem fallback.')
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
    rp = _rpc('otimizador_regua_v1') or {}
    gate = rp.get('gate') or {}
    if not gate.get('pode_rodar'):
        raise SystemExit('PAROU: gate de otimizador_regua_v1 recusou a regua; sem fallback.')

    molde = []
    for r in (rp.get('molde') or []):
        molde.append({'funcao_id': int(r['funcao_id']),
                      'attr': int(r['indice_otimizador']),
                      'alvo': r['alvo'], 'peso': r['peso']})

    funcoes = {int(x['funcao_id']): {
        'codigo_compatibilidade': x.get('codigo_compatibilidade'),
        'rotulo_apresentacao': x.get('rotulo_apresentacao'), 'ordem': x.get('ordem')}
        for x in (rp.get('funcoes') or [])}

    habilidades = {}
    for h in (rp.get('habilidades') or []):
        efeitos = {}
        for e in (h.get('efeitos') or []):
            d = {}
            if e.get('pct'): d['pct'] = float(e['pct'])
            if e.get('flat'): d['flat'] = float(e['flat'])
            if d: efeitos[int(e['indice_otimizador'])] = d
        habilidades[int(h['skill_id'])] = {
            'skill_id': int(h['skill_id']), 'bit_na_carta': int(h['bit_na_carta']),
            'fabricavel': bool(h.get('fabricavel')), 'vetada': bool(h.get('vetada')),
            'efeito': efeitos, 'nome_apresentacao': h.get('nome_apresentacao')}

    bloqueio = {}
    for b in (rp.get('bloqueios') or []):
        bloqueio.setdefault(int(b['funcao_id']), set()).add(int(b['skill_id']))
    bloqueio = {k: sorted(v) for k, v in bloqueio.items()}

    incidencia = {}
    for x in (rp.get('incidencias') or []):
        incidencia.setdefault(int(x['funcao_id']), {})[int(x['skill_id'])] = float(x['incidencia_pct'])

    tecnicos = {}
    for t in (rp.get('tecnicos') or []):
        boosts = t.get('boosts') or []
        if any(float(x.get('delta') or 0) != 1.0 for x in boosts):
            raise SystemExit('PAROU: tecnico %s tem delta de boost diferente de +1.' % t.get('tecnico_id'))
        tid = int(t['tecnico_id'])
        tecnicos[tid] = {'nome': t.get('nome_apresentacao'),
                         'boosts_canonicos': [int(x['indice_otimizador']) for x in boosts],
                         'proficiencias': {str(x['codigo_estilo']): float(x['valor'])
                                           for x in (t.get('proficiencias') or [])},
                         'proficiencia_maxima': t.get('proficiencia_maxima'),
                         'estilos_principais': t.get('estilos_principais') or []}

    _INSUMOS = {
        'contrato': rp.get('contrato'), 'gate': gate,
        'molde': molde,
        'funcoes': funcoes,
        'tecnicos_catalogo': tecnicos,
        'habilidades': habilidades,
        'bloqueio': bloqueio,
        'incidencia': incidencia,
        'parametro': rp.get('parametros') or {},
        'atributo': rp.get('atributos') or [],
        'barra': rp.get('barras') or {},
        'custo_nivel': rp.get('custo_nivel') or {},
        'multiplicador': rp.get('multiplicadores') or {},
        'fabricavel': [],
        'impeto': {},
        'versao_molde': rp.get('versao_molde'),
    }
    return _INSUMOS


def carimbo():
    """Assina a cabeça da fila pela porta v1, sem consultar RPC antiga."""
    try:
        cabeca = _rpc('otimizador_proxima_fila_v1', {'p_limite': 1}) or []
        bruto = json.dumps(cabeca, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(bruto).hexdigest()
    except Exception:
        return None


# ------------------------------------------------------------------ a fila
def proxima_fila(limite=200):
    """O próximo lote, identificado por ``funcao_id`` canônico."""
    return _rpc('otimizador_proxima_fila_v1', {'p_limite': limite}) or []


def gravar(linhas):
    """A volta. Grava na clube.build E TIRA a linha da fila, no mesmo comando."""
    if not linhas:
        return 0
    total = 0
    funcoes = carrega_tudo().get('funcoes') or {}
    for i in range(0, len(linhas), 200):
        compat = []
        for linha in linhas[i:i+200]:
            x = dict(linha)
            if 'funcao_id' not in x:
                raise SystemExit('PAROU: resultado sem funcao_id canônica.')
            fid = int(x.pop('funcao_id'))
            f = funcoes.get(fid) or {}
            codigo = f.get('codigo_compatibilidade')
            if not codigo:
                raise SystemExit('PAROU: funcao_id %s sem ponte de gravacao legada.' % fid)
            x['funcao_codigo'] = codigo
            compat.append(x)
        total += int(_rpc('gravar_build', {'p_linhas': compat}) or 0)
    return total


def estado():
    fila = proxima_fila(1)
    return {'contrato': 'otimizador_proxima_fila_v1', 'ha_fila': bool(fila)}


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
    """{skill_id: metadados}; rótulo fica somente em ``nome_apresentacao``."""
    h = carrega_tudo().get('habilidades') or {}
    if not h:
        raise SystemExit('PAROU: habilidades canônicas vieram vazias do contrato v1.')
    return h


def habilidades_de_goleiro():
    raise SystemExit('PAROU: classificação por nome/código textual foi removida; use bloqueio skill_id+funcao_id.')


def catalogo_fabricaveis():
    """Ímpetos continuam deliberadamente desligados neste contrato."""
    carrega_tudo()
    return []


def carrega_tecnicos_do_banco(tatica=None):
    """A lista de tecnicos no formato que o motor espera - o que era tecnicos.json.

    Vem do contrato canônico de clube_novo: identidade, cinco proficiencias e
    boosts ja resolvidos para o indice canônico do atributo.

    O Otimizador usa sempre o MAIOR valor; empate produz o mesmo multiplicador.
    ``tatica`` ficou apenas por compatibilidade de assinatura.
    """
    import equacao as _EQ
    cat = carrega_tudo().get('tecnicos_catalogo') or {}
    if not cat:
        raise SystemExit('PAROU: clube.tecnico veio vazia do banco.')
    out = []
    for tid, c in cat.items():
        b = [int(x) for x in (c.get('boosts_canonicos') or []) if 0 <= int(x) < 26]
        if not b:
            continue                      # era o hasBoost do arquivo
        sk = {k: float(v) for k, v in (c.get('proficiencias') or {}).items()}
        if not sk or c.get('proficiencia_maxima') is None:
            continue
        v = float(c['proficiencia_maxima'])
        out.append({'nome': c.get('nome'), 'id': int(tid), 'tat': v,
                    'm': _EQ.mult_de(v), 'boost': b,
                    'estilos_principais': c.get('estilos_principais') or []})
    return out


def peso_da_ordem():
    """{card_id: [vagas_de_impeto, orcamento]} das cartas que estao na fila.

    So serve para a ORDEM: carta com vaga de impeto livre + pool de habilidade
    roda um DP inteiro por candidato e chega a levar 4.953 s. Essas vao para o
    fim. Nao muda resultado nenhum.
    """
    return _rpc('otimizador_peso_ordem_v1') or {}
