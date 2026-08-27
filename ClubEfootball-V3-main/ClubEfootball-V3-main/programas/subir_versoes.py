# -*- coding: utf-8 -*-
r"""
SUBIR AS VERSOES — o molde inteiro e a identidade dos dois motores
16/08/2026

POR QUE ELE EXISTE
  Ordem do Luis, 16/08: "tem que colocar no banco a versao dele e tem que colocar ele
  INTEIRO, as regras dele... e as versoes anteriores, que ja tem, e as que virao.
  Ate pra saber, se der problema, qual foi."

  Hoje o banco MENTE sobre o molde: a tabela molde_versao diz que a versao 5 e a
  vigente, mas a tabela molde so tem linhas das versoes 2 e 3 — 468 linhas cada,
  que e o desenho de 18 funcoes. O molde 5 tem 494 itens e 19 funcoes.
  Esta assim desde 12/08. Qualquer conferencia feita pelo banco da resposta errada.

  E a identidade dos motores esta espalhada em quatro lugares diferentes:
  molde_versao, arquivos_insumo, builds.motor_versao e bonus.motor_bonus.

O QUE ELE FAZ
  1. sobe o dados/molde.json inteiro como VERSAO 5 (o que ja estiver la e atualizado)
  2. grava a identidade dos dois motores: qual versao, quando, o que mudou
  3. grava a IMPRESSAO DIGITAL de cada arquivo que compoe cada motor
  4. CONFERE antes e depois. Se o molde do arquivo nao tiver 19 funcoes, PARA.

  Com isso da para responder, um mes depois: "esta pontuacao saiu de qual molde e de qual
  motor?" — e provar, porque a impressao digital nao mente.

MODO CONFERIR
  Rodando com o argumento  conferir  ele NAO escreve nada: so compara a impressao
  digital dos arquivos de hoje com a que esta gravada no banco, e diz o que mudou.
  E a trava que impede rodar o motor com receita trocada sem ninguem perceber.

⛔ NAO CRIA TABELA. As duas tabelas novas tem que existir antes — o comando esta no
   CRIAR-VERSOES-NO-SUPABASE.html, com botao de copiar.
⛔ NAO APAGA NADA. As versoes 2 e 3 do molde ficam onde estao: sao historico.
"""
import json, os, sys, hashlib, urllib.request, urllib.error
from datetime import datetime, timezone

# ---- onde ele trabalha (procura, nao crava) -------------------------------
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
    print('⛔ nao achei o config.txt nem aqui nem nas pastas de cima.')
    sys.exit(1)
os.chdir(CASA)

def P(*a): print(*a, flush=True)

SO_CONFERIR = (len(sys.argv) > 1 and sys.argv[1].lower().startswith('confer'))

# ============================================================================
# QUEM COMPOE CADA MOTOR
# ============================================================================
# ⛔ Se alguem acrescentar um arquivo que muda a conta, TEM QUE ENTRAR AQUI.
#    Arquivo que muda a pontuacao e nao esta nesta lista e pontuacao que muda sem rastro.
MOTORES = {
    'otimizacao': {
        'versao': 6,
        'quando': '2026-08-07',
        'o_que_mudou': 'Rodada v6: o pool passou a ser a regra do jogo (nao a lista da '
                       'comunidade), entraram os cortes 10 e 11, a margem de impeto ficou '
                       'DESLIGADA (ela e 97x mais rapida e perde 55,5 pontos) e as linhas '
                       'caras foram para o fim da fila. '
                       '⚠️ 16/08: o motor.py e o equacao.py mudaram de md5 SEM mudar a '
                       'conta — os dois abriam JSON sem encoding e so nao quebravam por '
                       'causa do PYTHONUTF8 dos .bat. O dado lido e byte por byte o mesmo '
                       '(CAT_dom.json conferido: md5 do conteudo identico antes e depois). '
                       'A versao continua 6 porque a receita nao mudou; so a impressao '
                       'digital dos arquivos.',
        'arquivos': ['motor.py', 'roda_lote_v6.py', 'equacao.py', 'regua.py',
                     'funcao_nativa.py', 'dados/molde.json', 'HAB_EFEITOS_FINAL.json',
                     'tecnicos.json', 'habilidades_por_posicao.json',
                     'dados/raras_por_card.json', 'dados/falta_por_card.json',
                     'levelcap.json', 'CAT_dom.json'],
    },
    'bonus': {
        'versao': 1,
        'quando': '2026-08-15',
        'o_que_mudou': 'Nasceu. Os quatro bonus — corpo, pe ruim, estilo ligado e estilo '
                       'de jogo da IA — sairam de dentro da tela e viraram programa. '
                       'Provado em 884 cartas contra a conta antiga: zero divergencia. '
                       'Na mesma virada: a direcao do corpo foi corrigida (9 direcoes '
                       'estavam contra o dado), a punicao de estilo foi apagada e o teto '
                       'do estilo de IA caiu de 5 para 4.',
        'arquivos': ['motor_bonus.py', 'dados/insumos_bonus.json', 'dados/molde.json',
                     'pe_ruim.json'],
    },
}
MOLDE_VERSAO = 5

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

def le(u):
    r = urllib.request.Request(URL + '/rest/v1/' + u, headers=H)
    with urllib.request.urlopen(r, timeout=90) as f:
        return json.loads(f.read().decode('utf-8'))

def conta(u):
    """Quantas linhas existem — PERGUNTANDO, nao baixando e contando.

    ⛔ 16/08: a conferencia antiga baixava a tabela e fazia len(). O Supabase
       devolve no MAXIMO 1.000 linhas por leitura. Com o molde em 1.430 linhas
       (468 + 468 + 494) a conta parava em 1.000 e o programa dizia que a
       versao 5 tinha 64 linhas quando tinha 494. O banco estava certo; a
       conferencia e que tinha teto. Contar assim nao tem teto.
    """
    r = urllib.request.Request(URL + '/rest/v1/' + u,
                               headers=dict(H, Prefer='count=exact'), method='HEAD')
    with urllib.request.urlopen(r, timeout=90) as f:
        cr = f.headers.get('Content-Range') or ''
        return int(cr.split('/')[-1]) if '/' in cr else -1

def sobe(tabela, linhas, conflito, lote_tam=100):
    """Sobe e devolve (quantas eu mandei, quantas o SERVIDOR disse que gravou).

    ⛔ 16/08: antes esta funcao devolvia o que EU mandei, nao o que o banco
       aceitou. Resultado: o programa disse "494 subidas" e o banco tinha 0.
       Agora ela pede o retorno das linhas (return=representation) e conta
       o que voltou. O que volta e o que entrou de verdade.
    """
    mandei = gravou = 0
    for i in range(0, len(linhas), lote_tam):
        lote = linhas[i:i + lote_tam]
        u = URL + '/rest/v1/' + tabela + '?on_conflict=' + conflito
        d = json.dumps(lote, ensure_ascii=False).encode('utf-8')
        r = urllib.request.Request(u, data=d, headers=dict(
            H, Prefer='resolution=merge-duplicates,return=representation'), method='POST')
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                corpo = f.read().decode('utf-8', 'replace')
                try:
                    volta = json.loads(corpo)
                    g = len(volta) if isinstance(volta, list) else 0
                except Exception:
                    g = 0
                mandei += len(lote); gravou += g
                if g != len(lote):
                    P('      ⚠️ lote %d: mandei %d, o banco devolveu %d'
                      % (i // lote_tam + 1, len(lote), g))
                    if corpo[:200]:
                        P('         resposta: %s' % corpo[:200])
        except urllib.error.HTTPError as e:
            corpo = e.read().decode('utf-8', 'replace')
            P('      ⛔ lote %d: ERRO %s' % (i // lote_tam + 1, e.code))
            P('         %s' % corpo[:400])
            raise
    return mandei, gravou

def digital(caminho):
    """A impressao digital do arquivo. Le em pedaços para nao carregar 12 MB na memoria."""
    h = hashlib.md5()
    with open(caminho, 'rb') as f:
        for pedaco in iter(lambda: f.read(1 << 20), b''):
            h.update(pedaco)
    st = os.stat(caminho)
    return h.hexdigest(), st.st_size, datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()

P('=' * 74)
P('  AS VERSOES DO MOLDE E DOS MOTORES  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
if SO_CONFERIR:
    P('  MODO CONFERIR — nao escreve nada, so compara')
P('=' * 74)

# ============================================================================
# 1) A IMPRESSAO DIGITAL DE HOJE
# ============================================================================
P('')
P('1) A IMPRESSAO DIGITAL DOS ARQUIVOS DE HOJE')
hoje = {}
sumiu = []
for motor, m in MOTORES.items():
    for arq in m['arquivos']:
        cam = arq.replace('/', os.sep)
        if not os.path.exists(cam):
            sumiu.append((motor, arq))
            continue
        md5, tam, mt = digital(cam)
        hoje[(motor, arq)] = (md5, tam, mt)
        P('   %-11s %-32s %10s bytes  %s' % (motor, arq, '{:,}'.format(tam), md5[:12]))
if sumiu:
    P('')
    P('   ⛔ ESTES ARQUIVOS NAO EXISTEM NA PASTA:')
    for motor, arq in sumiu:
        P('      %s -> %s' % (motor, arq))
    P('   Sem eles a identidade do motor fica incompleta. Nada foi escrito.')
    sys.exit(1)

# ============================================================================
# MODO CONFERIR — para aqui
# ============================================================================
if SO_CONFERIR:
    P('')
    P('2) COMPARANDO COM O QUE ESTA GRAVADO NO BANCO')
    try:
        gravado = {(x['motor'], x['arquivo']): x for x in le('motor_arquivo?select=*')}
    except Exception as e:
        P('   ⛔ nao consegui ler a tabela motor_arquivo: %s' % e)
        P('   Ela existe? Rode antes o CRIAR-VERSOES-NO-SUPABASE.html')
        sys.exit(1)
    if not gravado:
        P('   a tabela esta vazia — nunca foi gravada. Rode sem o "conferir".')
        sys.exit(1)
    mudou, novo, igual = [], [], 0
    for k, (md5, tam, mt) in hoje.items():
        g = gravado.get(k)
        if not g:
            novo.append(k)
        elif g.get('md5') != md5:
            mudou.append((k, g.get('md5'), md5))
        else:
            igual += 1
    P('   iguais ......... %d' % igual)
    P('   MUDARAM ........ %d' % len(mudou))
    P('   nunca gravados . %d' % len(novo))
    for (motor, arq), antes, agora in mudou:
        P('')
        P('   ⚠️ %s · %s' % (motor, arq))
        P('      gravado: %s' % antes)
        P('      hoje:    %s' % agora)
    for motor, arq in novo:
        P('   ➕ %s · %s  (nunca foi gravado)' % (motor, arq))
    P('')
    if mudou:
        P('   ⛔ ALGUM ARQUIVO MUDOU desde a ultima gravacao.')
        P('      Rodar o motor assim PODE produzir pontuacao que nao bate com a do banco.')
        P('')
        P('      ⚠️ Esta trava compara md5. Ela NAO sabe a diferenca entre')
        P('         "mudou o arquivo" e "mudou a receita" — um comentario novo e')
        P('         uma formula nova dao o mesmo alarme. Quem sabe a diferenca e')
        P('         quem mexeu, e o lugar de escrever isso e o `o_que_mudou` da')
        P('         versao. Pendencia registrada em 16/08.')
        P('')
        P('      Ou grave a versao nova, ou volte os arquivos.')
        sys.exit(2)
    P('   ✅ nada mudou. Pode rodar o motor.')
    sys.exit(0)

# ============================================================================
# 2) O MOLDE INTEIRO — versao 5
# ============================================================================
P('')
P('2) O MOLDE — subindo a versao %d inteira' % MOLDE_VERSAO)
if not os.path.exists(os.path.join('dados', 'molde.json')):
    P('   ⛔ nao achei o dados/molde.json. Nada foi escrito.')
    sys.exit(1)
molde = json.load(open(os.path.join('dados', 'molde.json'), encoding='utf-8'))
funcoes_do_molde = sorted({r['funcao'] for r in molde})
P('   itens no arquivo ......... %d' % len(molde))
P('   funcoes no arquivo ....... %d' % len(funcoes_do_molde))

if len(funcoes_do_molde) != 19:
    P('   ⛔ o molde do arquivo tem %d funcoes, e o esperado sao 19.' % len(funcoes_do_molde))
    P('      Nada foi escrito. Confira o dados/molde.json antes.')
    sys.exit(1)

try:
    no_banco = {x['nome'] for x in le('funcoes?select=nome')}
except Exception as e:
    P('   ⛔ nao consegui ler a tabela funcoes: %s' % e); sys.exit(1)
orfas = [f for f in funcoes_do_molde if f not in no_banco]
if orfas:
    P('   ⛔ estas funcoes do molde NAO existem na tabela funcoes: %s' % ', '.join(orfas))
    P('      Subir assim quebraria a chave estrangeira. Nada foi escrito.')
    sys.exit(1)
P('   ✅ as 19 funcoes do molde existem na tabela funcoes')

try:
    vs = sorted({x['versao'] for x in le('molde_versao?select=versao')})
    P('   no banco ANTES ........... %s'
      % ' · '.join('v%d: %d' % (v, conta('molde?select=funcao&versao=eq.%d' % v)) for v in vs))
except Exception:
    pass

linhas = [{'funcao': r['funcao'], 'attr': r['attr'],
           'alvo': float(r['alvo']), 'peso': int(r['peso']),
           'versao': MOLDE_VERSAO} for r in molde]
try:
    mandei, gravou = sobe('molde', linhas, 'funcao,attr,versao')
    P('   mandei ................... %d linhas como versao %d' % (mandei, MOLDE_VERSAO))
    P('   o BANCO gravou ........... %d' % gravou)
    if gravou != mandei:
        P('')
        P('   ⛔ O banco aceitou menos do que eu mandei, e nao deu erro.')
        P('      Isso e trava de permissao na tabela `molde` (RLS), nao cache.')
        P('      A tabela molde tem a trava de seguranca LIGADA e a chave que o')
        P('      config.txt usa nao tem direito de INSERIR nela — so de ler e')
        P('      atualizar o que ja existe. Por isso as 19 funcoes (que ja')
        P('      existiam) foram atualizadas e as linhas novas do molde nao.')
        P('')
        P('      O CONSERTO, no SQL Editor do Supabase, uma linha:')
        P('         alter table molde disable row level security;')
        P('      (as outras tabelas de receita ja estao assim). Depois rode este')
        P('      .bat de novo.')
except urllib.error.HTTPError as e:
    P('   ⛔ ERRO %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]))
    sys.exit(1)

# ============================================================================
# 3) A IDENTIDADE DOS DOIS MOTORES
# ============================================================================
P('')
P('3) OS DOIS MOTORES')
linhas_v, linhas_a = [], []
for motor, m in MOTORES.items():
    linhas_v.append({'motor': motor, 'versao': m['versao'], 'quando': m['quando'],
                     'o_que_mudou': m['o_que_mudou'], 'vigente': True})
    for arq in m['arquivos']:
        md5, tam, mt = hoje[(motor, arq)]
        linhas_a.append({'motor': motor, 'versao': m['versao'], 'arquivo': arq,
                         'bytes': tam, 'md5': md5, 'modificado_em': mt})
try:
    _m, g1 = sobe('motor_versao', linhas_v, 'motor,versao')
    P('   motor_versao ............. mandei %d · o banco gravou %d' % (_m, g1))
    _m, g2 = sobe('motor_arquivo', linhas_a, 'motor,versao,arquivo')
    P('   motor_arquivo ............ mandei %d · o banco gravou %d' % (_m, g2))
except urllib.error.HTTPError as e:
    P('   ⛔ ERRO %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]))
    P('   As tabelas existem? Rode antes o CRIAR-VERSOES-NO-SUPABASE.html')
    sys.exit(1)

# ============================================================================
# 4) CONFERENCIA FINAL — relendo do banco
# ============================================================================
P('')
P('4) CONFERENCIA — lendo de volta')
# ⛔ 16/08: esta conferencia PARA o programa quando nao bate. Antes ela so imprimia.
falhou = []
try:
    vs = sorted({x['versao'] for x in le('molde_versao?select=versao')})
    P('   molde no banco ........... %s'
      % ' · '.join('v%d: %d' % (v, conta('molde?select=funcao&versao=eq.%d' % v)) for v in vs))
    n5 = conta('molde?select=funcao&versao=eq.%d' % MOLDE_VERSAO)
    f5 = len({x['funcao'] for x in le('molde?select=funcao&versao=eq.%d&limit=1000' % MOLDE_VERSAO)})
    if n5 != len(molde):
        falhou.append('a versao %d ficou com %d linhas e o arquivo tem %d'
                      % (MOLDE_VERSAO, n5, len(molde)))
    else:
        P('   ✅ a versao %d ficou com as %d linhas do arquivo, em %d funcoes'
          % (MOLDE_VERSAO, n5, f5))
except Exception as e:
    falhou.append('nao consegui contar a tabela molde: %s' % e)

try:
    nma = conta('motor_arquivo?select=motor')
    P('   impressoes digitais ...... %d' % nma)
    if nma != len(linhas_a):
        falhou.append('gravei %d impressoes digitais e o banco tem %d' % (len(linhas_a), nma))
except Exception as e:
    falhou.append('nao consegui contar a tabela motor_arquivo: %s' % e)

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
    P('  Se insistir: no painel do Supabase, Settings > API > "Reload schema cache".')
    P('=' * 74)
    sys.exit(1)

P('')
P('=' * 74)
P('  PRONTO E CONFERIDO. As versoes 2 e 3 do molde continuam onde estavam.')
P('  Para conferir antes de uma rodada:  SUBIR-VERSOES.bat conferir')
P('=' * 74)
