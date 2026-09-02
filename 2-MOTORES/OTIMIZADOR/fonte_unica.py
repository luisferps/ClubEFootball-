# -*- coding: utf-8 -*-
"""
FONTE ÚNICA — contrato versionado do Otimizador.

O QUE MUDOU
  Antes:  dados/base_unica.json  (um arquivo que alguém tinha que baixar)
  Agora:  o Supabase, somente pelas portas operacionais ``public.otimizador_*_v3``
          para carta e ``public.otimizador_regua_v2`` para a régua.

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


def _cabecalhos_supabase(chave):
    """Chave opaca sb_* segue apenas em apikey; JWT legado preserva Authorization."""
    cabecalhos = {
        'apikey': chave,
        'Content-Type': 'application/json',
        'User-Agent': 'ClubEfootballOtimizadorLocal/1.2',
    }
    if not chave.startswith('sb_'):
        cabecalhos['Authorization'] = 'Bearer ' + chave
    return cabecalhos


CAB = _cabecalhos_supabase(KEY)


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
        pacote = _rpc('otimizador_regua_v2') or {}
        return pacote.get('contrato') == 'otimizador_regua_v2'
    except SystemExit:
        return False


# ------------------------------------------------------------------ a carta
_CACHE = {}

def _traduz(j):
    """Contrato V3 -> estrutura interna; o motor recebe somente IDs e valores."""
    if not j:
        return None
    if j.get('contrato') != 'otimizador_entradas_v3':
        raise SystemExit('PAROU: contrato de carta inesperado; esperado otimizador_entradas_v3.')
    cid = str(j.get('card_id'))
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
        'nm':      [],                             # preenchido pela identidade da linha
        'posicao_id': j.get('posicao_principal_id'),
        'pos':     j.get('posicao_principal_id'),
        'np':      j.get('posicao_principal_id'),
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


def vetor_impetos_da_linha(c, codigo_condicional=None, nivel_condicional=None):
    """Materializa os efeitos equipados usando apenas código, nível e receita física."""
    vetor = [0] * 26
    condicionais = [x for x in (c.get('impetos') or [])
                    if x.get('codigo_impeto') is not None and bool(x.get('condicional'))]
    if len(condicionais) > 1:
        raise ValueError('carta possui mais de um impeto condicional')
    if condicionais:
        esperado = int(condicionais[0]['codigo_impeto'])
        if codigo_condicional is None or nivel_condicional is None:
            raise ValueError('codigo e nivel do impeto condicional sao obrigatorios')
        if int(codigo_condicional) != esperado:
            raise ValueError('impeto condicional nao pertence a carta')
        maximo = int(condicionais[0].get('nivel_maximo') or 0)
        if not 1 <= int(nivel_condicional) <= maximo:
            raise ValueError('nivel do impeto condicional fora da faixa fisica')
    elif codigo_condicional is not None or nivel_condicional is not None:
        raise ValueError('carta nao possui impeto condicional')

    for impeto in (c.get('impetos') or []):
        if impeto.get('codigo_impeto') is None:
            continue
        condicional = bool(impeto.get('condicional'))
        for efeito in (impeto.get('efeitos') or []):
            indice = int(efeito['indice_otimizador'])
            delta = int(nivel_condicional) if condicional else int(efeito['delta'])
            vetor[indice] += delta
    return [[indice,delta] for indice,delta in enumerate(vetor) if delta]


def aplica_impetos_da_linha(c, codigo_condicional=None, nivel_condicional=None):
    out = dict(c)
    out['nm'] = vetor_impetos_da_linha(out, codigo_condicional, nivel_condicional)
    out['impeto_condicional_codigo'] = (None if codigo_condicional is None else int(codigo_condicional))
    out['impeto_condicional_nivel'] = (None if nivel_condicional is None else int(nivel_condicional))
    return out

def carta(card_id):
    """Uma carta, do banco. Guarda em memoria."""
    cid = str(card_id).split('@')[0]
    if cid not in _CACHE:
        _CACHE[cid] = _traduz(_rpc('otimizador_carta_v3', {'p_card_id': cid}))
    return _CACHE[cid]


def carrega_base(ids=None):
    """{id_base: card} — o mesmo formato de antes.

    O fluxo oficial sempre entrega os IDs da fila selada.
    """
    if ids is None:
        raise SystemExit('PAROU: a fila legada foi desativada; informe os IDs da fila clube_novo.')

    # Carregamento em lote exclusivamente pelo contrato V3 de clube_novo.
    # Isso reduz chamadas por carta sem criar cache ou projeção paralela.
    base = {}
    ids = [str(c) for c in ids]
    LOTE = 500
    for i in range(0, len(ids), LOTE):
        pedaco = ids[i:i + LOTE]
        linhas = _rpc('otimizador_cartas_v3', {'p_ids': pedaco})
        if linhas is None:
            raise SystemExit('PAROU: otimizador_cartas_v3 nao devolveu o lote; sem fallback.')
        for j in linhas:
            c = _traduz(j)
            if c:
                base[str(c['id']).split('@')[0]] = c
                _CACHE[str(c['id'])] = c
        print('   base: %d/%d cartas' % (min(i + LOTE, len(ids)), len(ids)), flush=True)
    return base


# ------------------------------------------------------------------ insumos
_INSUMOS = None

def _traduz_regua_v2(rp):
    """Traduz o pacote selado da régua sem alterar qualquer regra de cálculo.

    A fila produtiva V3 entrega uma fotografia do mesmo contrato V2 para que o
    worker não recarregue pesos, molde ou técnico no meio de um lote. Esta função
    só adapta IDs e números para o formato interno que já existia.
    """
    gate = rp.get('gate') or {}
    if rp.get('contrato') != 'otimizador_regua_v2' or not gate.get('pode_rodar'):
        raise SystemExit('PAROU: gate de otimizador_regua_v2 recusou a regua; sem fallback.')

    molde = []
    for r in (rp.get('molde') or []):
        molde.append({'funcao_id': int(r['funcao_id']),
                      'attr': int(r['indice_otimizador']),
                      'alvo': r['alvo'], 'peso': r['peso']})

    funcoes = {int(x['funcao_id']): {
        'ordem': x.get('ordem')}
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
            'efeito': efeitos}

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
        tecnicos[tid] = {'boosts_canonicos': [int(x['indice_otimizador']) for x in boosts],
                         'proficiencias': {str(x['codigo_estilo']): float(x['valor'])
                                           for x in (t.get('proficiencias') or [])},
                         'proficiencia_maxima': t.get('proficiencia_maxima'),
                         'estilos_principais': t.get('estilos_principais') or []}

    impetos_catalogo = {}
    for impeto in (rp.get('impetos') or []):
        codigo = int(impeto['codigo_impeto'])
        impetos_catalogo[codigo] = {
            'condicional': bool(impeto.get('condicional')),
            'nivel_maximo': impeto.get('nivel_maximo'),
            'efeitos': {int(x['indice_otimizador']): int(x['delta'])
                        for x in (impeto.get('efeitos') or [])},
        }

    # Ímpetos adicionais são um catálogo próprio do contrato selado. Eles não
    # vêm dos dois Ímpetos já equipados na carta: aqueles continuam servindo
    # exclusivamente para descobrir quais slots estão vagos. A regra do
    # catálogo é validada novamente aqui para que uma régua incompleta ou
    # adulterada nunca silencie a busca com uma lista vazia.
    adicionais = []
    vistos_adicionais = set()
    for impeto in (rp.get('impetos_adicionais') or []):
        try:
            codigo = int(impeto['codigo_impeto'])
            slots = sorted({int(x) for x in (impeto.get('slots') or [])})
            regra = str(impeto.get('regra') or '')
            nome = str(impeto.get('nome_pt') or '')
        except (TypeError, ValueError, KeyError) as erro:
            raise SystemExit('PAROU: catálogo de Ímpetos adicionais inválido: %s.' % erro)
        if codigo < 0 or slots not in ([1], [2], [1, 2]):
            raise SystemExit('PAROU: catálogo de Ímpetos adicionais tem código ou slot inválido.')

        efeitos = []
        for efeito in (impeto.get('efeitos') or []):
            try:
                indice = int(efeito['indice_otimizador'])
                bruto = float(efeito['delta'])
            except (TypeError, ValueError, KeyError) as erro:
                raise SystemExit('PAROU: efeito de Ímpeto adicional inválido: %s.' % erro)
            if indice < 0 or indice >= 26 or not bruto.is_integer():
                raise SystemExit('PAROU: efeito de Ímpeto adicional fora do contrato.')
            efeitos.append((indice, int(bruto)))
        efeitos.sort()
        if not efeitos or len({indice for indice, _ in efeitos}) != len(efeitos):
            raise SystemExit('PAROU: Ímpeto adicional sem efeitos canônicos.')
        if regra == 'delta_mais_um':
            if any(delta != 1 for _, delta in efeitos):
                raise SystemExit('PAROU: candidato adicional delta_mais_um diverge do +1 oficial.')
        elif regra == 'pacote_total_excecao':
            if nome != 'Pacote total' or any(delta != 3 for _, delta in efeitos):
                raise SystemExit('PAROU: exceção Pacote total diverge do catálogo oficial.')
        else:
            raise SystemExit('PAROU: regra de Ímpeto adicional desconhecida.')
        for slot in slots:
            chave = (codigo, slot)
            if chave in vistos_adicionais:
                raise SystemExit('PAROU: catálogo de Ímpetos adicionais duplicou código e slot.')
            vistos_adicionais.add(chave)
            # O motor histórico usa 0 para slot 1 e 1 para slot 2.
            adicionais.append([codigo, slot - 1, [[indice, delta] for indice, delta in efeitos]])

    if not adicionais:
        raise SystemExit('PAROU: contrato não trouxe candidatos oficiais de Ímpeto adicional.')
    adicionais.sort(key=lambda x: (x[1], x[0], x[2]))

    return {
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
        'impetos_adicionais': adicionais,
        'impeto': impetos_catalogo,
        'versao_molde': rp.get('versao_molde'),
    }


def carrega_tudo():
    """Todos os insumos, do contrato ativo, no formato que o motor espera."""
    global _INSUMOS
    if _INSUMOS is not None:
        return _INSUMOS
    _INSUMOS = _traduz_regua_v2(_rpc('otimizador_regua_v2') or {})
    return _INSUMOS


def carrega_tudo_do_snapshot_v3(pacote):
    """Instala a régua já selada de um lote V3, sem consultar fonte paralela.

    É uma porta interna do worker; o navegador nunca recebe esta fotografia nem
    credenciais. O contrato e o gate continuam obrigatórios e a fórmula não é
    interpretada aqui.
    """
    global _INSUMOS
    _INSUMOS = _traduz_regua_v2(dict(pacote or {}))
    return _INSUMOS


def carimbo():
    """Assina a régua oficial; nunca consulta a fila histórica."""
    try:
        pacote = _rpc('otimizador_regua_v2') or {}
        bruto = json.dumps(pacote, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(bruto).hexdigest()
    except Exception:
        return None


# ------------------------------------------------------------------ a fila
def proxima_fila(limite=200):
    raise SystemExit('PAROU: use a fila selada de clube_novo; a fila historica esta proibida.')


def gravar(linhas):
    raise SystemExit('PAROU: gravacao historica desativada; use build_linha_card e build_otimizador.')


def estado():
    return {'contrato': 'otimizador_regua_v2', 'ha_fila_historica': False}


# ------------------------------------------------------- insumos que eram arquivo
# Ate 27/08 o equacao.py abria tabm_medido.json e HAB_EFEITOS_FINAL.json, e o
# motor.py abria CAT_dom.json. As regras agora moram nas tabelas oficiais de
# clube_novo e descem pelos contratos V3/V2. A conta nao mudou - so a porta.

def tabela_multiplicador():
    """{ponto: multiplicador} - o que era tabm_medido.json."""
    t = carrega_tudo().get('multiplicador') or {}
    if not t:
        raise SystemExit('PAROU: otimizador_multiplicador veio vazio de clube_novo.')
    return t


def catalogo_habilidades():
    """{skill_id: metadados}; nenhuma etiqueta entra no motor."""
    h = carrega_tudo().get('habilidades') or {}
    if not h:
        raise SystemExit('PAROU: habilidades canônicas vieram vazias do contrato v1.')
    return h


def habilidades_de_goleiro():
    raise SystemExit('PAROU: classificação por nome/código textual foi removida; use bloqueio skill_id+funcao_id.')


def catalogo_fabricaveis():
    """Candidatos adicionais oficiais do pacote selado, por slot físico."""
    insumos = carrega_tudo()
    catalogo = insumos.get('impetos_adicionais') or []
    if not catalogo:
        raise SystemExit('PAROU: catálogo oficial de Ímpetos adicionais está vazio.')
    return catalogo


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
        raise SystemExit('PAROU: tecnico_jogo veio vazia de clube_novo.')
    out = []
    for tid, c in cat.items():
        b = [int(x) for x in (c.get('boosts_canonicos') or []) if 0 <= int(x) < 26]
        if not b:
            continue                      # era o hasBoost do arquivo
        sk = {k: float(v) for k, v in (c.get('proficiencias') or {}).items()}
        if not sk or c.get('proficiencia_maxima') is None:
            continue
        v = float(c['proficiencia_maxima'])
        out.append({'nome': int(tid), 'id': int(tid), 'tat': v,
                    'm': _EQ.mult_de(v), 'boost': b,
                    'estilos_principais': c.get('estilos_principais') or []})
    return out


def peso_da_ordem():
    """{card_id: [vagas_de_impeto, orcamento]} das cartas que estao na fila.

    So serve para a ORDEM: carta com vaga de impeto livre + pool de habilidade
    roda um DP inteiro por candidato e chega a levar 4.953 s. Essas vao para o
    fim. Nao muda resultado nenhum.
    """
    raise SystemExit('PAROU: ordenacao pela fila historica foi desativada.')
