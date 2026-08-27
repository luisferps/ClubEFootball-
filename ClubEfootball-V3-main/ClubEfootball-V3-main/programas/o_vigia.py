# -*- coding: utf-8 -*-
r"""
O VIGIA — v3, 17/08/2026.  UM ARQUIVO. UM BOTAO.

Ordem do Luis, 17/08, depois de eu entregar quatro arquivos e tres botoes:

   "Eu quero um arquivo so. Aquele vigia la, ele tem que fazer isso ai tudo,
    ele tem que coletar tudo. Voce realmente acha que eu vou apertar esse tanto
    de botao? Eu vou apertar UM botao pra ele coletar."

Ele esta certo. Isto aqui faz tudo:

   1. abre o Chrome sozinho e manda nele
   2. le a lista de BOX do efHub (600, da mais recente para a mais velha)
   3. le as cartas de cada box
   4. descobre o que e box nova e o que e carta nova
   5. puxa a ficha inteira de cada carta, na ordem que o Luis mandou
   6. grava box_por_card.json e efhub_fichas.json
   7. diz o que fazer depois

⛔ POR QUE ELE PRECISA ABRIR O CHROME — e nao e frescura
   MEDIDO em 17/08 na maquina do Luis: o efHub devolve 403 para o Python
   (urllib), e devolve 200 para o mesmo endereco dentro do Chrome. Nao e login
   — e o site recusando quem nao parece navegador.
   Entao o vigia sobe um Chrome com a porta de comando aberta, manda o
   JavaScript para dentro dele, e recebe o resultado de volta. Nenhum passo
   fica para o Luis.

⛔ POR QUE A LISTA DE BOX, E NAO O INDICE
   MEDIDO: o indice tem 46.862 cartas em 1.953 paginas. A lista de box tem 600
   entradas, ja vem da mais recente para a mais velha, e cada box entrega os
   numeros das cartas dela de uma vez. Box nova aparece na PRIMEIRA pagina.
   Varrer 1.953 paginas para achar 11 cartas e trabalho jogado fora.

⛔ A ORDEM DA FILA — ordem do Luis, 17/08
      1. A BOX NOVA ........... carta que nao existe aqui. Prioridade sempre.
      2. O QUE FALTA REFAZER .. carta nossa com furo que o efHub responde.
                                A lista sai do dados/fila_de_coleta.json.
      3. O RESTANTE ........... por overall, o maior primeiro.

⛔ A DATA DO efHUB NAO E A DATA DE LANCAMENTO
   MEDIDO: as datas das box sao 13/08, 06/08, 30/07, 23/07... de sete em sete
   dias. E a coleta SEMANAL do efHub. A box "Summer Transfer 17 Aug '26" vem
   carimbada 13/08. Entao ela NAO entra no `dt`. A data de lancamento sai do
   NOME da box, no separar_a_data_do_box.py.

⛔ O QUE ELE NAO FAZ
   Nao fala com o banco para escrever. Nao apaga nada. Nao sobrescreve box boa.
   Faz backup antes de gravar.
"""
import base64, hashlib, json, os, re, shutil, socket, struct, subprocess
import sys, tempfile, time, urllib.request, urllib.error
from datetime import datetime

# ⛔ 18/08 — A REGRA DA BOX MORA EM ClubEfootball\programas\regras_do_card.py,
#    E SO LA. "Esse e o problema de ter tanto arquivo" (Luis, 18/08). Este
#    programa NAO tem copia da resposta para "isto e box?" — ele pergunta.
#    ⛔ E mora no ClubEfootball, nao na raiz: a raiz e legado e vai deixar de
#       existir. Coisa nova vai no ClubEfootball (regra do Luis, 17/08).
import sys as _sys, os as _os
_AQUI = _os.path.dirname(_os.path.abspath(__file__))
for _d in (_AQUI,
           _os.path.join(_os.getcwd(), 'ClubEfootball', 'programas'),
           _os.path.join(_os.path.dirname(_AQUI), 'programas'),
           _os.path.join(_AQUI, 'ClubEfootball', 'programas')):
    if _os.path.isdir(_d) and _d not in _sys.path:
        _sys.path.insert(0, _d)
import regras_do_card as REGRA


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

L = []


def P(msg=''):
    s = str(msg)
    L.append(s)
    try:
        print(s, flush=True)
    except Exception:
        pass


def fim(codigo=0):
    try:
        open('RELATORIO-DO-VIGIA.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    except Exception:
        pass
    sys.exit(codigo)


SO_OLHAR = '--conferir' in [a.lower() for a in sys.argv]
SO_AS_NOVAS = '--so-as-novas' in [a.lower() for a in sys.argv]

FICHAS = 'efhub_fichas.json'
ARQ_BOX = 'box_por_card.json'
FILA_DE_COLETA = os.path.join('dados', 'fila_de_coleta.json')
FLAG = 'VIGIA-ACHOU-NOVAS.txt'
PERFIL = os.path.join('dados', 'chrome_do_vigia')
PORTA = 9722

# ⛔ DECLARADO, nao medido — e eu preciso dizer isso.
#    O "~2.100 fichas por dia" que eu ja escrevi em outros arquivos eu NUNCA
#    medi. O que esta medido e so: sem pausa entre os pedidos, o site fecha.
# ============================================================================
#  ⛔ 18/08 — O TETO POR CARTA ACABOU. O LIMITE AGORA E O RELOGIO.
# ============================================================================
#  Pergunta do Luis: "por que que a gente vai levantar so esse tanto por dia,
#  sendo que a gente ja puxou mais de cem mil desses lugares? Por que nao
#  coloca pra ficar rodando constantemente, ate zerar?"
#
#  Ele esta certo, e a conta prova. Com a pausa de 350 ms:
#      2.347 cartas da pilha 2  =  ~14 minutos
#      5.370 (pilha 1 + 2)      =  ~31 minutos
#  O teto de 400 nao protegia de nada — so espalhava um servico de meia hora
#  por quinze dias. E o 429 nunca foi volume: o script do Luis puxou 44.862
#  cards com pausa MENOR que esta. O que segurava era desistir na primeira
#  recusa, e isso ja esta consertado no bloco das fichas.
#
#  Entao o limite deixa de ser "quantas cartas" e passa a ser "quanto tempo".
#  Ele puxa ate a fila acabar ou o relogio fechar — o que vier primeiro.
#  ⚠️ Se voltar a falhar muito, o numero a mexer e a PAUSA, nao o tempo.
TETO_DE_FICHAS = 0        # 0 = sem teto por carta. A fila inteira, se der tempo.
MINUTOS_DE_COLETA = 120   # o unico freio: 2 horas. A rodada da 4 (ver rodada_diaria)
PAUSA_MS = 350


# ============================================================================
#  FALAR COM O CHROME — websocket minimo, so com a biblioteca padrao
# ============================================================================
class Soquete(object):
    """O menor cliente de websocket que resolve: aperto de mao, mandar texto,
       receber texto. Sem biblioteca de fora — a maquina do Luis nao instala
       nada, e nao ha terminal para consertar se a instalacao falhar."""

    def __init__(self, url, timeout=180):
        m = re.match(r'ws://([^:/]+):(\d+)(/.*)$', url)
        if not m:
            raise IOError('endereco de websocket estranho: %s' % url)
        host, porta, caminho = m.group(1), int(m.group(2)), m.group(3)
        self.s = socket.create_connection((host, porta), timeout=20)
        self.s.settimeout(timeout)
        chave = base64.b64encode(os.urandom(16)).decode()
        pedido = (
            'GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n'
            'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
            'Sec-WebSocket-Version: 13\r\n\r\n' % (caminho, host, porta, chave))
        self.s.sendall(pedido.encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            p = self.s.recv(4096)
            if not p:
                raise IOError('o Chrome fechou durante o aperto de mao')
            buf += p
        if b'101' not in buf.split(b'\r\n')[0]:
            raise IOError('o Chrome recusou o websocket: %s' % buf[:80])
        esperado = base64.b64encode(hashlib.sha1(
            (chave + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        if esperado.lower().encode() not in buf.lower():
            raise IOError('aperto de mao do websocket nao conferiu')
        self.resto = buf.split(b'\r\n\r\n', 1)[1]

    def _le(self, n):
        while len(self.resto) < n:
            p = self.s.recv(65536)
            if not p:
                raise IOError('o Chrome fechou a conexao')
            self.resto += p
        fora, self.resto = self.resto[:n], self.resto[n:]
        return fora

    def manda(self, texto):
        dados = texto.encode('utf-8')
        cab = bytearray([0x81])
        n = len(dados)
        if n < 126:
            cab.append(0x80 | n)
        elif n < 65536:
            cab.append(0x80 | 126)
            cab += struct.pack('>H', n)
        else:
            cab.append(0x80 | 127)
            cab += struct.pack('>Q', n)
        mask = os.urandom(4)
        cab += mask
        self.s.sendall(bytes(cab) + bytes(b ^ mask[i % 4] for i, b in enumerate(dados)))

    def recebe(self):
        while True:
            b0, b1 = self._le(2)
            op = b0 & 0x0F
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack('>H', self._le(2))[0]
            elif n == 127:
                n = struct.unpack('>Q', self._le(8))[0]
            corpo = self._le(n)
            if op == 8:
                raise IOError('o Chrome fechou o canal')
            if op in (9, 10):
                continue
            return corpo.decode('utf-8', 'replace')

    def fecha(self):
        try:
            self.s.close()
        except Exception:
            pass


def acha_o_chrome():
    nomes = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        os.path.join(os.environ.get('LOCALAPPDATA', ''),
                     r'Google\Chrome\Application\chrome.exe'),
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    ]
    for n in nomes:
        if n and os.path.exists(n):
            return n
    for n in ('google-chrome', 'chromium', 'chromium-browser'):
        c = shutil.which(n)
        if c:
            return c
    return None


class Chrome(object):
    def __init__(self):
        self.proc = None
        self.ws = None
        self.n = 0

    def abre(self):
        exe = acha_o_chrome()
        if not exe:
            raise IOError('nao achei o Chrome nem o Edge instalados')
        os.makedirs(PERFIL, exist_ok=True)
        self.proc = subprocess.Popen(
            [exe, '--remote-debugging-port=%d' % PORTA,
             '--user-data-dir=' + os.path.abspath(PERFIL),
             '--no-first-run', '--no-default-browser-check',
             '--disable-popup-blocking', '--window-size=1100,800',
             'https://efhub.com/pt-BR'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        alvo = None
        for _ in range(60):
            time.sleep(1)
            try:
                with urllib.request.urlopen(
                        'http://127.0.0.1:%d/json/list' % PORTA, timeout=4) as r:
                    abas = json.loads(r.read().decode('utf-8', 'replace'))
                for a in abas:
                    if a.get('type') == 'page' and 'efhub.com' in (a.get('url') or ''):
                        alvo = a
                        break
                if alvo:
                    break
            except Exception:
                pass
        if not alvo:
            raise IOError('o Chrome abriu mas nao chegou no efhub.com')
        self.ws = Soquete(alvo['webSocketDebuggerUrl'])
        return exe

    def roda(self, js, segundos=600):
        self.n += 1
        eu = self.n
        # ⛔ 18/08 — ENDERECO INTEIRO, NUNCA RELATIVO.
        #    A rodada de 17/08 22:21 morreu aqui, no primeiro fetch:
        #      "Failed to execute 'fetch' on 'Window': Failed to parse URL from /a..."
        #    O `fetch('/api/...')` so funciona se o documento da aba tiver um
        #    endereco de base valido. Quando o Chrome abre e a pagina do efHub
        #    ainda nao assentou, o contexto e uma pagina em branco — e ai o
        #    caminho relativo nao tem de onde pendurar. Endereco inteiro nao
        #    depende de onde a aba esta.
        #    ⚠️ `var`, nao `const`: cada chamada e um script novo no MESMO
        #    contexto, e `const` repetido estoura "already been declared".
        js = "var EFHUB='https://efhub.com';\n" + js
        # ⛔ 17/08: O CANAL TEM QUE ESPERAR MAIS QUE A TAREFA.
        #    O soquete estava com 180s fixos e a leitura das 600 box leva ~240s.
        #    Deu "timed out" e o vigia parou achando que o Chrome tinha morrido —
        #    quando ele estava trabalhando direitinho. O limite de quem espera
        #    nunca pode ser menor que o de quem trabalha.
        try:
            self.ws.s.settimeout(segundos + 120)
        except Exception:
            pass
        self.ws.manda(json.dumps({
            'id': eu, 'method': 'Runtime.evaluate',
            'params': {'expression': js, 'awaitPromise': True,
                       'returnByValue': True, 'timeout': segundos * 1000}}))
        while True:
            msg = json.loads(self.ws.recebe())
            if msg.get('id') != eu:
                continue
            if 'error' in msg:
                raise IOError('o Chrome recusou: %s' % str(msg['error'])[:160])
            r = msg.get('result') or {}
            if r.get('exceptionDetails'):
                raise IOError('erro dentro da pagina: %s'
                              % str(r['exceptionDetails'])[:200])
            return (r.get('result') or {}).get('value')

    def fecha(self):
        try:
            if self.ws:
                self.ws.fecha()
        except Exception:
            pass
        try:
            if self.proc:
                self.proc.terminate()
        except Exception:
            pass


# ============================================================================
P('=' * 76)
P('  O VIGIA  ·  v3  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 76)
P('')
P('  UM arquivo, UM botao. Ele abre o Chrome sozinho e manda nele.')
P('')
P('  A ORDEM DA FILA — ordem do Luis, 17/08:')
P('     1. A BOX NOVA ............ carta que nao existe aqui')
P('     2. O QUE FALTA REFAZER ... carta nossa com furo que o efHub responde')
P('     3. O RESTANTE ............ por overall, o maior primeiro')
if SO_OLHAR:
    P('')
    P('  ⚠️ MODO CONFERIR: nada vai ser gravado.')

# --------------------------------------------- 1) o que ja temos
P('')
P('lendo o que a gente ja tem...')
temos_carta = set()
try:
    _b = json.load(open(os.path.join('dados', 'base_unica.json'), encoding='utf-8'))
    _b = _b.get('cards') if isinstance(_b, dict) else _b
    for c in (_b or []):
        i = str(c.get('id') or '').split('@')[0]
        if i:
            temos_carta.add(i)
except Exception as e:
    P('  ⛔ PAREI: nao consegui ler a base (%s).' % str(e)[:70])
    P('     Sem ela, TODA carta pareceria nova e eu sairia puxando o mundo.')
    fim(1)

B = {}
if os.path.exists(ARQ_BOX):
    try:
        B = json.load(open(ARQ_BOX, encoding='utf-8'))
    except Exception:
        B = {}
nossas_box = {str(v.get('box')) for v in B.values()
              if isinstance(v, dict) and v.get('box')}


def norm(s):
    return ' '.join(str(s or '').replace('\u2122', '').split()).strip().lower()


nossas_norm = {norm(x) for x in nossas_box}
P('  cartas na base ........ %s' % '{:,}'.format(len(temos_carta)))
P('  box que ja temos ...... %s' % '{:,}'.format(len(nossas_box)))

PRECISA_REFAZER = set()
try:
    F = json.load(open(FILA_DE_COLETA, encoding='utf-8'))
    for campo, v in (F.get('por_campo') or {}).items():
        if (v.get('quem_perguntar') or [None])[0] != 'efhub':
            continue
        for cid in (v.get('cartas_a_perguntar') or []):
            PRECISA_REFAZER.add(str(cid).split('@')[0])
    P('  com furo do efHub ..... %s  (a lista sai da fila de coleta)'
      % '{:,}'.format(len(PRECISA_REFAZER)))

    # ⛔ 18/08 — AS RESPOSTAS SUSPEITAS ENTRAM NA FILA TAMBEM.
    #    Ordem do Luis: "eles nao colocam a evolucao da carta na primeira vez.
    #    A gente ve 1/1, acha que e carta sem evolucao, fecha a questao e nunca
    #    mais olha. Dia seguinte eles atualizam e a gente fica defasado."
    #    Estas cartas TEM resposta — por isso nunca voltavam. Resposta errada
    #    parece resposta boa. Elas entram na PILHA 2 junto com os furos.
    _susp = F.get('respostas_suspeitas') or []
    if _susp:
        for x in _susp:
            c = str(x.get('card') or '').split('@')[0]
            if c:
                PRECISA_REFAZER.add(c)
        P('  respostas SUSPEITAS ... %s  (nivel 0 ou 1 em carta de box recente)'
          % '{:,}'.format(len(_susp)))
        for x in sorted(_susp, key=lambda y: -(y.get('ovr') or 0))[:5]:
            P('       %-24s ovr %s' % (str(x.get('nome'))[:24], x.get('ovr')))
except Exception:
    P('  sem a fila de coleta — a pilha 2 fica vazia.')

# --------------------------------------------- 2) abrir o Chrome
P('')
P('abrindo o Chrome...')
P('  ⚠️ vai aparecer uma janela do Chrome. NAO FECHE ela enquanto ele trabalha.')
ch = Chrome()
try:
    exe = ch.abre()
    P('  aberto .............. %s' % os.path.basename(exe))
    P('  perfil proprio ...... %s  (nao mexe no seu Chrome do dia a dia)' % PERFIL)
except Exception as e:
    P('')
    P('  ⛔ PAREI: %s' % str(e)[:150])
    P('')
    P('  O caminho de emergencia, na mao, e o Console do Chrome:')
    P('     ClubEfootball\\COLETAR-AS-BOX-NO-EFHUB.html')
    ch.fecha()
    fim(1)

try:
    # ⛔ 18/08 — dizer ONDE a aba esta antes de bater na porta. Sem isto, o erro
    #    do fetch nao conta se o problema foi a rede, o login ou a aba errada.
    _onde = ch.roda("(''+location.href)")
    P('  a aba esta em ....... %s' % str(_onde)[:70])
except Exception:
    P('  a aba esta em ....... (nao consegui perguntar)')

try:
    porta_ok = ch.roda(
        "(async()=>{const r=await fetch(EFHUB+'/api/public/packs?page=1',"
        "{credentials:'include'});const j=await r.json();"
        "return JSON.stringify({s:r.status,n:(j.packs||[]).length});})()")
    P('  a porta do efHub .... %s' % porta_ok)
except Exception as e:
    P('  ⛔ PAREI: %s' % str(e)[:150])
    ch.fecha()
    fim(1)

# --------------------------------------------- 3) as box
P('')
P('lendo a lista de box...')
JS_LISTA = r"""(async()=>{
 const packs=[]; let pg=1;
 while(pg<=80){
  const r=await fetch(EFHUB+'/api/public/packs?page='+pg,{credentials:'include'});
  if(!r.ok) break;
  const j=await r.json(); const p=j.packs||[];
  if(!p.length) break;
  packs.push(...p);
  if(!j.hasMore) break;
  pg++;
 }
 return JSON.stringify(packs.map(p=>[p.slug,p.name,p.playerCount,p.date]));
})()"""
try:
    LISTA = json.loads(ch.roda(JS_LISTA, segundos=300))
except Exception as e:
    P('  ⛔ PAREI na lista de box: %s' % str(e)[:150])
    ch.fecha()
    fim(1)
P('  box na lista ........ %s' % '{:,}'.format(len(LISTA)))

# ⛔ EM LEVAS, E NAO DE UMA VEZ SO. Duas razoes, as duas medidas hoje:
#    1. de uma vez so a tela fica 4 minutos parada e parece travada;
#    2. uma leva que falha derruba so ela, nao a coleta inteira.
P('  lendo as cartas de cada box, em levas de 50...')
JS_CARTAS = r"""(async()=>{
 const L=__LEVA__; const out={}; let erros=0;
 for(const p of L){
  try{
   const r=await fetch(EFHUB+'/pt-BR/packs/'+p[0],{credentials:'include'});
   const h=await r.text();
   out[p[0]]={nome:p[1], quantas:p[2], datapack:p[3],
     cartas:[...new Set([...h.matchAll(/player_cards\/(\d+)_/g)].map(m=>m[1]))]};
  }catch(e){ erros++; out[p[0]]={nome:p[1], quantas:p[2], datapack:p[3],
     cartas:[], erro:String(e).slice(0,60)}; }
  await new Promise(s=>setTimeout(s,__PAUSA__));
 }
 return JSON.stringify({box:out, erros:erros});
})()"""
CAIXAS, erros_box = {}, 0
LEVA = 50
for k in range(0, len(LISTA), LEVA):
    parte = LISTA[k:k + LEVA]
    try:
        r = json.loads(ch.roda(JS_CARTAS.replace('__LEVA__', json.dumps(parte))
                               .replace('__PAUSA__', str(PAUSA_MS)), segundos=300))
        CAIXAS.update(r.get('box') or {})
        erros_box += r.get('erros') or 0
    except Exception as e:
        P('     a leva a partir da %d nao veio (%s)' % (k, str(e)[:60]))
    P('     %s de %s box' % ('{:,}'.format(len(CAIXAS)), '{:,}'.format(len(LISTA))))

if not CAIXAS:
    P('  ⛔ PAREI: nenhuma box veio.')
    ch.fecha()
    fim(1)
P('  box lidas ........... %s' % '{:,}'.format(len(CAIXAS)))
if erros_box:
    P('  box com erro ........ %s' % erros_box)

# --------------------------------------------- 4) as tres pilhas
box_novas, pilha1, pilha2, pilha3 = [], [], [], []
de_qual_box = {}
for slug, d in CAIXAS.items():
    nome = d.get('nome')
    if norm(nome) not in nossas_norm:
        box_novas.append((d.get('datapack'), nome, len(d.get('cartas') or []), slug))
    for cid in (d.get('cartas') or []):
        cid = str(cid)
        de_qual_box.setdefault(cid, nome)
        if cid not in temos_carta:
            pilha1.append(cid)
        elif cid in PRECISA_REFAZER:
            pilha2.append(cid)
        else:
            pilha3.append(cid)

# tira repetido guardando a ordem (a mesma carta pode estar em duas box)
def enxuga(lista, ja):
    fora = []
    for c in lista:
        if c not in ja:
            ja.add(c)
            fora.append(c)
    return fora


ja = set()
pilha1 = enxuga(pilha1, ja)
pilha2 = enxuga(pilha2, ja)
pilha3 = enxuga(pilha3, ja)

P('')
P('-' * 76)
P('  AS TRES PILHAS')
P('-' * 76)
P('     1. A BOX NOVA ............ %s cartas' % '{:,}'.format(len(pilha1)))
P('     2. O QUE FALTA REFAZER ... %s cartas' % '{:,}'.format(len(pilha2)))
P('     3. O RESTANTE ............ %s cartas' % '{:,}'.format(len(pilha3)))

P('')
P('  AS BOX QUE O efHUB TEM E NOS NAO')
if not box_novas:
    P('     nenhuma.')
else:
    box_novas.sort(reverse=True)
    for data, nome, n, slug in box_novas[:30]:
        P('     %-12s %-46s %3d cartas' % (data, str(nome)[:46], n))
    if len(box_novas) > 30:
        P('     ... e mais %d' % (len(box_novas) - 30))

if pilha1:
    P('')
    P('  AS CARTAS QUE A BASE NAO TEM')
    for cid in pilha1[:40]:
        P('     %-16s  %s' % (cid, str(de_qual_box.get(cid))[:52]))
    if len(pilha1) > 40:
        P('     ... e mais %d' % (len(pilha1) - 40))

# ============================================================================
#  ⛔ 18/08 — A PILHA 2 NUNCA TINHA VEZ. E ela e a que o Luis pediu.
# ============================================================================
#  O QUE ACONTECIA: a fila era pilha1 + pilha2 + pilha3, cortada no teto.
#  Na rodada de 17/08 23:29 a pilha1 (box nova) tinha 3.023 cartas e o teto era
#  400. Ou seja: as 400 sairam TODAS da pilha1, e as 2.347 cartas que a gente
#  passou o dia identificando — as que estao sem estilo da IA e sem pe ruim —
#  nao foram perguntadas nenhuma vez.
#
#  Ordem do Luis, 18/08: "a gente passou um tempao falando 'vamos pegar de novo
#  os dados dessa carta, dessa e dessa'. Contamos tudo. Ai voce vem falar que
#  nao valeu de nada porque em vez de solicitar dessas cartas a gente solicitou
#  de outras. Tem que puxar as corretas, as que a gente verificou."
#
#  AGORA CADA PILHA TEM COTA GARANTIDA. Nenhuma come a vez da outra, e o que
#  sobrar de uma cota vai para as outras — cota nao vira desperdicio.
COTA = [
    ('1. box nova',        pilha1, 0.30),   # carta que a base nao tem
    ('2. furo conhecido',  pilha2, 0.55),   # <- a que o Luis mandou buscar
    ('3. o restante',      pilha3, 0.15),
]

_TETO = TETO_DE_FICHAS or (len(pilha1) + len(pilha2) + len(pilha3))

if SO_AS_NOVAS:
    fila = pilha1[:_TETO]
else:
    fila, sobra = [], 0
    escolhido = []
    for _rot, _p, _pct in COTA:
        _cota = int(_TETO * _pct)
        _pega = _p[:_cota]
        escolhido.append((_rot, len(_pega), _cota, len(_p)))
        fila.extend(_pega)
        sobra += _cota - len(_pega)
    # ⛔ a cota que sobrou nao se perde: volta para quem ainda tem fila
    if sobra > 0:
        for _rot, _p, _pct in COTA:
            if sobra <= 0:
                break
            _ja = set(fila)
            _mais = [x for x in _p if x not in _ja][:sobra]
            fila.extend(_mais)
            sobra -= len(_mais)
    fila = fila[:_TETO]

    P('')
    P('  A COTA DE CADA PILHA — nenhuma come a vez da outra')
    for _rot, _n, _cota, _tot in escolhido:
        P('     %-20s %4d de %4d na cota   (a pilha tem %s)'
          % (_rot, _n, _cota, '{:,}'.format(_tot)))
    P('     %d cartas nesta rodada' % len(fila))

# --------------------------------------------- 5) as fichas
fichas, falhou = {}, []
if fila and not SO_OLHAR:
    P('')
    P('puxando a ficha inteira, na ordem das pilhas...')
    P('  a fila desta rodada .. %d cartas' % len(fila))
    P('  o freio e o relogio .. %d minutos' % MINUTOS_DE_COLETA)
    # ========================================================================
    #  ⛔ 18/08 — O 429 NAO E RECUSA. E "ESPERA UM POUCO".
    # ========================================================================
    #  O QUE ESTAVA ERRADO: este bloco desistia no primeiro 429 e jogava a
    #  carta na lista de falhas. Medido na rodada de 17/08 23:29:
    #        pedidas 400 · vieram 192 · falharam 208, TODAS com HTTP429
    #  Metade do trabalho jogada fora por pressa.
    #
    #  O QUE O LUIS JA TINHA PROVADO: o script do
    #  COLETAR-EFHUB-PELO-CONSOLE.md puxou 44.862 cards em 1.870 paginas com
    #  uma pausa MENOR (260 ms). O que ele fazia de diferente nao era ir
    #  devagar — era NAO DESISTIR:
    #      429 -> dorme, DOBRA a espera (400ms ate 8s), tenta de novo, ate 5x
    #      e no fim volta ate 8 vezes em cima do que ainda faltou
    #
    #  E o mesmo desenho aqui. A pausa continua igual; o que muda e que a
    #  carta so vira falha depois de 5 tentativas com espera crescente.
    JS_FICHA = r"""(async()=>{
 const IDS=__IDS__, PAUSA=__PAUSA__; const ok={}, ruim=[];
 const dorme = ms => new Promise(r => setTimeout(r, ms));
 for(const id of IDS){
  let espera = 500, pegou = false;
  for(let t = 0; t < 5 && !pegou; t++){
   try{
    const r = await fetch(EFHUB+'/api/public/players/'+id,{credentials:'include'});
    if(r.status === 429){ await dorme(espera); espera = Math.min(espera*2, 8000); continue; }
    if(r.ok){ const j = await r.json(); ok[id] = (j&&j.player)?j.player:j; pegou = true; }
    else { ruim.push(id+' HTTP'+r.status); pegou = true; }
   }catch(e){ await dorme(espera); espera = Math.min(espera*2, 8000); }
  }
  if(!pegou) ruim.push(id+' HTTP429');
  await dorme(PAUSA);
 }
 return JSON.stringify({ok:ok, ruim:ruim});
})()"""
    passo = 100
    # ⛔ ATE 4 VOLTAS em cima do que faltou, como o script das 44.862 cards.
    #    Cada volta pede so o que ainda nao veio, e com o site ja mais calmo.
    a_pedir = list(fila)
    _t0_coleta = time.time()
    _antes_da_leva = len(fichas)
    _secas = 0
    for volta in range(1, 5):
        if not a_pedir:
            break
        if volta > 1:
            P('')
            P('  volta %d — faltam %d cartas' % (volta, len(a_pedir)))
            time.sleep(20)          # o site respira antes da proxima leva
        nesta = []
        for k in range(0, len(a_pedir), passo):
            # ⛔ O RELOGIO. Ele para entre levas, nunca no meio de uma — assim
            #    nenhuma ficha ja pedida se perde. O que nao deu tempo volta
            #    amanha, e amanha ele comeca por elas.
            if (time.time() - _t0_coleta) > MINUTOS_DE_COLETA * 60:
                P('')
                P('  ⏱ fecharam os %d minutos. Parei com %d fichas na mao.'
                  % (MINUTOS_DE_COLETA, len(fichas)))
                P('     O que faltou volta na proxima rodada, na frente.')
                a_pedir = []
                nesta = []
                break
            parte = a_pedir[k:k + passo]
            try:
                bruto = ch.roda(JS_FICHA.replace('__IDS__', json.dumps(parte))
                                .replace('__PAUSA__', str(PAUSA_MS)), segundos=1800)
                r = json.loads(bruto)
                fichas.update(r.get('ok') or {})
                for x in (r.get('ruim') or []):
                    _id = str(x).split(' ')[0]
                    if 'HTTP429' in str(x):
                        nesta.append(_id)       # 429 volta na proxima volta
                    else:
                        falhou.append(x)        # 404 e afins: nao adianta insistir
            except Exception as e:
                P('  a leva a partir da %d nao veio (%s)' % (k, str(e)[:70]))
                nesta.extend(parte)
            P('  %d fichas ate agora (volta %d)' % (len(fichas), volta))

            # ⛔ 18/08 (noite) — DUAS TRAVAS QUE FALTAVAM. O Luis, olhando a
            #    janela: "ta travado". Nao estava: o efHub tinha batido a cota
            #    do dia e devolvia 429 em tudo. Medido nesta rodada: 2.721
            #    fichas e depois 14 levas seguidas (1.400 cartas) sem UMA ficha
            #    nova, com o relogio de 120 minutos ainda correndo.
            #
            #    1. SALVA NO CAMINHO. As fichas so eram gravadas no fim; fechar
            #       a janela perdia as 2.721. Agora cada leva grava.
            if len(fichas) != _antes_da_leva:
                _antes_da_leva = len(fichas)
                _secas = 0
                try:
                    json.dump({'o_que_e': 'fichas cruas do efHub colhidas pelo vigia '
                                          '(PARCIAL — gravado a cada leva)',
                               'colhido_em': datetime.now().isoformat(timespec='seconds'),
                               'pedidas': len(fila), 'fichas': fichas},
                              open(FICHAS + '.PARCIAL', 'w', encoding='utf-8'),
                              ensure_ascii=False)
                except Exception:
                    pass
            else:
                #    2. PORTA FECHADA E PORTA FECHADA. Tres levas seguidas sem
                #       nenhuma ficha nova = a cota do dia acabou. Insistir so
                #       gasta o relogio; o que faltou volta amanha, na frente.
                _secas += 1
                if _secas >= 3:
                    P('')
                    P('  ⛔ %d levas seguidas sem uma ficha nova — a cota do efHub '
                      'acabou por hoje.' % _secas)
                    P('     Parei com %d fichas. O resto volta na proxima rodada, '
                      'na frente da fila.' % len(fichas))
                    a_pedir = []
                    nesta = []
                    break
        a_pedir = [x for x in nesta if x not in fichas]
    if a_pedir:
        falhou.extend(x + ' HTTP429' for x in a_pedir)
    P('  fichas que vieram ... %d de %d' % (len(fichas), len(fila)))
    if falhou:
        P('  NAO vieram .......... %d' % len(falhou))
        for x in falhou[:8]:
            P('     %s' % x)

# ============================================================================
#  A SEGUNDA FONTE — o efootbase, no mesmo Chrome
# ============================================================================
#  ⛔ ELE NAO E O EFHUB DE NOVO. A precedencia declarada no fila_de_coleta.py
#     poe o efootbase NA FRENTE do efHub no impeto e no `nm`:
#        impeto ..... efootbase -> efhub -> efscout -> jogo
#        nm ......... efootbase -> efscout -> jogo
#     Ate hoje ele so andava com o Luis colando um bloco no Console. Agora que
#     o vigia dirige o Chrome, ele anda sozinho.
#
#  ⛔ ELE GUARDA O PROGRESSO NO PROPRIO NAVEGADOR (localStorage EFB_COLETA_v1)
#     e o perfil do vigia e fixo — entao rodar de novo CONTINUA de onde parou.
#     Nao ha coleta perdida por a rodada ter acabado no meio.
JS_EFB = 'COLETAR-EFOOTBASE.js'
efb_trouxe = 0
if not SO_OLHAR and not SO_AS_NOVAS and os.path.exists(JS_EFB):
    P('')
    P('-' * 76)
    P('  A SEGUNDA FONTE — o efootbase')
    P('-' * 76)
    P('  a precedencia poe ele NA FRENTE do efHub no impeto e no nome do impeto')
    try:
        script = open(JS_EFB, encoding='utf-8').read()
        P('  o bloco tem ......... %s KB' % '{:,}'.format(len(script) // 1024))
        ch.roda("(async()=>{location.href='https://efootbase.com/pt-BR/players';"
                "return 1;})()", segundos=30)
        for _ in range(40):
            time.sleep(1)
            try:
                onde = ch.roda('location.host')
                if onde and 'efootbase' in str(onde):
                    break
            except Exception:
                pass
        P('  estou em ............ %s' % ch.roda('location.host'))
        antes_estado = ch.roda(
            "(()=>{try{const s=JSON.parse(localStorage.getItem('EFB_COLETA_v1'));"
            "return s?Object.keys(s.fichas||{}).length:0;}catch(e){return 0;}})()")
        P('  ja tinha colhido .... %s fichas (do proprio navegador)'
          % '{:,}'.format(int(antes_estado or 0)))

        # ================================================================
        #  ⛔ O PROGRESSO NAO PODE MORAR SO NO NAVEGADOR
        # ================================================================
        #  ORDEM DO LUIS, 18/08:
        #    "Nao pode ser assim nao, porque o computador corre o risco de
        #     ficar sem energia, falta energia, desliga, e nos vamos perder o
        #     servico todo. O navegador tambem pode fechar acidentalmente."
        #
        #  Ele esta certo e o desenho estava errado. A fase 2 do efootbase sao
        #  2.785 fichas a ~4s cada — quase 3 horas, ou seja 3 a 4 rodadas. Tudo
        #  isso vivia no localStorage do Chrome do vigia e so ia para o disco no
        #  FIM da perna. Queda de luz no meio = dias de coleta perdidos.
        #
        #  Agora sao duas travas:
        #    1. ELE VOLTA DO DISCO. Se o navegador estiver vazio (perfil novo,
        #       Chrome limpo, disco do perfil corrompido) e existir o
        #       efootbase_PROGRESSO.json, o estado e reposto ANTES de comecar.
        #    2. ELE SALVA ENQUANTO ANDA, de 2 em 2 minutos (ver o laco abaixo),
        #       e nao so no fim.
        ARQ_PROG = 'efootbase_PROGRESSO.json'
        if not int(antes_estado or 0) and os.path.exists(ARQ_PROG):
            try:
                _bruto = open(ARQ_PROG, encoding='utf-8').read()
                _mb = len(_bruto) / 1024.0 / 1024.0
                P('  o navegador esta vazio, mas o disco tem %s (%.1f MB).' % (ARQ_PROG, _mb))
                # em pedacos: string grande de uma vez estoura o canal do Chrome
                ch.roda("window.__EFBTMP=''", segundos=30)
                _passo = 400000
                for _k in range(0, len(_bruto), _passo):
                    _p = json.dumps(_bruto[_k:_k + _passo])
                    ch.roda('window.__EFBTMP += %s; 1' % _p, segundos=120)
                _ok = ch.roda("(()=>{try{JSON.parse(window.__EFBTMP);"
                              "localStorage.setItem('EFB_COLETA_v1', window.__EFBTMP);"
                              "delete window.__EFBTMP;"
                              "const s=JSON.parse(localStorage.getItem('EFB_COLETA_v1'));"
                              "return Object.keys(s.fichas||{}).length;}"
                              "catch(e){return -1;}})()", segundos=120)
                if int(_ok or -1) >= 0:
                    P('  ✅ REPUS do disco: %s fichas voltaram para o navegador.'
                      % '{:,}'.format(int(_ok)))
                else:
                    P('  ⛔ o arquivo do disco nao entrou (JSON invalido). Segui sem ele.')
            except Exception as _e:
                P('  nao consegui repor do disco: %s' % str(_e)[:100])

        def guarda_o_progresso(quieto=True):
            """Copia o estado do navegador para o disco. Chamado enquanto anda."""
            try:
                _b = ch.roda("localStorage.getItem('EFB_COLETA_v1')", segundos=180)
                if not _b:
                    return 0
                _tmp = ARQ_PROG + '.parcial'
                open(_tmp, 'w', encoding='utf-8', newline='').write(_b)
                os.replace(_tmp, ARQ_PROG)
                if not quieto:
                    P('     salvei o progresso em %s (%.1f MB)'
                      % (ARQ_PROG, len(_b) / 1024.0 / 1024.0))
                return len(_b)
            except Exception as _e:
                P('     nao consegui salvar o progresso: %s' % str(_e)[:90])
                return 0

        ch.roda(script, segundos=60)
        P('  o bloco entrou. Agora ele trabalha — eu olho de 30 em 30 segundos.')
        P('  ⛔ isto e demorado de verdade: sao milhares de fichas, com pausa.')
        # ⛔ 18/08 — O VIGIA OLHAVA O NUMERO ERRADO E DESISTIA DE UM TRABALHO
        #    QUE ESTAVA ANDANDO. Medido na rodada de 18/08 05h:
        #        0 fichas · indice 1,178 · nomes 138
        #        0 fichas · indice 1,315 · nomes 154
        #        0 fichas · indice 1,453 · nomes 172
        #        0 fichas · indice 1,638 · nomes 190
        #        "parou de crescer. Ou acabou, ou o site fechou a porta."
        #    O site NAO fechou a porta: o indice cresceu 460 em 90 segundos.
        #
        #    O bloco tem DUAS FASES. A fase 1 monta o indice (cardId -> playerId)
        #    procurando NOME por NOME; a fase 2 e que puxa as fichas. Durante a
        #    fase 1 inteira o contador `fichas` fica em ZERO — e era so ele que
        #    eu olhava. Tres leituras iguais e o vigia ia embora, sempre antes da
        #    fase 2 comecar. O efootbase e a fonte que MANDA no impeto: 853
        #    cartas ficaram com impeto em "nao sei" por causa disto.
        #
        #    ⛔ PAROU E QUANDO NADA MEXE — nome, indice E ficha. Nao um dos tres.
        parado, ultimo = 0, None
        limite = 120         # 120 x 30s = 60 minutos por rodada (era 30)
        for volta in range(limite):
            time.sleep(30)
            try:
                e = ch.roda("(()=>{try{return JSON.stringify(EFB.estado())}"
                            "catch(x){return null}})()")
                st = json.loads(e) if e else None
            except Exception:
                st = None
            if not st:
                P('     nao consegui perguntar o estado — paro esta perna aqui.')
                break
            _f = st.get('fichas', 0)
            _i = st.get('indice', 0)
            _n = st.get('nomes', 0)
            agora = (_n, _i, _f)
            P('     %s  %s fichas · indice %s · nomes %s'
              % ('FASE 2' if _f else 'FASE 1',
                 '{:,}'.format(_f), '{:,}'.format(_i), '{:,}'.format(_n)))
            if agora == ultimo:
                parado += 1
                if parado >= 3:
                    P('     nada mexeu em 90s — nem nome, nem indice, nem ficha.')
                    P('     Ou acabou, ou o site fechou a porta.')
                    break
            else:
                parado = 0
            ultimo = agora
            # ⛔ de 2 em 2 minutos o que esta no navegador vai para o disco.
            #    Se faltar luz agora, perde-se no maximo 2 minutos de trabalho.
            if volta % 4 == 3:
                guarda_o_progresso(quieto=(volta % 20 != 3))
        else:
            P('     fecharam os 60 minutos desta perna.')
        # ⛔ o ultimo salvamento, sempre — nao importa por que a perna acabou
        guarda_o_progresso(quieto=False)
        P('     o progresso esta em DOIS lugares: no Chrome do vigia E no')
        P('     efootbase_PROGRESSO.json. Amanha ele continua de onde parou,')
        P('     e continua mesmo que falte luz ou o Chrome se perca.')
        bruto = ch.roda("localStorage.getItem('EFB_COLETA_v1')", segundos=120)
        if bruto:
            S = json.loads(bruto)
            fichas_efb = S.get('fichas') or {}
            efb_trouxe = len(fichas_efb)
            if efb_trouxe:
                if os.path.exists('efootbase_coletado.json'):
                    shutil.copy2('efootbase_coletado.json',
                                 'efootbase_coletado.json.ANTES-DO-VIGIA-'
                                 + datetime.now().strftime('%Y%m%d-%H%M%S'))
                json.dump({'gerado': datetime.now().isoformat(timespec='seconds'),
                           'de_onde': 'o_vigia.py v3 — Chrome dirigido',
                           'indice': S.get('indice') or {},
                           'fichas': fichas_efb, 'quantos': efb_trouxe},
                          open('efootbase_coletado.json', 'w', encoding='utf-8'),
                          ensure_ascii=False)
                P('  gravei .............. efootbase_coletado.json (%s fichas)'
                  % '{:,}'.format(efb_trouxe))
                P('  ⛔ se ainda faltar, rode o vigia de novo: ele CONTINUA de onde')
                P('     parou — pelo Chrome, e pelo efootbase_PROGRESSO.json se o')
                P('     Chrome se perder.')
    except Exception as e:
        P('  a perna do efootbase parou: %s' % str(e)[:140])
        # ⛔ ate quando ela quebra, o que ja veio vai para o disco.
        try:
            guarda_o_progresso(quieto=False)
        except Exception:
            pass
        P('  o que ja tinha vindo esta guardado no navegador E no disco.')
elif not SO_OLHAR and not SO_AS_NOVAS:
    P('')
    P('  ⚠️ o efootbase ficou de fora: nao achei o %s na pasta.' % JS_EFB)
    P('     ele nasce do PREPARAR-EFOOTBASE.bat')

ch.fecha()

# ============================================================================
#  A TERCEIRA FONTE — o efootballdb, que responde sem navegador
# ============================================================================
#  ⛔ NAO REESCREVI ESTA PERNA. O braco_efootballdb.py e provado: rodou em
#     17/08 com 2.001 cartas, 0 erro de rede, e ja tem a contraprova que nao
#     sobrescreve dado bom. Reimplementar aqui seria criar um segundo programa
#     para envelhecer em paralelo.
if not SO_OLHAR and not SO_AS_NOVAS:
    braco = os.path.join('ClubEfootball', 'programas', 'braco_efootballdb.py')
    if os.path.exists(braco):
        P('')
        P('-' * 76)
        P('  A TERCEIRA FONTE — o efootballdb (responde sem navegador)')
        P('-' * 76)
        P('  quem responde: box, data e vaga de impeto, numa visita so')
        try:
            r = subprocess.run([sys.executable, braco], cwd=CASA)
            P('  o braco terminou com codigo %s' % r.returncode)
        except Exception as e:
            P('  a perna do efootballdb parou: %s' % str(e)[:140])
    else:
        P('')
        P('  ⚠️ o efootballdb ficou de fora: nao achei o %s' % braco)

# --------------------------------------------- 6) gravar
if SO_OLHAR:
    P('')
    P('=' * 76)
    P('  MODO CONFERIR: nada foi gravado.')
    P('=' * 76)
    fim(0)

# ============================================================================
#  ⛔ 18/08 — NOME DE CARTA NAO E NOME DE BOX
# ============================================================================
#  ORDEM DO LUIS, 18/08, e ele achou isto olhando a tela:
#    "Big Time e o TIPO da carta. E um card lancado especial para comemorar uma
#     partida em que o jogador jogou bem demais — por isso ela vem com a data
#     da partida. BOX, ou campanha, e ONDE VOCE RODA AS MOEDAS para obter as
#     cartas. Esse Big Time do Messi e esse do Cristiano Ronaldo sao da mesma
#     box: Living Legends 2026."
#
#  O QUE ACONTECIA: este bloco so preenchia a box quando ela estava VAZIA. Se
#  ja tivesse alguma coisa, virava "briga" e ficava como estava. So que o que
#  estava la nao era box — era a ETIQUETA DA CARTA, vinda do efootballdb.
#  Medido no BRIGA-DE-BOX.json da rodada de 17/08 (41 brigas, todas assim):
#      "Uruguay 2010"             x  National Teams Selection 13 Jul '26
#      "Big Time Italy 9 Jul '06" x  Italy Selection 11 Jun '26
#      "Brazil 2014"              x  National Teams Selection 29 Jun '26
#  Resultado na tela: 98 das 103 cartas Big Time em prateleira de UM card so.
#
#  ⛔ QUEM SABE O QUE E BOX E O efHUB. Ele nao "acha": ele LISTA as box e as
#     cartas de cada uma. Se o valor guardado nao e o nome de nenhuma box que
#     ele conhece, entao o valor guardado nao e box. Nesse caso ele perde.
#
#  ⛔ A ETIQUETA NAO SE PERDE. O que estava no campo `box` vai para
#     `etiqueta_do_card` — ela e informacao boa ("Big Time Italy 9 Jul '06"
#     diz o tipo da carta e a partida que ela comemora). So nao e box.
#
#  ⛔ BOX x BOX CONTINUA SENDO BRIGA. Se os dois nomes sao de box de verdade,
#     ninguem sobrescreve nada — vai para o BRIGA-DE-BOX.json como sempre.
#     Duas fontes dizendo box diferente e coisa para o Luis olhar.
#  ⛔ E A REGRA NAO MORA AQUI. Mora em regras_do_card.py, e so la. Este bloco
#     so ENTREGA a lista de box de hoje para a memoria acumulada e PERGUNTA.
_conhecidas = REGRA.grava_nomes_de_box(
    CAIXAS, hoje=datetime.now().strftime('%Y-%m-%d'))
P('  nomes de box conhecidos . %s (%s na lista de hoje)'
  % ('{:,}'.format(len(_conhecidas)), '{:,}'.format(len(CAIXAS))))
CARTAS_POR_NOME = REGRA.conta_cartas_por_nome(B)

preenchi, briga, corrigi = 0, [], []
for slug, d in CAIXAS.items():
    nome = d.get('nome')
    for cid in (d.get('cartas') or []):
        cid = str(cid)
        if cid not in temos_carta:
            continue
        v = B.get(cid)
        if not isinstance(v, dict):
            B[cid] = v = {}
        atual = v.get('box')
        # ⛔ QUEM DECIDE E O regras_do_card. Este programa so traz o que o efHub
        #    disse e obedece a resposta.
        fez = REGRA.guarda_o_nome(v, nome, 'efHub, lista de box (%s)' % slug,
                                  conhecidas=_conhecidas,
                                  cartas_por_nome=CARTAS_POR_NOME)
        if fez == 'box' and not atual:
            preenchi += 1
            v['datapack_do_efhub'] = d.get('datapack')
        elif fez == 'box':
            corrigi.append({'card': cid, 'era': atual, 'virou': nome})
            v['datapack_do_efhub'] = d.get('datapack')
        elif fez == 'briga':
            briga.append({'card': cid, 'ja_estava': atual, 'o_efhub_diz': nome})

P('')
P('-' * 76)
P('  O NOME DA BOX')
P('-' * 76)
P('     PREENCHI (estava vazio) .......... %s' % '{:,}'.format(preenchi))
P('     CORRIGI (era etiqueta de carta) .. %s' % '{:,}'.format(len(corrigi)))
if corrigi:
    P('        a etiqueta antiga ficou guardada em `etiqueta_do_card`:')
    for _x in corrigi[:10]:
        P('        %-34s -> %s' % (str(_x['era'])[:34], _x['virou']))
    if len(corrigi) > 10:
        P('        ... e mais %d' % (len(corrigi) - 10))
P('     ⛔ briga de BOX x BOX — nao mexi .. %s' % '{:,}'.format(len(briga)))
P('     ⛔ data NAO entra: a do efHub e a coleta semanal deles, nao o lancamento')

carimbo = datetime.now().strftime('%Y%m%d-%H%M%S')
if preenchi or briga or corrigi:
    if os.path.exists(ARQ_BOX):
        shutil.copy2(ARQ_BOX, '%s.ANTES-DO-VIGIA-%s' % (ARQ_BOX, carimbo))
    tmp = ARQ_BOX + '.tmp'
    json.dump(B, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    os.replace(tmp, ARQ_BOX)
    P('     gravei ........................... %s' % ARQ_BOX)
    if corrigi:
        json.dump({'o_que_e': ('onde o campo box guardava ETIQUETA DE CARTA e o efHub '
                               'deu a box de verdade. A etiqueta antiga foi guardada '
                               'em etiqueta_do_card — nada se perdeu.'),
                   'quando': datetime.now().isoformat(timespec='seconds'),
                   'quantas': len(corrigi), 'itens': corrigi},
                  open('BOX-CORRIGIDA.json', 'w', encoding='utf-8'), ensure_ascii=False)
        P('     gravei ........................... BOX-CORRIGIDA.json')
    if briga:
        json.dump({'o_que_e': 'onde as DUAS sao nome de box e discordam. NADA foi sobrescrito.',
                   'quando': datetime.now().isoformat(timespec='seconds'),
                   'quantas': len(briga), 'itens': briga},
                  open('BRIGA-DE-BOX.json', 'w', encoding='utf-8'), ensure_ascii=False)
        P('     gravei ........................... BRIGA-DE-BOX.json')

if fichas:
    # o parcial ja cumpriu o papel: o definitivo esta sendo gravado agora
    try:
        if os.path.exists(FICHAS + '.PARCIAL'):
            os.remove(FICHAS + '.PARCIAL')
    except Exception:
        pass
    if os.path.exists(FICHAS):
        shutil.copy2(FICHAS, '%s.ANTES-DO-VIGIA-%s' % (FICHAS, carimbo))
    json.dump({'o_que_e': 'fichas cruas do efHub colhidas pelo vigia',
               'colhido_em': datetime.now().isoformat(timespec='seconds'),
               'de_onde': 'o_vigia.py v3 — Chrome dirigido pelo proprio programa',
               'ordem_da_fila': ['1 box nova', '2 refazer', '3 restante'],
               'pedidas': len(fila), 'falhas': falhou, 'fichas': fichas},
              open(FICHAS, 'w', encoding='utf-8'), ensure_ascii=False)
    P('')
    P('     gravei ........................... %s  (%d fichas)'
      % (FICHAS, len(fichas)))
    with open(FLAG, 'w', encoding='utf-8') as f:
        f.write('o vigia colheu %d fichas em %s\n'
                % (len(fichas), datetime.now().strftime('%d/%m/%Y %H:%M')))
        f.write('  da box nova %d\n' % len(pilha1))
        for cid in fichas:
            f.write('%s\n' % cid)
elif os.path.exists(FLAG):
    os.remove(FLAG)

P('')
P('=' * 76)
if pilha1:
    P('  %d CARTAS DE BOX NOVA · %d fichas na mao.' % (len(pilha1), len(fichas)))
else:
    P('  NENHUMA CARTA NOVA. %d fichas atualizadas.' % len(fichas))
P('=' * 76)
P('  O QUE FAZER AGORA, na ordem:')
P('     1. ClubEfootball\\ENTRAR-COM-O-EFHUB.bat   leva as fichas para o banco')
P('     2. ClubEfootball\\SEPARAR-A-DATA-DO-BOX.bat  tira a data do NOME da box')
P('     3. FECHAR-O-CICLO.bat                     unificar, subir, conferir')
P('     4. BAIXAR-BASE.bat                        o banco volta a mandar')
fim(0)
