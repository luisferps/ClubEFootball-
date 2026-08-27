# -*- coding: utf-8 -*-
r"""
DO BANCO — todo insumo desce do Supabase antes da rodada.

ORDEM DO LUIS, 17/08/2026:
    "A gente baixou os insumos atraves do vigia, a gente sobe eles pro banco.
     Qual e o proximo passo? Tem que fazer uma rotina no qual os motores leem
     eles de dentro do banco de dados, processa, e o resultado salva de novo
     pro banco. E o encaixe vai la e puxa esses trem do banco tambem."
    e, fechando o desenho:
    "Esses arquivos, se voce quiser fazer uma coisa que ele continua existindo,
     pode fazer, nao tem problema. Eu so estou falando de ONDE VEM os dados e
     PRA ONDE eles vao."

O DESENHO

    vigia coleta  ->  sobe insumo  ->  [ BANCO ]
                                          |
                                     DO-BANCO.bat   (este programa)
                                          |
                                    arquivos da pasta        <- copia descartavel,
                                          |                     reescrita a cada rodada
                                    motores processam
                                          |
                                       [ BANCO ]   builds + bonus

O ARQUIVO NAO E MAIS FONTE. Ele e cache. Nasce do banco toda vez que a rodada
comeca, entao nao tem como envelhecer nem duplicar em dois computadores: o que
vale e o que esta no Supabase.

O QUE DESCE

    cards_base             ->  dados/base_unica.json      (via baixar_base.py)
    insumo_molde           ->  dados/molde.json
    insumo_tecnico         ->  tecnicos.json
    insumo_habilidade      ->  HAB_EFEITOS_FINAL.json
    insumo_bloqueio        ->  habilidades_por_posicao.json
    insumo_impeto          ->  CAT_dom.json   (1 impeto por linha, 18/08)

TRES TRAVAS, porque escrever por cima e o que da errado neste sistema

  1. TABELA VAZIA NAO ESCREVE. Se o banco devolver zero linhas, o arquivo bom
     da pasta fica onde esta. Banco fora do ar nunca apaga o que funciona.
  2. BACKUP DE TUDO que for tocado, com carimbo de hora, em backups_do_banco\.
  3. MERGE QUE SO ACRESCENTA. O banco manda no que ele tem. Campo que so existe
     no arquivo (o japName do tecnico, o _leia da tabela de bloqueio) e
     PRESERVADO. A regra da casa e acrescenta antes de tirar.

⛔ NAO desce o dados/cards.json: o alimentador escreve nele com o motor rodando.
⛔ NAO desce falta_por_card nem raras_por_card: sao congelados de proposito
   (roda_lote_v6.py, bloco CONGELADOS).

A CHAVE sai do config.txt na hora de rodar. Nunca e impressa nem gravada aqui.
"""
import json, os, sys, io, time, shutil, subprocess, urllib.request, urllib.error

# ---------------------------------------------------------------------------
# ONDE ELE RODA — o padrao do ClubEfootball
#   Este arquivo mora em ClubEfootball\programas\, mas TRABALHA na pasta do
#   sistema (a que tem o config.txt, o dados\ e o baixar_base.py). Entao ele
#   sobe as pastas ate achar o config.txt e muda o diretorio para la. Mesmo
#   jeito do o_que_o_banco_tem.py e dos outros programas da pasta.
# ---------------------------------------------------------------------------
AQUI = os.path.dirname(os.path.abspath(__file__))


def acha_a_pasta_do_sistema(inicio):
    p = inicio
    for _ in range(4):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None


CASA = acha_a_pasta_do_sistema(AQUI)
if not CASA:
    print('PAREI: nao achei o config.txt nem aqui nem nas pastas de cima.')
    sys.exit(1)
os.chdir(CASA)

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

PAGINA = 1000
CARIMBO = time.strftime('%Y%m%d-%H%M%S')
BACKUPS = 'backups_do_banco'
SO_CONFERIR = '--conferir' in sys.argv


def P(*a):
    print(*a, flush=True)


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


# --------------------------------------------------------------- o config
if not os.path.exists('config.txt'):
    P('Falta o config.txt (com SUPABASE_URL e SUPABASE_KEY).')
    pausa(); sys.exit(1)

cfg = {}
for _l in open('config.txt', encoding='utf-8'):
    _l = _l.strip()
    if _l and not _l.startswith('#') and '=' in _l:
        _k, _v = _l.split('=', 1)
        cfg[_k.strip()] = _v.strip()

URL = cfg.get('SUPABASE_URL', '').rstrip('/')
KEY = cfg.get('SUPABASE_KEY', '')
if not URL or not KEY or 'COLE_AQUI' in KEY:
    P('O config.txt esta sem a URL ou a chave do Supabase.')
    pausa(); sys.exit(1)


def puxa(tabela, ordem):
    """A tabela inteira, de mil em mil (o PostgREST corta em 1000)."""
    tudo = []
    de = 0
    while True:
        req = urllib.request.Request(
            '%s/rest/v1/%s?select=*&order=%s' % (URL, tabela, ordem),
            headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
                     'Range-Unit': 'items', 'Range': '%d-%d' % (de, de + PAGINA - 1)})
        with urllib.request.urlopen(req, timeout=180) as r:
            pedaco = json.loads(r.read().decode('utf-8'))
        if not pedaco:
            break
        tudo.extend(pedaco)
        if len(pedaco) < PAGINA:
            break
        de += PAGINA
    return tudo


def le_arquivo(p, padrao):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return padrao


def guarda(p):
    """Backup com carimbo. Devolve o caminho, ou None se o arquivo nao existia."""
    if not os.path.exists(p):
        return None
    os.makedirs(BACKUPS, exist_ok=True)
    destino = os.path.join(BACKUPS, os.path.basename(p) + '.' + CARIMBO)
    shutil.copy2(p, destino)
    return destino


def grava(p, obj, indent=None):
    """⛔ 17/08 — O FORMATO IMPORTA, e nao e frescura.

    O COMECAR-TUDO.bat tem uma TRAVA DE TAMANHO no dados/molde.json: se ele
    nao tiver exatamente 40.713 bytes, a rodada PARA antes de comecar. Gravado
    com o padrao do json.dump o mesmo conteudo da 34.783 e a trava dispara.
    Medido: `indent=1` da 40.713 na bala.

    Entao cada arquivo desce no formato em que ele ja estava. Conteudo igual
    com formatacao diferente e a maneira mais boba de derrubar a rodada.
    """
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    # ⛔ 17/08 — `newline=''` NAO E OPCIONAL, e foi o segundo tombo do molde.
    #    No Windows, open(...,'w') traduz cada \n para \r\n. O molde tem 2.966
    #    linhas, entao o arquivo saia com 2.965 bytes a mais:
    #        40.713 (o certo) + 2.965 = 43.678 (o que saiu)
    #    Ordem igual, tipos iguais, valores iguais — so a quebra de linha. E a
    #    trava de md5 do COMECAR-TUDO.bat, com razao, barrou a rodada.
    #    Testar no Linux nao pega isto: la nao existe a traducao.
    with open(p, 'w', encoding='utf-8', newline='') as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


placar = []          # (arquivo, tabela, no_banco, antes, depois, situacao)
FALHOU = []


def registra(arquivo, tabela, no_banco, antes, depois, situacao):
    placar.append((arquivo, tabela, no_banco, antes, depois, situacao))
    P('   %-30s %-24s banco %5d   arquivo %5d -> %-5s  %s'
      % (arquivo, tabela, no_banco, antes, depois, situacao))


P('=' * 78)
P('  DO BANCO — os insumos descem do Supabase para a pasta')
P('=' * 78)
if SO_CONFERIR:
    P('  MODO CONFERIR: baixa, compara e NAO ESCREVE NADA.')
else:
    P('  Regra: o BANCO manda. Campo que so existe no arquivo e preservado.')
P('  Backup de tudo que for tocado em: %s\\' % BACKUPS)
P('-' * 78)


# ===========================================================================
# 1. AS CARTAS  —  cards_base -> dados/base_unica.json
#
# ⛔ NAO reimplemento a conversao aqui. O baixar_base.py ja faz isso com 60
#    campos mapeados, os gemeos resolvidos e o relatorio de quem ganhou ou
#    perdeu carta na descida. Duplicar esse mapeamento seria criar a segunda
#    verdade que este programa existe para acabar.
# ===========================================================================
P('')
P('[1/6] AS CARTAS   cards_base -> dados/base_unica.json   (chamando o baixar_base.py)')
if not os.path.exists('baixar_base.py'):
    P('   ⛔ nao achei o baixar_base.py. As cartas NAO desceram.')
    FALHOU.append('cards_base (falta o baixar_base.py)')
else:
    antes = len((le_arquivo(os.path.join('dados', 'base_unica.json'), {}) or {}).get('cards') or [])
    # ⛔ 17/08 — A FLAG VAI SEM OS TRACOS, e nao e detalhe.
    #    O baixar_base.py decide assim:
    #        SO_CONFERIR = any(a.lower().startswith('confer') for a in sys.argv[1:])
    #    '--conferir' NAO comeca com 'confer' — comeca com '-'. Mandado com os
    #    tracos, ele ignorava o modo e GRAVAVA a base_unica.json enquanto esta
    #    tela dizia 'SO CONFERI. Nada foi escrito'. Medido em 17/08 na rodada
    #    do Luis: fez backup e gravou 6.469 cards. Nao estragou nada, mas
    #    mentiu — e um 'so olha' que escreve e pior que nao ter o modo.
    cmd = [sys.executable, 'baixar_base.py'] + (['conferir'] if SO_CONFERIR else [])
    amb = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    try:
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, env=amb,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=900)
        saida = r.stdout.decode('utf-8', 'replace')
        for linha in saida.splitlines():
            if linha.strip():
                P('      | ' + linha.rstrip())
        if r.returncode != 0:
            FALHOU.append('cards_base (o baixar_base.py saiu com erro)')
    except Exception as e:
        P('   ⛔ o baixar_base.py nao rodou: %s' % e)
        FALHOU.append('cards_base (%s)' % e)
    depois = len((le_arquivo(os.path.join('dados', 'base_unica.json'), {}) or {}).get('cards') or [])
    registra('dados/base_unica.json', 'cards_base', depois, antes, depois,
             'OK' if depois else 'VAZIO')


# ===========================================================================
# 2. O MOLDE  —  insumo_molde -> dados/molde.json
# ===========================================================================
P('')
P('[2/6] O MOLDE   insumo_molde -> dados/molde.json')
try:
    linhas = puxa('insumo_molde', 'funcao,attr')
except Exception as e:
    P('   ⛔ o banco recusou: %s' % e); FALHOU.append('insumo_molde'); linhas = []

alvo = os.path.join('dados', 'molde.json')
antes = len(le_arquivo(alvo, []) or [])
if not linhas:
    registra('dados/molde.json', 'insumo_molde', 0, antes, antes,
             'PULADO (banco vazio) — o arquivo bom FICA')
else:
    # =====================================================================
    # A ORDEM DAS LINHAS TEM QUE SER A DO ARQUIVO. Medido em 17/08.
    #
    #   O COMECAR-TUDO.bat confere o md5 do dados/molde.json. O banco devolve
    #   ordenado por funcao,attr (alfabetico), e nessa ordem o "Falso nove"
    #   cai entre "Centroavante movel" e "Goleiro defensivo". No arquivo ele
    #   esta em outro lugar, porque foi ACRESCENTADO em 13/08, no fim.
    #
    #   Mesmas 494 linhas, mesmos valores, md5 diferente -> a trava dispara e
    #   a rodada para. Foi o que aconteceu na primeira rodada do Luis:
    #      43.678 bytes gerados x 40.713 esperados.
    #
    #   Conferido: ordem do arquivo + valores do banco = 40.713 bytes e
    #   md5 1575341961641efd13f090639145ee6f, o mesmo que a trava pede.
    #
    #   ⛔ E os valores vao COMO O BANCO MANDOU. 282 alvos sao float (101.0),
    #      e 23 tem meia casa de verdade (o Falso nove tem 84,5). "Consertar"
    #      o 101.0 para 101 muda o md5 e nao conserta nada.
    # =====================================================================
    ordem = {}
    for i, r in enumerate(le_arquivo(alvo, []) or []):
        try:
            ordem[(r['funcao'], int(r['attr']))] = i
        except Exception:
            pass

    def onde(r):
        # o que ja existia fica onde estava; o que o banco trouxe de novo
        # vai para o fim, em ordem, para nao embaralhar o que ja passava
        return ordem.get((r['funcao'], int(r['attr'])),
                         10 ** 6 + len(ordem)), r['funcao'], int(r['attr'])

    novo = [{'funcao': r['funcao'], 'attr': int(r['attr']),
             'alvo': r.get('alvo'), 'peso': r.get('peso')}
            for r in sorted(linhas, key=onde)]
    _novas = sum(1 for r in linhas if (r['funcao'], int(r['attr'])) not in ordem)
    if _novas:
        P('   ⚠️ %d linhas de molde que o arquivo nao tinha — foram para o fim.' % _novas)
        P('      Se a trava de md5 do COMECAR-TUDO reclamar, e por causa delas.')
    if not SO_CONFERIR:
        guarda(alvo); grava(alvo, novo, indent=1)
    registra('dados/molde.json', 'insumo_molde', len(novo), antes,
             len(novo) if not SO_CONFERIR else antes,
             'CONFERIDO' if SO_CONFERIR else 'GRAVADO · %d funcoes'
             % len({x['funcao'] for x in novo}))


# ===========================================================================
# 3. OS TECNICOS  —  insumo_tecnico -> tecnicos.json
#
# O insumo_tecnico guarda o que o motor le (id, nome, boosts, proficiencias).
# O arquivo tem tambem japName, chineseName e affinity, que o banco nao tem.
# Esses ficam: MERGE, nao substituicao.
# ===========================================================================
P('')
P('[3/6] OS TECNICOS   insumo_tecnico -> tecnicos.json')
try:
    linhas = puxa('insumo_tecnico', 'id')
except Exception as e:
    P('   ⛔ o banco recusou: %s' % e); FALHOU.append('insumo_tecnico'); linhas = []

velho = le_arquivo('tecnicos.json', {}) or {}
antes = len(velho)
if not linhas:
    registra('tecnicos.json', 'insumo_tecnico', 0, antes, antes,
             'PULADO (banco vazio) — o arquivo bom FICA')
else:
    novo = {}
    preservados = 0
    for r in linhas:
        k = str(r['id'])
        base = dict(velho.get(k) or {})       # o que so o arquivo tem, fica
        if base:
            preservados += 1
        base.update({'id': int(r['id']), 'name': r.get('nome'),
                     'accentedName': r.get('nome_acentuado'),
                     'country': r.get('pais'), 'age': r.get('idade'),
                     'hasBoost': bool(r.get('tem_boost')),
                     'boosts': r.get('boosts') or [],
                     'skills': r.get('proficiencias') or {}})
        novo[k] = base
    # ⛔ tecnico que existe no arquivo e nao existe no banco NAO some.
    so_no_arquivo = [k for k in velho if k not in novo]
    for k in so_no_arquivo:
        novo[k] = velho[k]
    if not SO_CONFERIR:
        guarda('tecnicos.json'); grava('tecnicos.json', novo)
    obs = 'GRAVADO'
    if so_no_arquivo:
        obs += ' · %d so no arquivo, mantidos' % len(so_no_arquivo)
    registra('tecnicos.json', 'insumo_tecnico', len(linhas), antes,
             len(novo) if not SO_CONFERIR else antes,
             'CONFERIDO' if SO_CONFERIR else obs)


# ===========================================================================
# 4. AS HABILIDADES  —  insumo_habilidade -> HAB_EFEITOS_FINAL.json
# ===========================================================================
P('')
P('[4/6] AS HABILIDADES   insumo_habilidade -> HAB_EFEITOS_FINAL.json')
try:
    linhas = puxa('insumo_habilidade', 'chave')
except Exception as e:
    P('   ⛔ o banco recusou: %s' % e); FALHOU.append('insumo_habilidade'); linhas = []

velho = le_arquivo('HAB_EFEITOS_FINAL.json', {}) or {}
antes = len(velho)
if not linhas:
    registra('HAB_EFEITOS_FINAL.json', 'insumo_habilidade', 0, antes, antes,
             'PULADO (banco vazio) — o arquivo bom FICA')
else:
    novo = {}
    for r in linhas:
        k = r['chave']
        base = dict(velho.get(k) or {})
        nome = r.get('nome_pt') or base.get('arquivo')
        base.update({'arquivo': nome,
                     'tipo': r.get('tipo'),
                     'efeito': r.get('efeito') or {}})
        # ⛔ 17/08 — o `doc` NAO pode ser preenchido aqui.
        #    Medido: 27 das 65 habilidades tem `doc` NULO de proposito no
        #    arquivo. Escrever o nome por cima do nulo seria inventar dado na
        #    descida — e a descida do banco tem que devolver o que subiu, nao
        #    uma versao melhorada. So preenche se a chave nem existir.
        if 'doc' not in base:
            base['doc'] = nome
        novo[k] = base
    so_no_arquivo = [k for k in velho if k not in novo]
    for k in so_no_arquivo:
        novo[k] = velho[k]
    if not SO_CONFERIR:
        guarda('HAB_EFEITOS_FINAL.json'); grava('HAB_EFEITOS_FINAL.json', novo, indent=1)
    com = sum(1 for v in novo.values() if v.get('tipo') == 'comum')
    rar = sum(1 for v in novo.values() if v.get('tipo') == 'rara')
    registra('HAB_EFEITOS_FINAL.json', 'insumo_habilidade', len(linhas), antes,
             len(novo) if not SO_CONFERIR else antes,
             'CONFERIDO' if SO_CONFERIR else 'GRAVADO · %d comuns, %d raras' % (com, rar))


# ===========================================================================
# 5. O BLOQUEIO  —  insumo_bloqueio -> habilidades_por_posicao.json
#
# A tabela guarda o par habilidade x funcao JA EXPLODIDO, com o grupo ao lado.
# O arquivo guarda habilidade -> [grupos] mais quatro chaves de documentacao
# (_fonte, _leia, _nao_mapeadas, _nota_MC) que contam POR QUE cada bloqueio
# existe. Essas nao estao no banco e NAO PODEM SUMIR: e nelas que esta escrito
# o criterio dos 10% e a decisao do falso nove.
# ===========================================================================
P('')
P('[5/6] O BLOQUEIO   insumo_bloqueio -> habilidades_por_posicao.json')
try:
    linhas = puxa('insumo_bloqueio', 'habilidade,funcao')
except Exception as e:
    P('   ⛔ o banco recusou: %s' % e); FALHOU.append('insumo_bloqueio'); linhas = []

velho = le_arquivo('habilidades_por_posicao.json', {}) or {}
antes = len(velho.get('bloqueios') or {})
if not linhas:
    registra('habilidades_por_posicao.json', 'insumo_bloqueio', 0, antes, antes,
             'PULADO (banco vazio) — o arquivo bom FICA')
else:
    posicoes = {}
    bloqueios = {}
    for r in linhas:
        g, f, h = r.get('grupo'), r.get('funcao'), r.get('habilidade')
        if g and f:
            posicoes.setdefault(g, [])
            if f not in posicoes[g]:
                posicoes[g].append(f)
        if h and g:
            bloqueios.setdefault(h, [])
            if g not in bloqueios[h]:
                bloqueios[h].append(g)
    novo = dict(velho)                       # guarda _fonte, _leia, _nota_MC...
    # ⛔ o _posicoes do arquivo pode ter GRUPO SEM BLOQUEIO NENHUM (o MAT, o FN).
    #    Ele nao aparece na tabela, e sumir dali quebraria o grupo inteiro.
    p_final = dict(velho.get('_posicoes') or {})
    p_final.update(posicoes)
    novo['_posicoes'] = p_final
    novo['bloqueios'] = bloqueios
    if not SO_CONFERIR:
        guarda('habilidades_por_posicao.json')
        grava('habilidades_por_posicao.json', novo, indent=1)
    registra('habilidades_por_posicao.json', 'insumo_bloqueio', len(linhas), antes,
             len(bloqueios) if not SO_CONFERIR else antes,
             'CONFERIDO' if SO_CONFERIR
             else 'GRAVADO · %d habilidades, %d grupos' % (len(bloqueios), len(p_final)))


# ===========================================================================
# 6. O CATALOGO DE IMPETOS  —  insumo_impeto -> CAT_dom.json
# ===========================================================================
#  ⛔ MUDOU EM 18/08. Ordem do Luis:
#     "Tem que dar um jeito do motor saber sobre essas coisas. Nao adianta nada
#      a gente arrumar aqui no banco de dados e, quando ele for procurar la,
#      estar pre-definido, e ai ele achar que nao existe."
#
#     Antes esta etapa lia a tabela `insumo_impeto_catalogo`, que guardava um
#     registro por NOME COM O NIVEL COLADO ("Chute +1" e "Chute +3" como se
#     fossem dois impetos diferentes). Agora ela le a `insumo_impeto`: um
#     impeto por linha, o nivel como numero separado, os dois idiomas juntos.
#
#  ⛔ O SEGUNDO CAMPO DO CAT_dom NAO E "CONDICIONAL". E ADICIONAVEL.
#     O motor.py, linhas 80-82, faz:
#         self.L  = [x for x in CAT if x[1] == 0 ...] if sl[0] else []
#         self.Rr = [x for x in CAT if x[1] == 1 ...] if sl[1] else []
#     `sl[1]` quer dizer "esta carta tem vaga de impeto LIVRE". Entao a lista
#     que o motor usa para PREENCHER vaga vazia e a dos `x[1] == 1`.
#     Regra do Luis, 18/08: "O nivel +1 e para impetos ADICIONADOS. Voce nao
#     consegue adicionar um impeto com nivel maior do que um. Os outros niveis
#     — +2, +3, +4, +5 — sao para impetos que ja vem de fabrica."
#     Logo `x[1] == 1` tem que significar ADICIONAVEL, e adicionavel e sempre
#     no nivel 1. Antes vinha da coluna `condicional`, que por coincidencia
#     marcava os mesmos registros: resultado certo pelo motivo errado.
#
#  ⛔ O NOME QUE VAI PARA O ARQUIVO E O PORTUGUES quando existe. E ele que o
#     motor grava na linha e que aparece na tela do Encaixe. Trocar para o
#     ingles mudaria a cara de 12.368 linhas sem ninguem ter pedido.
#
#  ⛔ SO O NIVEL 1 VIRA CANDIDATO. Os niveis 2 a 5 entram no arquivo com o
#     segundo campo em 0: ficam legiveis, e o motor nunca os oferece.
# ===========================================================================
P('')
P('[6/6] O CATALOGO DE IMPETOS   insumo_impeto -> CAT_dom.json')
try:
    linhas = puxa('insumo_impeto', 'chave')
except Exception as e:
    P('   ⛔ o banco recusou: %s' % e)
    P('      -> falta rodar o ClubEfootball\\sql\\31-o-catalogo-de-impeto.sql')
    P('         e depois o MONTAR-O-CATALOGO-DE-IMPETO.bat')
    FALHOU.append('insumo_impeto'); linhas = []

antes = len(le_arquivo('CAT_dom.json', []) or [])
if not linhas:
    registra('CAT_dom.json', 'insumo_impeto', 0, antes, antes,
             'PULADO (banco vazio) — o arquivo bom FICA')
else:
    novo = []
    for r in linhas:
        nome = r.get('nome_pt') or r.get('nome_en') or r.get('chave')
        ats = r.get('atributos') or []
        niveis = r.get('niveis_vistos') or []
        adic = bool(r.get('adicionavel'))
        for lv in niveis:
            # O efeito e o nivel repetido em CADA atributo do impeto:
            # Chute +3 = +3 em cada um dos 4, nao 3 repartidos entre eles.
            efeito = [[int(a), int(lv)] for a in ats]
            candidato = 1 if (adic and int(lv) == 1) else 0
            novo.append(['%s +%d' % (nome, int(lv)), candidato, efeito])
    # ⛔ MERGE QUE SO ACRESCENTA — a regra da casa, e aqui ela tem um caso real.
    #    O catalogo novo nasce das CARTAS, entao impeto que nao aparece em carta
    #    nenhuma nao esta nele. O "Qualidade Goleiro +1" e exatamente isso:
    #    zero cartas na base, mas o motor JA O ESCOLHEU em 16 linhas de goleiro.
    #    Se eu simplesmente trocasse o arquivo, goleiro com vaga livre ficaria
    #    sem candidato nenhum. Entao o que ja estava no arquivo e nao veio do
    #    banco FICA, do jeito que estava.
    tem = {x[0] for x in novo}
    velho = le_arquivo('CAT_dom.json', []) or []
    herdados = [x for x in velho
                if isinstance(x, list) and len(x) == 3 and x[0] not in tem]
    novo.extend(herdados)
    novo.sort(key=lambda x: x[0])
    if not SO_CONFERIR:
        guarda('CAT_dom.json'); grava('CAT_dom.json', novo)
    cand = sum(1 for x in novo if x[1])
    registra('CAT_dom.json', 'insumo_impeto', len(novo), antes,
             len(novo) if not SO_CONFERIR else antes,
             'CONFERIDO' if SO_CONFERIR
             else 'GRAVADO · %d impetos · %d linhas · %d adicionaveis%s'
                  % (len(linhas), len(novo), cand,
                     ' · %d herdados do arquivo' % len(herdados) if herdados else ''))
    if herdados:
        P('   ⚠️ ficaram do arquivo (nao aparecem em carta nenhuma, mas o motor usa):')
        for x in herdados[:10]:
            P('        %s' % x[0])


# ===========================================================================
P('')
P('=' * 78)
P('  RESUMO')
P('=' * 78)
encolheu = [x for x in placar if x[4] < x[3] and 'PULADO' not in x[5]]
for arq, tab, banco, a, d, sit in placar:
    seta = '=' if d == a else ('+' if d > a else '-')
    P('  %-30s %5d -> %-5d %s   %s' % (arq, a, d, seta, sit))

if encolheu:
    P('')
    P('  ⚠️ ENCOLHERAM — o banco tem menos que a pasta tinha:')
    for arq, tab, banco, a, d, sit in encolheu:
        P('     %-30s %d -> %d   (tabela %s)' % (arq, a, d, tab))
    P('     Isso pode ser certo (a pasta tinha lixo) ou pode ser insumo que')
    P('     ainda nao subiu. Rode o SUBIR-INSUMOS.bat e confira antes de rodar')
    P('     o motor. O backup esta em %s\\' % BACKUPS)

if FALHOU:
    P('')
    P('  ⛔ NAO DESCERAM: %s' % ', '.join(FALHOU))
    P('     Os arquivos dessas tabelas ficaram como estavam. Nada foi apagado.')

P('')
if SO_CONFERIR:
    P('  SO CONFERI. Nada foi escrito.')
else:
    P('  Pronto. Os insumos da pasta agora sao copia do banco, de %s.'
      % time.strftime('%d/%m %H:%M'))
    P('  O resultado da rodada volta para o banco sozinho:')
    P('     builds  <- o motor, linha a linha (grava_direto, lote de 1)')
    P('     bonus   <- o motor de bonus, no fim da rodada')
P('=' * 78)
pausa()
sys.exit(1 if FALHOU else 0)
