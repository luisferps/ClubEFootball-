# -*- coding: utf-8 -*-
r"""
SUBIR O TRADUTOR — 16/08/2026

O QUE E, EM UMA FRASE
  Cada fonte chama a mesma coisa por um nome. Este programa poe todos esses nomes
  numa tabela so do banco, para nenhum programa precisar adivinhar de novo.

POR QUE ELE EXISTE
  Ordem do Luis, 16/08: "quando a gente vai procurar nos outros bancos de dados,
  as chaves deles sao outras. Tem que ter tipo um tradutor nesse meio."

  O tradutor JA TINHA SIDO FEITO em 14/08 — esta no CHAVES.json, com as nove
  entidades, tudo medido. So que ele ficou num arquivo que NENHUM programa le.
  Isso e a doenca do sistema: o trabalho existe e nao chega no lugar onde e usado.
  Este programa leva o CHAVES.json para o banco.

  A regra que esta escrita dentro do proprio CHAVES.json, e que vale aqui:
     "A correspondencia com cada fonte e MEDIDA, nunca deduzida do nome.
      Medido em 14/08: a regra 'camelCase vira snake_case' erra em 5 de 58."

O QUE ELE FAZ
  1. le o CHAVES.json (a fonte) e o dados/base_unica.json (para conferir)
  2. monta as linhas da tabela `traducao`
  3. preenche as colunas novas da tabela `funcoes`: codigo, rotulo, rotulo_curto,
     grupo e sigla_posicao
  4. CONFERE antes de subir: se qualquer funcao do banco nao tiver par, PARA.
  5. sobe por upsert — nada e apagado, o que ja existe e atualizado

⛔ O QUE ELE NAO FAZ
  Nao cria tabela. As tabelas tem que existir antes — o SQL esta no
  CRIAR-TRADUTOR-NO-SUPABASE.html, com botao de copiar.
  Nao apaga nada. Nao mexe em nenhuma linha de pontuacao.

A CHAVE
  Lida do config.txt na hora, igual aos outros. Nunca sai da maquina.
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime

# ============================================================================
# ONDE ESTE PROGRAMA TRABALHA — vale para AGORA e para DEPOIS DA MUDANCA
# ============================================================================
# Hoje ele mora na subpasta ClubEfootball e o config.txt esta na pasta DE CIMA.
# Decisao do Luis, 16/08 01h10: "no final a gente vai juntar todos os arquivos,
# inclusive os da pasta anterior, dentro dessa. E essa pasta vai valer."
# Quando isso acontecer, o config.txt vai passar a estar AQUI DENTRO.
#
# Entao ele NAO cravou o caminho. Ele PROCURA: comeca na propria pasta e vai
# subindo ate achar o config.txt. Funciona antes e depois da mudanca, sem
# ninguem precisar lembrar de editar nada.
AQUI = os.path.dirname(os.path.abspath(__file__))

def acha_a_pasta_do_sistema(inicio):
    p = inicio
    for _ in range(4):                       # a propria, e ate 3 niveis acima
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None

CASA = acha_a_pasta_do_sistema(AQUI)
if not CASA:
    print('⛔ nao achei o config.txt nem aqui nem nas pastas de cima.')
    print('   Este programa tem que ficar na pasta do sistema ou numa subpasta dela.')
    sys.exit(1)
os.chdir(CASA)

def P(*a): print(*a, flush=True)

# ============================================================================
# OS 19 ROTULOS DE TELA — decisao do Luis, ditada em 16/08/2026 00h45
# ============================================================================
# ⛔ ISTO NAO E MEDICAO, E DECISAO DELE. Nao mexer sem ordem expressa.
#
#   A chave da esquerda e a que esta na tabela `funcoes` do banco e dentro do
#   linhas.jsonl. Ela NAO MUDA — trocar ela apagaria 11 mil linhas de pontuacao,
#   porque tres tabelas apontam para ela com apagamento em cascata.
#   O que muda e o rotulo da direita.
#
#   As duas do meia lateral foram PROVADAS pelo molde, nao pela ordem da fala:
#     "por fora"  -> Passe alto alvo 100,0 peso 12  -> e quem CRUZA
#     "por dentro"-> Drible 107,0 peso 12, Aceleracao peso 12 -> e quem FINALIZA
#
FUNCOES = [
    # chave no banco              codigo (slug 14/08)      rotulo de hoje         rotulo curto     grupo               sigla
    ("Goleiro ofensivo",          "goleiro_ofensivo",      "Goleiro ofensivo",    "ofensivo",      "GOLEIRO",          "GO"),
    ("Goleiro defensivo",         "goleiro_defensivo",     "Goleiro defensivo",   "defensivo",     "GOLEIRO",          "GO"),
    ("Zagueiro de saída",         "zagueiro_de_saida",     "Zagueiro de saída",   "de saída",      "ZAGUEIRO",         "ZC"),
    ("Zagueiro de combate",       "zagueiro_de_combate",   "Zagueiro de combate", "de combate",    "ZAGUEIRO",         "ZC"),
    ("Lateral ofensivo",          "lateral_ofensivo",      "Lateral ofensivo",    "ofensivo",      "LATERAL",          "LE-LD"),
    ("Lateral defensivo",         "lateral_defensivo",     "Lateral defensivo",   "defensivo",     "LATERAL",          "LE-LD"),
    ("Volante de contenção",      "volante_de_contencao",  "Volante de contenção","de contenção",  "VOLANTE",          "VOL"),
    ("Volante de construção",     "volante_de_construcao", "Volante de construção","de construção","VOLANTE",          "VOL"),
    ("Meia central armador",      "meia_central_armador",  "Meia armador",        "armador",       "MEIA DE LIGAÇÃO",  "MLG"),
    ("Meia central de chegada",   "meia_central_de_chegada","Meia de arranque",   "de arranque",   "MEIA DE LIGAÇÃO",  "MLG"),
    ("Meia de lado por dentro",   "meia_de_lado_por_dentro","Ala finalizador",    "finalizador",   "MEIA LATERAL",     "MLE-MLD"),
    ("Meia de lado por fora",     "meia_de_lado_por_fora", "Ala cruzador",        "cruzador",      "MEIA LATERAL",     "MLE-MLD"),
    ("Meia ofensivo armador",     "meia_ofensivo_armador", "Meia ofensivo",       "ofensivo",      "MEIA ATACANTE",    "MAT"),
    ("Segundo atacante",          "segundo_atacante",      "Atacante infiltrador","infiltrador",   "MEIA ATACANTE",    "MAT"),
    ("Ponta criadora",            "ponta_criadora",        "Atacante criador",    "criador",       "PONTA",            "PTE-PTD"),
    ("Ponta finalizadora",        "ponta_finalizadora",    "Atacante finalizador","finalizador",   "PONTA",            "PTE-PTD"),
    ("Centroavante fixo",         "centroavante_fixo",     "Centroavante fixo",   "fixo",          "CENTROAVANTE",     "CA"),
    ("Centroavante móvel",        "centroavante_movel",    "Centroavante móvel",  "móvel",         "CENTROAVANTE",     "CA"),
    ("Falso nove",                "falso_nove",            "Falso nove",          "falso nove",    "CENTROAVANTE",     "CA"),
]

# ---- a chave -------------------------------------------------------------
def config():
    cfg = {}
    for ln in open('config.txt', encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if '=' in ln and not ln.startswith('#'):
            k, v = ln.split('=', 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

C = config()
URL = (C.get('SUPABASE_URL') or '').rstrip('/')
KEY = C.get('SUPABASE_KEY') or C.get('SUPABASE_SERVICE_KEY') or ''
if not URL or not KEY:
    P('NAO ACHEI SUPABASE_URL / SUPABASE_KEY no config.txt. Nada foi feito.')
    sys.exit(1)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}

def le(url):
    r = urllib.request.Request(URL + '/rest/v1/' + url, headers=H)
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.loads(f.read().decode('utf-8'))

def sobe(tabela, linhas, conflito):
    if not linhas:
        return 0
    n = 0
    for i in range(0, len(linhas), 200):
        lote = linhas[i:i + 200]
        u = URL + '/rest/v1/' + tabela + '?on_conflict=' + conflito
        d = json.dumps(lote, ensure_ascii=False).encode('utf-8')
        r = urllib.request.Request(u, data=d, headers=dict(
            H, Prefer='resolution=merge-duplicates,return=minimal'), method='POST')
        with urllib.request.urlopen(r, timeout=120):
            n += len(lote)
    return n

P('=' * 74)
P('  SUBIR O TRADUTOR  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 74)

# ---- 1) leitura ----------------------------------------------------------
if not os.path.exists('CHAVES.json'):
    P('⛔ nao achei o CHAVES.json. Ele e a fonte deste programa. Nada foi feito.')
    sys.exit(1)
CH = json.load(open('CHAVES.json', encoding='utf-8'))['entidades']
P('CHAVES.json lido — %d entidades: %s' % (len(CH), ', '.join(CH)))

# ---- 2) A CONFERENCIA, ANTES DE SUBIR ------------------------------------
P('')
P('CONFERENCIA (antes de escrever qualquer coisa)')
try:
    no_banco = [x['nome'] for x in le('funcoes?select=nome')]
except Exception as e:
    P('⛔ nao consegui ler a tabela funcoes: %s' % e); sys.exit(1)

nossas = [f[0] for f in FUNCOES]
faltando = [x for x in no_banco if x not in nossas]
sobrando = [x for x in nossas if x not in no_banco]
P('  funcoes no banco ................ %d' % len(no_banco))
P('  funcoes na nossa tabela ......... %d' % len(nossas))
if faltando or sobrando:
    P('')
    P('  ⛔ NAO BATEU. Nada foi subido.')
    for x in faltando: P('     esta no banco e nao na nossa tabela: %s' % x)
    for x in sobrando: P('     esta na nossa tabela e nao no banco: %s' % x)
    P('     Conserte a tabela FUNCOES la em cima antes de rodar de novo.')
    sys.exit(1)
P('  ✅ 19 de 19 batem, nenhuma sobrando dos dois lados.')

# confere os slugs contra o CHAVES.json
slugs_ch = CH.get('funcao', {}).get('itens', {})
ruins = [(c, s) for (c, s, _, _, _, _) in FUNCOES if s not in slugs_ch]
if ruins:
    P('  ⛔ estes codigos nao existem no CHAVES.json: %s' % ruins)
    sys.exit(1)
P('  ✅ os 19 codigos batem com o CHAVES.json de 14/08.')

# ---- 3) as colunas novas da tabela funcoes -------------------------------
P('')
P('1) tabela FUNCOES — o codigo fixo e os rotulos')
linhas_f = [{'nome': c, 'codigo': s, 'rotulo': r, 'rotulo_curto': rc,
             'grupo': g, 'sigla_posicao': sg}
            for (c, s, r, rc, g, sg) in FUNCOES]
try:
    n = sobe('funcoes', linhas_f, 'nome')
    P('   %d funcoes atualizadas (a chave `nome` nao foi tocada)' % n)
except urllib.error.HTTPError as e:
    P('   ⛔ ERRO %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]))
    P('   As colunas novas existem? Rode antes o CRIAR-TRADUTOR-NO-SUPABASE.html')
    sys.exit(1)

# ---- 4) a tabela traducao ------------------------------------------------
P('')
P('2) tabela TRADUCAO — como cada fonte chama cada coisa')
T = []
def add(assunto, chave, fonte, como, medido=False, obs=None):
    if como in (None, '', []):
        return
    T.append({'assunto': assunto, 'chave': str(chave), 'fonte': fonte,
              'como_chama': str(como), 'medido': bool(medido), 'observacao': obs})

# funcao
for (c, s, r, rc, g, sg) in FUNCOES:
    add('funcao', s, 'banco', c, True, 'a chave da tabela funcoes, do linhas.jsonl e das 3 chaves estrangeiras')
    add('funcao', s, 'tela', r, True, 'rotulo decidido pelo Luis em 15 e 16/08')
    add('funcao', s, 'tela_curto', rc, True, 'como aparece embaixo do grupo, na barra')
    add('funcao', s, 'grupo_da_tela', g, True, None)
    add('funcao', s, 'posicao_da_tela', sg, True, None)

# habilidade
for k, v in (CH.get('habilidade', {}).get('itens') or {}).items():
    add('habilidade', k, 'tela', v.get('pt'), v.get('medido'))
    add('habilidade', k, 'efhub', v.get('efhub'), v.get('medido'))
    add('habilidade', k, 'efhub_enum', v.get('enum_efhub'), v.get('medido'))
    add('habilidade', k, 'efootballdb', v.get('efootballdb'), v.get('medido'))
    add('habilidade', k, 'efscout', v.get('efscout'), v.get('medido'))
    add('habilidade', k, 'jogo', v.get('jogo'), True, 'conferido no jogo pelo Luis')
    for s in (v.get('sinonimos_pt') or []):
        add('habilidade', k, 'sinonimo_pt', s, True, 'nome antigo — a Konami renomeou')

# posicao
for k, v in (CH.get('posicao', {}).get('itens') or {}).items():
    add('posicao', k, 'tela', v.get('pt'), True, v.get('nota'))
    for s in (v.get('sinonimos') or []):
        add('posicao', k, 'sinonimo', s, True, 'outra grafia achada dentro do nosso proprio banco')

# atributo
for k, v in (CH.get('atributo', {}).get('itens') or {}).items():
    add('atributo', k, 'tela', v if isinstance(v, str) else v.get('pt'), True,
        'a chave e o indice 0 a 25, que ja e a ordem do vetor')

# estilo de jogo
for k, v in (CH.get('estilo_de_jogo', {}).get('itens') or {}).items():
    add('estilo_de_jogo', k, 'tela', k, True)
    add('estilo_de_jogo', k, 'efhub', (v or {}).get('efhub'), (v or {}).get('medido'))

# medida de corpo
for k, v in (CH.get('medida_de_corpo', {}).get('itens') or {}).items():
    add('medida_de_corpo', k, 'nosso', (v or {}).get('nosso'), True,
        'a chave e a posicao no vetor de 12')
    add('medida_de_corpo', k, 'efhub', (v or {}).get('efhub'), True)

try:
    n = sobe('traducao', T, 'assunto,chave,fonte')
    P('   %d linhas de traducao subidas' % n)
except urllib.error.HTTPError as e:
    P('   ⛔ ERRO %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]))
    P('   A tabela existe? Rode antes o CRIAR-TRADUTOR-NO-SUPABASE.html')
    sys.exit(1)

# ---- 5) o que AINDA FALTA no tradutor ------------------------------------
P('')
P('3) O QUE AINDA FALTA MEDIR — nao inventar, coletar')
buracos = []
h = CH.get('habilidade', {})
if h.get('A_MEDIR'):
    buracos.append(('habilidade', len(h['A_MEDIR']), ', '.join(h['A_MEDIR'])))
e = CH.get('estilo_de_jogo', {})
sem = [k for k, v in (e.get('itens') or {}).items() if not (v or {}).get('medido')]
if sem:
    buracos.append(('estilo de jogo', len(sem), ', '.join(sem[:8]) + (' ...' if len(sem) > 8 else '')))
imp = CH.get('impeto', {})
if imp.get('orfaos_que_os_cards_citam'):
    buracos.append(('impeto orfao', len(imp['orfaos_que_os_cards_citam']),
                    ', '.join(str(x) for x in imp['orfaos_que_os_cards_citam'])))
if not (CH.get('box', {}).get('itens')):
    buracos.append(('box', 0, 'a chave ainda nao foi definida — hoje junta pelo nome da campanha'))
for a, q, quais in buracos:
    P('   %-16s %3s  %s' % (a, q or '-', quais[:110]))
if not buracos:
    P('   nenhum. O tradutor esta completo.')

# ---- 6) conferencia final ------------------------------------------------
P('')
P('CONFERENCIA FINAL — lendo de volta do banco')
# ⛔ 16/08: esta conferencia PARA o programa quando nao bate.
#    Na primeira versao ela so IMPRIMIA. Resultado: o programa disse que tinha
#    subido, o .bat seguiu para o passo seguinte, e o banco estava vazio — o
#    numero so apareceu quando alguem foi conferir por fora. Programa que
#    anuncia sucesso sem provar e pior que programa que falha.
falhou = []
try:
    volta = le('funcoes?select=nome,codigo,rotulo&order=nome')
    sem_cod = [x['nome'] for x in volta if not x.get('codigo')]
    P('   funcoes com codigo ....... %d de %d' % (len(volta) - len(sem_cod), len(volta)))
    if sem_cod:
        falhou.append('%d funcoes ficaram SEM codigo: %s'
                      % (len(sem_cod), ', '.join(sem_cod[:6])))
except Exception as ex:
    falhou.append('nao consegui reler a tabela funcoes: %s' % ex)

try:
    cnt = le('traducao?select=assunto')
    por = {}
    for x in cnt:
        por[x['assunto']] = por.get(x['assunto'], 0) + 1
    P('   traducao no banco ........ %d linhas' % len(cnt))
    P('   por assunto .............. %s' % ', '.join('%s %d' % (k, v) for k, v in sorted(por.items())))
    if len(cnt) == 0:
        falhou.append('a tabela traducao ficou VAZIA (tentei subir %d linhas)' % len(T))
    elif len(cnt) < len(T) * 0.9:
        falhou.append('a traducao ficou com %d linhas e eu enviei %d' % (len(cnt), len(T)))
except Exception as ex:
    falhou.append('nao consegui reler a tabela traducao: %s' % ex)

if falhou:
    P('')
    P('=' * 74)
    P('  ⛔ NAO FECHOU. O banco NAO recebeu o que este programa enviou.')
    for f in falhou:
        P('     · %s' % f)
    P('')
    P('  A CAUSA MAIS PROVAVEL, e o conserto:')
    P('  O Supabase guarda um retrato do desenho do banco e demora um pouco para')
    P('  perceber tabela ou coluna recem-criada. Se voce acabou de rodar o')
    P('  1-COLAR-NO-SUPABASE.html, espere um minuto e rode este .bat de novo.')
    P('  Se insistir: no painel do Supabase va em Settings > API e clique em')
    P('  "Reload schema cache" (ou rode  notify pgrst, %s;  no SQL Editor).'
      % "'reload schema'")
    P('=' * 74)
    sys.exit(1)

P('')
P('=' * 74)
P('  PRONTO E CONFERIDO. Nada foi apagado.')
P('  A chave `nome` das funcoes continua a mesma.')
P('  O proximo passo (trocar a chave das 3 tabelas para o codigo) NAO')
P('  esta neste programa — ele se faz com o Luis acordado.')
P('=' * 74)
