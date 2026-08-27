# -*- coding: utf-8 -*-
"""
GERA O ENCAIXE — troca o `const D` do HTML pelos resultados da rodada v6.

Nao mexe em NADA do resto do HTML: le o arquivo, substitui a linha do `const D=`
inteira, e grava com nome novo. E o metodo registrado no HANDOFF de 07/08.

⛔ SO ENTRA O QUE A v6 RODOU. As fichas da v5 saem — ordem do Luis, 08/08.

De onde vem cada campo:
  motor (saida_v6/linhas.jsonl) .. b1 · sis · sisBar · imp · adds/HAB · TEC/TECB · arows[3,4]
                                   ⛔ sisBar sai em PORTUGUES (a casca compara com MBN)
                                   ⛔ sobra e CALCULADA aqui: orc - custo das barras
  molde (dados/molde.json v3) .... arows[0,1,2]  = attr · peso · alvo
  cards.json ..................... nome · tier · votos · ovr · max_ovr · pos · np · sec
                                   modelo · orc · altura · peso · pe · base · fab · falta
                                   raras · nm · sl · dt · slot
  HTML antigo (v164 / v171) ...... o que so existe na tela: com · age · wfa · wfu · inj
                                   mst · mx · maxOvr. Card que nao estava lá entra com
                                   esses campos vazios — é cosmético e nao entra na nota.
  b2..b5 = 0 ..................... os bonus de corpo e de IA sairam do ranking em 06/08
  b1n ............................ A NOTA = Sigma(peso x valor) / Sigma(peso x alvo) x 100
                                   ⛔ SEM ARREDONDAR por dentro (ordem do Luis, 06/08).
                                   Quem arredonda e a TELA.
"""
import json, os, sys, io, re, glob, collections, time

# ===========================================================================
#  ⛔ 19/08 — ESTE PROGRAMA MORA NO ClubEfootball\programas.
#     Ordem do Luis, repetida desde 17/08: "Nao existe mais essa pasta pro
#     futebol. A pasta agora e ClubEfootball. E tudo la."
#     O padrao e o mesmo de todos os programas de la: o arquivo mora em
#     `programas\`, mas TRABALHA na pasta que tem o config.txt — sobe as
#     pastas ate achar e faz os.chdir. Assim alcanca dados\, saida_v6\,
#     encaixe\ e o resto sem caminho fixo, e rodar de onde for da no mesmo.
# ===========================================================================
def _acha_a_casa(inicio):
    p = inicio
    for _ in range(5):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None

_MEU_LUGAR = os.path.dirname(os.path.abspath(__file__))
_CASA = _acha_a_casa(_MEU_LUGAR) or _acha_a_casa(os.getcwd())
if _CASA and os.path.abspath(os.getcwd()) != os.path.abspath(_CASA):
    os.chdir(_CASA)

# ⛔ 19/08 — A CASA ENTRA NO CAMINHO ANTES DOS IMPORTS.
#    O `funcao_nativa.py` (e outros modulos do motor) continuam na pasta do
#    sistema, nao em `programas`. Enquanto o gerador morava la, o import saia
#    de graca. Agora ele precisa dizer onde procurar — e nao se resolve
#    copiando o arquivo para ca: duas copias do mesmo modulo e a doenca.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if _CASA and _CASA not in sys.path:
    sys.path.insert(0, _CASA)
from funcao_nativa import funcao_nativa   # 13/08: o goleiro nao mistura

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
# ⛔ AS TELAS DA DESIGNER. moldes_design.py sai do arquivo dela pelo
#    extrai_design.py; telas.py so preenche. Se faltar, o gerador segue sem
#    elas (a tela antiga continua) em vez de parar.
try:
    import telas as TELAS
except Exception as _e:
    TELAS = None
    print('   (sem as telas da designer: %s)' % str(_e)[:80])


# ===========================================================================
#  AS LINHAS DA TELA VAO PARA O BANCO — 17/08/2026
#
#  Ordem do Luis: "a gente vai pegar esses mesmos dados do banco de dados,
#  online. So isso. O restante dele nao toca, e pra ficar do jeito que esta:
#  o design, os trem tudo."
#
#  ⛔ ESTE ARQUIVO NAO MONTA NADA DE NOVO. O sobe_a_tela recebe as linhas
#     PRONTAS, do jeito que este programa ja monta, e manda para o banco.
#     Reescrever a montagem em outro lugar criaria a segunda verdade que o
#     sistema inteiro esta tentando acabar.
#
#  ⛔ SE O MODULO NAO ESTIVER NA PASTA, OU O INTERRUPTOR ESTIVER DESLIGADO,
#     TUDO SEGUE EXATAMENTE COMO SEMPRE FOI. O encaixe nunca deixa de sair.
# ===========================================================================
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'ClubEfootball', 'programas'))
try:
    import sobe_a_tela as _tela
except Exception:
    class _tela:                      # sem o modulo, nada muda
        LIGADO = False
        SEM_DADOS = False
        @staticmethod
        def sobe(D, diz=print): return 0, 0
        @staticmethod
        def resumo(): return 'tela no banco: o modulo sobe_a_tela nao esta na pasta'


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty(): input(msg)
    except Exception: pass

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# ⛔ 19/08 — AQUI TINHA UM CHDIR PARA A PASTA DESTE ARQUIVO.
#    Enquanto o gerador morava na raiz da v6 dava no mesmo — a pasta dele ERA a
#    pasta do sistema. Agora que ele mora em ClubEfootball\programas, aquilo
#    jogava o cwd para dentro do `programas` e NADA era encontrado:
#    "NAO ACHEI a casca do HTML". A intencao do autor continua a mesma —
#    trabalhar na pasta do sistema — so que agora ela se acha pelo config.txt.
os.chdir(_CASA or os.path.dirname(os.path.abspath(__file__)))

LINHAS = 'saida_v6/linhas.jsonl'
CARDS  = 'dados/cards.json'
MOLDE  = 'dados/molde.json'
SAIDA  = 'encaixe/encaixe_v6_NOVO.html'

# ---------------------------------------------------------------- ESPELHO NO DRIVE
# Depois de gerar, copia o HTML para o Google Drive. SO o HTML vai — o resto da
# pasta continua no disco local, porque o motor grava linha a linha e o Drive
# tentando subir no meio da gravacao trava o arquivo (sharing violation no Windows).
#
# O nome no Drive e FIXO, para o link nao mudar nunca.
NOME_NO_DRIVE = 'ENCAIXE-TrueFootball.html'
ARQ_ESPELHO   = 'ESPELHO.txt'    # opcional: uma linha com a pasta de destino

# tentados nesta ordem quando o ESPELHO.txt nao existe
DRIVE_PALPITES = [
    r'G:\Meu Drive', r'G:\My Drive', r'H:\Meu Drive', r'H:\My Drive',
    os.path.expanduser(r'~\Meu Drive'), os.path.expanduser(r'~\My Drive'),
    os.path.expanduser(r'~\Google Drive'),
    os.path.expanduser(r'~\Google Drive\Meu Drive'),
]


def pasta_espelho():
    """Onde espelhar. O ESPELHO.txt manda; sem ele, procura o Drive."""
    if os.path.exists(ARQ_ESPELHO):
        for ln in open(ARQ_ESPELHO, encoding='utf-8', errors='replace'):
            ln = ln.strip().strip('"')
            if ln and not ln.startswith('#'):
                return ln if os.path.isdir(ln) else ('!' + ln)
        return None
    for p in DRIVE_PALPITES:
        if os.path.isdir(p):
            return p
    return None


def espelha(origem):
    import shutil
    d = pasta_espelho()
    if not d:
        return 'sem espelho — crie o %s com a pasta do Drive numa linha' % ARQ_ESPELHO
    if d.startswith('!'):
        return 'a pasta do %s nao existe: %s' % (ARQ_ESPELHO, d[1:])
    dest = os.path.join(d, NOME_NO_DRIVE)
    try:
        tmp = dest + '.parcial'
        shutil.copy2(origem, tmp)      # grava com outro nome e só então renomeia,
        os.replace(tmp, dest)          # para o Drive nunca ver arquivo pela metade
        return 'espelhado em ' + dest
    except Exception as e:
        return 'NAO consegui espelhar: %s' % e

# ============================================================================
#  A VERSAO QUE VAI PARA A INTERNET — 18/08/2026
# ============================================================================
#  Ordem do Luis, 18/08: "o encaixe e novo agora, precisa atualizar aquele
#  espelho do Drive de acordo com o encaixe novo."
#
#  O arquivo que fica na maquina continua GORDO (as linhas coladas dentro).
#  O que vai para o Drive e uma copia LEVE: as mesmas 193 funcoes, o mesmo
#  desenho, os mesmos patches — mas as linhas vem do banco em vez de estarem
#  coladas. 37 MB viram 2 MB, e o link do Drive nunca mais serve tela velha:
#  o desenho e do dia em que gerou, os dados sao os de agora.
#
#  ⛔ ELA NASCE DA MESMA GERACAO. Nao e arquivo mantido a mao: e o `novo`
#     pronto, com uma linha trocada. Se um patch novo entrar aqui, ele entra
#     nos dois no mesmo instante — foi por nao ser assim que a copia de 17/08
#     ficaria velha em silencio.
# ============================================================================
NOME_DO_BANCO = 'ENCAIXE-DO-BANCO.html'
PASTA_WEB     = os.path.join('ClubEfootball', 'encaixe-web')

JS_DO_BANCO = r"""(function(){
// ===========================================================================
//  AS LINHAS VEM DO BANCO — E NAO TODAS DE UMA VEZ
// ===========================================================================
//  ⛔ 18/08 — ORDEM DO LUIS:
//     "A pagina pros usuarios tem que ser dinamica, nao pode ficar esperando
//      dezessete segundos pra carregar tudo. E nem precisa carregar tudo:
//      precisa carregar o que esta dando na pagina. O resto pode carregar em
//      segundo plano."
//
//  O QUE ACONTECIA: as 17.023 linhas vinham em 18 requisicoes SINCRONAS antes
//  de qualquer coisa aparecer. Medido em 18/08, servindo de um servidor local
//  (o melhor caso possivel): 17,5 SEGUNDOS de tela branca. Pela internet, mais.
//  E o contador do cabecalho e escrito na geracao, entao ele mostrava
//  "17.187 de 18.598 linhas" com o painel vazio — parecia defeito, e nao era.
//
//  AGORA: a PRIMEIRA leva vem sincrona (a tela abre com ela, em ~1s) e o resto
//  vem em SEGUNDO PLANO, empurrando dentro do mesmo D e mandando a tela se
//  redesenhar a cada leva.
//
//  ⛔ POR QUE ISTO NAO OBRIGA A MEXER NAS 193 FUNCOES: `const D` continua sendo
//     o mesmo ARRAY desde o primeiro instante. `const` prende a referencia, nao
//     o conteudo — entao `D.push(...)` e legal e todo mundo que le o D ve o que
//     chegou. Quem redesenha ja existe e se chama render().
// ===========================================================================
  var URL  = 'https://trqqpsnafpbudtvvicch.supabase.co/rest/v1/tela_encaixe';
  var CHAVE = 'sb_publishable_XTKGboY9RyYiirPiIsWMhw_P8B51cHj';
  var PAGINA = 1000;
  var PRIMEIRA = 2;   // levas que vem antes da tela abrir
  // ⛔ SO AS FUNCOES DESTA GERACAO. Sem isto a tela puxa tambem as linhas de
  //    funcao RENOMEADA que ficaram no banco e monta uma tela que ela nao
  //    conhece. A lista e escrita pelo gerador, entao anda junto com o molde.
  var FUNCOES = __FUNCOES__;
  // ⛔ SEM encodeURIComponent: o navegador ja codifica o endereco sozinho.
  //    Codificar duas vezes foi o defeito da tela em branco de 18/08.
  var FILTRO = '&funcao=in.(' + FUNCOES.map(function(f){
      return '"' + String(f).replace(/"/g, '') + '"'; }).join(',') + ')';

  function endereco(de){
    return URL + '?select=linha' + FILTRO + '&order=card_id.asc,funcao.asc&limit=' + PAGINA + '&offset=' + de;
  }
  // ⛔ 18/08 (noite) — A ANCORA VEM ANTES DE TUDO.
  //    O "% do topo" divide a nota do card pela MAIOR nota daquela funcao. Se a
  //    tela so conhece 2.000 linhas, ela usa o maior DAQUELAS 2.000 — e cada
  //    usuario ve um numero diferente ate tudo carregar. Ordem do Luis: "isso
  //    tem que sair do banco, que ja sabe qual e o maior."
  //    A coluna `forca` (o Bloco 1 normalizado) veio para isso: estas 2.000
  //    linhas sao as mais fortes do banco inteiro, entao o topo de cada uma das
  //    19 funcoes esta aqui dentro. Os bonus somam de -2 a +4 sobre a forca —
  //    margem folgada para o topo real nao ficar de fora.
  var FORTES = 2000;
  function enderecoForte(){
    return URL + '?select=linha' + FILTRO + '&order=forca.desc.nullslast&limit=' + FORTES;
  }
  function erroNaTela(e){
    document.addEventListener('DOMContentLoaded', function(){
      document.body.innerHTML =
        '<div style="font:16px system-ui;padding:40px;color:#e6edf3;background:#0d1117;'
      + 'min-height:100vh"><h2 style="color:#f85149">Nao consegui ler as linhas no banco</h2>'
      + '<p>' + String(e.message || e) + '</p>'
      + '<p style="color:#8b949e">Confira a internet. Se o erro falar em 404 ou'
      + ' <i>schema cache</i>, as linhas ainda nao subiram.</p></div>';
    });
  }

  var fora = [], de = 0, acabou = false;
  // ⛔ 18/08 — A MESMA FUNCAO APARECIA DUAS VEZES NA FICHA DO CARD.
  //    Sem `order`, o PostgREST nao garante ordem entre uma pagina e a
  //    seguinte: a mesma linha vem em duas levas e OUTRA nunca vem. O
  //    `order=card_id,funcao` no endereco resolve; este cadeado e a segunda
  //    rede — se a ordem falhar de novo, entra uma vez so.
  var _visto = {};
  function _entra(L){
    if (L && L.id !== undefined && L.tipo !== undefined){
      var ch = L.id + '|' + L.tipo;
      if (_visto[ch]) return;
      _visto[ch] = 1;
    }
    fora.push(L);
  }
  // ---------- a primeira leva, sincrona: e ela que faz a tela abrir ----------
  try {
    // ---- leva 0: as mais fortes, so para a ancora nascer certa ----
    try {
      var xf = new XMLHttpRequest();
      xf.open('GET', enderecoForte(), false);
      xf.setRequestHeader('apikey', CHAVE);
      xf.setRequestHeader('Authorization', 'Bearer ' + CHAVE);
      xf.send(null);
      if (xf.status === 200) {
        var pf = JSON.parse(xf.responseText);
        for (var kf = 0; kf < pf.length; kf++) _entra(pf[kf].linha);
        console.log('[encaixe] ' + pf.length + ' linhas mais fortes — o topo de cada funcao ja e o definitivo');
      } else {
        console.warn('[encaixe] sem a coluna `forca` ainda (HTTP ' + xf.status
          + '): o topo so fica certo quando tudo carregar. Falta rodar o sql/33-a-forca-da-linha.sql.');
      }
    } catch (ef) { console.warn('[encaixe] nao consegui pedir as mais fortes: ' + ef); }

    for (var v = 0; v < PRIMEIRA && !acabou; v++) {
      var x = new XMLHttpRequest();
      x.open('GET', endereco(de), false);
      x.setRequestHeader('apikey', CHAVE);
      x.setRequestHeader('Authorization', 'Bearer ' + CHAVE);
      x.send(null);
      if (x.status !== 200) throw new Error('HTTP ' + x.status + ' - ' + x.responseText.slice(0,200));
      var p = JSON.parse(x.responseText);
      for (var k = 0; k < p.length; k++) _entra(p[k].linha);
      if (p.length < PAGINA) acabou = true;
      de += PAGINA;
    }
    if (!fora.length) throw new Error('o banco respondeu, mas nao veio linha nenhuma');
    console.log('[encaixe] ' + fora.length + ' linhas na primeira leva — a tela ja pode abrir');
  } catch (e) { erroNaTela(e); return []; }

  // ---------- o resto, em segundo plano ----------
  //  ⛔ Cada leva que chega entra no MESMO array e manda redesenhar. A tela vai
  //     enchendo na frente do usuario em vez de ficar branca esperando.
  function aviso(txt){
    try{
      var d = document.getElementById('_carregando_banco');
      if (!d && txt){
        d = document.createElement('div');
        d.id = '_carregando_banco';
        d.style.cssText = 'position:fixed;right:12px;bottom:56px;z-index:99999;'
          + 'background:#132a1f;color:#9fe8c0;border:1px solid #1f7a4d;'
          + 'border-radius:8px;padding:6px 11px;font:12px system-ui;opacity:.93';
        document.body.appendChild(d);
      }
      if (d){ if (txt) d.textContent = txt; else d.remove(); }
    }catch(e){}
  }
  function redesenha(){
    // guarda onde a pagina estava: redesenhar nao pode jogar o leitor pro topo
    var _sy = window.pageYOffset || document.documentElement.scrollTop || 0;
    // ⛔ 18/08 — O TOPO DA FUNCAO E MEMORIZADO (_TOPO), e quem memoriza no meio
    //    do carregamento guarda um topo PROVISORIO: a primeira leva tinha 2.000
    //    linhas, o Goleiro ofensivo mais alto dela valia menos que o que chegou
    //    depois — e o card virou "110,21% do topo". Nao e conta errada, e conta
    //    feita cedo demais. A cada leva o topo se apaga e nasce de novo.
    try{ if(typeof _TOPO !== 'undefined') _TOPO = {}; }catch(e){}
    // ⛔ SAO TRES TELAS, TRES DESENHADORES. Descoberto testando em 18/08: com
    //    so o render() a home dizia "0 boxes ativas" para sempre, porque o
    //    bloco de Lancamentos e montado pelo homeRender() e ele so rodava uma
    //    vez, no DOMContentLoaded — antes das linhas chegarem.
    // ⛔ primeiro a passada que carimba pacote e refaz o fisico, DEPOIS desenha
    try{ if (typeof window._pos_D === 'function') window._pos_D(); }catch(e){}
    try{ if (typeof render     === 'function') render(); }catch(e){}
    try{ if (typeof homeRender === 'function') homeRender(); }catch(e){}
    try{ if (typeof desenha    === 'function') desenha(); }catch(e){}
    if (_sy > 0) { try{ window.scrollTo(0, _sy); }catch(e){} }
  }
  function proxima(){
    if (acabou) { aviso(''); redesenha();
                  console.log('[encaixe] ' + fora.length + ' linhas no total'); return; }
    var r = new XMLHttpRequest();
    r.open('GET', endereco(de), true);
    r.setRequestHeader('apikey', CHAVE);
    r.setRequestHeader('Authorization', 'Bearer ' + CHAVE);
    r.onload = function(){
      try{
        if (r.status !== 200) { aviso(''); return; }
        var q = JSON.parse(r.responseText);
        for (var k = 0; k < q.length; k++) _entra(q[k].linha);
        if (q.length < PAGINA) acabou = true;
        de += PAGINA;
        aviso('carregando o resto — ' + fora.length.toLocaleString('pt-BR') + ' linhas');
        // ⛔ 18/08 (noite) — NAO SE REDESENHA A CADA LEVA. Ordem do Luis:
        //    "carrega um pouco, a tela fica piscando, carrega outro pouco —
        //     esta horrivel." Cada redesenho refaz o painel inteiro e as fotos
        //    recarregam: sao 17 piscadas ate o fim. A tela ja abre com as levas
        //    sincronas (as 2.000 mais fortes + 2.000), que e o que aparece na
        //    primeira dobra; o resto entra no D em silencio e a tela se redesenha
        //    UMA vez, quando acaba. O aviso do canto mostra o progresso.
        setTimeout(proxima, 0);
      }catch(e){ aviso(''); }
    };
    r.onerror = function(){ aviso(''); };
    r.send(null);
  }
  document.addEventListener('DOMContentLoaded', function(){
    aviso('carregando o resto — ' + fora.length.toLocaleString('pt-BR') + ' linhas');
    setTimeout(proxima, 60);
  });

  return fora;
})();"""


def patch_tema_padrao(html):
    """⛔ 18/08 — O PADRAO VOLTA A SER ESCURO.

    O que o Luis viu: "ele demorou pra carregar, deu uma piscadinha com as
    cartas, depois sumiram as cartas". Reproduzido aqui num navegador de
    verdade: o conteudo pinta e o tema CLARO apaga — o painel inteiro fica
    branco, com o menu da esquerda escuro do lado. Igualzinho a foto dele.

    A causa e uma linha da casca:
        document.documentElement.dataset.tema = salvo && ... ? salvo : "claro";
    O tema claro entrou como PADRAO antes de estar pronto: sao 79 regras de
    CSS para uma tela com centenas de pontos de cor. Quem abre pela primeira
    vez cai nele e ve tela branca.

    Isto NAO tira o tema claro nem o botao. So devolve o escuro como padrao,
    que e o unico que esta inteiro. Quem clicar no botao continua escolhendo,
    e a escolha continua sendo guardada.
    """
    velho = 'T.some(t=>t[0]===salvo)?salvo:"claro"'
    if velho in html:
        return html.replace(velho, 'T.some(t=>t[0]===salvo)?salvo:"escuro"'), 1
    return html, 0


def versao_do_banco(html_pronto, D=None):
    """A copia leve: mesma tela, linhas vindas do banco. Devolve o caminho.

    O D entra so para saber QUAIS FUNCOES esta geracao tem. Elas viram o filtro
    do pedido ao banco — e e isso que impede a tela de receber linha de funcao
    com nome velho, que foi o defeito de 18/08.
    """
    i = html_pronto.find('const D=')
    if i < 0:
        i = html_pronto.find('const D =')
    if i < 0:
        return None, 'nao achei o ponto das linhas no HTML gerado'
    j = html_pronto.find('\n', i)
    funcoes = sorted({str(r.get('tipo')) for r in (D or []) if r.get('tipo')})
    if not funcoes:
        return None, 'nao sei quais funcoes esta geracao tem — nao gero sem o filtro'
    js = JS_DO_BANCO.replace('__FUNCOES__',
                             json.dumps(funcoes, ensure_ascii=False))
    leve = html_pronto[:i] + 'const D=' + js + html_pronto[j:]

    # ⛔ 18/08 — A PASSADA QUE SO ACONTECIA UMA VEZ.
    #    Existe um bloco anonimo que percorre o D inteiro e faz duas coisas:
    #      1. carimba `pacote`/`NOVO` nos cards das campanhas no ar
    #      2. reconstroi o Bloco 4 (o fisico) das linhas que vieram sem corpo
    #    Ele roda UMA VEZ, na abertura. Isso era inofensivo quando o D chegava
    #    inteiro de uma vez — e virou defeito no carregamento progressivo: as
    #    linhas que chegam depois nunca passavam por ele.
    #    Medido no teste de 18/08: a home dizia "0 boxes ativas" com 17.030
    #    linhas carregadas, porque nenhuma das que chegaram depois foi carimbada.
    #
    #    ⛔ NAO SE COPIA A LOGICA. Dou um NOME ao bloco e chamo ele de novo a
    #       cada leva. Uma regra, um lugar.
    _marca = '(function(){\n  let n=0,marc=0;'
    _k = leve.find(_marca)
    if _k < 0:
        _marca = '(function(){ let n=0,marc=0;'
        _k = leve.find(_marca)
    if _k >= 0:
        # casamento de chaves para achar onde este bloco termina
        _d, _t = 0, None
        for _q in range(_k, len(leve)):
            if leve[_q] == '{':
                _d += 1
            elif leve[_q] == '}':
                _d -= 1
                if _d == 0:
                    _t = _q
                    break
        if _t and leve[_t:_t + 5] == '})();':
            corpo = leve[_k + len('(function(){'):_t]
            leve = (leve[:_k]
                    + 'window._pos_D=function(){' + corpo + '};window._pos_D();'
                    + leve[_t + 5:])
            print('   a passada do pacote/fisico virou window._pos_D() — sera chamada a cada leva')
        else:
            print('   ⚠️ nao consegui nomear a passada do pacote: o fim nao bateu')
    else:
        print('   ⚠️ nao achei a passada do pacote/fisico neste HTML')
    try:
        os.makedirs(PASTA_WEB, exist_ok=True)
        destino = os.path.join(PASTA_WEB, NOME_DO_BANCO)
        # grava com outro nome e so entao renomeia: ninguem le arquivo pela metade
        tmp = destino + '.parcial'
        open(tmp, 'w', encoding='utf-8').write(leve)
        os.replace(tmp, destino)
        return destino, '%.1f MB' % (len(leve.encode('utf-8')) / 1024 / 1024)
    except Exception as e:
        return None, str(e)


# a casca do HTML (e os metadados que so existem na tela). O primeiro que existir manda;
# os seguintes so completam metadado de card que faltou.
CASCAS = ['encaixe/encaixe_B_v171_datas_tela.html',
          'encaixe_B_v171_datas_tela.html',
          '../../encaixe_B_v171_datas_tela.html']
COMPLEMENTO = ['../../encaixe_B_v164_busca.html',
               'encaixe_B_v164_busca.html',
               'encaixe/encaixe_B_v164_busca.html']

SETOR = {
    'Goleiro ofensivo': 'GOLEIRO', 'Goleiro defensivo': 'GOLEIRO',
    'Zagueiro de combate': 'DEFESA', 'Zagueiro de saída': 'DEFESA',
    'Lateral defensivo': 'DEFESA', 'Lateral ofensivo': 'DEFESA',
    'Volante de contenção': 'DEFESA', 'Volante de construção': 'DEFESA',
    'Meia central armador': 'MEIO', 'Meia central de chegada': 'MEIO',
    'Meia de lado por dentro': 'MEIO', 'Meia de lado por fora': 'MEIO',
    'Meia ofensivo armador': 'MEIO', 'Segundo atacante': 'ATAQUE',
    'Ponta criadora': 'ATAQUE', 'Ponta finalizadora': 'ATAQUE',
    'Centroavante fixo': 'ATAQUE', 'Centroavante móvel': 'ATAQUE',
    'Falso nove': 'ATAQUE',
}
POS_DA_FUNCAO = {
    'Goleiro ofensivo': 'GK', 'Goleiro defensivo': 'GK',
    'Zagueiro de combate': 'ZC', 'Zagueiro de saída': 'ZC',
    'Lateral defensivo': 'LD', 'Lateral ofensivo': 'LD',
    'Volante de contenção': 'VOL', 'Volante de construção': 'VOL',
    'Meia central armador': 'MC', 'Meia central de chegada': 'MC',
    'Meia de lado por dentro': 'MLD', 'Meia de lado por fora': 'MLD',
    'Meia ofensivo armador': 'MO', 'Segundo atacante': 'MO',
    'Ponta criadora': 'PD', 'Ponta finalizadora': 'PD',
    'Centroavante fixo': 'CA', 'Centroavante móvel': 'CA',
    'Falso nove': 'CA',
}


def le_D(caminho):
    if not os.path.exists(caminho): return None, None, None
    s = open(caminho, encoding='utf-8', errors='replace').read()
    i = s.find('const D=')
    if i < 0: i = s.find('const D =')
    if i < 0: return s, None, None
    j = s.find('\n', i)
    try:
        D = json.loads(s[s.find('[', i):j].rstrip().rstrip(';'))
    except Exception as e:
        print('nao consegui ler o D de', caminho, e); D = None
    return s, (i, j), D


def sp_de(b, c, m, _POS=None):
    """As posicoes de TAMBEM JOGA, no formato [[pos, estrelas], ...]."""
    est = {str(p[0]).strip(): p[1] for p in (m.get('sp') or []) if p}
    nat = str(c.get('np') or c.get('pos') or '').strip()
    out = []
    for p in sorted(_POS or []):
        if p == nat: continue
        out.append([p, est.get(p, 1)])
    return out


def texto_impeto(v):
    if not v: return ''
    if isinstance(v, str): return v
    return ' + '.join(str(x) for x in v if x)


# ------------------------------------------------------- NOMES DAS BARRAS (PT)
# ⛔ ACHADO 08/08: o motor fala INGLES (shooting, dexterity...) e a CASCA fala
# PORTUGUES. A tela faz  MBK.find(k => MBN[k] === nm)  em _lvlDe(). Gravando em
# ingles nada casa: as barras aparecem todas em 0 e "sobram 62". Por isso o
# nome PT sai do proprio HTML da casca — assim nunca desencontra de novo.
MBN_PADRAO = {
    'shooting': 'Chute', 'passing': 'Passe', 'dribbling': 'Drible',
    'dexterity': 'Destreza', 'lowerBodyStrength': 'Força pernas',
    'aerialStrength': 'Força aérea', 'defending': 'Defesa',
    'gk1': 'GO reflexo/salto', 'gk2': 'GO defesa/alcance',
    'gk3': 'GO encaixe/reflexos',
}


def mbn_da_casca(html):
    m = re.search(r'const\s+MBN\s*=\s*\{(.*?)\}', html, re.S)
    if not m: return dict(MBN_PADRAO)
    d = {}
    for k, v in re.findall(r'(\w+)\s*:\s*"([^"]*)"', m.group(1)):
        d[k] = v
    return d or dict(MBN_PADRAO)


# custo de chegar ao nivel n = soma de ceil(k/4) para k=1..n  (19 niveis = 55)
ACCU = [0]
for _n in range(1, 26):
    ACCU.append(ACCU[-1] + -(-_n // 4))


def custo_barras(barras):
    return sum(ACCU[int(v)] for v in (barras or {}).values() if v)


# --------------------------------------------------- A REGRA DO IMPETO (Luis, 08/08)
# sl NAO e "quantos impetos a carta tem". sl e "quantas vagas ainda CABEM".
#   sl [0,0] + lancada DEPOIS de 12/09/2024  ->  ja vem com os DOIS de fabrica
#                                               (o efeito deles ja esta dentro do nm)
#   sl [0,1] -> um de fabrica + uma vaga livre
#   sl [1,1] -> duas vagas livres
#   lancada ANTES de 12/09/2024 -> o impeto nao existia: nao tem vaga nenhuma
IDS_SEM_VAGA = 'ids_sem_vaga_pela_data.json'


def ids_antes_do_impeto():
    try:
        j = json.load(open(IDS_SEM_VAGA, encoding='utf-8'))
        return {str(x) for x in (j['ids'] if isinstance(j, dict) else j)}
    except Exception:
        return set()


# ---------------------------------------------- NOME DO IMPETO DE FABRICA
# ⛔ 08/08 (Luis, no Sneijder e no Aguero): "qual impeto foi utilizado na conta?"
# O `boostId` vem NULO em quase toda a base, e a ficha escrevia um nome chutado —
# no Sneijder saiu "Agilidade +1" quando o efeito real era "Passe +2".
# A solucao nao precisa de fonte externa: a tabela `const CAT` da propria casca tem
# nome -> efeito de todos os impetos. Basta bater a ASSINATURA do `nm`.
# MEDIDO na base de 6.273 registros:
#   1 impeto de fabrica .. 2.078      2 impetos de fabrica ..   142
#   Geral +N .............   184      nao casou .............    42
def cat_da_casca(html):
    i = html.find('const CAT=[')
    if i < 0: return {}
    j = html.find('];', i)
    try:
        CAT = json.loads(html[i + 10:j + 1])
    except Exception:
        return {}
    u = {}
    for nome, slot, ef in CAT:
        u.setdefault(nome, {int(a): int(x) for a, x in ef})
    return u


def nome_do_nm(nm, uniq):
    """devolve o NOME do impeto de fabrica a partir do efeito somado (`nm`)."""
    ef = [x for x in (nm or []) if x]
    if not ef or not uniq: return ''
    k = tuple(sorted((int(a), int(x)) for a, x in ef))
    for nome, d in uniq.items():
        if tuple(sorted(d.items())) == k: return nome
    if len(ef) == 26 and len({int(x) for _, x in ef}) == 1:
        return 'Geral +%d' % int(ef[0][1])
    itens = list(uniq.items())
    for i in range(len(itens)):
        for j in range(i, len(itens)):
            d = dict(itens[i][1])
            for a, x in itens[j][1].items():
                d[a] = d.get(a, 0) + x
            if tuple(sorted(d.items())) == k:
                return '%s + %s' % (itens[i][0], itens[j][0])
    return '+%d em %d atributos' % (int(ef[0][1]), len(ef))


VAGA_ARQ = 'vaga_por_card.json'
_VAGAS = None


def _coleta_diz_que_tem_vaga(b):
    """True se a coleta do efootballdb viu vaga LIVRE nesta carta.

    None quando a coleta nao conhece a carta — ai quem decide e a data."""
    global _VAGAS
    if _VAGAS is None:
        try:
            _VAGAS = json.load(open(VAGA_ARQ, encoding='utf-8'))
        except Exception:
            _VAGAS = {}
    r = _VAGAS.get(str(b))
    if not isinstance(r, dict):
        return False
    return any(x == 'VAGA' for x in (r.get('v') or []))


def impeto_da_carta(b, sl, escolhido, antes, tem_nm=False, nome_fab=''):
    """devolve (texto do impeto, slot). slot=0 so quando a carta e velha de
    verdade — e a unica hora em que a tela deve gritar "SEM VAGA".

    ⛔ ACHADO 08/08 20:00 (Varane 87, id 88041460901956): a lista de datas dizia
    "lancada antes de 12/09/2024" para uma carta que TEM IMPETO DE FABRICA — o nm
    dela soma +3 em 4 atributos, e o numero na tabela ja mostrava isso. A tela
    gritava SEM VAGA e "Impeto: nenhum" com o efeito somado do lado.
    Carta que tem `nm` NAO pode ser de antes do impeto existir. Entao o `nm`
    manda, e a data so vale para quem nao tem nm.
    Tamanho do estrago medido: 598 registros · 248 cards nessa contradicao."""
    # 🔴 09/08 — DESFEITO a excecao do `nm`. O ACHADO-0708: a pagina do efHub e as
    # builds da comunidade sao SIMULADOR e aceitam booster em qualquer carta, logo o
    # `nm` NAO prova que a carta tem impeto. A trava da DATA manda (ordem do Luis: "1").
    # Quem sai da trava e so quem ele conferiu no jogo — e isso e resolvido no
    # corrigir_cards.py, que nem zera o sl desses. Aqui a lista `antes` manda, ponto.
    # 🟢 10/08 — A COLETA MANDA, A DATA SO DECIDE QUEM ELA NAO CONHECE.
    # Ordem do Luis: "tem que tirar a data, nao tem outro jeito".
    # Motivo, medido hoje: 70 cards estavam na lista da data (corte 12/09/2024) e
    # ao mesmo tempo o vaga_por_card.json — lido do efootballdb pelo sentinela
    # pes_id 136 / booster_type 4 — dizia ['NATIVO','VAGA',None], ou seja: vaga
    # livre. Entre eles Messi 88, Cruyff 87, Maldini 87, Cannavaro 88, Bale 88,
    # Figo 88, Varane 87, Nedved 87, Gullit 89 e o Iniesta 86 que abriu o caso.
    # A tela gritava SEM VAGA numa carta que tem vaga. O MOTOR ja estava certo
    # (as 3 linhas desses cards ja calculadas vieram COM impeto fabricado) —
    # era so a tela mentindo. Por isso nada volta para a fila.
    if b in antes and not _coleta_diz_que_tem_vaga(b):
        return '', 0
    livres = sum(1 for x in sl if x) if isinstance(sl, (list, tuple)) else None
    # a ficha mostra os DOIS pedacos: o que ja veio na carta e o que o motor pos.
    partes = []
    if nome_fab:
        partes.append('de fabrica: %s' % nome_fab)
    elif tem_nm:
        partes.append('de fabrica (efeito somado no card)')
    if escolhido:
        partes.append('o motor pos: %s' % escolhido)
    if not partes:
        return '', livres
    return ' · '.join(partes), (livres if escolhido else (None if livres == 0 else livres))


# ---------------------------------------------------- const PACOTE (as BOX da home)
# ⛔ 09/08: a home desenha as secoes de campanha a partir do `const PACOTE` da casca
# (card id -> nome da campanha). A casca vinha com 97 cards / 9 campanhas e faltavam
# a "Vozinha" e a "J.League 100 Year Vision League Monthly" — as duas que o Luis pediu.
# Agora o merge e feito AQUI, a cada geracao, lendo o campo `box` do fila_v6.json.
# Feito no gerador de proposito: trocar a casca nao desfaz mais.

# ------------------------------------------------------- MOLDE DO FISICO (10/08/2026)
# Substitui a regua antiga do Bloco 4 (espelho + FIS_HI/MID/LO/PT) pelo MOLDE DO FISICO
# fechado pelo Luis nas 3 etapas. Documento: docs/MOLDE-DO-FISICO.html
#
# Por que precisa ser um patch aqui e nao na casca:
#   quando este script troca o `const D`, o corpo dos cards vai junto (frows) e 86% das
#   linhas ficavam com Bloco 4 zerado. O corpo_efhub.js entra EMBUTIDO no HTML porque
#   so o HTML sobe para o Drive.
CORPO_ARQ = 'encaixe/corpo_efhub.js'

MF_BLOCO = r"""
  /* ===== MOLDE DO FISICO - 10/08/2026 - injetado pelo gera_encaixe.py ===== */
  /* 10/08 · FECHADO PELO LUIS: de -1,5 a +1,5 (amplitude 3 pontos). */
  let CORPO_MAX = 1.5;
  const MF_BAN={"Altura":[171,178,184,191],"Coxa":[5,7,8,10],"Panturrilha":[4,6,8,10],
   "Cintura":[3,5,7,8],"Peito":[3,5,7,9],"Tam. bra\u00e7o":[4,6,7,9],"Tam. pesco\u00e7o":[5,7,9,11],
   "Compr. perna":[5,7,10,12],"Compr. bra\u00e7o":[3,5,7,9],"Compr. pesco\u00e7o":[4,5,7,8],
   "Larg. ombro":[5,7,9,11],"Alt. ombro":[3,6,8,11]};
  const MF_BAN_GK_ALT=[179,184,189,194];
  const MF_A=["Altura","Coxa","Panturrilha","Cintura","Peito","Tam. bra\u00e7o","Tam. pesco\u00e7o"];
  const MF_B=["Compr. perna","Compr. bra\u00e7o","Compr. pesco\u00e7o"];
  const MF_C={"Larg. ombro":-1,"Alt. ombro":1};
  const MF_ORD=MF_A.concat(MF_B).concat(Object.keys(MF_C));
  const MF_PESO=m=>m==="Altura"?5:1;
  const MF_TIPO={"Zagueiro de sa\u00edda":["G","L"],"Zagueiro de combate":["G","L"],
   "Lateral defensivo":["G","L"],"Volante de conten\u00e7\u00e3o":["G","L"],"Centroavante fixo":["G","L"],
   "Centroavante m\u00f3vel":["M","L"],"Ponta finalizadora":["M","L"],"Meia lateral atacante":["M","L"],
   "Ponta criadora":["M","L"],"Segundo atacante":["M","L"],"Meia lateral cruzador":["M","L"],
   "Lateral ofensivo":["M","L"],"Meia ofensivo armador":["M","C"],"Meia de liga\u00e7\u00e3o armador":["M","C"],
   "Meia de liga\u00e7\u00e3o avan\u00e7ado":["M","C"],"Volante de constru\u00e7\u00e3o":["M","C"],
   "Goleiro ofensivo":["GK","GK"],"Goleiro defensivo":["GK","GK"]};
  const MF_GK={"Altura":1,"Coxa":-1,"Panturrilha":-1,"Cintura":-1,"Peito":-1,"Tam. bra\u00e7o":-1,
   "Tam. pesco\u00e7o":-1,"Compr. perna":1,"Compr. bra\u00e7o":1,"Compr. pesco\u00e7o":1,
   "Larg. ombro":-1,"Alt. ombro":1};
  const MF_EXC={"Centroavante fixo|Larg. ombro":1,"Meia ofensivo armador|Alt. ombro":-1};
  /* 10/08 · DIRECAO POR FUNCAO — cada uma das 18 pontua conforme o tipo
     fisico que ELA exige. Medido nos 40 melhores cards de cada funcao do
     proprio motor: desvio da media global / desvio-padrao, corte em 0,20.
     +1 = maior e melhor · -1 = menor e melhor · 0 = nao pesa nessa funcao.
     Antes eram 4 moldes (G/L, M/L, M/C, GK) para 18 funcoes — por isso o
     percentual saia igual em funcoes diferentes. Agora sao 17 perfis. */
  const MF_DIRF={"Falso nove": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": -1, "Peito": 1, "Tam. braço": 1, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 1, "Alt. ombro": -1}, "Centroavante fixo": {"Altura": 1, "Coxa": 0, "Panturrilha": 1, "Cintura": -1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Centroavante móvel": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 1, "Peito": 1, "Tam. braço": 1, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 1, "Compr. pescoço": 0, "Larg. ombro": 1, "Alt. ombro": -1}, "Goleiro defensivo": {"Altura": -1, "Coxa": -1, "Panturrilha": -1, "Cintura": 0, "Peito": -1, "Tam. braço": 1, "Tam. pescoço": 1, "Compr. perna": 1, "Compr. braço": 1, "Compr. pescoço": 1, "Larg. ombro": 1, "Alt. ombro": -1}, "Goleiro ofensivo": {"Altura": 1, "Coxa": -1, "Panturrilha": 1, "Cintura": 0, "Peito": -1, "Tam. braço": 1, "Tam. pescoço": -1, "Compr. perna": 1, "Compr. braço": 1, "Compr. pescoço": 1, "Larg. ombro": 1, "Alt. ombro": -1}, "Lateral defensivo": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Lateral ofensivo": {"Altura": -1, "Coxa": 0, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0}, "Meia de ligação armador": {"Altura": -1, "Coxa": 0, "Panturrilha": 1, "Cintura": -1, "Peito": -1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Meia de ligação avançado": {"Altura": -1, "Coxa": -1, "Panturrilha": 1, "Cintura": -1, "Peito": -1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": -1, "Larg. ombro": 0, "Alt. ombro": 0}, "Meia lateral atacante": {"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0}, "Meia lateral cruzador": {"Altura": 1, "Coxa": 0, "Panturrilha": 1, "Cintura": 1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Meia ofensivo armador": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 1, "Peito": 1, "Tam. braço": -1, "Tam. pescoço": 1, "Compr. perna": -1, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Ponta criadora": {"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 1, "Larg. ombro": -1, "Alt. ombro": -1}, "Ponta finalizadora": {"Altura": -1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 1, "Larg. ombro": 0, "Alt. ombro": -1}, "Segundo atacante": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 1, "Alt. ombro": -1}, "Volante de construção": {"Altura": -1, "Coxa": 1, "Panturrilha": 1, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 1, "Larg. ombro": 0, "Alt. ombro": -1}, "Volante de contenção": {"Altura": 1, "Coxa": 1, "Panturrilha": 0, "Cintura": -1, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 1, "Compr. perna": 0, "Compr. braço": 0, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": -1}, "Zagueiro de combate": {"Altura": 1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 0, "Larg. ombro": 0, "Alt. ombro": 0}, "Zagueiro de saída": {"Altura": 1, "Coxa": 0, "Panturrilha": 0, "Cintura": 0, "Peito": 0, "Tam. braço": 0, "Tam. pescoço": 0, "Compr. perna": 0, "Compr. braço": -1, "Compr. pescoço": 1, "Larg. ombro": -1, "Alt. ombro": -1}};
  const MF_FAIXA={"Goleiro ofensivo":[-12,22],"Goleiro defensivo":[-12,22],
   "Zagueiro de sa\u00edda":[-11,16],"Zagueiro de combate":[-11,16],"Lateral defensivo":[-19,14],
   "Lateral ofensivo":[-16,15],"Volante de conten\u00e7\u00e3o":[-19,10],"Volante de constru\u00e7\u00e3o":[-12,20],
   "Meia de liga\u00e7\u00e3o armador":[-7,22],"Meia de liga\u00e7\u00e3o avan\u00e7ado":[-7,22],
   "Meia ofensivo armador":[-8,20],"Meia lateral atacante":[-8,18],"Meia lateral cruzador":[-8,18],
   "Ponta criadora":[-8,19],"Ponta finalizadora":[-8,19],"Segundo atacante":[-12,18],
   "Centroavante fixo":[-17,16],"Centroavante m\u00f3vel":[-15,16]};
  const MF_CORPO=(()=>{const R={};const t=(typeof window!=="undefined"&&window.CORPO_EFHUB)||"";
   if(!t)return R;
   for(const p of t.split(" ")){const a=p.split(":");if(a.length!==3)continue;
    R[a[0]]=[parseInt(a[1],10)].concat(a[2].split("").map(c=>parseInt(c,16)));}
   return R;})();
  const MF_ARQIDX={"Altura":0,"Coxa":1,"Panturrilha":2,"Cintura":3,"Peito":4,"Tam. bra\u00e7o":5,
   "Tam. pesco\u00e7o":6,"Compr. perna":7,"Compr. bra\u00e7o":8,"Compr. pesco\u00e7o":9,
   "Larg. ombro":10,"Alt. ombro":11};
  const MF_IDX={"Altura":0,"Coxa":9,"Panturrilha":12,"Cintura":10,"Peito":5,"Tam. bra\u00e7o":11,
   "Tam. pesco\u00e7o":6,"Compr. perna":8,"Compr. bra\u00e7o":2,"Compr. pesco\u00e7o":4,
   "Larg. ombro":3,"Alt. ombro":7};
  function mfMedidas(c){const b=String(c.id).split("@")[0];
   /* 1o o corpo que o MOTOR mediu (saida_v6/bonus.jsonl, do dia) */
   const mo=(typeof window!=="undefined"&&window.CORPO_MOTOR)?window.CORPO_MOTOR[b]:null;
   if(mo){const o={};for(const m in MF_ARQIDX){const x=mo[MF_ARQIDX[m]];
    if(typeof x!=="number")return _mfDoArquivo(c,b); o[m]=x;} return o;}
   return _mfDoArquivo(c,b);}
  /* rede: o corpo_efhub.js, para card que o motor nao rodou */
  function _mfDoArquivo(c,b){const a=MF_CORPO[b];
   if(a){const o={};for(const m in MF_ARQIDX)o[m]=a[MF_ARQIDX[m]];return o;}
   const v=(typeof fisVals==="function")?fisVals(c):null; if(!v)return null;
   const o={};for(const m in MF_IDX){const x=v[MF_IDX[m]];if(typeof x!=="number")return null;o[m]=x;}
   return o;}
  function mfDir(m,f){const dd=MF_DIRF[f]; if(dd&&dd[m]!==undefined)return dd[m];
   if(MF_EXC[f+"|"+m]!==undefined)return MF_EXC[f+"|"+m];
   const t=MF_TIPO[f]; if(!t)return 0;
   if(t[0]==="GK")return MF_GK[m];
   if(MF_A.indexOf(m)>=0)return t[0]==="G"?1:-1;
   if(MF_B.indexOf(m)>=0)return t[1]==="L"?1:-1;
   return MF_C[m];}
  function mfCortes(m,f){const t=MF_TIPO[f];
   return (t&&t[0]==="GK"&&m==="Altura")?MF_BAN_GK_ALT:MF_BAN[m];}
  function mfNota(v,c){return v<=c[0]?-2:v<=c[1]?-1:v<=c[2]?0:v<=c[3]?1:2;}
  function mfFaixaTxt(m,f,n){const c=mfCortes(m,f);
   return n===0?("\u2264"+c[0]):n===1?((c[0]+1)+"-"+c[1]):n===2?((c[1]+1)+"-"+c[2]):n===3?((c[2]+1)+"-"+c[3]):("\u2265"+(c[3]+1));}
  /* o ALVO da linha: com +1 o ideal e o topo, com -1 e o piso, com 0 nao pesa */
  function mfAlvoTxt(m,f){const d=mfDir(m,f); if(!d)return "\u2014";
   return mfFaixaTxt(m,f,d>0?4:0);}
  function mfSoma(card){const v=mfMedidas(card); if(!v||!MF_TIPO[card.tipo])return null;
   let s=0; for(const m of MF_ORD){const x=v[m]; if(typeof x!=="number")continue;
    s+=mfNota(x,mfCortes(m,card.tipo))*mfDir(m,card.tipo)*MF_PESO(m);}
   return s;}
  const MF_TETO=(f)=>{let t=0; for(const m of MF_ORD){if(mfDir(m,f))t+=MF_PESO(m)*2;} return t||1;};
  function mfPct(card){const s=mfSoma(card); if(s===null)return null;
   const te=MF_DIRF[card.tipo]?MF_TETO(card.tipo):null;
   if(te){return Math.max(-100,Math.min(100,s/te*100));}
   const fa=MF_FAIXA[card.tipo]; if(!fa)return null;
   const p=s>=0? s/fa[1]*100 : s/Math.abs(fa[0])*100;
   return Math.max(-100,Math.min(100,p));}
  function mfFrows(card){const v=mfMedidas(card); if(!v||!MF_TIPO[card.tipo])return [];
   return MF_ORD.map(m=>{const x=v[m],d=mfDir(m,card.tipo),pe=MF_PESO(m);
    const n=(typeof x==="number")?mfNota(x,mfCortes(m,card.tipo)):0;
    return [m,d?pe:0,mfAlvoTxt(m,card.tipo),x,n,d,n*d*pe];});}
  (function(){let n=0;
   for(const c of D){ if(c.id==="MOLDE")continue;
    const p=mfPct(c); if(p===null)continue;
    c.frows=mfFrows(c); c.b4r=mfSoma(c); c.b4=p; c._fb=undefined; delete c._n; n++;}
   const sem=D.filter(c=>c.id!=="MOLDE"&&mfPct(c)===null).length;
   console.log("%cMOLDE DO FISICO - "+n+" linhas com corpo - "+sem+" sem corpo - tabela: "
    +((typeof window!=="undefined"&&window.CORPO_MOTOR)
       ?(Object.keys(window.CORPO_MOTOR).length+" cards do MOTOR (bonus.jsonl)")
       :((Object.keys(MF_CORPO).length||"NAO CARREGADA")+" cards do corpo_efhub.js"))
    +" - CORPO_MAX="+CORPO_MAX,
    "color:"+(sem?"#f0a531":"#22c58b")+";font-weight:700");})();
  /* ===== FIM DO MOLDE DO FISICO ===== */
"""


def patch_molde_fisico(html):
    """Injeta o MOLDE DO FISICO e a tabela de corpo dentro do HTML gerado."""
    if 'MOLDE DO FISICO' in html or 'MOLDE DO F\u00cdSICO' in html:
        return html, 'ja estava'
    # 1) tabela de corpo EMBUTIDA (so o HTML sobe pro Drive)
    corpo = ''
    if os.path.exists(CORPO_ARQ):
        corpo = open(CORPO_ARQ, encoding='utf-8').read()
    if not corpo:
        return html, 'FALTA ' + CORPO_ARQ
    if '</head>' not in html:
        return html, 'nao achei </head>'
    html = html.replace('</head>', '<script>\n' + corpo + '\n</script>\n</head>', 1)
    # 2) o bloco do molde + a nova fisBonus, no lugar da regua velha
    alvo = 'function fisBonus(c){'
    i = html.find(alvo)
    if i < 0:
        return html, 'nao achei fisBonus'
    ini = html.rfind('\n', 0, i) + 1
    d, k = 0, html.index('{', i)
    while True:
        if html[k] == '{': d += 1
        elif html[k] == '}':
            d -= 1
            if d == 0: break
        k += 1
    velha = html[ini:k + 1]
    nova = ('  function fisBonus(c){const p=mfPct(c); if(p===null)return 0;\n'
            '   return p/100*CORPO_MAX;}\n')
    html = (html[:ini] + MF_BLOCO + nova
            + '  /* regua ANTIGA do Bloco 4, desativada em 10/08/2026:\n  '
            + velha.strip().replace('*/', '* /') + '\n  fim da regua antiga */\n'
            + html[k + 1:])
    # 3) rotulos da linha TOTAL da ficha
    html = html.replace('<span class=mini>bruto ${(c.b4r||0).toFixed(2)}</span>',
                        '<span class=mini>soma ${(c.b4r||0).toFixed(0)} de \u00b1${MF_FAIXA[c.tipo]?MF_FAIXA[c.tipo][1]:32}</span>')
    html = html.replace('<span class=mini>molde 85,7</span>',
                        '<span class=mini>b\u00f4nus ${((c._fb!==undefined?c._fb:0)>=0?"+":"")+(c._fb!==undefined?c._fb:0).toFixed(2)}</span>')
    html = html.replace("${c.b4>=85.7?'#22c58b':'#e0533d'}\">${c.b4.toFixed(1)}</b>",
                        "${c.b4>=0?'#22c58b':'#e0533d'}\">${c.b4>=0?'+':''}${c.b4.toFixed(0)}%</b>")
    return html, 'OK (%d cards de corpo)' % corpo.count(':')

def patch_pacote(html):
    # ⛔ 18/08 (tarde) — A SEXTA TORNEIRA. O Luis: "as boxes continuam com o
    #    erro ja detectado", olhando `Boxes anteriores` cheia de
    #    "Big Time 14 Nov '98" com uma carta cada.
    #
    #    De manha eu fechei quem CRIAVA campanha no historico. Mas a home nao
    #    monta os blocos pelo historico: ela monta pelo carimbo `pacote` de
    #    cada card, e quem carimba e ESTA funcao — lendo o campo `box` do
    #    box_por_card, que carrega etiqueta desde antes da regra existir.
    #    Agora todo nome passa pela regra antes de virar carimbo.
    _conh = {}
    try:
        _conh = REGRA.le_nomes_de_box()
    except Exception:
        pass

    # ⛔ 18/08 (noite) — O CARD NUNCA SOME. Ordem do Luis: "nessa box aqui esta
    #    faltando um card do Messi, um do Cristiano — deve estar acontecendo em
    #    todas as box." Medido: ao barrar os nomes de etiqueta eu tirei o carimbo
    #    e nao pus nada no lugar; 662 cards ficaram sem box nenhuma e sumiram.
    #    Agora, quando o nome e etiqueta:
    #      1. se o efHub lista aquele CARD em alguma box, vale essa box;
    #      2. se nao lista, o card vai para SEM_BOX — aparece num bloco proprio,
    #         em vez de desaparecer. A regra continua de pe: etiqueta nao vira box.
    SEM_BOX = 'Sem box confirmada'
    _dono = {}
    try:
        for _r in _conh.values():
            for _c in (_r.get('cartas') or []):
                _dono.setdefault(str(_c), _r.get('nome'))
    except Exception:
        pass

    def _e_box(nome):
        try:
            return not REGRA.e_etiqueta_provada(nome, _conh)
        except Exception:
            return True

    _barrados = {}
    _resgatados = {'pelo_efhub': 0, 'sem_box': 0}

    def _poe(dic, card, nome):
        if not nome:
            return
        if not _e_box(nome):
            _barrados.setdefault(nome, set()).add(str(card))
            _alt = _dono.get(str(card))
            if _alt:
                dic[str(card)] = _alt
                _resgatados['pelo_efhub'] += 1
            else:
                dic[str(card)] = SEM_BOX
                _resgatados['sem_box'] += 1
            return
        dic[str(card)] = nome

    try:
        F = json.load(open('fila_v6.json', encoding='utf-8'))
    except Exception as e:
        print('nao consegui ler a fila para o PACOTE: %s' % e)
        return html, 0
    novo = {}
    for r in F:
        b = str(r.get('card_id') or '').split('@')[0]
        if b and r.get('box'):
            _poe(novo, b, r['box'])
    # 10/08 · a campanha nova do efHub (ex.: "Encored AC Milan") ainda nao esta
    # gravada no campo `box` da fila — sem isto a secao nem aparece na home.
    try:
        _e = json.load(open('campanhas_efhub.json', encoding='utf-8'))
        for _nome, _ids in (_e.get('campanhas') or {}).items():
            for _i in _ids:
                _poe(novo, str(_i).split('@')[0], _nome)
    except Exception:
        pass
    # e as campanhas ja encerradas: o box_por_card guarda de qual box saiu cada
    # carta. Sem isso a aba "boxes anteriores" nunca ganha bloco.
    try:
        _bp = json.load(open('box_por_card.json', encoding='utf-8'))
        for _b, _r in _bp.items():
            _n = (_r or {}).get('box')
            if _n and str(_b) not in novo:
                _poe(novo, _b, _n)
    except Exception:
        pass
    if _barrados:
        print('PACOTE · nomes barrados pela regra: %d (%d cards) — sao etiqueta '
              'de carta, nao box' % (len(_barrados),
                                     sum(len(v) for v in _barrados.values())))
        print('PACOTE · desses, %d cards foram para a box que o efHub aponta e '
              '%d ficaram em "%s" (nenhum sumiu)'
              % (_resgatados['pelo_efhub'], _resgatados['sem_box'], SEM_BOX))
        try:
            json.dump({'o_que_e': ('nomes que o box_por_card/fila traziam no campo `box` e que a '
                                   'regra PROVOU nao serem box: lixo ("dummy", "0"), tipo de card '
                                   '("Big Time ...") ou data anterior a 2021. Nao viram bloco na '
                                   'home. Quem decide isto e ClubEfootball/programas/regras_do_card.py.'),
                       'quando': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
                       'quantos': len(_barrados),
                       'itens': {k: sorted(v) for k, v in sorted(_barrados.items())}},
                      open('PACOTE-BARRADO-PELA-REGRA.json', 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
        except Exception:
            pass
    i = html.find('const PACOTE')
    if i < 0 or not novo:
        return html, 0
    k = html.find('=', i); j = html.find('};', k)
    try:
        atual = json.loads(html[k + 1:j + 1])
    except Exception:
        atual = {}
    antes_c, antes_n = len(set(atual.values())), len(atual)
    atual.update(novo)
    html = html[:k + 1] + json.dumps(atual, ensure_ascii=False) + html[j + 1:]
    print('PACOTE ................. %d -> %d cards · %d -> %d campanhas'
          % (antes_n, len(atual), antes_c, len(set(atual.values()))))
    return html, 1


# ============================================================================
#  A CASCA DO TURNO 6 — o desenho que o Luis mandou em 18/08
# ============================================================================
#  ETAPA 1 de 5 (casca) · faltam: Inicio, Meu time, Boxes anteriores,
#  Como calculamos. O arquivo do design: EncaixeDirecoes.dc.html, blocos
#  6a a 6d.
#  ⛔ NADA E RECRIADO. A aba nova chama a MESMA funcao do botao velho
#     (homeToggle, mtToggle, boxModo) e o botao continua no DOM — e por
#     isso que os outros 40 patches continuam achando #fbt, #homebt e
#     #mtbt. O que muda e so quem o usuario ve.
# ============================================================================
T6_CSS = """
<style id=t6css>
@import url('https://fonts.googleapis.com/css2?family=Carlito:wght@400;700&display=swap');

/* ---------- as cores do turno 6 ---------- */
html[data-tema=escuro]{
 --bg:#0b0d0c; --surf:#111714; --surf2:#0d1211;
 --line:rgba(255,255,255,.075); --line2:rgba(255,255,255,.05);
 --txt:#e6ebe8; --txt2:#8b968f; --txt3:#6b766f;
 --acc:#7df2a8; --acc2:#5ddb8c; --accbg:rgba(125,242,168,.14); --onacc:#08130f;
 --sombra:rgba(0,0,0,.45); --zebra:rgba(255,255,255,.028);
 /* ⛔ --barra e --dourado NAO se mexem: quem pinta a barra lateral inteira
    (#filtros), o topo das tabelas e a tarja do card e o --barra, com texto
    branco por cima. Trocar por claro apaga a lateral. A barra de cima ganhou
    cor propria (--t6bar). */
 --t6bar:rgba(12,18,14,.92); --t6bartxt:#e6ebe8;
}
html[data-tema=claro]{
 --bg:#eef1ee; --surf:#ffffff; --surf2:#f4f7f4;
 --line:rgba(0,0,0,.08); --line2:rgba(0,0,0,.055);
 --txt:#14181b; --txt2:#5c6560; --txt3:#7c847f;
 --acc:#0a7d4f; --acc2:#0b6b45; --accbg:rgba(10,125,79,.09); --onacc:#ffffff;
 --sombra:rgba(16,40,30,.13); --zebra:rgba(10,125,79,.03);
 --t6bar:rgba(255,255,255,.94); --t6bartxt:#14181b;
 /* item 19 · o amarelo puro (#ffcc00) e ilegivel no branco */
 --dourado:#8a5a00;
}
/* ⛔ Item 1 do Luis: "algo simples e singelo, estilo Calibri". Os numeros
   saem do DM Mono e vao para a mesma fonte; o alinhamento em coluna passa a
   ser garantido pelo tabular-nums, nao pela fonte de maquina de escrever. */
html[data-tema] *{font-variant-numeric:tabular-nums}
html[data-tema] body,html[data-tema] button,html[data-tema] input,html[data-tema] select,
html[data-tema] textarea,html[data-tema] table{
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}

/* ---------- a barra ---------- */
html[data-tema=claro] header,html[data-tema=escuro] header{
 background:var(--t6bar)!important;border-bottom:1px solid var(--line)!important;
 backdrop-filter:blur(10px);padding:0!important;display:block!important}
html[data-tema=claro] header h1,html[data-tema=escuro] header h1{color:var(--txt2)!important}
#t6bar{display:flex;align-items:center;gap:16px;height:56px;padding:0 18px;width:100%;
 border-bottom:1px solid var(--line);flex-wrap:nowrap;overflow:visible}
#t6logo{font-weight:700;font-size:14.5px;letter-spacing:.4px;white-space:nowrap;
 background:linear-gradient(96deg,var(--txt),var(--acc));-webkit-background-clip:text;
 background-clip:text;color:transparent;cursor:pointer}
#t6tabs{display:flex;gap:3px;background:var(--line2);padding:3px;border-radius:10px;
 border:1px solid var(--line)}
.t6tab{font-size:12.5px;padding:6px 13px;border-radius:8px;color:var(--txt2);cursor:pointer;
 white-space:nowrap;transition:background .18s ease,color .18s ease;font-weight:500}
.t6tab:hover{color:var(--txt);background:var(--line2)}
.t6tab.on{color:var(--txt);font-weight:600;background:var(--surf);
 box-shadow:0 1px 0 rgba(255,255,255,.06) inset,0 1px 6px var(--sombra)}
#t6bar #q{flex:0 1 300px;max-width:320px;height:34px;border-radius:10px;border:1px solid var(--line);
 background:var(--line2);color:var(--txt);padding:0 12px;font-size:12.5px;font-family:inherit;
 outline:none;min-width:150px}
#t6bar #q::placeholder{color:var(--txt3)}
#t6dir{margin-left:auto;display:flex;align-items:center;gap:12px;flex:0 0 auto;
 white-space:nowrap;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:11px;color:var(--txt2)}
/* os tres que viraram aba somem da fila de baixo */
#homebt,#mtbt,#boxbt{display:none!important}
#t6dir b,#t6dir strong{color:var(--acc)}
#t6dir #t6contas{color:var(--txt3);font-size:11px}
#t6dir #t6contas b{color:var(--dourado);font-size:16px;font-weight:700;letter-spacing:-.2px}
#t6dir #contbar b{color:var(--acc)}
#t6dir #contbar,#t6dir #cnt{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;
 font-size:11px!important;color:var(--txt2)!important;margin:0!important}
#t6dir #contbar span{color:var(--acc)!important}
#t6dir button{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;font-size:11px!important;
 padding:5px 10px!important;border:1px solid var(--line)!important;border-radius:8px!important;
 background:transparent!important;color:var(--acc)!important;cursor:pointer}

/* ⛔ 18/08 — A SEGUNDA FILA DO CABECALHO SAI DE CENA.
   O desenho da designer tem UMA fila so (marca · abas · busca · contadores ·
   tema). Os controles que moravam nesta fila voltam dentro da tela do Ranking,
   na barra que ela desenhou. Esconder, e nao apagar, porque 40 patches ainda
   procuram esses botoes pelo id. */
html[data-tema] header h1,html[data-tema] header .sub{display:none!important}

/* a linha dos controles vira a segunda fila, discreta */
html[data-tema] header h1{font-size:12.5px!important;font-weight:500!important;
 display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0!important;padding:0 18px 8px!important}
html[data-tema] header .sub{padding:0 18px 8px!important}
html[data-tema] header .fbt,html[data-tema] header .sub button{
 border-radius:8px!important;font-size:11.5px!important;padding:5px 11px!important;
 border:1px solid var(--line)!important;background:transparent!important;color:var(--txt2)!important}
html[data-tema] header .fbt:hover{color:var(--txt)!important;border-color:var(--acc)!important}

/* ⛔ O CABECALHO NO CELULAR. Uma fila so, e a fila das abas rola de lado —
   e o que a foto 14 mostra. Sem isto a pagina inteira ficava com 1295px de
   largura num aparelho de 390. */
@media(max-width:820px){
 html[data-tema] header{padding:0!important}
 html[data-tema] header #t6bar{flex-wrap:wrap!important;gap:8px!important;
  padding:10px 12px!important;height:auto!important;align-items:center!important}
 html[data-tema] header #t6logo{flex:none!important}
 html[data-tema] header #t6tabs{order:9;width:100%!important;overflow-x:auto;
  -webkit-overflow-scrolling:touch;flex-wrap:nowrap!important;scrollbar-width:none;
  margin:0!important}
 html[data-tema] header #t6tabs::-webkit-scrollbar{display:none}
 html[data-tema] header #t6tabs>*{flex:none!important;white-space:nowrap}
 html[data-tema] header #q{order:8;width:100%!important;min-width:0!important;
  flex:none!important;margin:0!important}
 html[data-tema] header #t6dir{order:7;width:100%!important;flex-wrap:wrap!important;
  gap:8px!important;margin:0!important;justify-content:flex-start!important}
 html[data-tema] header #t6contas,html[data-tema] header #contbar{font-size:10.5px!important}
 html,body{overflow-x:hidden!important;max-width:100%!important}
 html[data-tema] main{padding:0 10px!important}
}

/* ---------- cantos e sombras ---------- */
html[data-tema] .hbox,html[data-tema] .cd,html[data-tema] #box,
html[data-tema] .mtcx,html[data-tema] .mtfora{border-radius:14px!important}
html[data-tema] .hbox{box-shadow:0 10px 30px var(--sombra)!important;border:1px solid var(--line)!important}
html[data-tema] .hsub,html[data-tema] .mini{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif}
html[data-tema] #homewrap,html[data-tema] .hbloco{scroll-margin-top:110px}
</style>
"""

T6_JS = """
<script>
/* A CASCA DO TURNO 6 — abas no lugar dos botoes soltos.
   Nada e recriado: o botao velho continua no DOM e a aba chama a MESMA
   funcao dele (homeToggle, mtToggle, boxModo). */
(function(){
  function ver(id){ var e=document.getElementById(id); return !!(e && e.offsetParent!==null); }
  var ABAS=[
    {n:'Inicio',   t:'In\\u00edcio',
     f:function(){ window._t6abaBox=false; window._t6cc=false;
                   if(window.t6Painel){ window.t6Painel('inicio'); return; }
                   homeToggle(1); if(window.boxModo) boxModo(0);
                   try{ homeRender(); }catch(e){} window.scrollTo(0,0); },
     on:function(){ if(window.T6TELAS) return ver('homewrap') && window._t6aba==='inicio';
                     return ver('homewrap') && !ver('mtwrap')
                      && !window._t6box && !window._t6abaBox && !window._t6cc; }},
    {n:'MeuTime',  t:'Meu time',
     f:function(){ window._t6aba=null; try{ homeToggle(0); }catch(e){}
                   if(!ver('mtwrap')) mtToggle(); window.scrollTo(0,0); },
     on:function(){ return ver('mtwrap'); }},
    {n:'Ranking',  t:'Ranking',
     f:function(){ window._t6aba=null; if(ver('mtwrap')) mtToggle(); homeToggle(0); window.scrollTo(0,0); },
     on:function(){ return !ver('homewrap') && !ver('mtwrap'); }},
    {n:'BoxAtual', t:'Boxes atuais',
     f:function(){ window._t6abaBox=true; window._t6cc=false;
                   if(window.t6Painel){ window.t6Painel('boxatual'); return; }
                   homeToggle(1); if(window.boxModo) boxModo(0);
                   try{ homeRender(); }catch(e){} window.scrollTo(0,0); },
     on:function(){ if(window.T6TELAS) return ver('homewrap') && window._t6aba==='boxatual';
                     return ver('homewrap') && !!window._t6abaBox
                      && !window._t6box && !window._t6cc; }},
    {n:'BoxAnt',   t:'Boxes anteriores',
     f:function(){ window._t6abaBox=false; window._t6cc=false;
                   if(window.t6Painel){ window.t6Painel('boxant'); return; }
                   homeToggle(1); if(window.boxModo) boxModo(1); window.scrollTo(0,0); },
     on:function(){ if(window.T6TELAS) return ver('homewrap') && window._t6aba==='boxant';
                     return ver('homewrap') && !!window._t6box && !window._t6cc; }}
  ];
  function monta(){
    var h=document.querySelector('header');
    if(!h || document.getElementById('t6bar')) return;
    var bar=document.createElement('div'); bar.id='t6bar';
    var lg=document.createElement('div'); lg.id='t6logo'; lg.textContent='ClubEfootball';
    lg.onclick=function(){ ABAS[0].f(); };
    var nav=document.createElement('div'); nav.id='t6tabs';
    ABAS.forEach(function(a){
      var d=document.createElement('div'); d.className='t6tab'; d.textContent=a.t;
      d.dataset.aba=a.n; d.onclick=function(){ try{ a.f(); }catch(e){} pinta();
        setTimeout(function(){ window.dispatchEvent(new Event('resize')); },50); };
      nav.appendChild(d); a.el=d;
    });
    var dir=document.createElement('div'); dir.id='t6dir';
    bar.appendChild(lg); bar.appendChild(nav);
    var q=document.getElementById('q'); if(q) bar.appendChild(q);
    bar.appendChild(dir);
    h.insertBefore(bar,h.firstChild);
    recolhe();
    /* a casca calcula a altura do cabecalho num --hh; a barra nova mudou essa
       altura DEPOIS do DOMContentLoaded, e sem avisar o conteudo passa por
       baixo dela. O resize e o proprio aviso que a casca ja escuta. */
    setTimeout(function(){ window.dispatchEvent(new Event('resize')); },60);
    /* o titulo velho sai do caminho — os botoes dele continuam ali */
    var h1=h.querySelector('h1');
    if(h1) for(var k=0;k<h1.childNodes.length;k++){
      var n=h1.childNodes[k];
      if(n.nodeType===3 && n.textContent.indexOf('Encaixe')>=0) n.textContent='';
    }
    pinta();
  }
  /* ⛔ 25 · os botoes que viraram aba nao ficam escondidos: saem do DOM.
     Estavam so com display:none, e o documento do design pede que nao existam
     mais. Os outros patches nao dependem deles (dependem de #fbt). */
  function tiraOsVelhos(){
    ['homebt','mtbt'].forEach(function(id){
      var e=document.getElementById(id);
      if(e && e.parentNode) e.parentNode.removeChild(e);
    });
  }
  /* o contador, o tema e o #cnt sobem para a barra assim que existirem —
     eles sao criados por outros patches, em outra hora. E os tres botoes que
     viraram aba somem da fila de baixo: ⌂ inicio, ★ elenco e boxes anteriores. */
  function recolhe(){
    var dir=document.getElementById('t6dir'); if(!dir) return;
    tiraOsVelhos();
    ['contbar','temabt'].forEach(function(id){
      var e=document.getElementById(id);
      if(e && e.parentNode!==dir) dir.appendChild(e);
    });
    /* nao adianta so mexer no style: outro patch reacende esses tres.
       Quem apaga de verdade e o CSS com !important la de cima. */
  }
  function pinta(){
    for(var i=0;i<ABAS.length;i++){
      if(!ABAS[i].el) return;
      var lig=false; try{ lig=!!ABAS[i].on(); }catch(e){}
      ABAS[i].el.className='t6tab'+(lig?' on':'');
    }
  }
  function liga(){ monta(); pinta(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',liga);
  else liga();
  setInterval(function(){ if(!document.getElementById('t6bar')) monta();
                          else { recolhe(); pinta(); } },1400);
})();
</script>
"""


T6_CSS2 = """
<style id=t6css2>
/* ---------- ETAPA 2 · a tela de INICIO do turno 6 ---------- */
.t6kk{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10.5px;letter-spacing:1.6px;
 color:var(--acc);text-transform:uppercase;margin-bottom:8px}
.t6hero{position:relative;border-radius:18px;padding:28px 30px;margin:0 0 22px;
 border:1px solid var(--accbg);overflow:hidden;
 background:radial-gradient(700px 300px at 88% 20%,var(--accbg),transparent 66%),
            linear-gradient(120deg,var(--surf),var(--surf2))}
.t6hero h2{margin:0 0 10px;font-size:27px;line-height:1.16;font-weight:700;color:var(--txt);max-width:620px}
.t6hero p{margin:0 0 18px;font-size:13.5px;line-height:1.6;color:var(--txt2);max-width:600px}
.t6hero p b{color:var(--txt)}
.t6cta{display:flex;gap:10px;flex-wrap:wrap}
.t6b1,.t6b2{font-family:inherit;font-size:13px;font-weight:600;padding:11px 18px;border-radius:11px;
 cursor:pointer;border:1px solid transparent;transition:transform .15s ease,filter .15s ease}
.t6b1{background:linear-gradient(180deg,var(--acc),var(--acc2));color:var(--onacc)}
.t6b2{background:transparent;color:var(--txt);border-color:var(--line)}
.t6b1:hover,.t6b2:hover{transform:translateY(-1px);filter:brightness(1.06)}
.t6faixa{display:flex;align-items:center;gap:24px;flex-wrap:wrap;justify-content:space-between;
 border-radius:16px;padding:22px 26px;margin:22px 0;border:1px solid var(--line);
 background:linear-gradient(120deg,var(--surf),var(--surf2))}
.t6faixa h3{margin:0 0 6px;font-size:19px;font-weight:700;color:var(--txt)}
.t6faixa p{margin:0;font-size:12.5px;color:var(--txt2);max-width:520px;line-height:1.55}
/* item 15 · o botao GRANDE de ver as outras boxes, no fim do bloco */
.t6todas{display:block;width:100%;margin:14px 0 4px;font-family:inherit!important;
 font-size:14px!important;font-weight:700!important;letter-spacing:.2px;
 padding:15px 18px!important;border-radius:14px!important;cursor:pointer;
 border:1px solid var(--line)!important;color:var(--acc)!important;
 background:linear-gradient(180deg,var(--surf),var(--surf2))!important;
 transition:border-color .15s ease,transform .15s ease}
.t6todas:hover{border-color:var(--acc)!important;transform:translateY(-1px)}
.hbox.t6esconde,section.t6esconde{display:none!important}
.t6jgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.t6j{position:relative;border:1px solid var(--line);border-radius:16px;padding:16px 18px;
 background:linear-gradient(150deg,var(--surf),var(--surf2));overflow:hidden}
.t6j:before{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:var(--acc)}
.t6j{display:flex;gap:14px;align-items:flex-start}
.t6jtx{min-width:0;flex:1}
/* item 24 (Luis, 18/08): "a foto ficou pequena, tem espaco pra ficar maior" */
.t6jfoto{width:96px;height:128px;object-fit:cover;border-radius:11px;flex:0 0 auto;
 background:var(--line2);border:1px solid var(--line)}
.t6flfoto{width:40px;height:54px;object-fit:cover;border-radius:7px;
 background:var(--line2);border:1px solid var(--line)}
.t6j .t6jr{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10.5px;color:var(--txt3);
 letter-spacing:1.2px}
.t6j .t6jn{font-size:17px;font-weight:700;color:var(--txt);margin:3px 0 2px}
.t6j .t6jf{font-size:12px;color:var(--txt2);margin-bottom:10px}
.t6j .t6jp{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:29px;font-weight:600;color:var(--acc);
 line-height:1}
.t6j .t6jp s{text-decoration:none;font-size:15px}
.t6j .t6jb{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10.5px;color:var(--txt3);margin-top:8px}
.t6j .t6jpos{position:absolute;top:14px;right:14px;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;
 font-size:10.5px;font-weight:600;color:var(--acc);border:1px solid var(--line);
 border-radius:7px;padding:3px 8px;background:var(--accbg)}
.t6setor{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10px;letter-spacing:1.8px;
 text-transform:uppercase;color:var(--txt3);margin:16px 0 8px}
.t6fgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.t6fn{border:1px solid var(--line);border-radius:14px;padding:13px 14px;background:var(--surf2)}
.t6fnt{display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin-bottom:9px;
 cursor:pointer}
.t6fnt b{font-size:13.5px;color:var(--txt);font-weight:600}
.t6fnt span{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10.5px;color:var(--txt3)}
.t6fnt:hover span{color:var(--acc)}
.t6fl{display:grid;grid-template-columns:14px 40px 1fr auto auto;gap:10px;align-items:center;
 padding:5px 0;border-top:1px solid var(--line2);cursor:pointer}
.t6fl:hover b{color:var(--acc)}
.t6fl i{font-style:normal;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10.5px;color:var(--txt3)}
.t6fl b{font-size:12.5px;font-weight:500;color:var(--txt);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.t6fl u{text-decoration:none;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:12.5px;
 font-weight:600;color:var(--acc)}
.t6fl s{text-decoration:none;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10.5px;color:var(--txt3);
 min-width:52px;text-align:right}
</style>
"""

T6_JS2 = """
<script>
/* ETAPA 2 · O INICIO — o bloco de destaque, a faixa da build e o Top 3 de cada
   funcao. Tudo entra DEPOIS do homeRender, sem reescrever o homeRender: ele
   continua sendo o dono dos Lancamentos e do Top 3 do jogo. */
(function(){
  var TODAS=false;
  /* ⛔ OS CORTES DO VEREDICTO MORAM AQUI. Medidos na distribuicao real do
     % do topo; para mudar, muda esta linha e mais nada. */
  window.T6_CORTES = window.T6_CORTES || [99, 95];
  function n2(v){ return (Math.round(v*100)/100).toFixed(2); }   /* ponto, item 10 */
  function pt(v){ return (v||0).toLocaleString('pt-BR'); }
  function vaFuncao(f){
    var el=document.querySelector('.tab[data-t="'+f+'"]');
    if(el){ el.click(); }
    try{ homeToggle(0); }catch(e){}
    window.scrollTo(0,0);
  }
  function topo3(){
    /* melhor card por nome, dentro de cada funcao */
    var por={};
    for(var i=0;i<D.length;i++){
      var c=D[i]; if(!c || c.id==='MOLDE' || !c.tipo) continue;
      var v; try{ v=nota(c); }catch(e){ continue; }
      if(!(v>0)) continue;
      var g=por[c.tipo]||(por[c.tipo]={}), k=c.nome||c.id;
      if(!g[k] || v>g[k][1]) g[k]=[c,v];
    }
    var saida=[];
    for(var f in por){
      var lst=Object.keys(por[f]).map(function(k){return por[f][k];})
               .sort(function(a,b){return b[1]-a[1];}).slice(0,3);
      var t=0; try{ t=topoDoTipo(f)||0; }catch(e){}
      saida.push([f,lst,t]);
    }
    return saida.sort(function(a,b){ return a[0].localeCompare(b[0],'pt-BR'); });
  }
  function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
  /* ⛔ TODO CARD TEM FOTO. Ordem do Luis, 18/08: "tem vários cards do mesmo
     jogador, só o nome não identifica." O endereço e o mesmo que a casca ja usa. */
  window.t6Foto = function(c, cls){
    if(!c || !c.id) return '';
    return '<img class="'+(cls||'t6foto')+'" loading="lazy" src="'
      + 'https://efimg.com/efootballhub22/images/player_cards/'
      + String(c.id).split('@')[0] + '_l.png" '
      + 'onerror="this.style.visibility=&quot;hidden&quot;">';
  };
  function foto(c, cls){ return window.t6Foto(c, cls); }

  function hero(){
    var q=(typeof CONT!=='undefined')?CONT:{};
    return '<div class="t6hero">'
     + '<div class="t6kk">antes de contratar</div>'
     + '<h2>Quer saber se vale a pena gastar seus pontos?</h2>'
     + '<p>A melhor build de cada card, testada por IA em milh&otilde;es de combina&ccedil;&otilde;es. '
     + '<b>' + pt(q.cards||0) + '</b> cards medidos em <b>19</b> fun&ccedil;&otilde;es: '
     + 'voc&ecirc; sabe quanto rende <b>antes</b> de gastar GP.</p>'
     + '<div class="t6cta"><button class="t6b1" id=t6h1>Abrir o elenco &rarr;</button>'
     + '<button class="t6b2" id=t6h2>Ver o ranking geral &rarr;</button></div></div>';
  }
  function faixa(){
    return '<div class="t6faixa"><div>'
     + '<div class="t6kk">build pronta</div>'
     + '<h3>Voc&ecirc; n&atilde;o precisa mais ficar indeciso</h3>'
     + '<p>Barras, &iacute;mpeto, t&eacute;cnico e habilidades j&aacute; resolvidos em cada card. '
     + 'A build que o motor escolheu &eacute; a que d&aacute; a maior nota naquela fun&ccedil;&atilde;o.</p>'
     + '</div><button class="t6b1" id="t6otm">Otimizar meus cards &rarr;</button></div>';
  }
  function blocoFuncoes(){
    var L=topo3(); if(!L.length) return '';
    /* item 3: as 19 fun&ccedil;&otilde;es AGRUPADAS POR SETOR. O setor sai da propria
       barra lateral (t6Setor), entao nao existe segunda lista aqui. */
    var SET={}, ordem=[];
    try{ SET=window.t6Setor?window.t6Setor():{}; }catch(e){}
    var porSetor={};
    for(var s=0;s<L.length;s++){
      var st=SET[L[s][0]]||'OUTRAS';
      if(!porSetor[st]){ porSetor[st]=[]; ordem.push(st); }
      porSetor[st].push(L[s]);
    }
    var pref=['GOLEIRO','DEFESA','MEIO','ATAQUE'];
    ordem.sort(function(a,b){
      var ia=pref.indexOf(a), ib=pref.indexOf(b);
      return (ia<0?9:ia)-(ib<0?9:ib);
    });
    var h='<section class="hbloco t6fns"><div class=htt><h2>Top 3 de cada fun&ccedil;&atilde;o</h2>'
      + '<span class=hsub>' + L.length + ' fun&ccedil;&otilde;es &middot; clique para abrir o ranking da fun&ccedil;&atilde;o</span>'
      + '</div>';
    for(var o=0;o<ordem.length;o++){
      h += '<div class="t6setor">'+esc(ordem[o])+'</div><div class="t6fgrid">'
         + blocoDoSetor(porSetor[ordem[o]]) + '</div>';
    }
    return h+'</section>';
  }
  function blocoDoSetor(L){
    var h='';
    for(var i=0;i<L.length;i++){
      var f=L[i][0], lst=L[i][1], t=L[i][2];
      h+='<div class="t6fn"><div class="t6fnt" data-f="'+esc(f)+'"><b>'+esc(f)+'</b><span>ranking &rarr;</span></div>';
      for(var j=0;j<lst.length;j++){
        var c=lst[j][0], v=lst[j][1], p=t>0?(100*v/t):0;
        h+='<div class="t6fl" data-k="'+esc(c.id+'|'+c.tipo)+'"><i>'+(j+1)+'</i>'
         + foto(c,'t6flfoto') + '<b>'+esc(c.nome)+'</b>'
         + '<u>'+n2(v)+'</u><s>'+n2(p)+'%</s></div>';
      }
      h+='</div>';
    }
    return h;
  }

  function blocoJogo(){
    var m=[];
    for(var i=0;i<D.length;i++){
      var c=D[i]; if(!c||c.id==='MOLDE'||!c.tipo) continue;
      var v; try{ v=nota(c); }catch(e){ continue; }
      if(v>0) m.push([c,v]);
    }
    m.sort(function(a,b){return b[1]-a[1];});
    var vistos={}, top=[];
    for(var j=0;j<m.length && top.length<3;j++){
      var k=m[j][0].nome||m[j][0].id;
      if(vistos[k]) continue;
      vistos[k]=1; top.push(m[j]);
    }
    if(!top.length) return '';
    var h='<section class="hbloco t6jogo"><div class=htt><h2>Top 3 do jogo</h2>'
      + '<span class=hsub>as tr&ecirc;s maiores pontua&ccedil;&otilde;es entre todas as fun&ccedil;&otilde;es</span>'
      + '</div><div class="t6jgrid">';
    for(var i=0;i<top.length;i++){
      var c=top[i][0], v=top[i][1], t=0; try{ t=topoDoTipo(c.tipo)||0; }catch(e){}
      var p=t>0?(100*v/t):0, s=n2(v).split('.');
      h+='<div class="t6j" data-k="'+esc(c.id+'|'+c.tipo)+'">'
       + '<div class="t6jpos">'+esc(c.np||c.pos||'')+'</div>'
       + foto(c,'t6jfoto')
       + '<div class="t6jtx">'
       + '<div class="t6jr">'+(i+1)+'\u00ba lugar</div>'
       + '<div class="t6jn">'+esc(c.nome)+'</div>'
       + '<div class="t6jf">'+esc(c.tipo)+(c.modelo?(' \u00b7 '+esc(c.modelo)):'')+'</div>'
       + '<div class="t6jp">'+s[0]+'<s>.'+s[1]+'</s></div>'
       + '<div class="t6jb">'+n2(p)+'% do topo'+(c.pacote?(' \u00b7 '+esc(c.pacote)):'')+'</div>'
       + '</div></div>';
    }
    return h+'</div></section>';
  }

  /* ⛔ UMA FUNCAO SO: o Inicio e a aba Boxes atuais carimbam o mesmo
     veredicto, e duas copias iam divergir na primeira mudanca. */
  function veredicto(w, sec){
    try{
      var ix={};
      for(var i=0;i<D.length;i++){ var c=D[i]; if(c&&c.id&&c.tipo) ix[c.id+'|'+c.tipo]=c; }
      w.querySelectorAll('.hbox .cd[data-k], .grade .cd[data-k]').forEach(function(el){
        if(el.querySelector('.t6ver')) return;
        var c=ix[el.dataset.k]; if(!c) return;
        var t=0; try{ t=topoDoTipo(c.tipo)||0; }catch(e){}
        if(!(t>0)) return;
        var p=100*nota(c)/t;
        /* item 3 · a escala de preco (Luis, 18/08): "todo card vale a pena
           dependendo do preco". Os cortes vivem em T6_CORTES, medidos, nao
           chutados — e mudam num lugar so. */
        var C=window.T6_CORTES||[99,95];
        var q=(p>=C[0])?['CONTRATAR A QUALQUER CUSTO','t6ver1']
             :((p>=C[1])?['CONTRATAR SE FOR BARATO','t6ver2']
                        :['CONTRATAR SE FOR GR\u00c1TIS','t6ver3']);
        var d=document.createElement('div');
        d.className='t6ver '+q[1]; d.textContent=q[0];
        var rod=el.querySelector('.t6rod');
        if(rod) rod.insertBefore(d, rod.firstChild);
        else { var alvo=el.querySelector('.mi')||el;
               alvo.parentNode.insertBefore(d, alvo.nextSibling); }
      });
      var tt2=sec?sec.querySelector('.htt h2'):null;
      if(tt2 && !tt2.parentNode.querySelector('.t6i')){
        var iel=document.createElement('span'); iel.className='t6i'; iel.textContent='i';
        var C2=window.T6_CORTES||[99,95];
        iel.title='A conta e o % do topo da fun\u00e7\u00e3o. '
                + 'A QUALQUER CUSTO: '+C2[0]+'% ou mais \u00b7 '
                + 'SE FOR BARATO: entre '+C2[1]+'% e '+C2[0]+'% \u00b7 '
                + 'SE FOR GR\u00c1TIS: abaixo de '+C2[1]+'%';
        tt2.appendChild(iel);
      }
    }catch(e){}

  }

  function enfeita(){
    var w=document.getElementById('homewrap');
    if(!w || w.style.display==='none' || !w.innerHTML) return;
    if(window._t6cc) return;            /* a aba Como calculamos manda no painel */
    if(window.T6TELAS) return;          /* ⛔ as telas da designer mandam agora */
    /* ⛔ item 4 · nada de trabalho repetido — mas a trava NAO pode ser uma
       assinatura do estado: quando o homeRender limpa o painel, o estado volta
       a ser um que ja foi visto e o bloco nunca mais nasceria. Cada pedaco
       tem a sua propria pergunta ("ja existe?"), logo abaixo. Custo por volta:
       meia duzia de querySelector. */
    if(window.HOME_CHEIA){
      /* item 18 · a box aberta em tela cheia tambem leva o veredicto.
         Antes eu saia daqui antes de carimbar, e a etiqueta sumia justo na
         tela em que o Luis decide se contrata. */
      veredicto(w, w.querySelector('.hbloco'));
      return;
    }
    if(window._t6box){                          /* boxes anteriores: so a lista */
      var v=w.querySelector('.t6hero'); if(v) v.remove();
      var f=w.querySelector('.t6faixa'); if(f) f.remove();
      var s=w.querySelector('.t6fns'); if(s) s.remove();
      var jg=w.querySelector('.t6jogo'); if(jg) jg.remove();
      var bx=w.getElementsByClassName('hbox');
      for(var i=0;i<bx.length;i++) bx[i].classList.remove('t6esconde');
      var bb=w.querySelector('.t6todas'); if(bb) bb.remove();
      return;
    }
    if(window._t6abaBox){
      /* ABA PROPRIA DAS BOXES ATUAIS (item 8): so a lista, e todas elas. */
      ['.t6hero','.t6faixa','.t6jogo','.t6fns','.t6todas'].forEach(function(s){
        var e=w.querySelector(s); if(e) e.remove(); });
      var vel=w.querySelectorAll('section.hbloco');
      for(var vi=0;vi<vel.length;vi++){
        var h2v=vel[vi].querySelector('.htt h2');
        if(h2v && /Top 3 de cada/.test(h2v.textContent)) vel[vi].classList.add('t6esconde');
      }
      var bxs=w.getElementsByClassName('hbox');
      for(var bi=0;bi<bxs.length;bi++) bxs[bi].classList.remove('t6esconde');
      var h2b=w.querySelector('.hbloco .htt h2');
      if(h2b && h2b.textContent!=='Boxes atuais') h2b.textContent='Boxes atuais';
      veredicto(w, w.querySelector('.hbloco'));
      return;
    }
    if(!w.querySelector('.t6hero')) w.insertAdjacentHTML('afterbegin', hero());
    var sec=w.querySelector('.hbloco');
    if(sec && !w.querySelector('.t6faixa')) sec.insertAdjacentHTML('afterend', faixa());
    /* ⛔ O PODIO VELHO E O MESMO ASSUNTO. O bloco "Top 3 de cada funcao" com os
       degraus dourados e do turno 3; o arquivo do turno 6 pede a lista curta.
       Some da tela, mas continua sendo montado pelo homeTop3 — voltar e apagar
       uma linha. */
    var velhos=w.querySelectorAll('section.hbloco');
    for(var i=0;i<velhos.length;i++){
      var ht=velhos[i].querySelector('.htt h2');
      if(ht && /Top 3 de cada/.test(ht.textContent) && !velhos[i].classList.contains('t6fns'))
        velhos[i].classList.add('t6esconde');
    }
    if(!w.querySelector('.t6jogo')) w.insertAdjacentHTML('beforeend', blocoJogo());
    if(!w.querySelector('.t6fns')) w.insertAdjacentHTML('beforeend', blocoFuncoes());

    /* 3 de N boxes, com o botao de ver todas.
       ⛔ QUEM MANDA NO display DAS BOXES E O aplica() DO PATCH DAS BOXES, e ele
          roda a cada 1,2s. Brigar com ele no style inline da pisca. Entao aqui
          se esconde por CLASSE com !important — o inline dele perde, e a lista
          de quais boxes estao no ar sai do BOXATIVA, nao do que esta na tela. */
    if(sec){
      var ativas={}; try{ for(var a=0;a<BOXATIVA.length;a++) ativas[BOXATIVA[a]]=1; }catch(e){}
      var caixas=[].slice.call(sec.getElementsByClassName('hbox')).filter(function(e){
        var n=e.querySelector('.hboxn'); return n && ativas[n.textContent.trim()];
      });
      if(!sec.querySelector('.t6todas')){
        var b=document.createElement('button'); b.className='t6todas';
        b.onclick=function(){ TODAS=!TODAS; enfeita(); };
        sec.appendChild(b);        /* botao GRANDE, no fim do bloco */
      }
      var bt=sec.querySelector('.t6todas');
      /* item 15 (Luis, 18/08): "poe 4 box aqui na previsualizacao" */
      var QUANTAS_NA_PREVIA = 4;
      for(var i=0;i<caixas.length;i++)
        caixas[i].classList.toggle('t6esconde', !TODAS && i>=QUANTAS_NA_PREVIA);
      if(bt) bt.textContent = TODAS
        ? ('\\u2190 mostrar s\\u00f3 ' + QUANTAS_NA_PREVIA + ' de ' + caixas.length)
        : ('ver as outras ' + Math.max(0, caixas.length - QUANTAS_NA_PREVIA)
           + ' boxes atuais \\u2192');
    }

    veredicto(w, sec);

    /* os cliques */
    var h1=document.getElementById('t6h1');
    if(h1) h1.onclick=function(){ try{ homeToggle(0); }catch(e){} window.scrollTo(0,0); };
    var h2=document.getElementById('t6h2');
    if(h2) h2.onclick=function(){ vaFuncao('\\u2605 GERAL'); };
    var ot=document.getElementById('t6otm');
    if(ot) ot.onclick=function(){ try{ if(!document.getElementById('mtwrap').offsetParent) mtToggle(); }catch(e){} window.scrollTo(0,0); };
    w.querySelectorAll('.t6fnt').forEach(function(el){
      el.onclick=function(){ vaFuncao(el.dataset.f); }; });
    w.querySelectorAll('.t6fl,.t6j').forEach(function(el){
      el.onclick=function(){ try{ abrir(el.dataset.k); }catch(e){} }; });
  }

  if(typeof window.homeRender==='function'){
    var _hr=window.homeRender;
    window.homeRender=function(){ var r=_hr.apply(this,arguments); try{ enfeita(); }catch(e){} return r; };
  }
  setInterval(function(){ try{ enfeita(); }catch(e){} }, 2000);
})();
</script>
"""


T6_CSS3 = """
<style id=t6css3>
/* ==========================================================================
   ETAPA 3 · O ELENCO E A FICHA no desenho do turno 6
   O Luis, 18/08: "voce subiu so um pedaco dele. Deixou o modal fora, o elenco
   fora. Boa parte do site ta operando com design antigo."
   Aqui nada de estrutura muda: sao as mesmas classes que a casca ja monta.
   O que muda e cor, fonte, canto e sombra — e o AZUL some, porque ele nao
   existe na paleta do arquivo.
   ⛔ Muito !important de proposito: metade destas cores esta em style inline
      dentro do HTML gerado, e inline so perde para !important.
   ========================================================================== */

/* ---------------- o card do elenco ---------------- */
html[data-tema] .cd{
 background:linear-gradient(160deg,var(--surf),var(--surf2))!important;
 border:1px solid var(--line)!important;border-radius:14px!important;
 box-shadow:0 6px 20px var(--sombra)!important;overflow:hidden;
 transition:transform .15s ease,border-color .15s ease}
html[data-tema] .cd:hover{transform:translateY(-2px);border-color:var(--acc)!important}
html[data-tema] .cd:before{display:none!important}          /* a tarja escura sai */
html[data-tema] .cd .rk,html[data-tema] .cd .ovx{
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;font-size:10.5px!important;
 letter-spacing:.6px;color:var(--txt3)!important;background:transparent!important;
 border:none!important;padding:0!important}
html[data-tema] .cd .nt{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;
 font-weight:600!important;letter-spacing:-.5px}
/* item 17 (Luis, 18/08): "ta escondendo informacao, pontuacao 83..." — os
   centavos ficavam minusculos e apagados. Menores sim, ilegiveis nao. */
html[data-tema] .cd .ndec{font-size:.72em!important;opacity:1!important}
html[data-tema] .ntsub{font-size:12px!important;color:var(--txt2)!important}
html[data-tema] .ntsub .ndec{font-size:.86em!important;opacity:1!important;font-weight:700}
html[data-tema] .t6bp s,html[data-tema] .t6jp s{opacity:1}
/* item 22 (Luis, 18/08): "colocar o nome do jogador maior tambem" */
html[data-tema] .cd .nm{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;
 font-weight:700!important;color:var(--txt)!important;font-size:15.5px!important;
 line-height:1.25!important;margin-top:4px!important}
html[data-tema] .cd.cdbx .nm{font-size:16.5px!important}
html[data-tema] .cd.cdbx .nt{font-size:30px!important;letter-spacing:-.6px}
html[data-tema] .cd .mi,html[data-tema] .cd .ntsub{color:var(--txt2)!important}
html[data-tema] .cd .tg,html[data-tema] .cd .tags span{
 border-radius:999px!important;border:1px solid var(--line)!important;
 background:var(--surf2)!important;color:var(--txt2)!important;
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;font-size:9.5px!important}
/* a barrinha dos blocos: o azul vira o verde da paleta */
html[data-tema] .mb{border-radius:999px!important;overflow:hidden;height:4px!important}
html[data-tema] .mb>div:nth-child(1){background:var(--acc)!important}
html[data-tema] .mb>div:nth-child(2){background:var(--acc2)!important}
html[data-tema] .mb>div:nth-child(3){background:var(--dourado)!important}
html[data-tema] .mb>div:nth-child(4){background:#e0533d!important}

/* ---------------- a ficha do card (o modal) ---------------- */
html[data-tema] #box{
 background:linear-gradient(180deg,var(--surf),var(--surf2))!important;
 border:1px solid var(--line)!important;border-radius:18px!important;
 box-shadow:0 30px 80px var(--sombra)!important}
html[data-tema] #box .close{color:var(--txt2)!important;font-size:22px!important}
html[data-tema] #box .close:hover{color:var(--acc)!important}
html[data-tema] .fhdnome>div{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;font-weight:700!important;
 letter-spacing:-.3px}
html[data-tema] .fhdnat,html[data-tema] .fhd .mini{
 background:var(--surf2)!important;border:1px solid var(--line)!important;
 border-radius:12px!important}
html[data-tema] .pslb,html[data-tema] .fhdbtstt,html[data-tema] .fhdl,
html[data-tema] .grptt,html[data-tema] .receitatt,html[data-tema] .iasub{
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;letter-spacing:1.4px!important;
 text-transform:uppercase;color:var(--txt3)!important}
html[data-tema] .fhdsig{color:var(--acc)!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] .fhddt,html[data-tema] .fhdovr{color:var(--txt2)!important;
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] .fhdovr b{color:var(--txt)!important}
/* o bloco da pontuacao: o numero grande em ambar, o % do topo em verde */
html[data-tema] .fhdnota{background:linear-gradient(160deg,var(--surf2),var(--surf))!important;
 border:1px solid var(--line)!important;border-radius:14px!important}
html[data-tema] .fhdn{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;
 color:var(--dourado)!important;font-weight:600!important}
html[data-tema] .fhdtopo b{color:var(--acc)!important}
html[data-tema] .fhdmel{color:var(--txt3)!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}

/* os botoes das funcoes — o azul do nativo vira o verde da paleta */
html[data-tema] .cbfn{border-radius:11px!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] .cbfn b{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] .cbfnq{border-color:var(--acc)!important;
 box-shadow:0 0 0 1px var(--accbg)!important}
html[data-tema] .cbnat{background:var(--acc)!important;color:var(--onacc)!important;
 border-color:var(--acc)!important;box-shadow:0 0 0 2px var(--accbg)!important}
html[data-tema] .cbfab{box-shadow:inset 0 0 0 2px var(--dourado)!important}
html[data-tema] .cbsec{background:var(--surf)!important;color:var(--txt)!important;
 border-color:var(--line)!important}
html[data-tema] .cboff{background:var(--line2)!important;color:var(--txt3)!important;
 border-color:transparent!important}
html[data-tema] .cbcampo{background:linear-gradient(180deg,var(--surf2),var(--surf))!important;
 border:1px solid var(--line)!important;border-radius:14px!important}
html[data-tema] .cbnv{color:var(--txt2)!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] .cbnv b{color:var(--acc)!important}
html[data-tema] .cbp{border-radius:8px!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}

/* habilidades, tecnico, impeto: tudo em pilula */
html[data-tema] #box .chip,html[data-tema] #box .chips span{
 border-radius:999px!important;border:1px solid var(--line)!important;
 background:var(--surf2)!important;color:var(--txt)!important}
html[data-tema] #box select,html[data-tema] #box input{
 background:var(--surf2)!important;color:var(--txt)!important;
 border:1px solid var(--line)!important;border-radius:10px!important;
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] #box .bpan,html[data-tema] #box .receita,html[data-tema] #box .pvbox{
 background:var(--surf2)!important;border:1px solid var(--line)!important;
 border-radius:14px!important}
html[data-tema] #box .bn,html[data-tema] #box .bnum,html[data-tema] #box .ptsbig,
html[data-tema] #box .bhdnum{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] #box .bp,html[data-tema] #box .bp2{border-radius:999px!important}
html[data-tema] #box .bp>i,html[data-tema] #box .bp2>i{background:var(--acc)!important}
/* as tabelas de atributos */
html[data-tema] #box table th,html[data-tema] #box .athead{
 background:var(--surf2)!important;color:var(--txt3)!important;
 border-bottom:1px solid var(--line)!important;
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;letter-spacing:1px!important;
 text-transform:uppercase}
html[data-tema] #box table td{border-color:var(--line2)!important}
html[data-tema] #box .up{color:var(--acc)!important}
html[data-tema] #box .dn{color:#e0533d!important}
/* o botao de voltar e os dois grandes */
html[data-tema] #voltar{background:linear-gradient(180deg,var(--acc),var(--acc2))!important;
 color:var(--onacc)!important;border:none!important;border-radius:11px!important;
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;font-weight:600!important;
 box-shadow:0 8px 24px var(--sombra)!important}
html[data-tema] #box .encaba{border-radius:11px!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;
 background:var(--surf2)!important;border:1px solid var(--line)!important;color:var(--txt2)!important}
html[data-tema] #box .encabaon{background:linear-gradient(180deg,var(--acc),var(--acc2))!important;
 color:var(--onacc)!important;border-color:transparent!important;font-weight:600!important}

/* ---------------- o azul que sobrou ---------------- */
/* o retangulo grande da funcao no alto da ficha vinha #1553c8 com !important */
html[data-tema] .fhdestbox{
 background:linear-gradient(180deg,var(--acc),var(--acc2))!important;
 color:var(--onacc)!important;border:1px solid transparent!important;
 border-radius:12px!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important;
 font-weight:700!important;letter-spacing:-.2px}
html[data-tema] .fhdbasico{background:var(--surf)!important;color:var(--dourado)!important;
 border:1px solid var(--line)!important;border-radius:999px!important}

/* ---------------- a barra lateral so no Ranking ---------------- */
/* Ordem do Luis, 18/08: "essa barra lateral vai passar a existir agora somente
   na aba ranking". Nas outras abas ela sai e a tela ocupa a largura inteira. */
html.t6semlat #filtros,html.t6semlat #navbt{display:none!important}
html.t6semlat header,html.t6semlat main{margin-left:0!important}
html.t6semlat main{padding-left:22px!important;padding-right:22px!important}

/* o azul do botao da funcao escolhida: azul so vale para SIGLA DE POSICAO */
html[data-tema] .cbfnq{background:linear-gradient(180deg,var(--acc),var(--acc2))!important;
 border-color:var(--acc)!important;color:var(--onacc)!important;
 box-shadow:0 0 0 2px var(--accbg)!important}
html[data-tema] .cbfnq i,html[data-tema] .cbfnq u,html[data-tema] .cbfnq b{color:var(--onacc)!important}
/* a sigla da posicao — o unico azul que fica */
html[data-tema] .hpos,html[data-tema] .fhdsig,html[data-tema] .t6jpos{color:#6ea8ff!important}
html[data-tema] .t6jpos{border-color:rgba(110,168,255,.35)!important;background:rgba(110,168,255,.10)!important}

/* ---------------- o veredicto de contratacao ---------------- */
.t6rod{display:flex;align-items:center;justify-content:space-between;gap:6px 8px;
 flex-wrap:wrap;margin-top:10px;padding-top:9px;border-top:1px solid var(--line2)}
.t6pct{font-weight:700;font-size:12.5px;white-space:nowrap;margin-left:auto}
.t6pct .ndec{font-size:.78em;opacity:1}
.t6ver{display:inline-block;margin:0;white-space:nowrap;font-size:9px;padding:3px 7px;padding:3px 9px;border-radius:999px;
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:9.5px;font-weight:600;
 letter-spacing:1px;text-transform:uppercase;white-space:nowrap}
.t6ver1{background:var(--accbg);color:var(--acc);border:1px solid var(--acc)}
.t6ver2{background:rgba(240,180,41,.12);color:var(--dourado);border:1px solid var(--dourado)}
html[data-tema=claro] .t6ver2{background:rgba(138,90,0,.08)}
html[data-tema=claro] .t6ver1{background:rgba(10,125,79,.09)}
.t6ver3{background:var(--line2);color:var(--txt3);border:1px solid var(--line)}
.t6i{display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;
 margin-left:8px;border-radius:999px;border:1px solid var(--line);color:var(--txt3);
 font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10px;cursor:help;vertical-align:middle}
.t6i:hover{color:var(--acc);border-color:var(--acc)}
</style>
"""


T6_JS3 = """
<script>
/* ETAPA 3 · a barra lateral so existe no Ranking. */
(function(){
  function ver(id){ var e=document.getElementById(id); return !!(e && e.offsetParent!==null); }
  function aplica(){
    var noRanking = !ver('homewrap') && !ver('mtwrap');
    document.documentElement.classList.toggle('t6semlat', !noRanking);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',aplica);
  else aplica();
  setInterval(aplica, 600);
})();
</script>
"""


T6_CSS4 = """
<style id=t6css4>
/* ==========================================================================
   ETAPA 4 · o resto do arquivo de orientacoes
   ========================================================================== */

/* --- 5. Ranking: top 3 em cards grandes, do 4o em diante a grade ---
   A grade vira de 6 colunas: o molde ocupa a linha inteira, os tres primeiros
   ocupam duas colunas cada (uma linha so, lado a lado) e o resto flui de seis
   em seis. Sem isso o "span 2" empurrava o terceiro para a linha de baixo. */
@media(min-width:1100px){
 html[data-tema] #out .grade{grid-template-columns:repeat(6,minmax(0,1fr))!important;
  align-items:start}
 html[data-tema] #out .grade>#moldecd{grid-column:span 6}
 html[data-tema] #out .grade>#moldecd~.cd:nth-child(-n+4){grid-column:span 2;min-height:210px}
}
html[data-tema] #out .grade>#moldecd~.cd:nth-child(-n+4) .nt{font-size:2.1em!important}
html[data-tema] #out .grade>#moldecd~.cd:nth-child(-n+4) .nm{font-size:1.25em!important}
/* as etiquetas do podio: 1o verde, 2o ambar, 3o azul (item 5) */
html[data-tema] #out .grade>#moldecd~.cd:nth-child(2) .rk{color:var(--acc)!important}
html[data-tema] #out .grade>#moldecd~.cd:nth-child(3) .rk{color:var(--dourado)!important}
html[data-tema] #out .grade>#moldecd~.cd:nth-child(4) .rk{color:#6ea8ff!important}

/* --- 6. Ficha: coluna da esquerda fixa, estilo em ambar --- */
html[data-tema] #box .fhdcol{position:sticky;top:8px;align-self:flex-start}
html[data-tema] #box .fhdestbox{background:linear-gradient(180deg,var(--dourado),#c98a1f)!important;
 color:#1b1405!important}
html[data-tema] #box .fhdpos{color:var(--txt)!important}

/* --- 7. Meu time ---
   ⛔ O CAMPO JA E VERTICAL E JA TEM AS MARCACOES DE VERDADE (as classes
      r-borda, r-meio, r-circulo, r-areaG, r-areaP, r-pena sao da casca).
      Nao se desenha marcacao de novo aqui — seria a segunda verdade, e as
      duas apareceriam sobrepostas. O que falta e so o acabamento. */
html[data-tema] #mtwrap .mtcampo{
 max-width:660px;margin:0 auto;border:1px solid var(--line)!important;
 border-radius:16px!important;
 background:linear-gradient(180deg,#12281d,#0e2018)!important}
html[data-tema] #mtwrap .risco,html[data-tema] #mtwrap .r-borda,
html[data-tema] #mtwrap .r-meio,html[data-tema] #mtwrap .r-circulo,
html[data-tema] #mtwrap .r-areaG,html[data-tema] #mtwrap .r-areaP{
 border-color:rgba(255,255,255,.16)!important}
/* as 11 vagas sao cards QUADRADOS (item 7) */
html[data-tema] #mtwrap .elvagafixa,html[data-tema] #mtwrap .elvazia,
html[data-tema] #mtwrap .elvazio{aspect-ratio:1!important;border-radius:12px!important}
html[data-tema] #mtwrap .elcard{border-radius:12px!important;border:1px solid var(--line)!important;
 background:linear-gradient(160deg,var(--surf),var(--surf2))!important}
/* o banco de reservas em duas colunas, ate 12 */
html[data-tema] #mtwrap .mtbanco{display:grid!important;
 grid-template-columns:1fr 1fr!important;gap:8px!important}
html[data-tema] #mtwrap .mtfora,html[data-tema] #mtwrap .mtforagrid{width:100%!important}
html[data-tema] #mtwrap .eleyebrow{color:var(--txt3)!important}
html[data-tema] #mtwrap .elnota2,html[data-tema] #mtwrap .elpt,
html[data-tema] #mtwrap .elnum{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] #mtwrap .elfn{text-transform:uppercase;letter-spacing:.4px}

/* --- 9. Como calculamos --- */
.t6cc{display:flex;flex-direction:column;gap:22px}
.t6ccbig{border:1px solid var(--line);border-radius:18px;padding:26px 28px;
 background:radial-gradient(700px 300px at 88% 10%,var(--accbg),transparent 66%),
            linear-gradient(120deg,var(--surf),var(--surf2));
 display:flex;gap:26px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.t6ccbig h2{margin:0 0 8px;font-size:26px;font-weight:700;color:var(--txt)}
.t6ccbig p{margin:0;color:var(--txt2);font-size:13.5px;max-width:620px;line-height:1.6}
.t6ccnums{display:flex;gap:10px;flex-wrap:wrap}
.t6ccn{border:1px solid var(--line);border-radius:14px;padding:12px 18px;background:var(--surf2);min-width:120px}
.t6ccn u{text-decoration:none;display:block;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;
 font-size:9.5px;letter-spacing:1.4px;text-transform:uppercase;color:var(--txt3);margin-bottom:4px}
.t6ccn b{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:23px;font-weight:600;color:var(--txt)}
.t6ccn.ok b{color:var(--dourado)}
.t6ccpassos{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.t6ccp{border:1px solid var(--line);border-radius:14px;padding:16px 18px;background:var(--surf2)}
.t6ccp i{font-style:normal;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:19px;
 font-weight:600;color:var(--acc)}
.t6ccp.q i{color:var(--dourado)}
.t6ccp b{display:block;margin:8px 0 6px;font-size:14px;color:var(--txt)}
.t6ccp span{font-size:12.5px;color:var(--txt2);line-height:1.55}
.t6ccduo{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.t6ccbox{border:1px solid var(--line);border-radius:16px;padding:18px 20px;background:var(--surf2)}
.t6ccbox h3{margin:0 0 14px;font-size:15px;color:var(--txt)}
.t6ccl{display:grid;grid-template-columns:150px 1fr auto;gap:10px;align-items:center;margin-bottom:9px;
 font-size:12.5px;color:var(--txt2)}
.t6ccbar{height:7px;border-radius:999px;background:var(--line2);overflow:hidden}
.t6ccbar>i{display:block;height:100%;background:linear-gradient(90deg,var(--acc),var(--acc2))}
.t6ccl u{text-decoration:none;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;color:var(--txt);font-size:12px}
.t6ccfonte{display:flex;gap:9px;align-items:flex-start;margin-bottom:9px;font-size:12.5px;color:var(--txt2)}
.t6ccfonte i{font-style:normal;color:var(--acc);font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif}
.t6ccfonte.nao i{color:#e0533d}

/* --- item 12 · a barra lateral no desenho novo --- */
html[data-tema=claro] #filtros,html[data-tema=escuro] #filtros{
 background:var(--surf2)!important;border-right:1px solid var(--line)!important;
 color:var(--txt)!important}
html[data-tema] #filtros .setl{color:var(--txt3)!important;font-size:9.5px!important;
 letter-spacing:1.8px!important;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif!important}
html[data-tema] #filtros .famt,html[data-tema] #filtros .fld span,
html[data-tema] #filtros .dst>b{color:var(--txt2)!important}
html[data-tema] #filtros .famt.fambt{background:transparent!important;
 border:1px solid var(--line)!important;border-radius:9px!important;color:var(--txt)!important}
html[data-tema] #filtros .tab{color:var(--txt2)!important;border-radius:8px!important;
 padding:5px 9px!important;font-size:12px!important;white-space:normal!important;
 overflow:visible!important;text-overflow:clip!important}
html[data-tema] #filtros .tab:hover{color:var(--txt)!important;background:var(--line2)!important}
html[data-tema] #filtros .tab.on,html[data-tema] #filtros .tab.sel{
 background:var(--accbg)!important;color:var(--acc)!important;font-weight:600!important}

/* --- item 11 · a tela de resultado da busca --- */
.t6bgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:12px}
.t6bcard{display:flex;gap:11px;padding:11px;border:1px solid var(--line);border-radius:14px;
 background:linear-gradient(160deg,var(--surf),var(--surf2));cursor:pointer;
 transition:transform .15s ease,border-color .15s ease}
.t6bcard:hover{transform:translateY(-2px);border-color:var(--acc)}
.t6bfoto{width:54px;height:72px;object-fit:cover;border-radius:8px;flex:0 0 auto;
 background:var(--line2);border:1px solid var(--line)}
.t6btx{min-width:0}
.t6bp{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:22px;font-weight:600;color:var(--acc);line-height:1}
.t6bp s{text-decoration:none;font-size:13px}
.t6bt{font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif;font-size:10.5px;color:var(--txt3);margin:3px 0 6px}
.t6bn{font-weight:600;font-size:13.5px;color:var(--txt);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.t6bf{font-size:11.5px;color:var(--txt2)}
.t6bf b{color:#6ea8ff;font-family:Calibri,Carlito,'Segoe UI',system-ui,sans-serif}
.t6bm{font-size:11px;color:var(--txt3)}
</style>
"""

T6_JS4 = """
<script>
/* ETAPA 4 · Boxes atuais como aba propria, Top 3 por setor, Como calculamos. */
(function(){
  function n2(v){ return (Math.round(v*100)/100).toFixed(2); }
  function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
  function pt(v){ return (v||0).toLocaleString('pt-BR'); }

  /* ---------- o setor de cada funcao sai da propria barra lateral ---------- */
  window.t6Setor = function(){
    if(window._t6set) return window._t6set;
    var m={};
    try{
      document.querySelectorAll('#filtros .setor').forEach(function(s){
        var nome=(s.querySelector('.setl')||{}).textContent||'';
        nome=nome.trim();
        if(!nome || nome==='\\u2605') return;
        s.querySelectorAll('.tab[data-t]').forEach(function(t){
          var f=t.dataset.t; if(f && f.indexOf('\\u2605')<0) m[f]=nome;
        });
      });
    }catch(e){}
    if(Object.keys(m).length) window._t6set=m;
    return m;
  };

  /* ---------- a pagina Como calculamos ---------- */
  function medias(){
    var s={b1:0,fb:0,ia:0,pr:0,es:0}, n=0;
    for(var i=0;i<D.length;i++){
      var c=D[i]; if(!c||c.id==='MOLDE') continue;
      var nb; try{ nb=notaBase(c); }catch(e){ continue; }
      var nt; try{ nt=nota(c); }catch(e){ continue; }
      s.b1+=nb; s.fb+=(c._fb||0); s.ia+=(c._ia||0); s.pr+=(c._pr||0);
      s.es+=(nt-nb-(c._fb||0)-(c._ia||0)-(c._pr||0));
      n++;
    }
    if(!n) return null;
    return {n:n, b1:s.b1/n, fb:s.fb/n, ia:s.ia/n, pr:s.pr/n, es:s.es/n};
  }
  function paginaComoCalculamos(){
    var q=(typeof CONT!=='undefined')?CONT:{}, m=medias();
    var h='<div class="t6cc">'
     + '<div class="t6ccbig"><div>'
     + '<div class="t6kk">metodologia</div>'
     + '<h2>A nota n&atilde;o &eacute; opini&atilde;o, &eacute; medi&ccedil;&atilde;o</h2>'
     + '<p>Cada card recebe uma nota por fun&ccedil;&atilde;o. A nota compara o card com o molde daquela '
     + 'fun&ccedil;&atilde;o \\u2014 o que a elite dela realmente tem \\u2014 e n&atilde;o com um ideal inventado.</p>'
     + '</div><div class="t6ccnums">'
     + '<div class="t6ccn"><u>cards medidos</u><b>'+pt(q.cards_total||0)+'</b></div>'
     + '<div class="t6ccn"><u>fun&ccedil;&otilde;es</u><b>19</b></div>'
     + '<div class="t6ccn ok"><u>linhas prontas</u><b>'+pt(q.linhas||0)+'</b></div>'
     + '</div></div>'
     + '<div class="t6ccpassos">'
     + '<div class="t6ccp"><i>01</i><b>O molde da fun&ccedil;&atilde;o</b><span>Reunimos os cards que a '
     + 'comunidade usa naquela fun&ccedil;&atilde;o e medimos o que eles t&ecirc;m de fato. Sai um alvo por '
     + 'atributo \\u2014 o retrato da elite da fun&ccedil;&atilde;o.</span></div>'
     + '<div class="t6ccp"><i>02</i><b>O peso de cada atributo</b><span>O alvo define o peso. Atributo que a '
     + 'elite tem alto pesa muito; o que ela n&atilde;o usa pesa zero. Nada de peso escolhido no chute.</span></div>'
     + '<div class="t6ccp"><i>03</i><b>A r&eacute;gua da nota</b><span>Cada atributo do card &eacute; comparado ao '
     + 'alvo em nove degraus. Ficar acima rende b&ocirc;nus, ficar abaixo do piso &eacute; punido \\u2014 n&atilde;o '
     + 'existe compensar defeito com sobra.</span></div>'
     + '<div class="t6ccp q"><i>04</i><b>O motor da build</b><span>Com a nota pronta, varremos as '
     + 'combina&ccedil;&otilde;es de barras, &iacute;mpeto, t&eacute;cnico e habilidades e devolvemos a que d&aacute; '
     + 'a maior nota naquela fun&ccedil;&atilde;o.</span></div>'
     + '</div>'
     + '<div class="t6ccduo">';
    /* o que entra na nota — medido no que esta carregado, nao chutado */
    h += '<div class="t6ccbox"><h3>O que entra na nota <span class="t6i" title="medido agora, '
       + 'na m&eacute;dia de todas as linhas carregadas">i</span></h3>';
    if(m){
      var itens=[['Bloco 1 \\u2014 atributos, habilidades, &iacute;mpeto e t&eacute;cnico', m.b1, 1],
                 ['F&iacute;sico e p&eacute;', Math.abs(m.fb)+Math.abs(m.pr), 0],
                 ['Estilo de jogo da IA', Math.abs(m.ia), 0],
                 ['Estilo ativo na fun&ccedil;&atilde;o', Math.abs(m.es), 0]];
      var tot=0; itens.forEach(function(x){ tot+=x[1]; });
      itens.forEach(function(x){
        var p=tot>0?(100*x[1]/tot):0;
        h+='<div class="t6ccl"><span>'+x[0]+'</span>'
         + '<div class="t6ccbar"><i style="width:'+p.toFixed(1)+'%"></i></div>'
         + '<u>'+n2(x[1])+' pts</u></div>';
      });
      h+='<div style="font-size:11.5px;color:var(--txt3);margin-top:10px">M&eacute;dia medida em '
       + pt(m.n)+' linhas. O peso muda de fun&ccedil;&atilde;o para fun&ccedil;&atilde;o: para um goleiro o '
       + 'f&iacute;sico pesa mais; para um ala cruzador as habilidades de cruzamento sobem.</div>';
    } else {
      h+='<div style="color:var(--txt3);font-size:12.5px">as linhas ainda est&atilde;o carregando</div>';
    }
    h+='</div>';
    h += '<div class="t6ccbox"><h3>De onde v&ecirc;m os dados</h3>'
       + '<div class="t6ccfonte"><i>\\u2192</i><span>Atributos lidos do pr&oacute;prio jogo, card por card, no '
       + 'n&iacute;vel m&aacute;ximo de treino.</span></div>'
       + '<div class="t6ccfonte"><i>\\u2192</i><span>Efeito de habilidade e &iacute;mpeto medido dentro do jogo, '
       + 'n&atilde;o estimado.</span></div>'
       + '<div class="t6ccfonte"><i>\\u2192</i><span>Molde de cada fun&ccedil;&atilde;o constru&iacute;do a partir '
       + 'dos cards que a comunidade competitiva usa nela.</span></div>'
       + '<div class="t6ccfonte nao"><i>\\u00d7</i><span>N&atilde;o usamos nota de site, voto de usu&aacute;rio '
       + 'nem opini&atilde;o de streamer.</span></div>'
       + '</div>';
    return h+'</div></div>';
  }

  /* ---------- item 8 · quantas contas o motor ja fez ----------
     ⛔ NUMERO MEDIDO, NAO CHUTADO. O motor escolhe as habilidades adicionadas
        dentro do pool da funcao: sao C(pool, adicionadas) combinacoes por linha.
        Isso e uma PARTE do trabalho dele (faltam barras, impeto e tecnico, que
        ele resolve por programacao dinamica e por isso nao da para contar
        daqui). O "i" diz exatamente isso — melhor um numero verdadeiro menor do
        que um "1.4 bi" bonito e inventado. */
  function combinacoes(){
    function C(n,k){ if(k<0||k>n) return 0; k=Math.min(k,n-k);
      var r=1; for(var i=1;i<=k;i++) r=r*(n-k+i)/i; return r; }
    var soma=0;
    for(var i=0;i<D.length;i++){
      var c=D[i]; if(!c||c.id==='MOLDE') continue;
      var p=(c.pool||[]).length, a=(c.adds||[]).length;
      if(p>0 && a>0) soma += C(p,a);
    }
    return Math.round(soma);
  }
  /* ⛔ item 23 · O NUMERO GRANDE VAI ESCRITO. Luis, 18/08: "477.252.554 o povo
     nao fixa; '477 milhoes' fixa." Entao escreve-se a grandeza por extenso, e
     ela sobe sozinha: passando de mil milhoes vira "1,2 bilhao".
     ⚠️ Hoje sao 477 MILHOES, nao bilhoes. Escrever bilhao seria mentira na
        vitrine — e e justamente este numero que sustenta a confianca. */
  function porExtenso(n){
    if(n>=1e9){
      var b=n/1e9;
      var s=(b>=10)?String(Math.round(b)):b.toFixed(1).replace('.',',');
      return s+(b<2?' bilh\u00e3o':' bilh\u00f5es');
    }
    if(n>=1e6){
      var m=Math.round(n/1e6);
      return m+' milh'+(m===1?'\u00e3o':'\u00f5es');
    }
    if(n>=1e3) return Math.round(n/1e3)+' mil';
    return String(n);
  }
  function poeContador(){
    var dir=document.getElementById('t6dir'); if(!dir) return;
    var el=document.getElementById('t6contas');
    if(!el){
      el=document.createElement('span'); el.id='t6contas';
      el.title='combina\u00e7\u00f5es de habilidades que o motor avaliou para chegar '
             + 'nestas notas. Barras, \u00edmpeto e t\u00e9cnico ele resolve por outro '
             + 'caminho e n\u00e3o entram nesta conta.';
      dir.insertBefore(el, dir.firstChild);
    }
    var n=combinacoes();
    if(n>0 && el.dataset.n!==String(n)){
      el.dataset.n=String(n);
      el.innerHTML='<b>'+porExtenso(n)+'</b> de contas do motor';
    }
    /* "linhas" e palavra de dentro de casa: o usuario nao sabe o que e.
       Vira "avaliacoes" (carta em cada funcao) e "cards avaliados". */
    var c=document.getElementById('contbar');
    if(c && typeof CONT!=='undefined'){
      var novo='<b>'+(CONT.linhas||0).toLocaleString('pt-BR')+'</b> avalia\u00e7\u00f5es'
             + ' &nbsp;\u00b7&nbsp; <b>'+(CONT.cards||0).toLocaleString('pt-BR')
             + '</b> cards avaliados';
      if(c.innerHTML!==novo){
        c.innerHTML=novo;
        c.title='cada avalia\u00e7\u00e3o e um card medido em uma fun\u00e7\u00e3o';
      }
    }
  }
  setInterval(poeContador, 2500);

  /* ---------- itens 9 e 12 · a barra lateral ----------
     A ordem das 19 funcoes e ditada pelo Luis (18/08) e mora AQUI, num lugar so.
     A lateral nao e recriada: os mesmos elementos sao renomeados para o nome
     por extenso e reordenados — assim os cliques que a casca ja pendurou
     continuam valendo. */
  var ORDEM_DAS_FUNCOES = [
    'Goleiro defensivo','Goleiro ofensivo',
    'Zagueiro de combate','Zagueiro de sa\u00edda',
    'Lateral defensivo','Lateral ofensivo',
    'Volante de constru\u00e7\u00e3o','Volante de conten\u00e7\u00e3o',
    'Meia armador','Meia de arranque',
    'Ala cruzador','Ala finalizador',
    'Meia ofensivo','Atacante infiltrador',
    'Atacante criador','Atacante finalizador',
    'Falso nove','Centroavante m\u00f3vel','Centroavante fixo'
  ];
  window.t6Ordem = ORDEM_DAS_FUNCOES;
  function ordemDe(f){
    var i=ORDEM_DAS_FUNCOES.indexOf(f);
    return i<0 ? 99 : i;
  }
  function arrumaLateral(){
    var fam=document.getElementById('fam'); if(!fam) return;
    var tabs=fam.querySelectorAll('.tab[data-t]');
    if(!tabs.length) return;
    /* 1 · nome por extenso — nunca abreviar (item 2 das orientacoes) */
    for(var i=0;i<tabs.length;i++){
      var f=tabs[i].dataset.t;
      if(f && f.indexOf('\u2605')<0 && tabs[i].textContent.trim()!==f) tabs[i].textContent=f;
    }
    /* 2 · ordem dentro de cada familia */
    fam.querySelectorAll('.tabs').forEach(function(box){
      var arr=[].slice.call(box.querySelectorAll('.tab[data-t]'));
      if(arr.length<2) return;
      arr.sort(function(a,b){ return ordemDe(a.dataset.t)-ordemDe(b.dataset.t); });
      arr.forEach(function(el){ box.appendChild(el); });
    });
    /* 3 · ordem das familias dentro do setor */
    fam.querySelectorAll('.setg').forEach(function(sg){
      var gs=[].slice.call(sg.children);
      if(gs.length<2) return;
      function menor(g){
        var ts=g.querySelectorAll('.tab[data-t]'), m=99;
        for(var k=0;k<ts.length;k++) m=Math.min(m, ordemDe(ts[k].dataset.t));
        return m;
      }
      gs.sort(function(a,b){ return menor(a)-menor(b); });
      gs.forEach(function(g){ sg.appendChild(g); });
    });
    fam.dataset.t6ordem='1';
  }
  var _tent=0;
  var _iv=setInterval(function(){
    arrumaLateral();
    if(++_tent>20 || (document.getElementById('fam')||{}).dataset&&document.getElementById('fam').dataset.t6ordem)
      clearInterval(_iv);
  }, 500);

  /* ---------- item 11 · a TELA de resultado da busca ---------- */
  window.t6Busca = function(termo){
    var w=document.getElementById('homewrap'); if(!w) return;
    var nz=function(s){ return (s||'').toString().normalize('NFD')
      .replace(/[\u0300-\u036f]/g,'').toLowerCase(); };
    var q=nz(termo).trim(); if(q.length<2) return;
    var achou=[], vis={};
    for(var i=0;i<D.length;i++){
      var c=D[i]; if(!c||c.id==='MOLDE'||!nz(c.nome).includes(q)) continue;
      var v; try{ v=nota(c); }catch(e){ continue; }
      var k=String(c.id).split('@')[0];
      if(!vis[k] || v>vis[k][1]) vis[k]=[c,v];
    }
    for(var k2 in vis) achou.push(vis[k2]);
    achou.sort(function(a,b){ return b[1]-a[1]; });
    window._t6cc=true; window._t6busca=true; window._t6abaBox=false;
    try{ homeToggle(1); }catch(e){}
    var h='<section class="hbloco"><div class=htt><h2>'+esc(termo)+'</h2>'
      + '<span class=hsub>'+achou.length+' card'+(achou.length===1?'':'s')
      + ' \u00b7 um por card, na fun&ccedil;&atilde;o em que ele pontua mais</span></div>'
      + '<div class="t6bgrid">';
    for(var j=0;j<achou.length;j++){
      var c=achou[j][0], v=achou[j][1], t=0;
      try{ t=topoDoTipo(c.tipo)||0; }catch(e){}
      var p=t>0?(100*v/t):0, s=n2(v).split('.');
      h+='<div class="t6bcard" data-k="'+esc(c.id+'|'+c.tipo)+'">'
       + (window.t6Foto?window.t6Foto(c,'t6bfoto'):'')
       + '<div class="t6btx"><div class="t6bp">'+s[0]+'<s>.'+s[1]+'</s></div>'
       + '<div class="t6bt">'+n2(p)+'% do topo</div>'
       + '<div class="t6bn">'+esc(c.nome)+'</div>'
       + '<div class="t6bf">'+esc(c.tipo)+' <b>'+esc(c.np||c.pos||'')+'</b></div>'
       + (c.modelo?('<div class="t6bm">'+esc(c.modelo)+'</div>'):'')
       + '</div></div>';
    }
    w.innerHTML = h + '</div></section>';
    w.querySelectorAll('.t6bcard').forEach(function(el){
      el.onclick=function(){ try{ abrir(el.dataset.k); }catch(e){} }; });
    window.scrollTo(0,0);
  };

  function abreComoCalculamos(){
    var w=document.getElementById('homewrap'); if(!w) return;
    window._t6cc=true; window._t6busca=false;
    try{ homeToggle(1); }catch(e){}
    w.innerHTML = paginaComoCalculamos();
    window.scrollTo(0,0);
  }
  window.t6ComoCalculamos = abreComoCalculamos;

  /* a aba nova entra na barra */
  function poeAba(){
    var nav=document.getElementById('t6tabs');
    if(!nav || nav.querySelector('[data-aba=Como]')) return;
    var d=document.createElement('div');
    d.className='t6tab'; d.dataset.aba='Como'; d.textContent='Como calculamos';
    d.onclick=function(){
      if(window.t6Painel){ window._t6cc=true; window._t6busca=false;
                           window.t6Painel('como'); pintaCC(); return; }
      abreComoCalculamos(); pintaCC(); };
    nav.appendChild(d);
  }
  function pintaCC(){
    var el=document.querySelector('.t6tab[data-aba=Como]');
    if(el) el.className='t6tab'+(((window.T6TELAS? window._t6aba==='como' : window._t6cc) && !window._t6busca)?' on':'');
  }
  /* qualquer outra aba desliga o Como calculamos */
  document.addEventListener('click', function(ev){
    var t=ev.target;
    if(t && t.classList && t.classList.contains('t6tab') && t.dataset.aba!=='Como'){
      window._t6cc=false; window._t6busca=false;
      setTimeout(function(){ try{ homeRender(); }catch(e){} pintaCC(); },30);
    }
  }, true);

  setInterval(function(){ poeAba(); pintaCC(); }, 900);
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',poeAba);
  else poeAba();
})();
</script>
"""


T6_CSS5 = """
<style id=RANKING_1808>
/* ==========================================================================
   RANKING_1808 — a tela do Ranking igual as fotos 5 e 6 do pacote da designer.
   SUBSTITUI: a grade de cards da casca (#out .grade) e a barra lateral como
   navegacao. Nao ha sobreposicao: o conteudo de #out passa a ser escrito por
   t6Ranking(), e a barra lateral deixa de ser renderizada (o seletor de funcao
   do topo faz o papel dela).
   ⛔ Cor so por variavel de tema. Fonte: a do sistema (Calibri), por ordem do
      Luis — e a unica coisa que muda em relacao ao arquivo do design.
   ========================================================================== */

/* a barra de funcao, no lugar da lateral */
/* ⛔ A BARRA DE FUNCAO VEM DO MOLDE DA DESIGNER (ela mora dentro do #out).
   A barra montada a mao fica fora de cena — duas barras no mesmo lugar foi
   o que deixou a tela diferente da foto 5. */
html[data-tema] #t6fnbar{display:none!important}
#t6fnbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
 padding:10px 18px;border-bottom:1px solid var(--line);background:var(--t6bar)}
#t6fnbar .setl6{font-size:10px;letter-spacing:1.8px;text-transform:uppercase;color:var(--txt3)}
#t6fnbar .fnativa{background:linear-gradient(180deg,var(--acc),var(--acc2));color:var(--onacc);
 font-weight:700;font-size:13.5px;padding:9px 18px;border-radius:11px;border:none;cursor:pointer}
#t6fnbar .fntodas{background:var(--surf2);color:var(--txt);border:1px solid var(--line);
 font-weight:600;font-size:13px;padding:9px 16px;border-radius:11px;cursor:pointer}
#t6fnbar .fndir{margin-left:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#t6fnbar .fchip{background:var(--accbg);color:var(--acc);border:1px solid var(--acc);
 border-radius:999px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer}
#t6fnbar .fbtn{background:var(--surf2);color:var(--txt2);border:1px solid var(--line);
 border-radius:11px;padding:8px 14px;font-size:12.5px;font-weight:600;cursor:pointer}
#t6fnmenu{position:absolute;z-index:80;margin-top:6px;background:var(--surf);
 border:1px solid var(--line);border-radius:14px;padding:12px;box-shadow:0 20px 50px var(--sombra);
 display:none;grid-template-columns:repeat(4,minmax(150px,1fr));gap:14px}
#t6fnmenu.on{display:grid}
#t6fnmenu h6{margin:0 0 6px;font-size:10px;letter-spacing:1.6px;text-transform:uppercase;
 color:var(--txt3);font-weight:600}
#t6fnmenu a{display:block;padding:6px 8px;border-radius:8px;font-size:12.5px;color:var(--txt2);
 cursor:pointer;text-decoration:none}
#t6fnmenu a:hover{background:var(--line2);color:var(--txt)}
#t6fnmenu a.on{color:var(--acc);font-weight:700;background:var(--accbg)}

/* ---------------- os cards do ranking ---------------- */
#out .rkwrap{display:flex;flex-direction:column;gap:14px}
#out .rktop3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
#out .rkgrid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
@media(max-width:1500px){#out .rkgrid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:1100px){#out .rkgrid{grid-template-columns:repeat(3,minmax(0,1fr))}
 #out .rktop3{grid-template-columns:1fr}}

#out .rkbig{position:relative;border:1px solid var(--line);border-radius:16px;padding:18px;
 background:linear-gradient(160deg,var(--surf),var(--surf2));cursor:pointer;
 transition:border-color .15s ease,transform .15s ease}
#out .rkbig:hover{border-color:var(--acc);transform:translateY(-2px)}
#out .rkbigtop{display:flex;gap:16px;align-items:flex-start}
#out .rkbig img{width:86px;height:114px;object-fit:cover;border-radius:12px;flex:0 0 auto;
 background:var(--line2);border:1px solid var(--line)}
#out .rklug{font-size:11px;color:var(--txt3);letter-spacing:.6px}
#out .rklug b{color:var(--txt2);font-weight:700}
#out .rknome{font-size:22px;font-weight:700;color:var(--txt);line-height:1.15;margin:2px 0 4px}
#out .rkest{font-size:13px;color:var(--txt2)}
#out .rkpos{position:absolute;top:16px;right:16px;font-size:11.5px;font-weight:700;
 color:#6ea8ff;background:rgba(110,168,255,.12);border:1px solid rgba(110,168,255,.35);
 border-radius:8px;padding:4px 10px}
#out .rkfn{margin:14px 0 12px;background:var(--surf2);border:1px solid var(--line);
 border-radius:10px;padding:10px 14px;font-size:13px;color:var(--txt2)}
#out .rknums{display:flex;align-items:flex-end;justify-content:space-between;gap:10px}
#out .rknums .np{font-size:34px;font-weight:700;color:var(--acc);line-height:1;letter-spacing:-1px}
#out .rknums .rot{display:block;font-size:9.5px;letter-spacing:1.6px;text-transform:uppercase;
 color:var(--txt3);margin-top:5px}
#out .rknums .pt{font-size:22px;font-weight:700;color:var(--txt);line-height:1}
#out .rknums .dir{text-align:right}
#out .rkbar{height:5px;border-radius:999px;background:var(--line2);margin-top:12px;overflow:hidden}
#out .rkbar>i{display:block;height:100%;background:linear-gradient(90deg,var(--acc),var(--acc2))}

#out .rkcd{position:relative;border:1px solid var(--line);border-radius:14px;padding:13px;
 background:linear-gradient(160deg,var(--surf),var(--surf2));cursor:pointer;
 transition:border-color .15s ease,transform .15s ease}
#out .rkcd:hover{border-color:var(--acc);transform:translateY(-2px)}
#out .rkcd .rkcdtop{display:flex;align-items:center;gap:9px;margin-bottom:9px}
#out .rkcd img{width:34px;height:44px;object-fit:cover;border-radius:7px;
 background:var(--line2);border:1px solid var(--line)}
#out .rkcd .rkrk{font-size:12px;color:var(--txt3)}
#out .rkcd .rkpos{position:static;margin-left:auto;font-size:10.5px;padding:3px 8px}
#out .rkcd .rknome{font-size:14px;font-weight:700;margin:0 0 2px}
#out .rkcd .rkest{font-size:11.5px;color:var(--txt3)}
#out .rkcd .rkfn2{font-size:11.5px;color:var(--txt2);margin:2px 0 8px}
#out .rkcd .rknums2{display:flex;align-items:baseline;justify-content:space-between;gap:8px}
#out .rkcd .rknums2 b{font-size:21px;font-weight:700;color:var(--txt);letter-spacing:-.5px}
#out .rkcd .rknums2 s{text-decoration:none;font-size:12px;font-weight:700;color:var(--acc)}
#out .rkcd .rkbar{margin-top:9px}
#out .rkbas{display:inline-block;margin-left:6px;font-size:9px;font-weight:700;letter-spacing:.6px;
 color:var(--dourado);border:1px solid var(--dourado);border-radius:999px;padding:1px 6px}
</style>
"""

T6_JS5 = """
<script>
/* RANKING_1808 — escreve o #out no desenho das fotos 5 e 6.
   ⛔ NAO e uma camada por cima: o conteudo antigo de #out e substituido.
      A casca continua dona do filtro e da ordem (lista()), so a montagem muda. */
(function(){
  function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
  function n2(v){ return (Math.round(v*100)/100).toFixed(2); }
  function foto(c,cls){
    return '<img class="'+(cls||'')+'" loading="lazy" src="https://efimg.com/efootballhub22/'
      + 'images/player_cards/'+String(c.id).split('@')[0]+'_l.png" '
      + 'onerror="this.style.visibility=&quot;hidden&quot;">';
  }
  function pctDe(c){
    try{ var t=topoDoTipo(c.tipo); return t>0?(100*nota(c)/t):0; }catch(e){ return 0; }
  }
  function basico(c){
    try{ return estiloAtiva(c)?'':'<span class=rkbas>BÁSICO</span>'; }catch(e){ return ''; }
  }

  function cardGrande(c,i){
    var v=nota(c), p=pctDe(c), s=n2(v);
    return '<div class="rkbig" data-k="'+esc(c.id+'|'+c.tipo)+'">'
     + '<div class="rkpos">'+esc(c.np||c.pos||'')+'</div>'
     + '<div class="rkbigtop">'+foto(c)
     + '<div><div class="rklug"><b>'+(i+1)+'\\u00ba</b> LUGAR</div>'
     + '<div class="rknome">'+esc(c.nome)+basico(c)+'</div>'
     + '<div class="rkest">'+esc(c.modelo||'')+'</div></div></div>'
     + '<div class="rkfn">'+esc(c.tipo)+'</div>'
     + '<div class="rknums"><div><span class="np">'+s+'</span>'
     + '<span class="rot">pontua\\u00e7\\u00e3o</span></div>'
     + '<div class="dir"><span class="pt">'+n2(p)+'%</span>'
     + '<span class="rot">% do topo</span></div></div>'
     + '<div class="rkbar"><i style="width:'+Math.max(2,Math.min(100,p)).toFixed(1)+'%"></i></div>'
     + '</div>';
  }
  function cardPequeno(c,i){
    var v=nota(c), p=pctDe(c);
    return '<div class="rkcd" data-k="'+esc(c.id+'|'+c.tipo)+'">'
     + '<div class="rkcdtop">'+foto(c)+'<span class="rkrk">'+(i+1)+'\\u00ba</span>'
     + '<span class="rkpos">'+esc(c.np||c.pos||'')+'</span></div>'
     + '<div class="rknome">'+esc(c.nome)+basico(c)+'</div>'
     + '<div class="rkest">'+esc(c.modelo||'')+'</div>'
     + '<div class="rkfn2">'+esc(c.tipo)+'</div>'
     + '<div class="rknums2"><b>'+n2(v)+'</b><s>'+n2(p)+'</s></div>'
     + '<div class="rkbar"><i style="width:'+Math.max(2,Math.min(100,p)).toFixed(1)+'%"></i></div>'
     + '</div>';
  }

  window.t6Ranking=function(){
    var out=document.getElementById('out');
    if(!out || !out.offsetParent) return;
    try{ if(S.view!=='cards') return; }catch(e){ return; }
    /* ⛔ QUANDO A CAMADA DAS TELAS EXISTE, O MOLDE E O DELA. A casca continua
       dona do filtro, da ordem e do VIS; so a montagem muda. Duas montagens
       para o mesmo #out foi o que fez a tela piscar. */
    if(window.t6TelaRanking){
      /* ⛔ SO REPINTA QUANDO MUDA. Este bloco e chamado tambem pelo relogio de
         1,2s (porque nem todo caminho da casca passa por render()); sem a
         assinatura ele reescreveria o #out cinco vezes por segundo — foi isso
         que fez a tela piscar da primeira vez. */
      var _L; try{ _L=lista(); }catch(e){ _L=[]; }
      var _t=''; try{ _t=S.tipo||''; }catch(e){}
      var _c=0;  try{ _c=(typeof CMODE!=='undefined')?CMODE:0; }catch(e){}
      var _v=0;  try{ _v=VIS||0; }catch(e){}
      var _ass=_t+'|'+((_L&&_L.length)||0)+'|'+_v+'|'+_c+'|'
             +((_L&&_L[0]&&(_L[0].id+'|'+_L[0].tipo))||'');
      if(out.querySelector('.t6tela') && window._t6rkAss===_ass) return;
      var _h=''; try{ _h=window.t6TelaRanking(); }catch(e){ _h=''; }
      if(_h){
        window._t6rkAss=_ass;
        var _s=window.pageYOffset||document.documentElement.scrollTop||0;
        out.innerHTML='<div class="t6tela">'+_h+'</div>';
        try{ window.t6Cliques(out); }catch(e){}
        try{ window.t6FnMenu(out); }catch(e){}
        if(_s>0) window.scrollTo(0,_s);
        return;
      }
    }
    var L; try{ L=lista(); }catch(e){ return; }
    if(!L || !L.length){ return; }
    var lim; try{ lim=VIS; }catch(e){ lim=100; }
    var mostra=L.slice(0, Math.max(3, lim||100));
    var h='<div class="rkwrap"><div class="rktop3">';
    for(var i=0;i<Math.min(3,mostra.length);i++) h+=cardGrande(mostra[i],i);
    h+='</div>';
    if(mostra.length>3){
      h+='<div class="rkgrid">';
      for(var j=3;j<mostra.length;j++) h+=cardPequeno(mostra[j],j);
      h+='</div>';
    }
    out.innerHTML=h+'</div>';
    out.querySelectorAll('[data-k]').forEach(function(el){
      el.onclick=function(){ try{ abrir(el.dataset.k); }catch(e){} };
    });
  };

  /* ---------- a barra de funcao, no lugar da barra lateral ---------- */
  function setorDe(f){
    try{ var m=window.t6Setor?window.t6Setor():{}; return m[f]||''; }catch(e){ return ''; }
  }
  function montaBarra(){
    var h=document.querySelector('header');
    if(!h || document.getElementById('t6fnbar')) return;
    var bar=document.createElement('div'); bar.id='t6fnbar';
    bar.innerHTML='<span class="setl6"></span>'
      + '<button class="fnativa"></button>'
      + '<button class="fntodas">19 fun\\u00e7\\u00f5es \\u25be</button>'
      + '<span class="fndir"></span>';
    h.appendChild(bar);
    var menu=document.createElement('div'); menu.id='t6fnmenu';
    h.appendChild(menu);
    bar.querySelector('.fntodas').onclick=function(ev){
      ev.stopPropagation(); menu.classList.toggle('on'); if(menu.classList.contains('on')) enche(menu);
    };
    document.addEventListener('click',function(){ menu.classList.remove('on'); });
    bar.querySelector('.fnativa').onclick=function(ev){
      ev.stopPropagation(); menu.classList.toggle('on'); if(menu.classList.contains('on')) enche(menu);
    };
  }
  window.t6EncheMenu=function(menu){ return enche(menu); };
  function enche(menu){
    var ordem=(window.t6Ordem||[]), set=(window.t6Setor?window.t6Setor():{});
    var pref=['GOLEIRO','DEFESA','MEIO','ATAQUE'], por={};
    ordem.forEach(function(f){ var s=set[f]||'OUTRAS'; (por[s]=por[s]||[]).push(f); });
    var h='';
    pref.concat(Object.keys(por).filter(function(k){return pref.indexOf(k)<0;}))
      .forEach(function(s){
        if(!por[s]) return;
        h+='<div><h6>'+s+'</h6>'+por[s].map(function(f){
          var on=false; try{ on=(S.tipo===f); }catch(e){}
          return '<a data-f="'+f.replace(/"/g,'')+'"'+(on?' class=on':'')+'>'+f+'</a>';
        }).join('')+'</div>';
      });
    menu.innerHTML=h;
    menu.querySelectorAll('a[data-f]').forEach(function(a){
      a.onclick=function(ev){ ev.stopPropagation();
        var el=document.querySelector('.tab[data-t="'+a.dataset.f+'"]');
        if(el) el.click();
        menu.classList.remove('on'); pintaBarra();
      };
    });
  }
  function pintaBarra(){
    var bar=document.getElementById('t6fnbar'); if(!bar) return;
    var f=''; try{ f=S.tipo; }catch(e){}
    var geral=(f||'').indexOf('\\u2605')>=0 || (f||'').indexOf('grp:')===0;
    bar.querySelector('.setl6').textContent = geral?'':setorDe(f);
    bar.querySelector('.fnativa').textContent = geral?'Ranking geral':f;
    /* os filtros ligados viram etiqueta, como na foto */
    var dir=bar.querySelector('.fndir'), chips='';
    try{
      var vm=+(document.getElementById('vm')||{}).value||0;
      if(vm>0) chips+='<span class="fchip">votos \\u2265 '+vm+'</span>';
      var tier=(document.getElementById('tier')||{}).value||'';
      if(tier) chips+='<span class="fchip">tier '+tier+'</span>';
      var mdl=(document.getElementById('mdl')||{}).value||'';
      if(mdl) chips+='<span class="fchip">'+mdl+'</span>';
    }catch(e){}
    chips+='<button class="fbtn" id=t6filtros>filtros</button>';
    if(dir.innerHTML!==chips) dir.innerHTML=chips;
    var b=document.getElementById('t6filtros');
    if(b) b.onclick=function(){ try{ toggleFiltros(); }catch(e){} };
    /* a barra so existe no Ranking */
    var noRanking = !(document.getElementById('homewrap')||{}).offsetParent
                 && !(document.getElementById('mtwrap')||{}).offsetParent;
    bar.style.display = noRanking ? '' : 'none';
  }

  if(typeof window.render==='function'){
    var _r=window.render;
    window.render=function(){ var x=_r.apply(this,arguments);
      try{ t6Ranking(); }catch(e){} try{ pintaBarra(); }catch(e){} return x; };
  }
  /* ⛔ NEM TODO CAMINHO DA CASCA PASSA POR render(). Clicar na aba Ranking
     e um deles — por isso a tela do Ranking so aparecia quando alguem
     chamava a funcao na mao. O relogio fecha o buraco; quem impede o
     repinte a toa e a assinatura la dentro. */
  setInterval(function(){ montaBarra(); pintaBarra();
    try{ t6Ranking(); }catch(e){} }, 1200);
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',montaBarra);
  else montaBarra();
  setTimeout(function(){ try{ t6Ranking(); }catch(e){} }, 1500);
})();
</script>
"""


T6_CSS6 = """
<style id=MEUTIME_1808>
/* ==========================================================================
   MEUTIME_1808 — a aba Meu time igual a foto 2 do pacote da designer.
   SUBSTITUI o acabamento antigo do #mtwrap. Nao troca a marcacao (o arrastar,
   o salvar, a formacao e o tecnico continuam sendo os mesmos elementos): o que
   muda e a pele, e ela vem das mesmas variaveis --d.. das outras telas.
   ⛔ Cor so por variavel. Fonte: a do sistema, ordem do Luis.
   ========================================================================== */

/* ⛔ 18/08 — O FUNDO DO MEU TIME PASSA A SER O DO TEMA.
   Era aqui que o tema claro quebrava: o #mtwrap ficava com a superficie escura
   da casca velha, e todo texto em cima (rgba preto sobre escuro) sumia.
   Agora o fundo sai da mesma variavel das outras telas. */
html[data-tema] #mtwrap{background:linear-gradient(180deg,var(--d4),var(--d5))!important;
 color:var(--d1)!important}
html[data-tema] #mtwrap *{color:inherit}
html[data-tema] #mtwrap .mini,html[data-tema] #mtwrap .bhd,
html[data-tema] #mtwrap .eleyebrow{color:var(--d17)!important}

/* ---------- o cabecalho do elenco ---------- */
html[data-tema] #mtwrap .mthd{align-items:center!important;gap:20px!important;
 padding:18px 22px!important;border-bottom:1px solid var(--d10)!important;
 background:var(--d64)!important}
html[data-tema] #mtwrap .mthd>div:first-child>b{font-size:24px!important;
 font-weight:800!important;letter-spacing:-.5px!important;color:var(--d1)!important}
html[data-tema] #mtwrap .mtkk{font-family:inherit;font-size:9px;letter-spacing:1.4px;
 color:var(--d17);display:block;margin-bottom:3px}
html[data-tema] #mtstats{margin-left:auto;display:flex;gap:11px;flex-wrap:wrap}
html[data-tema] #mtstats .mtst{min-width:104px;display:flex;flex-direction:column;gap:4px;
 padding:11px 14px;border-radius:12px;background:var(--d12);border:1px solid var(--d20)}
html[data-tema] #mtstats .mtst u{text-decoration:none;font-family:inherit;font-size:9px;
 letter-spacing:1.3px;color:var(--d17)}
html[data-tema] #mtstats .mtst b{font-family:inherit;font-size:20px;font-weight:700;color:var(--d1)}
html[data-tema] #mtstats .mtst.med{min-width:126px;
 background:linear-gradient(150deg,var(--d51),var(--d52));border:1px solid var(--d65)}
html[data-tema] #mtstats .mtst.med u{color:var(--d50)}
html[data-tema] #mtstats .mtst.med b{background:linear-gradient(180deg,var(--d54),var(--d55));
 -webkit-background-clip:text;background-clip:text;color:transparent}
html[data-tema] #mtstats .mtst.tec{min-width:150px}
html[data-tema] #mtstats .mtst.tec b{font-size:15px}
/* a fila de controles fica discreta, embaixo — a foto nao os mostra em destaque */
html[data-tema] #mtwrap .mthd>div:last-child{display:flex;flex-wrap:wrap;gap:7px;
 align-items:center;width:100%;order:9;margin-top:12px}
html[data-tema] #mtwrap .mthd>div:last-child .btn,
html[data-tema] #mtwrap .mthd>div:last-child select{
 font-size:11.5px!important;padding:6px 12px!important;border-radius:9px!important;
 background:var(--d14)!important;border:1px solid var(--d18)!important;color:var(--d30)!important}
html[data-tema] #mtwrap .mthd{flex-wrap:wrap!important}

/* ---------- as seis acoes ---------- */
html[data-tema] #mtwrap .mtacts{display:flex!important;flex-wrap:wrap!important;gap:8px!important;
 padding:14px 22px!important;border-bottom:1px solid var(--d10)!important;background:transparent!important}
html[data-tema] #mtwrap .mtacts .mtbt{text-transform:none!important;letter-spacing:0!important;
 font-size:12.5px!important;font-weight:600!important;padding:9px 16px!important;
 border-radius:11px!important;background:var(--d14)!important;border:1px solid var(--d18)!important;
 color:var(--d30)!important;box-shadow:none!important;transition:all .18s ease}
html[data-tema] #mtwrap .mtacts .mtbt:hover{border-color:var(--d57)!important;color:var(--d1)!important}
html[data-tema] #mtwrap .mtacts .mtbt:first-child{
 background:linear-gradient(180deg,var(--d25),var(--d26))!important;
 color:var(--d27)!important;border:none!important;font-weight:700!important;
 box-shadow:0 6px 18px var(--d93)!important}

/* ---------- a coluna da esquerda ---------- */
html[data-tema] #mtwrap .mtgrid{grid-template-columns:404px minmax(0,1fr)!important;gap:0!important}
html[data-tema] #mtwrap #mtesq{border-right:1px solid var(--d10)!important;padding:18px!important;
 display:flex!important;flex-direction:column!important;gap:16px!important}
html[data-tema] #mtwrap .mttec,html[data-tema] #mtwrap .mtbanco,
html[data-tema] #mtwrap .mtresumo{
 border-radius:13px!important;padding:13px 15px!important;
 background:linear-gradient(158deg,var(--d20),var(--d58))!important;
 border:1px solid var(--d59)!important}
html[data-tema] #mtwrap .bhd{font-family:inherit!important;font-size:9.5px!important;
 letter-spacing:1.4px!important;color:var(--d17)!important;text-transform:uppercase}
html[data-tema] #mtwrap #mtesq select{width:100%;font-size:12.5px;padding:8px 11px;
 border-radius:10px;background:var(--d9);border:1px solid var(--d7);color:var(--d1)}

/* ---------- o gramado ---------- */
html[data-tema] #mtwrap .mtcampo{
 background:repeating-linear-gradient(180deg,var(--d75) 0 82px,var(--d76) 82px 164px)!important;
 border-radius:16px!important;border:none!important;overflow:hidden!important;
 position:relative!important}
html[data-tema] #mtwrap .mtcampo::before{content:"";position:absolute;inset:14px;
 border:2px solid var(--d77);border-radius:4px;pointer-events:none;z-index:0}
html[data-tema] #mtwrap .mtcampo::after{content:"";position:absolute;left:14px;right:14px;
 top:50%;height:2px;background:var(--d77);pointer-events:none;z-index:0}
/* ⛔ NAO SE MEXE NO `position` DAS VAGAS: elas sao posicionadas em absoluto
   pelo motor da formacao. So o z-index, para ficarem acima do gramado. */
html[data-tema] #mtwrap .mtcampo .mtsl{z-index:1}
html[data-tema] #mtwrap .mtcampo{max-width:660px!important;margin:0 auto!important}
/* ⛔ O :before e o :after DO CAMPO JA EXISTEM na casca (linha do meio e
   circulo central). Nao se cria pseudo novo — pseudo so tem um de cada, e
   criar por cima apagaria o circulo. Aqui eles so trocam de cor e de medida. */
html[data-tema] #mtwrap .mtcampo{outline:2px solid var(--d77);outline-offset:-14px}
html[data-tema] #mtwrap .mtcampo:before{left:14px!important;right:14px!important;
 background:var(--d77)!important;height:2px!important;z-index:0}
html[data-tema] #mtwrap .mtcampo:after{width:172px!important;height:172px!important;
 margin:-86px 0 0 -86px!important;border:2px solid var(--d77)!important;z-index:0}
/* as marcas que a casca nao tem entram como elemento, nao como pseudo */
html[data-tema] #mtwrap .mtcampo .mtmk{position:absolute;pointer-events:none;z-index:0}
html[data-tema] #mtwrap .mtcampo .mtmk.ag1{left:50%;top:14px;width:340px;height:128px;
 margin-left:-170px;border:2px solid var(--d77);border-top:none;border-radius:0 0 5px 5px}
html[data-tema] #mtwrap .mtcampo .mtmk.ap1{left:50%;top:14px;width:158px;height:52px;
 margin-left:-79px;border:2px solid var(--d79);border-top:none;border-radius:0 0 4px 4px}
html[data-tema] #mtwrap .mtcampo .mtmk.ag2{left:50%;bottom:14px;width:340px;height:128px;
 margin-left:-170px;border:2px solid var(--d77);border-bottom:none;border-radius:5px 5px 0 0}
html[data-tema] #mtwrap .mtcampo .mtmk.ap2{left:50%;bottom:14px;width:158px;height:52px;
 margin-left:-79px;border:2px solid var(--d79);border-bottom:none;border-radius:4px 4px 0 0}
html[data-tema] #mtwrap .mtcampo .mtmk.pt{left:50%;top:50%;width:8px;height:8px;
 margin:-4px 0 0 -4px;border-radius:50%;background:var(--d78)}
html[data-tema] #mtwrap .mtcampo .mtmk.meio{left:14px;right:14px;top:50%;height:2px;
 background:var(--d77)}
html[data-tema] #mtwrap .mtcampo .mtmk.cir{left:50%;top:50%;width:172px;height:172px;
 margin:-86px 0 0 -86px;border:2px solid var(--d77);border-radius:50%}
/* os pseudo antigos do campo saem: quem desenha agora sao os .mtmk */
html[data-tema] #mtwrap .mtcampo:before,
html[data-tema] #mtwrap .mtcampo:after{display:none!important}
/* as riscas antigas somem: quem desenha o campo agora e este bloco */
html[data-tema] #mtwrap .risco,html[data-tema] #mtwrap .r-borda,
html[data-tema] #mtwrap .r-meio,html[data-tema] #mtwrap .r-circulo,
html[data-tema] #mtwrap .r-areaG,html[data-tema] #mtwrap .r-areaP{display:none!important}

/* ---------- as vagas ---------- */
html[data-tema] #mtwrap .mtsl{border-radius:13px!important;
 background:linear-gradient(158deg,var(--d20),var(--d58))!important;
 border:1px solid var(--d59)!important;box-shadow:0 8px 22px var(--d96)!important;
 transition:transform .18s ease,border-color .18s ease}
html[data-tema] #mtwrap .mtsl:hover{border-color:var(--d25)!important;transform:translateY(-2px)}
html[data-tema] #mtwrap .mtsl.vaz{background:var(--d80)!important;
 border:1px dashed var(--d18)!important;box-shadow:none!important}
html[data-tema] #mtwrap .mtpos{display:inline-block!important;width:auto!important;
 font-family:inherit!important;font-size:10px!important;
 letter-spacing:.6px!important;color:var(--d45)!important;background:var(--d86)!important;
 border:1px solid var(--d99)!important;border-radius:7px!important;padding:2px 7px!important;
 align-self:flex-start}
html[data-tema] #mtwrap .mtsl{display:flex!important;flex-direction:column!important;
 align-items:center!important;justify-content:center!important;gap:4px!important;
 padding:8px!important;text-align:center}
html[data-tema] #mtwrap .mtcampo .mtsl .mtnm,html[data-tema] #mtwrap .mtnm{
 font-size:12px!important;font-weight:700!important;color:var(--d1)!important}
html[data-tema] #mtwrap .mtcampo .mtsl .mtfn,html[data-tema] #mtwrap .mtfn{
 font-size:9.5px!important;letter-spacing:.5px!important;
 color:var(--d13)!important;text-transform:uppercase}
html[data-tema] #mtwrap .mtcampo .mtsl .mtmais{color:var(--d13)!important}
/* ⛔ O BOTAO DO TEMA SOME NO CLARO. Ele e o unico jeito de voltar ao escuro:
   nao pode ficar cinza-claro sobre branco. */
html[data-tema] header #temabt,html[data-tema] header .temabt,
html[data-tema=claro] header button[id*=tema],html[data-tema=claro] header button[class*=tema]{
 color:var(--d1)!important;border:1px solid var(--d18)!important;background:var(--d14)!important}
html[data-tema] #mtwrap .mtnt,html[data-tema] #mtwrap .mtsl b.nt{
 font-family:inherit!important;font-weight:700!important;color:var(--d8)!important}

/* ---------- fora do banco ---------- */
html[data-tema] #mtwrap .mtfora{padding:18px 22px!important;border-top:1px solid var(--d10)!important;
 background:transparent!important}
html[data-tema] #mtwrap .mtforagrid{display:grid!important;
 grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:12px!important}
html[data-tema] #mtwrap .mtbc{border-radius:14px!important;padding:13px!important;
 background:linear-gradient(158deg,var(--d42),var(--d43))!important;
 border:1px solid var(--d102)!important;transition:transform .2s ease,border-color .2s ease}
html[data-tema] #mtwrap .mtbc:hover{transform:translateY(-3px);border-color:var(--d57)!important}
html[data-tema] #mtwrap .mtfin{font-size:11.5px!important;padding:6px 12px!important;
 border-radius:9px!important;background:var(--d14)!important;border:1px solid var(--d18)!important;
 color:var(--d30)!important}
@media(max-width:1180px){
 html[data-tema] #mtwrap .mtgrid{grid-template-columns:1fr!important}
 html[data-tema] #mtwrap #mtesq{border-right:none!important}
 html[data-tema] #mtwrap .mtforagrid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
}
</style>
"""

T6_JS6 = """
<script>
/* ===== MEUTIME_1808 — os quatro numeros do alto e os nomes das acoes ===== */
(function(){
  if(window.MEUTIME_1808) return; window.MEUTIME_1808=1;
  /* ⛔ 18/08 — os rotulos sao os do arquivo dela, sem emoji e sem caixa alta.
     A ordem e a mesma; so o texto muda. Nao se troca o onclick. */
  var NOMES=['Deixar o time no ideal','Melhor função de cada um',
             'Onde meu time está fraco','Melhor formação pro meu elenco',
             'Técnico do time inteiro','Comparar com outro time'];
  function acoes(){
    var bs=document.querySelectorAll('#mtwrap .mtacts .mtbt');
    for(var i=0;i<bs.length && i<NOMES.length;i++){
      if(bs[i].textContent.trim()!==NOMES[i]) bs[i].textContent=NOMES[i];
    }
  }
  function txt(el){ return el?String(el.textContent||'').trim():''; }
  function stats(){
    var hd=document.querySelector('#mtwrap .mthd'); if(!hd) return;
    var cx=document.getElementById('mtstats');
    if(!cx){
      cx=document.createElement('div'); cx.id='mtstats';
      cx.innerHTML='<div class="mtst"><u>FORMAÇÃO</u><b></b></div>'
                  +'<div class="mtst"><u>EM CAMPO</u><b></b></div>'
                  +'<div class="mtst med"><u>PONTUAÇÃO MÉDIA</u><b></b></div>'
                  +'<div class="mtst tec"><u>TÉCNICO</u><b></b></div>';
      var pri=hd.firstElementChild;
      if(pri) hd.insertBefore(cx, pri.nextSibling); else hd.appendChild(cx);
      /* o rotulo de cima: ELENCO em cima, "Meu time" embaixo — igual a foto */
      var b=hd.querySelector('div:first-child b');
      if(b && b.textContent.indexOf('ELENCO')>=0){
        var k=document.createElement('span'); k.className='mtkk'; k.textContent='ELENCO';
        b.parentNode.insertBefore(k,b); b.textContent='Meu time';
      }
    }
    var vs=cx.querySelectorAll('.mtst b');
    var sel=document.querySelector('#mtwrap .mthd select');
    vs[0].textContent = sel ? sel.value : '';
    var slots=document.querySelectorAll('#mtwrap .mtcampo .mtsl');
    var cheios=0;
    for(var i=0;i<slots.length;i++) if(slots[i].className.indexOf('vaz')<0) cheios++;
    vs[1].textContent = cheios + '/' + (slots.length||11);
    var m=document.querySelector('#mtwrap .mthd .mini b');
    vs[2].textContent = txt(m) || '0.0';
    var ts=document.querySelector('#mtwrap .mttec select');
    var nt = ts ? (ts.options[ts.selectedIndex]||{}).text : '';
    if(!nt || nt.indexOf('sem técnico')>=0) nt='— sem técnico —';
    vs[3].textContent = nt;
  }
  /* as marcas do gramado que a casca nao desenha */
  function marcas(){
    var c=document.querySelector('#mtwrap .mtcampo');
    if(!c || c.querySelector('.mtmk')) return;
    ['ag1','ap1','ag2','ap2','meio','cir','pt'].forEach(function(k){
      var d=document.createElement('div'); d.className='mtmk '+k; c.appendChild(d);
    });
  }
  /* ⛔ 19/08 — O NUMERO CRU NA FAIXA DO MODELO.
     A faixa escrevia "Atributos 99.10545752974969". Nao e conta errada: e
     numero sem arredondar chegando na tela. Duas casas, como no resto. */
  function arredonda(){
    var f=document.getElementById('mline')||document.querySelector('.mline');
    if(!f) return;
    var t=f.innerHTML, u=t.replace(/(\\d+\\.\\d{3,})/g, function(m){
      return (Math.round(parseFloat(m)*100)/100).toFixed(2); });
    if(u!==t) f.innerHTML=u;
  }
  function tudo(){ try{ acoes(); }catch(e){} try{ stats(); }catch(e){}
                   try{ marcas(); }catch(e){} try{ arredonda(); }catch(e){} }
  setInterval(tudo, 1200);
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',tudo);
  else tudo();
})();
</script>
"""


T6_JS7 = """
<script>
/* ===== FICHA_1808 — a ficha do card no molde da designer (fotos 6, 8 e 9) =====
   ⛔ SUBSTITUI, NAO SOBREPOE. O `abrir()` da casca continua sendo quem calcula
      tudo; o que muda e quem escreve o #box. E se a ficha nova nao der conta,
      a ficha antiga volta na hora — nunca fica em branco. */
(function(){
  if(window.FICHA_1808) return; window.FICHA_1808=1;
  function liga(){
    if(typeof window.abrir!=='function') return setTimeout(liga,400);
    if(window._abrirAntigo) return;
    window._abrirAntigo=window.abrir;
    window.abrir=function(key){
      /* ⛔ 19/08 — A CASCA PODE ESTOURAR, E A FICHA NOVA NAO PODE MORRER JUNTO.
         Medido no Ruud Gullit: clicar em 9 das 15 funcoes nao fazia nada. A
         ficha nova estava PRONTA (109.017 caracteres, 5.261 de texto) e nunca
         chegava na tela, porque o `abrir` da casca lancava
         `Cannot read properties of undefined (reading 'b1n')` ANTES — e a
         excecao subia por cima do try/catch que vem depois.
         Agora o calculo da casca e protegido: se ele cair, a ficha nova
         desenha assim mesmo, e o erro fica registrado em window._T6_ERRO_CASCA
         em vez de sumir. */
      var r;
      try{ r=window._abrirAntigo.apply(this,arguments); }
      catch(eCasca){
        window._T6_ERRO_CASCA = String(key) + ' :: ' + (eCasca && eCasca.message || eCasca);
        if(window.console) console.warn('a casca caiu ao calcular', key, eCasca);
      }
      try{
        /* A fonte compartilhada e a unica dona do desenho e dos cliques. A
           casca antiga fica acima apenas para preparar a entrada e como
           retorno de seguranca. */
        if(window.t6DesenhaFicha && window.t6DesenhaFicha(key)) return r;
        if(!window.t6TelaFicha) return r;
        var box=document.getElementById('box'); if(!box) return r;
        var h=window.t6TelaFicha(key);
        if(!h || String(h).replace(/<[^>]*>/g,'').trim().length<40) return r;
        box.innerHTML='<div class="t6tela t6ficha">'+h+'</div>';
        window.t6FichaCliques(box, key);
      }catch(e){
        if(window.console) console.warn('FICHA_1808 caiu para a ficha antiga:', e);
        try{ window._abrirAntigo(key); }catch(e2){}
      }
      return r;
    };
  }
  liga();
})();
</script>
"""

T6_CSS7 = """
<style id=FICHA_1808>
/* a ficha da designer e uma grade de duas colunas (340px + o resto).
   O #box e o modal da casca: aqui ele so vira o palco. */
html[data-tema] #box:has(.t6ficha){padding:0!important;background:transparent!important;
 border:none!important;box-shadow:none!important;max-width:1320px!important;width:96vw!important}
/* a moldura vem do proprio arquivo dela (grade 340px + resto); aqui so a
   largura vira fluida, porque o desenho dela e de 1280 fixo. */
html[data-tema] .t6ficha>div{width:100%!important;max-width:1280px;margin:0 auto}
html[data-tema] .t6ficha{width:100%}
html[data-tema] .t6ficha *{box-sizing:border-box}
html[data-tema] #box .t6ficha select option{background:var(--d4);color:var(--d1)}
@media(max-width:900px){
 html[data-tema] .t6ficha [style*="grid-template-columns:340px minmax(0,1fr)"]{
  grid-template-columns:1fr!important}
 html[data-tema] .t6ficha [style*="grid-template-columns:130px 88px repeat(11"]{
  grid-template-columns:110px 70px repeat(11,minmax(0,1fr))!important;font-size:10px}
}
</style>
"""


# ⛔ 19/08 — A VERSAO CARREGA A HORA DA GERACAO.
#    O dia inteiro saiu como `v1908-5`: eu instalei doze mudancas e todas
#    apareciam com o mesmo numero. O Luis mandava print achando que era a tela
#    nova e era a velha, e nenhum dos dois tinha como saber. Numero fixo so
#    serve quando alguem lembra de subir — e ninguem lembra.
#    Agora a marca do rodape muda sozinha a cada geracao. Se dois prints tem a
#    mesma marca, sao a mesma tela. Sem discussao.
VERSAO_DA_TELA = 'v1908-6 · ' + time.strftime('%d/%m %H:%M')

T6_JS8 = (r"""
<script>
/* ===== SOCORRO_1908 — a tela nunca fica muda =====
   ⛔ Nasceu de um defeito real: na maquina do Luis o painel ficou EM BRANCO e
      nao havia como saber por que — ele nao usa terminal e o arquivo abre por
      file://, fora do meu alcance. Entao a propria tela passa a contar.
   Duas coisas, e so isso:
     1. uma marca de versao no rodape — para saber QUAL arquivo esta aberto;
     2. se o painel ficar vazio por 6 segundos, ele escreve na tela o que
        aconteceu, em portugues, com um botao de copiar. */
(function(){
  if(window.SOCORRO_1808) return; window.SOCORRO_1808=1;
  var VER = '__VERSAO__';
  var erros = [];
  window.addEventListener('error', function(e){
    erros.push((e.message||'erro') + ' @ ' + (e.filename||'').split('/').pop() + ':' + (e.lineno||0));
  });
  window.addEventListener('unhandledrejection', function(e){
    erros.push('promessa: ' + ((e.reason && e.reason.message) || e.reason || ''));
  });

  function marca(){
    if(document.getElementById('t6ver')) return;
    var d=document.createElement('div'); d.id='t6ver';
    d.textContent=VER;
    d.title='versao desta tela — cite este codigo quando falar de um defeito';
    d.style.cssText='position:fixed;left:8px;bottom:6px;z-index:99998;font:10px/1 '
      +'Calibri,Carlito,system-ui,sans-serif;letter-spacing:.5px;opacity:.42;'
      +'color:#8b968f;pointer-events:none;user-select:text';
    document.body.appendChild(d);
  }

  function diagnostico(){
    var w=document.getElementById('homewrap');
    var L=[];
    L.push('VERSÃO: '+VER);
    L.push('tema: '+(document.documentElement.getAttribute('data-tema')||'(sem data-tema)'));
    L.push('linhas carregadas: '+((typeof D!=='undefined'&&D)?D.length:'D não existe'));
    L.push('moldes da designer: '+(window.T6M?('sim, '+Object.keys(window.T6M).join(', ')):'NÃO CHEGARAM'));
    L.push('t6Painel: '+(typeof window.t6Painel));
    L.push('desenho antigo: '+(typeof window._t6homeAntigo));
    L.push('aba: '+(window._t6aba||'(nenhuma)'));
    L.push('trava de pintura: '+(window._t6pintando?'PRESA':'solta'));
    try{ L.push('t6TelaInicio devolveu: '+String(window.t6TelaInicio()).length+' caracteres'); }
    catch(e){ L.push('t6TelaInicio ESTOUROU: '+e.message); }
    L.push('erros do navegador: '+(erros.length?erros.slice(-6).join(' | '):'nenhum'));
    return L.join('\n');
  }
  window.t6Diagnostico = diagnostico;

  function vazio(){
    var w=document.getElementById('homewrap');
    if(!w || !w.offsetParent) return false;
    return (w.innerText||'').trim().length < 3;
  }
  var desde=0;
  setInterval(function(){
    marca();
    if(!vazio()){ desde=0; var a=document.getElementById('t6socorro'); if(a) a.remove(); return; }
    if(!desde){ desde=Date.now(); return; }
    if(Date.now()-desde < 6000) return;
    if(document.getElementById('t6socorro')) return;
    var txt=diagnostico();
    var d=document.createElement('div'); d.id='t6socorro';
    d.style.cssText='max-width:760px;margin:40px auto;padding:20px 22px;border-radius:14px;'
      +'background:#171b19;border:1px solid #3a4a41;color:#e6ebe8;'
      +'font:13px/1.6 Calibri,Carlito,system-ui,sans-serif';
    d.innerHTML='<div style="font-size:17px;font-weight:700;margin-bottom:4px">'
      +'A tela não conseguiu desenhar</div>'
      +'<div style="color:#8b968f;margin-bottom:14px">Isto não é a tela normal — é o aviso que '
      +'aparece quando ela falha. Copie o texto abaixo e mande para o Claude.</div>'
      +'<pre id="t6soctxt" style="white-space:pre-wrap;background:#0e1210;border:1px solid #2a332e;'
      +'border-radius:10px;padding:12px;font:12px/1.5 Consolas,monospace;color:#c8d2cc;'
      +'user-select:all;margin:0"></pre>'
      +'<button id="t6soccp" style="margin-top:12px;padding:8px 16px;border-radius:9px;border:none;'
      +'background:#7df2a8;color:#062012;font-weight:700;font-size:12.5px;cursor:pointer">'
      +'copiar</button>';
    /* ⛔ O AVISO MORA FORA DO PAINEL. Se ele entrasse dentro do #homewrap, o
       painel deixaria de estar vazio e o proprio vigia apagaria o aviso dois
       segundos depois — foi o que aconteceu no primeiro teste. */
    var w=document.getElementById('homewrap');
    var pai=(w&&w.parentNode)||document.querySelector('main')||document.body;
    if(w&&w.parentNode) pai.insertBefore(d, w.nextSibling); else pai.appendChild(d);
    document.getElementById('t6soctxt').textContent=txt;
    document.getElementById('t6soccp').onclick=function(){
      try{ navigator.clipboard.writeText(txt); this.textContent='copiado!'; }
      catch(e){ this.textContent='selecione o texto e copie'; }
    };
  }, 2000);
})();
</script>
""").replace('__VERSAO__', VERSAO_DA_TELA)


# ---------------------------------------------------------------------------
#  ⛔ 19/08 — A PONTE DOS DOIS NOMES DA MESMA FUNCAO
# ---------------------------------------------------------------------------
#  O nome da funcao na TELA foi fechado pelo Luis em 15/08; a CHAVE do banco
#  continua a antiga (o motor nao sabe que o nome mudou, e nao precisa saber).
#  So que a casca tem uma duzia de tabelas indexadas POR NOME, e parte delas
#  foi regravada com o nome novo enquanto o `c.tipo` de cada linha continua com
#  a chave velha.
#
#  O que isso custou, medido em 19/08 no Ruud Gullit: clicar em 9 das 15
#  funcoes da ficha NAO FAZIA NADA. A causa, com a pilha inteira:
#
#      MED['Meia de lado por fora']  ->  undefined
#      notaMed()                     ->  Cannot read properties of undefined
#      abrir()                       ->  morre antes de escrever o #box
#
#  A ficha nova estava pronta (109.017 caracteres, 5.261 de texto) e nunca
#  chegava na tela. Silencioso: nenhum aviso — o clique so nao respondia.
#
#  O conserto NAO e escolher um nome: e as tabelas responderem pelos DOIS.
#  Cada entrada ganha a irma. Nao se apaga chave nenhuma — regra da casa:
#  acrescenta antes de tirar.
# ---------------------------------------------------------------------------
NOMES_IRMAOS = {
    'Meia central armador':     'Meia armador',
    'Meia central de chegada':  'Meia de arranque',
    'Meia de lado por dentro':  'Ala finalizador',
    'Meia de lado por fora':    'Ala cruzador',
    'Meia lateral atacante':    'Ala finalizador',
    'Meia lateral cruzador':    'Ala cruzador',
    'Meia ofensivo armador':    'Meia ofensivo',
    'Segundo atacante':         'Atacante infiltrador',
    'Ponta criadora':           'Atacante criador',
    'Ponta finalizadora':       'Atacante finalizador',
}

TABELAS_POR_NOME = ('MED', 'REGUA', 'FX_ANC', 'FX_K', 'FIS_KON', 'FIS_P',
                    'MF_TIPO', 'MF_FAIXA', 'FILA', 'B5V', 'ESTV', 'MF_DIRF',
                    'FUNC_POS', 'ALT_FUNC')


def _fim_do_valor(bloco, j):
    """Onde termina o valor que comeca em `j`, equilibrando chaves e aspas."""
    d, dentro, esc = 0, None, False
    for t in range(j, len(bloco)):
        ch = bloco[t]
        if dentro:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == dentro:
                dentro = None
            continue
        if ch == '"' or ch == "'":
            dentro = ch
        elif ch == '{' or ch == '[':
            d += 1
        elif ch == '}' or ch == ']':
            if d == 0:
                return t
            d -= 1
            if d == 0:
                return t + 1
        elif ch == ',' and d == 0:
            return t
    return len(bloco)


def _valor_da_chave(bloco, chave):
    """O texto do valor de `"chave":` dentro de `bloco`, ou None."""
    for asp in ('"', "'"):
        alvo = asp + chave + asp + ':'
        i = bloco.find(alvo)
        if i < 0:
            continue
        j = i + len(alvo)
        while j < len(bloco) and bloco[j] in ' \t\n':
            j += 1
        return bloco[j:_fim_do_valor(bloco, j)]
    return None


def _fim_do_objeto(html, i):
    """Onde fecha o objeto que abre em `i` (html[i] == '{')."""
    d, dentro, esc = 0, None, False
    for j in range(i, len(html)):
        ch = html[j]
        if dentro:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == dentro:
                dentro = None
            continue
        if ch == '"' or ch == "'":
            dentro = ch
        elif ch == '{':
            d += 1
        elif ch == '}':
            d -= 1
            if d == 0:
                return j
    return None


def patch_ponte_dos_nomes(html):
    """Faz cada tabela indexada por nome de funcao responder pelas DUAS grafias."""
    import re as _re
    postos = 0
    for tab in TABELAS_POR_NOME:
        m = _re.search(r'\b' + tab + r'\s*=\s*\{', html)
        if not m:
            continue
        i = html.find('{', m.end() - 1)
        fim = _fim_do_objeto(html, i)
        if fim is None:
            continue
        bloco = html[i:fim + 1]
        faltando = []
        for velho, novo in NOMES_IRMAOS.items():
            tem_v = _valor_da_chave(bloco, velho)
            tem_n = _valor_da_chave(bloco, novo)
            if tem_v is not None and tem_n is None:
                faltando.append((novo, tem_v))
            elif tem_n is not None and tem_v is None:
                faltando.append((velho, tem_n))
        if not faltando:
            continue
        miolo = bloco[1:-1].rstrip()
        if miolo.endswith(','):
            miolo = miolo[:-1]
        extra = ''.join(',"%s":%s' % (k, v) for k, v in faltando)
        html = html[:i] + '{' + miolo + extra + '}' + html[fim + 1:]
        postos += len(faltando)
        print('   ponte de nomes: %-10s +%d chaves' % (tab, len(faltando)))

    a = "function notaMed(t){const m=MED[t];let s=0,tt=0;"
    b = "function notaMed(t){const m=MED[t];if(!m)return 0;let s=0,tt=0;"
    if a in html:
        html = html.replace(a, b)
        print('   ponte de nomes: notaMed nao estoura mais em chave desconhecida')
    if postos:
        print('   ponte de nomes: %d chaves acrescentadas ao todo' % postos)
    return html


def _js_valido(codigo, nome):
    """Passa o bloco pelo `node --check`. Sem node, deixa passar (nao trava)."""
    import subprocess, tempfile
    try:
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                         encoding='utf-8') as f:
            f.write(codigo)
            caminho = f.name
        r = subprocess.run(['node', '--check', caminho],
                           capture_output=True, text=True, timeout=25)
        os.unlink(caminho)
        if r.returncode != 0:
            print('   ⚠️  BLOCO %s TEM ERRO DE SINTAXE — ficou de fora:' % nome)
            for linha in (r.stderr or '').strip().splitlines()[:4]:
                print('       ' + linha)
            return False
        return True
    except FileNotFoundError:
        return True          # sem node nesta maquina: segue como sempre foi
    except Exception as e:
        print('   (nao consegui conferir %s: %s)' % (nome, str(e)[:60]))
        return True


def patch_direcao_1808(html):
    """A CASCA DO TURNO 6 — o desenho que o Luis mandou em 18/08.

    ETAPA 1: cabecalho, cores, fonte, cantos.
    ETAPA 2: a tela de INICIO — bloco de destaque, 3 de N boxes com o botao de
             ver todas, a faixa da build, o Top 3 do jogo e o Top 3 de cada
             funcao na lista curta do arquivo (o podio do turno 3 fica escondido).
    Faltam: Meu time, Boxes anteriores, Como calculamos.

    O botao velho continua no DOM e a aba nova chama a MESMA funcao — e por isso
    que os outros 40 patches continuam achando #fbt, #homebt e #mtbt.
    """
    if 't6bar' in html:
        return html, 0
    i = html.rfind('</body>')
    if i < 0:
        return html, 0
    # ⛔ ITEM 10 DAS ORIENTACOES: separador decimal com PONTO em todos os
    #    numeros. O `_nd` e o formatador central da casca; os outros lugares
    #    fazem `.replace('.',',')` na mao. Isto roda ANTES de colar os blocos
    #    do turno 6, senao mexeria no que eu mesmo escrevi.
    html = html.replace(".replace('.',',')", "")
    html = html.replace('.replace(".",",")', "")
    # o Meu time tem o proprio formatador (doisDec) e escreve <i>,dd</i>
    html = html.replace('return s[0]+"<i>,"+s[1]+"</i>";',
                        'return s[0]+"<i>."+s[1]+"</i>";')

    # ⛔ item 19 · CONTRASTE NO TEMA CLARO. Luis, 18/08: "pessimo contraste do
    #    amarelo com o branco no fundo." As quatro cores da nota estao escritas
    #    dentro do HTML na hora de desenhar (cor()), entao nao da para consertar
    #    por CSS: troca-se a funcao. No escuro fica tudo como estava; no claro
    #    o verde-claro e o ambar escurecem ate ficarem legiveis no branco.
    # ⛔ item 20 · A ORDEM DE LEITURA DO CARD DA BOX. Luis, 18/08: "agora que a
    #    gente inventou essa etiqueta, o certo e por a pontuacao em evidencia, ai
    #    o nome, ai as outras informacoes, e por ultimo, junto da etiqueta, o
    #    percentual." SO no card de box — o do podio nao muda.
    #  ⛔ A troca e feita DENTRO do trecho da funcao cdBox. O card do podio
    #     (cdPodio) termina com as mesmas linhas, e trocar no arquivo inteiro
    #     levava para la um `pc` que la nao existe: ReferenceError, homeTop3
    #     morria e a home ficava sem bloco nenhum. Achado testando.
    _i = html.find('function cdBox')
    _f = html.find('\n }', _i) if _i > 0 else -1
    if _i > 0 and _f > _i:
        _cd = html[_i:_f]
        # a nota grande passa a ser a PONTUACAO; o % desce para o rodape.
        # Feito em tres trocas curtas — a linha inteira nao casava por causa
        # das aspas escapadas dentro do proprio HTML gerado.
        _cd = _cd.replace('"<div class=nt style=\\"color:"+cr+"\\">"',
                          '"<div class=nt style=\\"color:"+cor(n,ref)+"\\">"+_nd(n)')
        # ⛔ a troca do separador decimal so acontece MAIS ABAIXO neste mesmo
        #    patch — aqui o texto ainda pode estar com virgula. Por isso os dois.
        for _v in (',', '.'):
            _cd = _cd.replace('+ pc[0] + "<span class=ndec>' + _v
                              + '"+pc[1]+"</span><span class=bxsg>%</span>"\n', '')
        _cd = _cd.replace('+ "<span class=ntsub><b style=\\"color:"+cor(n,ref)+"\\">pontuação "+_nd(n)+"</b></span>"\n', '')
        _cd = _cd.replace(
            '   + "<div class=mi><b>"+c.tipo+"</b> <span class=hpos>"+(c.np||"")+"</span>"\n'
            '     + est + "</div>"\n'
            '   + "</div>";',
            '   + "<div class=mi><b>"+c.tipo+"</b> <span class=hpos>"+(c.np||"")+"</span>"\n'
            '     + est + "</div>"\n'
            '   + "<div class=t6rod><span class=t6pct style=\\"color:"+cr+"\\">"\n'
            '     + pc[0] + "<span class=ndec>."+pc[1]+"</span>% do topo</span></div>"\n'
            '   + "</div>";')
        html = html[:_i] + _cd + html[_f:]

    # o rotulo acima do numero grande do card de box agora e a PONTUACAO
    html = html.replace('html[data-tema] .cdbx .nt:before{content:"% do topo"!important}',
                        'html[data-tema] .cdbx .nt:before{content:"pontuação"!important}')

    html = html.replace(
        "function cor(n,ref){return n>=ref+12?'#22c58b':n>=ref?'#8fd694':n>=ref-12?'#f0a531':'#e0533d';}",
        "function cor(n,ref){\n"
        " var _c = document.documentElement.getAttribute('data-tema')==='claro'\n"
        "   ? ['#0a7d4f','#2f7d55','#8a5a00','#b3361f']\n"
        "   : ['#22c58b','#8fd694','#f0a531','#e0533d'];\n"
        " return n>=ref+12?_c[0]:n>=ref?_c[1]:n>=ref-12?_c[2]:_c[3];}")

    # ------------------------------------------------------------------
    #  A BUSCA — ordem do Luis, 18/08 (itens 7 e 11 do documento)
    #    "nao aparece a foto, tem que aparecer, senao nao da pra saber"
    #    "se o cara tem varias funcoes aparece a linha que ele tem mais pontos"
    #    "aperta Enter e ele manda pra tela com todos os cards"
    #  ⛔ Tres trocas cirurgicas no bloco que ja existe. Nao se reescreve a
    #     busca: ela ja acha certo, so mostrava errado.
    # ------------------------------------------------------------------
    html = html.replace(
        "  LIN=cs.slice(0,40); sel=-1;",
        "  var _vis={}, _um=[];\n"
        "  for(var _i=0;_i<cs.length;_i++){ var _k=String(cs[_i].id).split('@')[0];\n"
        "    if(_vis[_k]) continue; _vis[_k]=1; _um.push(cs[_i]); }\n"
        "  LIN=_um.slice(0,40); sel=-1; window._t6achou=_um.length;")
    html = html.replace(
        "   return `<div class=\"gbR\" data-i=\"${i}\">\n    <div class=gbN>",
        "   return `<div class=\"gbR\" data-i=\"${i}\">\n"
        "    <img class=gbFoto loading=lazy src=\"https://efimg.com/efootballhub22/images/"
        "player_cards/${String(c.id).split('@')[0]}_l.png\" onerror=\"this.style.visibility='hidden'\">\n"
        "    <div class=gbN>")
    html = html.replace(
        " } else if(e.key==='Enter'){ ir(sel<0?0:sel); }",
        " } else if(e.key==='Enter'){\n"
        "   if(sel<0 && typeof window.t6Busca==='function' && IN.value.trim().length>=2){\n"
        "     window.t6Busca(IN.value); fechar(); return; }\n"
        "   ir(sel<0?0:sel); }")
    html = html.replace(
        " .gbNota{font-weight:800;font-size:15px;min-width:52px;text-align:right}",
        " .gbNota{font-weight:800;font-size:15px;min-width:52px;text-align:right}\n"
        " .gbFoto{width:26px;height:34px;object-fit:cover;border-radius:5px;flex:0 0 auto;\n"
        "   background:var(--line2,#1e2733);border:1px solid var(--line,#2a3441)}")
    # o cdBox monta o "% do topo" na mao, com virgula
    html = html.replace('+ pc[0] + "<span class=ndec>,"+pc[1]+"</span>',
                        '+ pc[0] + "<span class=ndec>."+pc[1]+"</span>')
    html = html.replace("return s[0]+'<span class=ndec>,'+s[1]+'</span>';",
                        "return s[0]+'<span class=ndec>.'+s[1]+'</span>';")
    html = patch_ponte_dos_nomes(html)
    i = html.rfind('</body>')
    # ⛔ UMA CAMADA SO. Regra de ouro da designer, e reclamacao do Luis:
    #    "do que adianta alterar num lugar se depois volta ao que era?"
    #    Os blocos abaixo sao escritos separados no gerador (para dar para ler),
    #    mas entram no HTML como UM <style> e UM <script>, com nome. Nada de
    #    pilha de camadas anonimas se sobrescrevendo.
    def _corpo(bloco, tag):
        s = bloco.find('>', bloco.find('<' + tag))
        e = bloco.rfind('</' + tag + '>')
        return bloco[s + 1:e] if (s > 0 and e > s) else bloco

    _blocos_css = [('T6_CSS', T6_CSS), ('T6_CSS2', T6_CSS2), ('T6_CSS3', T6_CSS3),
                   ('T6_CSS4', T6_CSS4), ('T6_CSS5', T6_CSS5), ('T6_CSS6', T6_CSS6),
                   ('T6_CSS7', T6_CSS7)]
    _blocos_js = [('T6_JS', T6_JS), ('T6_JS2', T6_JS2), ('T6_JS3', T6_JS3),
                  ('T6_JS4', T6_JS4), ('T6_JS5', T6_JS5), ('T6_JS6', T6_JS6),
                  ('T6_JS7', T6_JS7), ('T6_JS8', T6_JS8)]
    if TELAS is not None:
        _blocos_css.append(('CSS_TELAS', TELAS.CSS_TELAS))
        _blocos_js.append(('JS_TELAS', TELAS.js_telas()))
    _css = ''.join(_corpo(b, 'style') for _, b in _blocos_css)
    # ⛔ 19/08 — UM BLOCO QUEBRADO NAO PODE DERRUBAR OS OUTROS.
    #    Tudo entra num <script> so (uma camada, ordem do Luis). Mas um erro de
    #    SINTAXE num bloco mata o <script> INTEIRO — e a tela fica em branco.
    #    Medido: um `\n` mal escapado no bloco de socorro derrubou as telas todas.
    #    Agora cada bloco passa pelo `node --check` antes de entrar. Quem nao
    #    passa fica de fora, com aviso — perde-se um pedaco, nunca a tela.
    _bons = []
    for _nome, _b in _blocos_js:
        _c = _corpo(_b, 'script')
        if _js_valido(_c, _nome):
            _bons.append(_c)
    _js = ''.join(_bons)
    _uma = ('\n<style id="CLUBEFOOTBALL_1808">' + _css + '</style>\n'
            + '<script id="CLUBEFOOTBALL_1808_JS">' + _js + '</script>\n')
    return html[:i] + _uma + html[i:], 1



def main():
    base_html = next((p for p in CASCAS if os.path.exists(p)), None)
    if not base_html:
        print('NAO ACHEI a casca do HTML. Procurei em:')
        for p in CASCAS: print('   ', p)
        pausa(); return
    print('casca ...................', base_html)
    for p in (LINHAS, CARDS, MOLDE):
        if not os.path.exists(p):
            print('NAO ACHEI', p); pausa(); return
    os.makedirs(os.path.dirname(SAIDA) or '.', exist_ok=True)

    res = [json.loads(l) for l in open(LINHAS, encoding='utf-8') if l.strip()]
    print('linhas da rodada v6 .....', len(res))

    # ⛔ 18/08 — A ULTIMA LINHA DE CADA card+funcao MANDA.
    #    Desde hoje o motor REFAZ uma linha sem arrancar a antiga do arquivo
    #    (a linha volta pelo fila_EXTRA com a marca `refazer`). Isso e o que
    #    permite coletar e rodar ao mesmo tempo — mas deixa DUAS linhas com a
    #    mesma chave no linhas.jsonl, e este laco criaria a carta DUAS VEZES na
    #    mesma funcao. Como o arquivo e escrito em ordem, a de baixo e a nova.
    _antes = len(res)
    _por_chave = {}
    for _x in res:
        _por_chave[(str(_x.get('card_id')), _x.get('funcao'))] = _x
    res = list(_por_chave.values())
    if _antes != len(res):
        print('linhas refeitas (fiquei com a mais nova)', _antes - len(res))

    # 13/08 (ordem do Luis): ENQUANTO O MOTOR REFAZ, A TELA NAO FICA VAZIA.
    # Quando um lote de linhas e derrubado para recalculo, a funcao inteira some da
    # tela ate o motor terminar — foi o que aconteceu com as 10 funcoes dos bloqueios.
    # Agora o gerador completa o buraco com a linha ANTIGA (do backup) e marca
    # `velha`. Assim que a linha nova fica pronta, ela MANDA e a velha e ignorada.
    # ⚠️ Isto NAO mexe no motor: ele continua lendo so o linhas.jsonl e refazendo.
    _velhas = 0
    _tem = {(str(x.get('card_id')), x.get('funcao')) for x in res}
    for _bak in sorted(glob.glob(os.path.join(os.path.dirname(LINHAS) or '.',
                                              'linhas.jsonl.ANTES-*'))
                       + glob.glob(os.path.join(os.path.dirname(LINHAS) or '.',
                                                'linhas-ANTES-*.jsonl')), reverse=True):
        try:
            for _l in open(_bak, encoding='utf-8'):
                if not _l.strip(): continue
                try: _x = json.loads(_l)
                except Exception: continue
                _k = (str(_x.get('card_id')), _x.get('funcao'))
                if not _x.get('card_id') or not _x.get('funcao') or _k in _tem:
                    continue
                _x['_velha'] = True
                res.append(_x); _tem.add(_k); _velhas += 1
        except Exception as _e:
            print('  nao consegui ler o backup %s: %s' % (_bak, _e))
    if _velhas:
        print('linhas ANTIGAS de reserva .', _velhas,
              '(o motor ainda esta refazendo — a tela mostra a nota anterior)')

    # ================================================================
    # A FONTE UNICA — a TELA le do mesmo lugar que o motor. (Luis, 14/08)
    #
    # Sem isto o motor lia dados/base_unica.json e a tela continuava lendo
    # dados/cards.json: a tela mostraria dado velho — o Hazard sem impeto,
    # a habilidade com o nome antigo. O Luis pegou isso antes de ligar.
    #
    # Com o FONTE-UNICA.txt na pasta, le a base. Sem ele, nada muda.
    # ================================================================
    _fonte_cards = CARDS
    if os.path.exists('FONTE-UNICA.txt') and os.path.exists('dados/base_unica.json'):
        try:
            _bu = json.load(open('dados/base_unica.json', encoding='utf-8'))
            _lista = _bu.get('cards') or []
            if _lista:
                _fonte_cards = 'dados/base_unica.json'
                print('fonte dos cards ......... A BASE UNICA (%d registros)' % len(_lista))
            else:
                _lista = json.load(open(CARDS, encoding='utf-8'))
                print('fonte dos cards ......... cards.json (a base veio vazia)')
        except Exception as _e:
            _lista = json.load(open(CARDS, encoding='utf-8'))
            print('fonte dos cards ......... cards.json (nao consegui ler a base: %s)' % _e)
    else:
        _lista = json.load(open(CARDS, encoding='utf-8'))
        print('fonte dos cards ......... cards.json')

    C, POS = {}, collections.defaultdict(set)
    for c in _lista:
        b = str(c['id']).split('@')[0]
        if b not in C or (c.get('orc') or 0) > (C[b].get('orc') or 0): C[b] = c
        for k in ('pos', 'np'):
            if c.get(k): POS[b].add(str(c[k]).strip())
        for x in str(c.get('sec') or '').split('/'):
            if x.strip(): POS[b].add(x.strip())

    # A build e uma so por funcao; apenas o bonus de estilo pode variar por
    # posicao. O motor_bonus grava essas pequenas variantes separadamente.
    BONUS_POS = collections.defaultdict(dict)
    _bp_arq = os.path.join('saida_v6', 'bonus_posicao.jsonl')
    if os.path.exists(_bp_arq):
        for _l in open(_bp_arq, encoding='utf-8'):
            try: _r = json.loads(_l)
            except Exception: continue
            _cid, _fun, _pos = _r.get('card_id'), _r.get('funcao'), _r.get('posicao')
            if _cid and _fun and _pos:
                BONUS_POS[(str(_cid), _fun)][_pos] = {
                    'estilo_ativo': bool(_r.get('estilo_ativo')),
                    'b_estilo': _r.get('b_estilo'), 'b_total': _r.get('b_total')}
        print('variantes de bonus/posicao', sum(len(v) for v in BONUS_POS.values()))

    M = collections.defaultdict(dict)
    for r in json.load(open(MOLDE, encoding='utf-8')):
        M[r['funcao']][r['attr']] = (r['peso'], r['alvo'])

    html, pos, Dvelho = le_D(base_html)
    MBN = mbn_da_casca(html or '')
    CATU = cat_da_casca(open(base_html, encoding='utf-8', errors='replace').read())
    print('impetos na tabela CAT ...', len(CATU))
    ANTES = ids_antes_do_impeto()
    print('cards de antes do impeto', len(ANTES), '(esses sim ficam SEM VAGA)')
    print('nomes PT das barras .....', len(MBN), 'lidos da casca')
    if pos is None:
        print('nao achei o const D no', base_html); pausa(); return
    meta = {}
    for fonte in ([p for p in COMPLEMENTO if os.path.exists(p)] + [base_html]):
        _, _, Dx = le_da = le_D(fonte)
        if not Dx: continue
        for r in Dx:
            meta.setdefault(str(r['id']).split('@')[0], r)
    print('metadados de tela disponiveis para', len(meta), 'cards')

    D, faltou = [], collections.Counter()
    for x in res:
        b = str(x['card_id']).split('@')[0]
        c = C.get(b)
        if not c:
            faltou['card fora do cards.json'] += 1; continue
        f = x['funcao']
        # 13/08 (ordem do Luis): O GOLEIRO NAO MISTURA.
        # Defensivo so lista goleiro defensivo, ofensivo so lista ofensivo. Antes
        # a familia dava as DUAS funcoes ao mesmo goleiro e o Buffon (ofensivo)
        # aparecia em primeiro na tela do defensivo.
        if f in ('Goleiro defensivo', 'Goleiro ofensivo'):
            _nat = funcao_nativa(c.get('np') or c.get('pos'), c.get('modelo'))
            if _nat and _nat != f:
                faltou['goleiro fora do proprio estilo'] += 1
                continue
        mol = M.get(f)
        if not mol:
            faltou['funcao fora do molde'] += 1; continue
        m = meta.get(b, {})
        vals = x.get('vals') or []
        arows = []
        for a in range(26):
            peso, alvo = mol.get(a, (0, 0))
            v = vals[a] if a < len(vals) else 0
            arows.append([a, peso, alvo, v, round(v - alvo, 2)])
        # b1n = A NOTA: percentual de cumprimento do molde. NAO arredondar por dentro.
        num = den = 0.0
        for a, peso, alvo, v, _ in arows:
            if peso:
                num += peso * v; den += peso * alvo
        b1n = (100.0 * num / den) if den else 0.0
        barras = x.get('barras') or {}
        _nm = c.get('nm') or []
        _tem_nm = any(_nm)
        nome_fab_txt = nome_do_nm(_nm, CATU)
        _imp, _slot = impeto_da_carta(b, c.get('sl'), texto_impeto(x.get('impeto')),
                                      ANTES, _tem_nm, nome_fab_txt)

        # ===== DEGRAUS 2 e 3 DO IMPETO CONDICIONAL =====================
        # O motor ja refaz a build INTEIRA para +2 e +3 (campo `cond` do
        # linhas.jsonl). Aqui esse resultado vai junto para o HTML, senao o
        # botao da tela nao tem o que trocar (era o buraco: cdelta sempre 0).
        # ⛔ Nao soma por fora: troca a build toda, como o Luis exigiu.
        _cd = {}
        _cx = x.get('cond') or {}
        if isinstance(_cx, dict):
            for _g in ('2', '3'):
                _r = _cx.get(_g)
                if not isinstance(_r, dict):
                    continue
                _v = _r.get('vals') or []
                if not _v:
                    continue
                _num = _den = 0.0
                for _a in range(26):
                    _peso, _alvo = mol.get(_a, (0, 0))
                    if _peso:
                        _num += _peso * (_v[_a] if _a < len(_v) else 0)
                        _den += _peso * _alvo
                _bar = _r.get('barras') or {}
                _cd[_g] = {
                    'b1': _r.get('b1'),
                    'b1n': (100.0 * _num / _den) if _den else 0.0,
                    'v': [(_v[_a] if _a < len(_v) else 0) for _a in range(26)],
                    'bar': [[MBN.get(_k, _k), _vv] for _k, _vv in _bar.items() if _vv],
                    'TEC': _r.get('tecnico'), 'TECB': _r.get('boost_tecnico') or [],
                    'HAB': _r.get('habilidades') or [],
                    'sobra': (c.get('orc') or 0) - custo_barras(_bar),
                }
        D.append({
            'tipo': f, 'fam': SETOR.get(f, ''), 'pos': POS_DA_FUNCAO.get(f, ''),
            'id': b, 'nome': c.get('nome'), 'ovr': c.get('ovr') or 0,
            'bonus_posicoes': BONUS_POS.get((b, f), {}),
            'votos': c.get('votos') or 0, 'tier': c.get('tier') or '?',
            'sec': c.get('sec'), 'h': c.get('altura'), 'w': c.get('peso'),
            'foot': c.get('pe'), 'temMax': bool(c.get('max_ovr')),
            # 13/08: levelCap 0 no efHub NAO e 'sem progressao' — e progressao
            # ainda nao publicada. Card de um dia de vida. Nao afirmar o que nao se sabe.
            'capdesc': bool(c.get('capdesc')),
            'velha': bool(x.get('_velha')),
            'b1': x.get('b1'), 'b2': 0, 'b3': 0, 'b4': 0, 'b5': 0,
            'imp': _imp, 'nao_cabe_mais': 1 if _slot is None and not x.get('impeto') else 0,
            # o motor nao grava sobra (vem None nas 177 linhas) — a conta e aqui
            'sobra': (c.get('orc') or 0) - custo_barras(barras),
            'arows': arows, 'frows': [],
            'fab': c.get('fab') or [], 'falta': x.get('pool_disponivel') or [],
            'raras': c.get('raras') or [], 'com': m.get('com') or [],
            # 10/08: os NOMES do impeto de fabrica, decodificados do efscout
            # (bits 552 e 720) e traduzidos pelo const CAT da casca.
            # 10/08 · O NOME DO IMPETO NATIVO E CALCULADO, NAO LIDO.
            # O `nmn` gravado no cards.json estava errado em 115 de 115 cards
            # de DOIS impetos: repetia "+3 +3" quando o segundo e +1.
            #   Neuer  gravado: Defesaca +3 + Passe +3
            #          real   : Passe +1 + Defesaca +3
            # O certo sai de bater a assinatura do `nm` contra o const CAT da
            # casca — mesma conta que o motor usa. Uma fonte so, sem chute.
            'nmn': ([x.strip() for x in nome_fab_txt.split(' + ')]
                    if nome_fab_txt else (c.get('nmn') or [])),
            'sisOvr': c.get('ovr') or 0, 'b1n': b1n,
            'estilo': 'Ofensivo', 'modelo': c.get('modelo'),
            # 13/08: card novo nao tem metadado de tela ainda (o `meta` sai do HTML
            # anterior). Cai para o proprio cards.json, que agora traz esses campos
            # do efHub. Sem isso a ficha mostrava "null anos" e "pe ruim —/—".
            'wfu': m.get('wfu') if m.get('wfu') is not None else c.get('wfu'),
            'wfa': m.get('wfa') if m.get('wfa') is not None else c.get('wfa'),
            'age': m.get('age') if m.get('age') is not None else c.get('age'),
            'inj': m.get('inj') if m.get('inj') is not None else c.get('inj'),
            'base': c.get('base') or [], 'mx': m.get('mx') or c.get('base') or [],
            'sis': vals,
            'baseOvr': c.get('ovr') or 0,
            # ⛔ 19/08 — VOLTOU A ORDEM ORIGINAL, com a razao medida.
            #    Eu tinha trocado a prioridade para `max_ovr`. A sessao do
            #    encaixe mediu nas 2.786 bases: 2.468 tem `maxOvr` QUEBRADO —
            #    ou seja ele nunca foi OVR da Konami — e o `max_ovr` do banco
            #    tambem nao esta conferido. Trocar a fonte so trocava um numero
            #    errado por outro, e este campo e lido em outros lugares.
            #    O bloco saiu da ficha (ordem do Luis); a fonte fica como estava.
            'maxOvr': m.get('maxOvr') or c.get('max_ovr') or c.get('ovr') or 0,
            'sisBar': [[MBN.get(k, k), v] for k, v in barras.items() if v],
            'mst': m.get('mst'),
            'adds': x.get('habilidades') or [],
            # 15/08 — O POOL REAL DA CARTA (o que ela PODE destravar).
            # A tela oferecia so `c.falta` (o que falta do ideal da funcao) e
            # por isso o Luis nao conseguia adicionar varias habilidades.
            'pool': x.get('pool_disponivel') or [],
            # a tela le habsAtual(c) -> c.HAB, e tecAtual(c) -> c.TECB
            'HAB': x.get('habilidades') or [],
            # NEU = da pra selecionar e a nota NAO muda · TECIG = outro tecnico, mesma nota
            'NEU': x.get('neutras') or [],
            'TECIG': x.get('tecnicos_iguais') or [],
            # Chave estavel. `TEC` continua por compatibilidade com as telas
            # antigas, mas codigo novo resolve primeiro pelo ID.
            'TECID': x.get('tecnico_id'),
            'TECB': x.get('boost_tecnico') or [],
            'b4r': 0, 'np': c.get('np') or c.get('pos'),
            # sp = TAMBEM JOGA. A estrela vem do metadado de tela quando existe
            # (o efHub da familiarity 1 ou 2); sem ele entra 1.
            'sp': sp_de(b, c, m, POS.get(b)),
            'orc': c.get('orc') or 0, 'nm': c.get('nm') or [],
            'sl': c.get('sl') or [], 'MIG': 1 if str(x.get('origem') or '').startswith('comprada') else 0,
            # 15/08 — A TELA NAO PODE DIZER "nao tem" PARA CARD QUE TEM.
            # O card veio do efHub com boostId, mas o efeito (nm) esta vazio:
            # o catalogo nao conhece esse id. Sao 16 cards (Diego Costa, Messi,
            # Lamine Yamal...) que o motor otimizou SEM o impeto de fabrica.
            # Escrever "nao tem" esconde isso — e foi assim que passou por todo
            # mundo ate o Luis ver na ficha, em 15/08.
            'impDesc': 1 if ((c.get('boostId') or c.get('boostId2')) and not c.get('nm')) else 0,
            # ⛔ 19/08 — TRES ESTADOS, NAO DOIS. Medido no banco, 6.902 cards:
            #     3.255 dizem que TEM  ->  e os 3.255 tem o efeito (zero furo)
            #     3.214 dizem que NAO tem
            #       433 nunca foram conferidos
            #       191 tem o codigo do impeto e o catalogo nao conhece o efeito
            #   Escrever "nao tem" nos 433 + 191 e mentir com cara de certeza.
            #   `None` aqui NAO e falso: e "ninguem perguntou ainda".
            'temImp': (None if c.get('impeto_tem') is None
                       else (1 if c.get('impeto_tem') else 0)),
            'boostIds': [x for x in (c.get('boostId'), c.get('boostId2')) if x],
            'NOVO': 1, 'TEC': x.get('tecnico'),
            'dt': c.get('dt'), 'slot': _slot,
            'CD': _cd,
        })

    print('registros gerados ......', len(D))
    #  ⛔ 19/08 — GUARDA AS CHAVES QUE A TELA VAI USAR.
    #  Serve para uma trava so: conferir, na hora de colar o BONUS_PRONTO, se a
    #  chave dele casa com a chave da linha. Ver `patch_bonus_pronto`.
    global CHAVES_DA_TELA
    CHAVES_DA_TELA = set('%s|%s' % (str(r.get('id')).split('@')[0], r.get('tipo'))
                         for r in D if r.get('id') != 'MOLDE' and r.get('tipo'))
    if faltou:
        for k, n in faltou.most_common(): print('  fora:', k, n)
    # CONFERENCIA — REGRA DE OURO: nunca sobra ponto de barra
    ruins = [r for r in D if r['orc'] and r['sobra'] != 0]
    print('sobrou ponto de barra ...', len(ruins), '(tem que ser 0)')
    if ruins:
        for r in ruins[:10]:
            print('   ⛔', r['nome'], '|', r['tipo'], 'orc', r['orc'], 'sobra', r['sobra'])
        print('PAREI. Nao gravei nada — corrija antes de gerar.')
        pausa(); return
    print('ja vem com os 2 .........', sum(1 for r in D if r.get('nao_cabe_mais')), 'linhas')
    print('sem vaga (carta velha) ..', sum(1 for r in D if r.get('slot') == 0), 'linhas')
    print('barras em portugues .....',
          sum(1 for r in D if r['sisBar']), 'linhas com barra')
    print('cards distintos ........', len({r['id'] for r in D}))
    print('funcoes ................', len({r['tipo'] for r in D}))
    print('sem metadado de tela ...', sum(1 for r in D if r['id'] not in meta),
          'linhas (com, age, pe fraco e MAX vazios — cosmetico)')

    # ===== AS LINHAS DA TELA VAO PARA O BANCO =============================
    # Aqui o D ja passou por todas as travas deste programa — inclusive a que
    # PARA e nao grava nada se sobrar ponto de barra. E o momento certo de
    # mandar: linha conferida, do jeito que a tela recebe.
    try:
        _tela.sobe(D)
        print(_tela.resumo())
    except Exception as _e:
        print('   [tela] %s' % _e)
        print('   [tela] segui em frente — o encaixe e gerado do mesmo jeito.')

    # ⛔ ETAPA 2: com o arquivo TELA-SEM-DADOS.txt na pasta, o encaixe sai SEM
    #    as linhas dentro e passa a busca-las no banco. Sem esse arquivo, sai
    #    como sempre saiu. E o interruptor que garante que o Luis nunca fica
    #    sem tela por causa de uma mudanca minha.
    _dentro = '[]' if getattr(_tela, 'SEM_DADOS', False) \
              else json.dumps(D, ensure_ascii=False)
    novo = html[:pos[0]] + 'const D=' + _dentro + html[pos[1]:]
    novo, _tema = patch_tema_padrao(novo)
    novo, quantos = patch_tambem_joga(novo)
    novo, _p1 = patch_interface_p1(novo)
    novo, _p2 = patch_interface_p2(novo)
    novo, _p3 = patch_interface_p3(novo)
    novo, _cnd = patch_condicional(novo)
    novo, _tr = patch_trocas(novo)
    novo, _pk = patch_pacote(novo)
    novo, _bh = patch_boxes_home(novo)
    _hist = guarda_historico_de_campanhas()
    novo, _ct = patch_contador(novo, res)
    novo, _mt = patch_meu_time(novo)
    novo, _vl = patch_vaga_no_lugar(novo)
    novo, _lt = patch_limpa_tarjas(novo)
    novo, _fp = patch_fecha_pesos(novo)
    novo, _pr = patch_pe_ruim(novo)
    novo, _ml = patch_mt_layout(novo)
    novo, _ni = patch_nome_impeto(novo)
    novo, _ts = patch_tecnico_sugestao(novo)
    novo, _mf = patch_molde_fisico(novo)
    novo, _fn = patch_falso_nove(novo)
    print('FALSO NOVE (19a funcao) .........:', '%d de 16' % _fn)
    novo, _st = patch_setores(novo)
    novo, _ev = patch_edicao_viva(novo)
    print('EDICAO VIVA 14/08 (nota se refaz + condicional):', '%d de 2' % _ev)
    novo, _cm = patch_conta_do_motor(novo)
    novo, _cab = patch_modal_cabecalho(novo)
    novo, _nb = patch_nota_1508c(novo)
    print('BONUS NA NOTA 15/08 (ACH_BONUS + pe ruim):', '%d de 2' % _nb)
    _dc = novo.count('"Volante de conten\\u00e7\\u00e3o": {"Altura": 1') \
        + novo.count('"Volante de contenção": {"Altura": 1')
    print('DIRECAO DO CORPO CORRIGIDA 15/08 (21 celulas):',
          'entrou' if _dc else 'NAO ENTROU')
    novo, _ap = patch_apaga_punicao(novo)
    print('PUNICAO DE MIGRACAO APAGADA 15/08:', '%d de 5' % _ap)
    novo, _bl = patch_barra_lateral(novo)
    print('NOMES DA BARRA LATERAL 15/08:', '%d rotulos' % _bl)
    novo, _bp = patch_bonus_pronto(novo)
    print('BONUS PRONTO DO MOTOR 15/08 (a tela nao calcula mais):', _bp)
    novo, _v2 = patch_visual_1508b(novo)
    novo, _ce = patch_conserto_elenco_1608(novo)
    novo, _md = patch_modal_1608(novo)
    novo, _m2 = patch_modal_1608b(novo)
    novo, _nm = patch_nota_do_meu_time_1608(novo)
    novo, _hb = patch_home_blocos_1608(novo)
    novo, _pt = patch_pontuacao_e_podio_1608(novo)
    novo, _cf = patch_cabecalho_e_filtros_1608(novo)
    novo, _el = patch_elenco_1608(novo)
    novo, _bu = patch_build_do_usuario_1608(novo)
    novo, _sc = patch_seletor_de_card_1608(novo)
    novo, _t6 = patch_direcao_1808(novo)
    print('A ABA MEU TIME MEDIA NA REGUA 16/08:',
          ('%d lugares (uma r\u00e9gua s\u00f3 para o b1n)' % _nm) if _nm >= 2
          else ('\u26d4 s\u00f3 %d lugar — a casca mudou, CONFERIR' % _nm))
    print('CONSERTO DA ABA DO ELENCO 16/08:', _ce)
    print('TELA DE INICIO EM BLOCOS 16/08:', _hb)
    print('PONTUACAO + PODIO + PAGINA DE POSICOES 16/08:', _pt)
    print('CABECALHO + FILTROS + ALCANCE DA BUSCA 16/08:', _cf)
    print('A ABA DO ELENCO 16/08:', _el)
    print('FAZER MINHA BUILD 16/08:', _bu)
    print('SELETOR DE CARD 16/08:', _sc)
    print('CASCA DO TURNO 6 18/08 (abas + cores + fonte):',
          'entrou' if _t6 else 'JA ESTAVA')
    print('CONSERTOS DO MODAL 16/08:', _md)
    print('MODAL 2a LEVA 16/08 (barras, botao, colunas, pool):', _m2)
    print('VISUAL DO MODAL 15/08 - 2a leva (13 ajustes):',
          'entrou' if _v2 else 'JA ESTAVA')
    print('CABECALHO DO MODAL 15/08 (campinho + botoes por proficiencia):',
          '%d de 39' % _cab)
    print('CONTA DO MOTOR 15/08 (a tela usa a equacao do motor):',
          ('%d habilidades + multiplicador do tecnico' % _cm) if _cm else 'NAO ENTROU')
    print('setores 12/08 (VOL->defesa, SA->ataque):', '%d de 3' % _st)
    # ======================================================================
    #  A TRAVA DE SINTAXE — 15/08/2026
    #  Em 15/08 a tela foi ao chao inteira por UM caractere: um `${...}` posto
    #  dentro de uma string de aspas simples fez o travessao fechar a string,
    #  o <script> do `const D` nao compilou e a pagina abriu vazia. O gerador
    #  disse "gravado" do mesmo jeito.
    #  Agora ele CONFERE cada bloco <script> antes de gravar. Se algum nao
    #  compilar, NAO grava e mostra onde esta o erro — o arquivo bom que ja
    #  esta no disco continua de pe.
    # ======================================================================
    def _confere_js(txt):
        import shutil, subprocess, tempfile
        # REDE 1 (sempre roda, nao precisa de nada instalado): o padrao exato
        # que derrubou a tela em 15/08 — um `${...}` DENTRO de uma string de
        # aspas simples. Ali o `${` nao interpola e o primeiro acento/travessao
        # de dentro fecha a string, matando o <script> inteiro.
        for m in re.finditer(r"\$\{[^{}]{0,120}?\?'[^']{0,300}?\$\{", txt):
            return -1, ('${...} dentro de uma string de aspas simples:\n\n   '
                        + txt[m.start():m.start() + 220]
                        + '\n\n   Dentro de string, CONCATENA: \'texto \'+(x)+\' resto\'')
        # REDE 2 (so quando ha node): compila cada bloco de verdade
        if not shutil.which('node'):
            return None, 'ok pela conferencia interna (sem node para compilar)'
        for k, m in enumerate(re.finditer(r'<script[^>]*>(.*?)</script>', txt, re.S)):
            corpo = m.group(1)
            if not corpo.strip():
                continue
            with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                             encoding='utf-8') as f:
                f.write(corpo); nome = f.name
            r = subprocess.run(['node', '--check', nome],
                               capture_output=True, text=True)
            try: os.remove(nome)
            except Exception: pass
            if r.returncode:
                return k, (r.stderr or '')[:1200]
        return None, 'ok'

    # ======================================================================
    #  O RETRATO DA GERACAO — 16/08/2026
    #  Ordem do Luis: *"o console tem um trilhao de linhas, como e que eu vou
    #  achar isso numa janela dessas? Nao tem jeito nao."*  Tem: o que
    #  interessa passa a ficar num arquivo de meia tela, sempre no mesmo lugar.
    #  ⛔ So escreve um .txt. Nao muda nada do que a tela faz.
    # ======================================================================
    try:
        # ------------------------------------------------------------------
        #  O ALARME NO TOPO — 16/08, 2a ordem do Luis: *"nao tem como eu fazer
        #  isso nao velho, e gigantesca a tela"*. Meia tela ainda e tela demais
        #  quando esta tudo certo. Entao: se estiver tudo certo, a PRIMEIRA
        #  linha diz isso e acabou. Se nao estiver, a primeira linha e o que
        #  deu errado. Ele nao precisa ler o resto nunca.
        # ------------------------------------------------------------------
        _erros = []
        if not _cm:
            _erros.append('a CONTA DO MOTOR nao entrou  ->  leia o POR-QUE-A-CONTA-NAO-ENTROU.txt')
        if _nm != 2:
            _erros.append('a nota da aba MEU TIME: %d de 2 (era para ser 2)  ->  a casca mudou' % _nm)
        if 'return d?100*n/d:0;})(c.arows)' not in novo:
            _erros.append('a conta nova da aba MEU TIME NAO esta no HTML gerado')
        if not _dc:
            _erros.append('a direcao do corpo nao entrou')
        if _hb.startswith('NAO'):
            _erros.append('a TELA DE INICIO EM BLOCOS nao entrou: %s' % _hb)
        if 'HOME_EM_BLOCOS_1608' not in novo:
            _erros.append('a TELA DE INICIO EM BLOCOS nao esta no HTML gerado')
        if 'NAO ACHEI' in _pt:
            _erros.append('a troca de NOTA por PONTUACAO nao achou tudo: %s' % _pt)
        if 'PODIO_E_BLOCOS_1608' not in novo:
            _erros.append('o PODIO E OS 4 BLOCOS nao estao no HTML gerado')
        if 'CABECALHO_E_FILTROS_1608' not in novo:
            _erros.append('o CABECALHO E OS FILTROS novos nao estao no HTML gerado')
        if _el.startswith('NAO'):
            _erros.append('a ABA DO ELENCO nao entrou: %s' % _el)
        if 'ELENCO_1608' not in novo:
            _erros.append('a ABA DO ELENCO nao esta no HTML gerado')
        if _bu.startswith('NAO'):
            _erros.append('a FAZER MINHA BUILD nao entrou: %s' % _bu)
        if 'BUILD_DO_USUARIO_1608' not in novo:
            _erros.append('a FAZER MINHA BUILD nao esta no HTML gerado')
        if 'FAZER MINHA BUILD' not in novo:
            _erros.append('o rotulo da aba continua MEU CARD  ->  o alvo mudou de forma')
        if 'SELETOR_1608' not in novo:
            _erros.append('o SELETOR DE CARD enxuto nao esta no HTML gerado')

        _linhas = [
            'RETRATO DA GERACAO — abra este arquivo em vez de procurar no console',
            '',
        ]
        if _erros:
            _linhas += ['#' * 66,
                        '  ⛔ OLHA AQUI — %d coisa(s) para resolver:' % len(_erros)]
            _linhas += ['     %d. %s' % (i + 1, e) for i, e in enumerate(_erros)]
            _linhas += ['#' * 66, '']
        else:
            _linhas += ['  ✅ TUDO CERTO NESTA GERACAO. Nao precisa ler mais nada abaixo.',
                        '']
        _linhas += [
            'CONTA DO MOTOR (o CONTA-DO-MOTOR.js, com a equacao de 15/08)',
            ('   ENTROU — %d habilidades' % _cm) if _cm
            else '   NAO ENTROU  <<<<<< o motivo esta no POR-QUE-A-CONTA-NAO-ENTROU.txt',
            '',
            'A NOTA DA ABA MEU TIME (conserto de 16/08)',
            #  Antes, o notaComTec e o notaCfg reescreviam o c.b1n com o b1nDe
            #  — a REGUA reescalada (92 + b1*20/topo) — e nao com o percentual
            #  do molde. Medido em 12.203 cards: mediana 13,88 pontos de
            #  diferenca, e 5,9% dos pares da mesma funcao trocavam de ordem.
            ('   CONSERTADA — %d de 2 (notaComTec e notaCfg)' % _nm) if _nm == 2
            else '   ⛔ %d de 2  <<<<<< a casca mudou, o alvo se perdeu' % _nm,
            '',
            'OS BLOCOS DA SESSAO DA TELA (16/08)',
            '   aba do ELENCO ...: %s' % _ce,
            '   modal 1a leva ...: %s' % _md,
            '   modal 2a leva ...: %s' % _m2,
            '   tela de inicio ..: %s (blocos, %% do topo, box em tela cheia)' % _hb,
            '   pontuacao/podio .: %s' % _pt,
            '   cabecalho/filtros: %s' % _cf,
            '   aba do ELENCO ...: %s' % _el,
            '',
            'CONTADOR DO CABECALHO',
            '   %s' % _ct,
            '',
            'OUTROS',
            '   falso nove ......: %d de 16' % _fn,
            '   bonus pronto ....: %s' % _bp,
            '   direcao do corpo : %s' % ('entrou' if _dc else 'NAO ENTROU'),
            '',
            'CONFERENCIA RAPIDA DENTRO DO HTML GERADO',
            '   punicao com teto 9 .......: %s' % ('sim' if 'PUNICAO_COM_TETO' in novo else 'NAO'),
            '   conta do motor embutida ..: %s' % ('sim' if 'CONTA_DO_MOTOR_1508' in novo else 'NAO'),
            '   duas abas (MEU CARD) .....: %s' % ('sim' if 'MEU CARD' in novo else 'NAO'),
            '   tarja NAO SEI fora .......: %s' % ('sim' if 'A TARJA DO NAO SEI' not in novo else 'NAO'),
            '   inicio em blocos .........: %s' % ('sim' if 'HOME_EM_BLOCOS_1608' in novo else 'NAO'),
            '   podio 1-2-3 e 4 blocos ...: %s' % ('sim' if 'PODIO_E_BLOCOS_1608' in novo else 'NAO'),
            '   cabecalho e filtros novos : %s' % ('sim' if 'CABECALHO_E_FILTROS_1608' in novo else 'NAO'),
            '   aba do elenco nova .......: %s' % ('sim' if 'ELENCO_1608' in novo else 'NAO'),
            '   FAZER MINHA BUILD ........: %s' % ('sim' if 'BUILD_DO_USUARIO_1608' in novo else 'NAO'),
            '   seletor de card enxuto ...: %s' % ('sim' if 'SELETOR_1608' in novo else 'NAO'),
            '   o rotulo da aba ..........: %s' % ('FAZER MINHA BUILD' if 'FAZER MINHA BUILD' in novo else 'AINDA E MEU CARD'),
            '   a palavra "nota" na tela ..: %s' % ('trocada' if 'content:"pontuação"' in novo else 'AINDA ESTA LA'),
        ]
        open('RETRATO-DA-GERACAO.txt', 'w', encoding='utf-8').write(
            '\r\n'.join(_linhas) + '\r\n')
    except Exception as _e:
        print('nao consegui gravar o RETRATO-DA-GERACAO.txt: %s' % _e)

    # O catalogo era declarado como `const HABEF` dentro da casca. As telas
    # compartilhadas sao avaliadas por outra camada e, nessa camada, o nome
    # lexical nao existe: o seletor de habilidades adicionais nascia vazio.
    # Publica o mesmo objeto no `window`; o motor continua lendo `HABEF` e a
    # tela passa a ler `window.HABEF`, sem duplicar catalogo nem regra.
    novo = novo.replace('const HABEF=', 'window.HABEF=', 1)

    _bloco, _msg = _confere_js(novo)
    if _bloco is not None:
        print()
        print('=' * 70)
        print('  NAO GRAVEI — A TELA SAIRIA QUEBRADA'
              + ('' if _bloco < 0 else ' (bloco <script> n%d)' % _bloco))
        print('=' * 70)
        print(_msg)
        print()
        print('  O %s ANTIGO continua no lugar, inteiro.' % SAIDA)
        pausa()
        sys.exit(1)
    print('sintaxe dos scripts .....', _msg)

    open(SAIDA, 'w', encoding='utf-8').write(novo)
    print('etiqueta TAMBEM JOGA virou botao:', 'SIM' if quantos else 'NAO ACHEI O TRECHO')
    print('interface parte 1 (09/08) .......:', '%d de 7' % _p1)
    print('interface parte 2 (09/08) .......:', '%d de 7' % _p2)
    print('interface parte 3 (09/08) .......:', '%d de 7' % _p3)
    print('IMPETO CONDICIONAL (botao) ......:', 'LIGADO' if _cnd else 'ja estava')
    print('bloco 2 · lista de fora .........:', '%d' % _tr)
    print('SUGESTAO DE TECNICO (na tela) ...:', _ts)
    print('MOLDE DO FISICO .................:', _mf)
    print('BOXES na home (ativas/aba) ......:', _bh)
    print('HISTORICO de campanhas ..........:', _hist)
    print('CONTADOR na barra ...............:', _ct)
    print('MEU TIME (elenco semeado) .......:', _mt)
    print('VAGA no bloco do impeto .........:', '%d de 2' % _vl)
    print('LIMPEZA das tarjas e do MAX .....:', '%d de 4' % _lt)
    print('PESOS fechados (IA=1 · fisico=1) :', '%d de 3' % _fp)
    print('PE RUIM (bonus ate +1,00) .......:', _pr)
    print('LAYOUT do MEU TIME ..............:', _ml)
    print('NOME DO IMPETO na ficha .........:', _ni)
    print()
    print('TEMA padrao escuro ..............:', 'sim' if _tema else 'a casca ja mudou — CONFERIR')
    print('gravado:', SAIDA, '%.1f MB' % (os.path.getsize(SAIDA) / 1024 / 1024))

    # ⛔ 18/08 — O QUE VAI PARA O DRIVE E A VERSAO LEVE, nao a gorda.
    #    O arquivo da maquina continua com as linhas dentro (funciona offline,
    #    e o Luis abre ele direto). O do Drive busca as linhas no banco: 2 MB
    #    em vez de 37, e o link nunca mais serve tela velha.
    #    Se a copia leve falhar por qualquer motivo, o espelho manda a GORDA —
    #    tela velha e ruim, tela nenhuma e pior.
    _leve, _quanto = versao_do_banco(novo, D)
    if _leve:
        print('versao do banco:', _leve, _quanto)
        print('espelho:', espelha(_leve))
    else:
        print('versao do banco: NAO SAIU (%s) — espelhando a versao gorda' % _quanto)
        print('espelho:', espelha(SAIDA))
    print()
    print('Abra ele no navegador. As fichas da v5 NAO estao la — so o que a v6 rodou.')
    if not int(os.environ.get('ENCAIXE_CICLO', '0') or 0):
        pausa()




# ============================================================================
#  A ETIQUETA DE "TAMBEM JOGA" VIRA BOTAO
#
#  Pendencia aberta desde 06/08: "as etiquetas parecem botao e nao sao
#  (posLinha() sem onclick)". O Luis clicava em Meia ofensivo / Segundo atacante
#  na ficha do card e nao vinha nada.
#
#  A regra, ditada por ele em 08/08: "se e SA artilheiro, se e artilheiro e a
#  mesma funcao, e so repetir no botao". Ou seja:
#
#      clica na posicao -> funcao = REGRA[posicao](estilo do card) -> abre aquela ficha
#
#  Se duas posicoes caem na mesma funcao, as duas apontam para ela. Se a funcao
#  ainda nao tem linha calculada, o botao fica apagado e o titulo diz o motivo —
#  nunca mais clique que nao faz nada em silencio.
#
#  ⛔ Isto NAO toca no molde nem na nota. E so navegacao.
# ============================================================================


# ============================================================================
#  INTERFACE — PARTE 1 (Luis, 09/08). SO APARENCIA. Nao encosta no motor.
#
#  1 impeto de fabrica com o NOME na ficha
#  2 posicao com a sigla do jogo:  Meia de ligacao (MLG)
#  3 tira o "+X% vs molde" do cabecalho da nota (a nota ja diz isso)
#  4 renomeia 4 funcoes (so nomenclatura)
#  5 MAX = OVR maximo da carta (maxOvr), nao o sisOvr
#  6 bloco da direita vira coluna: tecnico usado / sugestoes / impeto nativo
#  7 habilidades em topicos, uma por linha; "De fora" vira "Nao alteram a nota"
#
#  Feito AQUI e nao na casca de proposito: trocar a casca nao desfaz.
# ============================================================================
RENOMEIA_FUNCAO = [
    # 15/08: a nomenclatura certa e 'Ponta finalizador' (Luis).
    # ⛔ SO NA TELA. No banco a funcao continua 'Ponta finalizadora' —
    #    trocar la mexeria na tabela `funcoes` e em 1.140 linhas de build.
    # 15/08 — o CRITERIO que acabou com a ambiguidade (Luis): se comeca com
    # 'Ponta', e POSICAO; se e 'Atacante ...', e FUNCAO. Assim o nome ja
    # diz qual das duas coisas a pessoa esta lendo.
    ('Ponta finalizadora', 'Atacante finalizador'),
    ('Ponta criadora', 'Atacante criador'),
    # 15/08, 2a leva: o Luis trocou 'Ala atacante' por 'Ala finalizador'.
    # ⛔ SO NA TELA. No banco a funcao continua 'Meia lateral atacante'.
    ('Meia lateral atacante', 'Ala finalizador'),
    ('Meia lateral cruzador', 'Ala cruzador'),
    ('Ponta de lan\u00e7a', 'Atacante infiltrador'),
    ('Meia ofensivo armador', 'Meia ofensivo'),
    # 15/08 — o meio pela CADEIA do jogo (raciocinio do Luis):
    #   volante toma -> volante constroi -> ARMADOR passa e espera
    #                                    -> ARRANQUE recebe e leva
    #   -> meia ofensivo / ataque
    # Confere com o molde: o que a 'avancada' tem a mais que a armadora e
    # Aceleracao +4 e Potencia de chute +4 — ela arranca e arrisca.
    ('Meia de liga\u00e7\u00e3o armador', 'Meia armador'),
    ('Meia de liga\u00e7\u00e3o avan\u00e7ado', 'Meia de arranque'),
    ('Meia central armador', 'Meia armador'),
    ('Meia central de chegada', 'Meia de arranque'),
    # 15/08: a FUNCAO 'Segundo atacante' vira 'Ponta de lanca' — o nome
    # colidia com a POSICAO SA (Segundo atacante) e confundia todo mundo.
    # 15/08 — o trio do ataque fecha pelo que cada um FAZ:
    #   Atacante criador (passe) · finalizador (gol) · infiltrador (chegada)
    ('Segundo atacante', 'Atacante infiltrador'),

    ('Meia central armador',    'Meia de ligação armador'),
    ('Meia central de chegada', 'Meia de ligação avançado'),
    ('Meia de lado por dentro', 'Ala finalizador'),
    ('Meia de lado por fora',   'Ala cruzador'),
]


def _esc(s):
    """O mesmo texto na forma que o json.dumps(ensure_ascii=True) grava.

    ⚠️ 15/08 — o defeito que isto conserta: o `RENOMEIA_FUNCAO` e um replace
    de texto no HTML, mas varias tabelas sao injetadas com `ensure_ascii`,
    isto e, com o acento virando `\u00e7`. O nome 'Meia de ligacao armador'
    aparecia ESCAPADO no `MF_FAIXA`, o replace nao casava, e a tabela ficava
    com o nome velho enquanto a linha ja vinha com o novo.
    Medido nas 12.161 linhas: 1.439 (887 Meia armador + 552 Meia de arranque)
    estavam com o bloco FISICO ZERADO — b4r 0 e bonus 0 — porque
    `MF_FAIXA[c.tipo]` nao achava a funcao. O corpo vale de -1,5 a +1,5, entao
    essas duas funcoes estavam ranqueando SEM o fisico, em silencio.
    """
    return ''.join(c if ord(c) < 128 else '\\u%04x' % ord(c) for c in s)


def _renomeia(html):
    """Troca os nomes das funcoes nas DUAS formas: com acento e escapado."""
    for velho, novo in RENOMEIA_FUNCAO:
        if velho in html:
            html = html.replace(velho, novo)
        ev = _esc(velho)
        if ev != velho and ev in html:
            html = html.replace(ev, _esc(novo))
    html = html.replace('SA:"Atacante infiltrador"', 'SA:"Segundo atacante"')
    html = html.replace("SA:'Atacante infiltrador'", "SA:'Segundo atacante'")
    return html


_CSS_P1 = ("\n<style>\n"
           ".hbgrp{margin:7px 0 2px}\n"
           ".hbgrp>b{display:block;font-size:10.5px;text-transform:uppercase;"
           "letter-spacing:.5px;color:#8fa4c4;margin-bottom:3px}\n"
           ".hblist{list-style:none;margin:0;padding:0}\n"
           ".hblist li{padding:1px 0;line-height:1.55}\n"
           "html[data-tema] .hbgrp>b{color:var(--txt2)!important}\n"
           "</style>\n")


def patch_interface_p1(html):
    ok = 0

    # ---- 5. MAX = o OVR maximo da carta ------------------------------------
    a = 'OVR base ${c.ovr} \u2192 M\u00c1X ${c.sisOvr.toFixed(2)}'
    b = 'OVR base ${c.ovr} \u2192 M\u00c1X ${(c.maxOvr||c.sisOvr||0)}'
    if a in html:
        html = html.replace(a, b); ok += 1

    # ---- 3. tira o "% vs molde" do cabecalho --------------------------------
    pat = re.compile(chr(101)+chr(108)+r'\.innerHTML=t\+.{0,400}?vs molde</span>.;', re.S)
    if pat.search(html):
        html = pat.sub('el.innerHTML=t;', html); ok += 1

    # ---- 2. posicao com a sigla do jogo -------------------------------------
    i = html.find('const POSN={')
    j = html.find('};', i)
    if i > 0 and j > i:
        novo = ('const POSN={GK:"Goleiro",ZC:"Zagueiro",LE:"Lateral esq.",LD:"Lateral dir.",'
                'VOL:"Volante",MC:"Meia de liga\u00e7\u00e3o",MLE:"Meia lateral esquerda",'
                'MLD:"Meia lateral direita",MO:"Meia atacante",PE:"Ponta esquerda",'
                'PD:"Ponta direita",SA:"Segundo atacante",CA:"Centroavante"};\n'
                'const SIGJ={GK:"GO",ZC:"ZC",LE:"LE",LD:"LD",VOL:"VOL",MC:"MLG",MLE:"MLE",'
                'MLD:"MLD",MO:"MAT",PE:"PTE",PD:"PTD",SA:"SA",CA:"CA"};')
        html = html[:i] + novo + html[j + 2:]
        ok += 1
    a = "function posLabel(p){return MODO_ADM?(POSN[p]||p||'\u2014'):(p||'\u2014');}"
    b = ("function posLabel(p){if(!p)return '\u2014';"
         "return (POSN[p]||p)+' ('+(SIGJ[p]||p)+')';}")
    if a in html:
        html = html.replace(a, b); ok += 1

    # ---- 7. habilidades em topicos -----------------------------------------
    i = html.find('const _recHab=')
    j = html.find('const _recMot=', i)
    if i > 0 and j > i:
        novo = (
            "const _recHab=`<div class=receita><b class=receitatt>Habilidades</b>`\n"
            "  +`<div class=hbgrp><b>Nativas</b><ul class=hblist>"
            "${(_nat.length?_nat:['\u2014']).map(s=>`<li>${s}</li>`).join('')}</ul></div>`\n"
            "  +`<div class=hbgrp><b>Adicionadas</b><ul class=hblist>"
            "${_hab.length?_hab.map((s,ix)=>`<li><span class=chip "
            "style=\"border-color:#f0a531;color:#f0a531\">${s} "
            "<b style=\"cursor:pointer\" onclick=\"remHab('${K}',${ix})\">\u00d7</b>"
            "</span></li>`).join(''):'<li>nenhuma</li>'}</ul>`\n"
            "  +(_hab.length<5&&_pool.length?`<select style=\"max-width:170px\" "
            "onchange=\"addHab('${K}',this.value);this.value=''\">"
            "<option value=\"\">+ adicionar\u2026</option>"
            "${_pool.map(s=>`<option>${s}</option>`).join('')}</select>`:'')\n"
            "  +`</div>`\n"
            "  +((c.NEU&&c.NEU.length)?`<div class=hbgrp><b>Boas op\u00e7\u00f5es</b>"
            "<ul class=hblist>${c.NEU.map(x=>`<li><span class=chip "
            "style=\"border-color:#5d6673;color:#8d97a3\">${x}</span></li>`).join('')}"
            "</ul></div>`:'')\n"
            "  +`</div>`;\n "
        )
        html = html[:i] + novo + html[j:]
        ok += 1

    # ---- 1 + 6. o bloco da direita, em coluna ------------------------------
    i = html.find('const _recMot=')
    j = html.find('`</div>`;', i)
    if i > 0 and j > i:
        novo = (
            "const _recMot=`<div class=receita>`\n"
            # 15/08 — as HABILIDADES ESPECIAIS sobem para ca. Ordem do Luis:
            #   "so interessa essa parte; nao faz sentido ficar separado la —
            #    poe em cima do tecnico utilizado".
            "  +((c.raras&&c.raras.length)?`<div class=hbgrp>"
            "<b>Habilidades especiais</b><div class=chips>"
            # 15/08: sem o numero na frente — *"nao precisa desse numero"*
            "${c.raras.map(s=>`<span class=\"chip rr\">${s}</span>`).join('')}"
            "</div></div>`:'')\n"
            # 15/08 — o SELETOR do tecnico vem morar aqui. Ordem do Luis:
            #   "o tecnico ja tem aqui, olha: TECNICO UTILIZADO. Entao poe
            #    so la; ai o cara troca se ele quiser."
            "  +`<div class=hbgrp><b>T\u00e9cnico utilizado"
            "${(c._tecNome!==undefined&&window.ENC_MODO!=='insumos')?"
            "' <b class=receitadim>\u00b7 trocado</b>':''}"
            "</b>${tecSel}</div>`\n"
            "  +((c.TECIG&&c.TECIG.length)?`<div class=hbgrp><b>Sugest\u00f5es de t\u00e9cnico</b>"
            "<ul class=hblist>${c.TECIG.slice(0,5).map(x=>`<li>${x}</li>`).join('')}"
            "</ul></div>`:'')\n"
            "  +`<div class=hbgrp><b>\u00cdmpeto nativo</b><ul class=hblist>"
            "${(function(){const f=(c.nmn&&c.nmn.length)?c.nmn:(c.imps||[]).filter(x=>x&&x.f).map(x=>x.n).filter(Boolean);"
            "return f.length?f.map(n=>`<li>${n}</li>`).join(''):'<li>n\u00e3o tem</li>';})()}"
            "</ul></div>`\n"
            "  +((c.slot===0&&String(c.imp||'').trim())?`<div class=hbgrp>"
            "<b style=\"color:#e46a6a\">\u26a0 carta SEM VAGA \u2014 o \u00edmpeto escolhido "
            "n\u00e3o existe no jogo</b></div>`:'')\n"
            "  +(_cond?`<div class=hbgrp><button class=bbt style=\"width:auto;padding:0 8px\" "
            "onclick=\"toggleCondCard('${K}')\" title=\"\u00edmpeto condicional deste card\">"
            "\u2692 condicional \u00b7 degrau ${c.cmode||1}</button>"
            "</div>`:'')\n"
            "  +"
        )
        html = html[:i] + novo + html[j:]
        ok += 1

    # ---- 8. o botao GLOBAL do impeto condicional (10/08) -------------------
    # Ele ja existia, mas com a classe `admonly` — so aparecia no modo
    # administrador. O Luis pediu os dois: um na ficha do card (ja existe,
    # toggleCondCard) e um na tela geral, que troca todos e reordena.
    a = 'class="hb admonly" id=condbt'
    if a in html:
        html = html.replace(a, 'class="hb" id=condbt title="troca TODOS os '
                               '\u00edmpetos condicionais: +1 (1 a 7 jogadores) \u00b7 '
                               '+2 (8 a 10) \u00b7 +3 (11 a 23)"')
        ok += 1

    # ---- 4. os nomes novos das funcoes (SO nomenclatura) -------------------
    html = _renomeia(html)
    # a POSICAO SA nao muda de nome — so a FUNCAO. Como o replace acima e
    # global, aqui a posicao e devolvida ao nome dela nas duas tabelas.
    html = html.replace('SA:"Atacante infiltrador"', 'SA:"Segundo atacante"')
    html = html.replace("SA:'Atacante infiltrador'", "SA:'Segundo atacante'")
    html = html.replace('"Meia de liga\u00e7\u00e3o armador":"armador"',
                        '"Meia de liga\u00e7\u00e3o armador":"armador"')
    html = html.replace('"Meia de liga\u00e7\u00e3o avan\u00e7ado":"de chegada"',
                        '"Meia de liga\u00e7\u00e3o avan\u00e7ado":"avan\u00e7ado"')
    html = html.replace('"Meia lateral atacante":"por dentro"',
                        '"Meia lateral atacante":"atacante"')
    html = html.replace('"Meia lateral cruzador":"por fora"',
                        '"Meia lateral cruzador":"cruzador"')
    html = html.replace('"MEIA CENTRAL":"MC"', '"MEIA DE LIGA\u00c7\u00c3O":"MLG"')
    html = html.replace('"MEIA CENTRAL"', '"MEIA DE LIGA\u00c7\u00c3O"')
    html = html.replace("'MEIA CENTRAL'", "'MEIA DE LIGA\u00c7\u00c3O'")
    html = html.replace('"MEIA LATERAL":"MLE \u00b7 MLD"', '"MEIA LATERAL":"MLE \u00b7 MLD"')
    html = html.replace('"MEIA OFENSIVO":"MO \u00b7 SA"', '"MEIA OFENSIVO":"MAT \u00b7 SA"')
    html = html.replace('"PONTA":"PE \u00b7 PD"', '"PONTA":"PTE \u00b7 PTD"')
    html = html.replace('"GOLEIRO":"GK"', '"GOLEIRO":"GO"')

    # ---- css dos topicos ---------------------------------------------------
    k = html.find('</head>')
    if k > 0:
        html = html[:k] + _CSS_P1 + html[k:]
        ok += 1
    return html, ok



# ============================================================================
#  INTERFACE — PARTE 2 (Luis, 09/08). SO APARENCIA.
#   1 titulo "Bloco 1 · Atributos vs molde do tipo" vira so "Atributos", maior
#   2 "Level Cap" vira "Nivel"; some a palavra "Pontos"; 62/62 em fonte maior
#   4 tabela de atributos: base primeiro, habilidade separada em nativas e
#     adicionadas, depois Total, Alvo, vs alvo, Pontos. Tudo centralizado.
# ============================================================================
_CSS_P2 = ("\n<style>\n"
           ".h3big{font-size:16.5px!important;letter-spacing:.3px!important}\n"
           ".ptsbig{font-size:15px}\n"
           ".atgc{grid-template-columns:minmax(136px,1fr) 88px 44px 50px 50px 52px 50px 60px 64px "
           "50px 44px 46px 56px!important;text-align:center!important}\n"
           ".atgc>span:first-child,.atgc>b:first-child{text-align:left}\n"
           "</style>\n")


def patch_interface_p2(html):
    ok = 0

    # ---- 1. o titulo -------------------------------------------------------
    a = "<h3>${MODO_ADM?'Bloco 1 \u00b7 Atributos vs molde do tipo':'Atributos'}</h3>"
    if a in html:
        html = html.replace(a, "<h3 class=h3big>Atributos</h3>"); ok += 1

    # ---- 2. nivel + pontos -------------------------------------------------
    a = "Level Cap <b>${lc}</b> \u00b7 Pontos <b>${gasto}</b>/<b>${c.orc}</b>"
    b = "N\u00edvel <b>${lc}</b> \u00b7 <b class=ptsbig>${gasto}/${c.orc}</b>"
    if a in html:
        html = html.replace(a, b); ok += 1

    # ---- 4a. helper: o valor so com as habilidades NATIVAS -----------------
    a = "function etapas(c,lvl){"
    b = ("function _e4nat(c,lvl){const E=etapas(c,lvl),bf=buffDe(c.fab||[]);\n"
         " return E.map((e,i)=>bf[i]?aplicaBuff(e[3],bf[i][0],bf[i][1]):e[3]);}\n"
         "function etapas(c,lvl){")
    if a in html and '_e4nat' not in html:
        html = html.replace(a, b, 1); ok += 1

    a = "const ET=c.base?etapas(c,_lvlDe(c)):null;"
    b = ("const ET=c.base?etapas(c,_lvlDe(c)):null;\n"
         " const ETN=c.base?_e4nat(c,_lvlDe(c)):null;")
    if a in html:
        html = html.replace(a, b, 1); ok += 1

    # ---- 4b. o cabecalho da tabela -----------------------------------------
    a = ("'<div class=\"athead atgc\"><span>Atributo</span><span>Classe</span>"
         "<span>Alvo</span><span>base</span><span>+barras</span><span>+\\u00edmpeto</span>"
         "<span>+t\\u00e9cnico</span><span>+habilid.</span><span>No jogo</span>"
         "<span>vs alvo</span><span>Pontos</span></div>'")
    b = ("'<div class=\"athead atgc\"><span>Atributo</span><span>Classe</span>"
         "<span>Base</span><span>+barras</span><span>+\\u00edmpeto</span>"
         "<span>+t\\u00e9cnico</span><span>Na tela</span><span>+hab. nativas</span>"
         "<span>+hab. adicionadas</span><span>Total</span><span>Alvo</span>"
         "<span>vs alvo</span><span>Pontos</span></div>'")
    if a in html:
        html = html.replace(a, b, 1); ok += 1

    # ---- 4c. a linha -------------------------------------------------------
    a = ("<span class=mini>${r[2]}</span><span class=mini>${e[0]}</span>"
         "${dd(e[0],e[1])}${dd(e[1],e[2])}${dd(e[2],e[3])}${dd(e[3],e[4])}<b>${jogo}</b>"
         "<span class=\"${p?(r[4]>=0?'up':'dn'):'mini'}\">")
    b = ("<span class=mini>${e[0]}</span>"
         "${dd(e[0],e[1])}${dd(e[1],e[2])}${dd(e[2],e[3])}"
         "<b>${e[3]}</b>"
         "${dd(e[3],(ETN?ETN[r[0]]:e[3]))}${dd((ETN?ETN[r[0]]:e[3]),e[4])}"
         "<b>${jogo}</b><span class=mini>${r[2]}</span>"
         "<span class=\"${p?(r[4]>=0?'up':'dn'):'mini'}\">")
    if a in html:
        html = html.replace(a, b, 1); ok += 1

    # troca a REGRA ORIGINAL da grade (nao adianta so acrescentar CSS:
    # a regra antiga vem depois no arquivo e ganha)
    import re as _re
    _g = ('grid-template-columns:minmax(136px,1fr) 88px 44px 50px 50px 52px 50px '
          '60px 64px 50px 44px 46px 56px!important;text-align:center!important')
    _n = 0
    def _sub(mm):
        return '.atgc{display:grid!important;' + _g + ';gap:5px!important;align-items:center}'
    html, _n = _re.subn(r'\.atgc\{[^}]*\}', _sub, html)
    if _n:
        ok += 1
    k = html.find('</head>')
    if k > 0:
        html = html[:k] + _CSS_P2 + html[k:]
    return html, ok



# ============================================================================
#  INTERFACE — PARTE 3 (Luis, 09/08). SO APARENCIA.
#   · tira o "Bloco N ·" de TODOS os titulos
#   · as listas de habilidade (blocos 2 e 5) viram coluna, uma embaixo da outra
# ============================================================================
def patch_interface_p3(html):
    import re as _re
    ok = 0

    # 1. os titulos ---------------------------------------------------------
    pares = [
        ('Bloco 4 \u00b7 F\u00edsico \u2014 molde da fun\u00e7\u00e3o',
         'F\u00edsico \u2014 molde da fun\u00e7\u00e3o'),
        ('Bloco 2 \u00b7 Habilidades', 'Habilidades'),
        ('Bloco 5 \u00b7 Habilidades especiais', 'Habilidades especiais'),
        ('Bloco 3 \u00b7 Estilo de jogo da IA', 'Estilo de jogo da IA'),
        ('TOTAL DO BLOCO 1', 'TOTAL'),
        ('Bloco 2 N\u00c3O \u00e9 reescalado', 'o quadro de habilidades N\u00c3O \u00e9 reescalado'),
    ]
    for velho, novo in pares:
        if velho in html:
            html = html.replace(velho, novo)
            ok += 1

    # 2. as listas de chip em coluna ---------------------------------------
    css = ("\n<style>\n"
           ".chips{display:flex!important;flex-direction:column!important;"
           "align-items:flex-start!important;gap:3px!important;flex-wrap:nowrap!important}\n"
           ".chips>.chip,.chips>span{width:fit-content}\n"
           # 10/08 · a barrinha de arrastar estava presa em 74px por uma regra
           # antiga, e a coluna sobrava espaco a direita. Agora ela ocupa tudo.
           # a coluna da distribuicao era estreita demais: o trio dava 1.45fr pra ela
           # e as outras tres colunas comiam 248px dos ~315. Agora ela pega o dobro
           # das outras duas, e o rotulo/pts/botoes encolhem.
           ".bptrio{grid-template-columns:minmax(0,.85fr) minmax(0,.75fr) minmax(0,2.4fr)!important;gap:6px 14px!important}\n"
           ".bp2{grid-template-columns:1fr!important}\n"
           ".brow{grid-template-columns:110px 1fr 46px 76px!important;gap:10px!important}\n"
           ".brow input[type=range]{width:100%!important;height:7px!important;"
           "-webkit-appearance:none;appearance:none;background:#2a3442;"
           "border-radius:4px;cursor:pointer}\n"
           ".brow input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;"
           "width:17px;height:17px;border-radius:50%;background:#fff;cursor:pointer;"
           "box-shadow:0 0 0 3px #2b5fd955}\n"
           ".brow input[type=range]::-moz-range-thumb{width:17px;height:17px;"
           "border:none;border-radius:50%;background:#fff;cursor:pointer}\n"
           "html[data-tema=claro] .brow input[type=range]{background:#c9d2de}\n"
           "</style>\n")
    flut = ('\n<script>\n(function(){\n'
            ' function poe(){ if(document.getElementById("condflut")) return;\n'
            '  var alvo=document.getElementById("fbt");\n'
            '  if(!alvo) return setTimeout(poe,200);\n'
            '  var b=document.createElement("button"); b.id="condflut";\n'
            '  b.className=alvo.className;\n'
            '  b.style.cssText="display:inline-block;margin-left:8px;'
            'border-color:#f0a531;color:#f0a531;font-weight:700";\n'
            '  var T=["\\u2b21 condicional +1","\\u2b21 condicional +2",'
            '"\\u2b21 condicional +3"];\n'
            '  function pinta(){ var m=(typeof CMODE!=="undefined")?(CMODE||0):0;\n'
            '   b.textContent=T[m]||T[0];\n'
            '   b.style.background=m?"#f0a531":"transparent";\n'
            '   b.style.color=m?"#0e1116":"#f0a531"; }\n'
            '  b.title="troca TODOS os impetos condicionais e reordena o ranking";\n'
            '  b.onclick=function(){ try{ toggleCond(); }catch(e){} pinta(); };\n'
            '  alvo.parentNode.insertBefore(b, alvo.nextSibling); pinta(); }\n'
            ' setInterval(function(){ if(!document.getElementById("condflut")) poe(); }, 900);\n'
            ' poe();\n})();\n</script>\n')
    _k = html.rfind('</body>')
    if _k < 0:
        _k = len(html)
    html = html[:_k] + flut + html[_k:]
    ok += 1

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + html[k:]
    ok += 1
    return html, ok


def patch_tambem_joga(html):
    """Acha a linha do `const sec=sp.map(...)` dentro do posLinha e troca ela inteira.

    Casa pelo INICIO da linha, nao pelo conteudo — o simbolo da estrela vem
    escapado no HTML (\\u2605) e comparar isso em Python passa por duas camadas
    de escape. Localizar a linha e mais seguro.
    """
    regra = json.load(open('regra.json', encoding='utf-8')) if os.path.exists('regra.json') else None
    if not regra:
        print('  (sem regra.json — a etiqueta fica como estava)')
        return html, False

    marca = 'const sec=sp.map'
    i = html.find(marca)
    if i < 0:
        return html, False
    fim = html.find('\n', i)
    if fim < 0:
        return html, False

    subst = (
        "const sec=sp.map(x=>{"
        "const f=funcDaPos(x[0],c.modelo);"
        "const alvo=f?irmAll(c).find(y=>y.tipo===f):null;"
        "const est=x[1]>=2?'\\u2605\\u2605':'\\u2605';"
        "if(alvo)return `<span class=ps2 style=\"cursor:pointer;border-color:#22c58b\" "
        "title=\"abre ${f}\" onclick=\"reabrir('${alvo.id}|${alvo.tipo}')\">"
        "${posLabel(x[0])}<b>${est}</b></span>`;"
        "return `<span class=ps2 style=\"opacity:.45;cursor:not-allowed\" "
        "title=\"${f?('a funcao '+f+' ainda nao foi calculada para este card'):"
        "('nao ha regra de funcao para a posicao '+x[0])}\">"
        "${posLabel(x[0])}<b>${est}</b></span>`;"
        "}).join('');"
        "function irmAll(c){const b=String(c.id).split('@')[0];"
        "return D.filter(x=>x.id!=='MOLDE'&&String(x.id).split('@')[0]===b);}"
    )
    html = html[:i] + subst + html[fim:]

    js = ("\n<script>\n"
          "/* posicao + estilo -> funcao. Mesma tabela do funcao_nativa.py, secao 2.2-B. */\n"
          "const TJ_REGRA=" + json.dumps(regra['REGRA'], ensure_ascii=False) + ";\n"
          "const TJ_SA=" + json.dumps(regra['SA_FAMILIA'], ensure_ascii=False) + ";\n"
          "function funcDaPos(p,modelo){\n"
          " if(!p)return null;p=String(p).trim();\n"
          " if(p==='SA'||p==='SS')p=TJ_SA[modelo]||'MO';\n"
          " const r=TJ_REGRA[p];if(!r)return null;\n"
          " return (r[0]||[]).indexOf(modelo)>=0?r[1]:r[2];\n"
          "}\n</script>\n")
    k = html.find('</head>')
    if k < 0: k = html.find('<script')
    html = html[:k] + js + html[k:]
    return html, True


def patch_trocas(html):
    """Duas sugestoes na ficha, as duas de nota IDENTICA (Luis, 08/08):

      · na caixa Habilidades, uma terceira lista "De fora" — so as que da pra
        selecionar e nao alteram a nota em nada. Teto de 5.
      · na Receita do motor, os outros tecnicos que dao a mesma nota.
    """
    ok = 0
    marca = "  +`<b>Adicionadas:</b> ${_hab.map((s,ix)=>"
    i = html.find(marca)
    if i >= 0:
        j = html.find("\n", i)
        extra = (
            "\n  +((c.NEU&&c.NEU.length)?`<br><b>De fora:</b> "
            "<span class=mini>(da pra selecionar e a nota nao muda)</span><br>"
            "${c.NEU.map(x=>`<span class=chip style=\"border-color:#5d6673;color:#8d97a3\" "
            "title=\"por esta no lugar de uma das adicionadas nao muda a nota\">${x}</span>`)"
            ".join(' ')}`:'')")
        html = html[:j] + extra + html[j:]
        ok += 1

    marca2 = "  +`<b>Técnico:</b> ${((c._tecNome!==undefined?c._tecNome:c.TEC)||'nenhum')}"
    i = html.find(marca2)
    if i >= 0:
        j = html.find("\n", i)
        extra = (
            "\n  +((c.TECIG&&c.TECIG.length)?`<b class=receitadim>mesma nota com:</b> "
            "${c.TECIG.map(x=>`<span class=chip style=\"border-color:#5d6673;color:#8d97a3\" "
            "title=\"este tecnico da a mesma nota\">${x}</span>`).join(' ')}<br>`:'')")
        html = html[:j] + extra + html[j:]
        ok += 1

    # ⛔ 09/08: o BLOCO 2 ainda mostrava "falta do ideal da funcao (incidencia)" —
    # a lista vermelha do pool inteiro, que a regra do pool de 08/08 aposentou
    # ("nao se faz escolha por incidencia"). Troca pela lista DE FORA (as que da
    # pra selecionar sem mudar a nota, teto 5) e joga o pool inteiro num
    # <details> fechado, para quem quiser conferir. Isto e feito AQUI e nao na
    # casca de proposito: assim sobrevive a qualquer troca da casca.
    import re as _re
    _pat = _re.compile(r'<div class="mini admonly"[^>]*>falta do ideal da fun\u00e7\u00e3o'
                       r'.*?</div><div class="chips admonly">\$\{c\.falta\.map.*?</div>',
                       _re.S)
    _m = _pat.search(html)
    if _m:
        novo = ('<div class="mini admonly" style="margin-top:7px">de fora '
                '\u2014 d\u00e1 pra selecionar e a nota N\u00c3O muda</div>'
                '<div class="chips admonly">'
                '${(c.NEU||[]).map(s=>`<span class="chip" style="border-color:#5d6673;'
                'color:#8d97a3">${s}</span>`).join('')||'
                "'<span class=mini>nenhuma troca neutra</span>'}</div>"
                '<details class=admonly style="margin-top:6px"><summary class=mini>'
                'o pool inteiro que o motor pode escolher (${(c.falta||[]).length})'
                '</summary><div class=chips>'
                '${(c.falta||[]).map(s=>`<span class="chip no">${s}</span>`)'
                ".join('')}</div></details>")
        html = html[:_m.start()] + novo + html[_m.end():]
        ok += 1
    return html, ok


def patch_condicional(html):
    """O BOTAO DO IMPETO CONDICIONAL PASSA A FUNCIONAR.

    A casca tinha a maquina pronta, mas ela depende de `c.cdelta` e o
    gerador nunca montava esse campo — `recalcCard` saia na primeira
    linha e clicar no botao nao fazia nada (medido 10/08: 0 de 2.156
    registros com cdelta).

    Aqui o toggleCond e substituido: em vez de somar por fora, ele TROCA
    a build inteira pela que o motor ja calculou para +2 e +3 (campo CD).
    Volta ao +1 restaurando o original guardado na primeira troca.
    """
    if 'condQuantas' in html:
        return html, 0
    sc = "\n<script>\n(function(){\n var ORIG=null;\n function guarda(){\n  if(ORIG) return;\n  ORIG=D.map(function(c){\n   return {b1:c.b1,b1n:c.b1n,v:c.arows.map(function(r){return r[3];}),\n           bar:c.sisBar,TEC:c.TEC,TECB:c.TECB,HAB:c.HAB,adds:c.adds,sobra:c.sobra};\n  });\n }\n function aplica(m){\n  guarda();\n  var g=String(m+1),i,a,c,o,f;\n  for(i=0;i<D.length;i++){\n   c=D[i]; o=ORIG[i]; if(!o) continue;\n   f=(m>0 && c.CD && c.CD[g]) ? c.CD[g] : null;\n   c.b1   = f? f.b1   : o.b1;\n   c.b1n  = f? f.b1n  : o.b1n;\n   c.sisBar = f? f.bar : o.bar;\n   c.TEC  = f? f.TEC  : o.TEC;\n   c.TECB = f? f.TECB : o.TECB;\n   c.HAB  = f? f.HAB  : o.HAB;\n   c.adds = f? f.HAB  : o.adds;\n   c.sobra= f? f.sobra: o.sobra;\n   delete c._n;\n   var vv = f? f.v : o.v;\n   if(c.arows && vv){\n    for(a=0;a<c.arows.length;a++){\n     if(vv[a]===undefined) continue;\n     c.arows[a][3]=vv[a];\n     c.arows[a][4]=Math.round((vv[a]-c.arows[a][2])*100)/100;\n    }\n   }\n  }\n }\n function pinta(){\n  var b=document.getElementById(\"condbt\");\n  if(b && typeof CTXT!==\"undefined\"){\n   b.textContent=CTXT[CMODE];\n   b.style.background=CMODE?\"#f0a531\":\"#1a1206\";\n   b.style.color=CMODE?\"#0e1116\":\"#f0a531\";\n  }\n }\n window.toggleCond=function(){\n  CMODE=(CMODE+1)%3;\n  aplica(CMODE);\n  try{ traducaoViva(); }catch(e){}\n  pinta();\n  try{ render(); }catch(e){}\n };\n window.condQuantas=function(){\n  var n=0; for(var i=0;i<D.length;i++){ if(D[i].CD && D[i].CD[\"2\"]) n++; }\n  return n;\n };\n})();\n</script>\n"
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    return html[:k] + sc + html[k:], 1


def patch_boxes_home(html, dias=21):
    """A HOME so com as boxes ATIVAS + aba 'boxes anteriores'.

    ATIVA = lancada nos ultimos `dias`. A data vem do box_por_card.json
    (COLETAR-BOX.bat) cruzado com a box de cada card na fila_v6.
    Nao mexe no homeRender da casca: so esconde/mostra os blocos .hbox.
    """
    import datetime
    try:
        BP = json.load(open('box_por_card.json', encoding='utf-8'))
        F = json.load(open('fila_v6.json', encoding='utf-8'))
    except Exception as e:
        return html, 'sem box_por_card/fila (' + str(e) + ')'
    dtb = {}
    for r in F:
        b = str(r.get('card_id') or '').split('@')[0]
        nome = r.get('box')
        d = (BP.get(b) or {}).get('dt')
        if nome and d:
            if nome not in dtb or d < dtb[nome]:
                dtb[nome] = d
    if not dtb:
        return html, 'nenhuma box com data'
    # ===== QUEM ESTA ATIVA =====================================================
    # A API do efootballdb so tem `release_date` — nao existe data de encerramento
    # em lugar nenhum (conferido em 10/08 nos 7,9 MB do SONDA 4).
    # Mas o efscout guarda a HOME DO JOGO em `konamiSections`: a lista de
    # campanhas que estao no ar NAQUELE momento. Box que saiu da home, acabou.
    # Entao a verdade sobre "ativa" e o efscout_campanhas.json, atualizado pelo
    # COLETAR-EFSCOUT.bat. O corte por data fica so de reserva.
    ativas, fonte = [], 'data'
    _norm = lambda t: ' '.join(str(t).lower().split())
    # 1a) A HOME DO efHUB e a verdade mais nova. O efscout_campanhas so e
    #     atualizado quando o Luis roda o COLETAR-EFSCOUT, e em 10/08 ele estava
    #     de 06/08 — sem a "Encored AC Milan", que ja estava no ar.
    try:
        _e = json.load(open('campanhas_efhub.json', encoding='utf-8'))
        _ord = _e.get('ordem') or []
        if _ord:
            _viva = {_norm(x) for x in _ord}
            ativas = [n for n in dtb if _norm(n) in _viva]
            # campanha do efHub que a nossa base ainda nao conhece entra assim mesmo
            for n in _ord:
                if _norm(n) not in {_norm(x) for x in ativas}:
                    ativas.append(n)
                    dtb.setdefault(n, _e.get('quando') or '')
            ativas = sorted(set(ativas), key=lambda x: _ord.index(x) if x in _ord else 999)
            if ativas:
                fonte = 'efhub-home ' + str(_e.get('quando') or '')
    except Exception:
        pass
    try:
        if ativas:
            raise StopIteration
        _c = json.load(open('efscout_campanhas.json', encoding='utf-8'))
        _camp = list((_c.get('campanhas') or {}).keys())
        if _camp:
            _viva = {_norm(x) for x in _camp}
            ativas = sorted(n for n in dtb if _norm(n) in _viva)
            if ativas:
                fonte = 'efscout ' + str(_c.get('dataVersion') or '')
    except (StopIteration, Exception):
        pass
    if not ativas:
        corte = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
        ativas = sorted(n for n, d in dtb.items() if d >= corte)
    if not ativas:
        mais = max(dtb.values())
        ativas = sorted(n for n, d in dtb.items() if d == mais)
    try:
        _H = json.load(open('campanhas_historico.json', encoding='utf-8'))
    except Exception:
        _H = {}
    sc = ('\n<script>\nconst BOXDT=' + json.dumps(dtb, ensure_ascii=False)
          + ';\nconst BOXATIVA=' + json.dumps(ativas, ensure_ascii=False)
          + ';\nconst BOXHIST=' + json.dumps(_H, ensure_ascii=False) + ';\n'
          + "(function(){\n var ATIVA=new Set(BOXATIVA), ORDEM={}, modo=0;\n for(var i=0;i<BOXATIVA.length;i++) ORDEM[BOXATIVA[i]]=i;\n function nome(el){var n=el.querySelector(\".hboxn\");return n?n.textContent.trim():\"\";}\n function dt(n){ var H=(typeof BOXHIST!==\"undefined\")?BOXHIST:{};\n   return (H[n]&&H[n].visto)||(typeof BOXDT!==\"undefined\"&&BOXDT[n])||\"\"; }\n function pinta(){\n  var b=document.getElementById(\"boxbt\");\n  if(!b) return;\n  b.textContent = modo ? \"← voltar às ativas\" : \"▦ boxes anteriores\";\n  b.style.borderColor = modo ? \"#f0a531\" : \"\";\n  b.style.color = modo ? \"#f0a531\" : \"\";\n }\n function aplica(){\n  window._t6box=!!modo;\n  var w=document.getElementById(\"homewrap\"); if(!w) return;\n  var sec=w.querySelector(\".hbloco\"); if(!sec) return;\n  var bx=Array.prototype.slice.call(sec.getElementsByClassName(\"hbox\"));\n  if(!bx.length) return;\n  var mostra=[], n=0;\n  for(var i=0;i<bx.length;i++){\n   var nm=nome(bx[i]), a=ATIVA.has(nm);\n   var ver=(modo===0)?a:!a;\n   var _d=ver?\"\":\"none\";\n   if(bx[i].style.display!==_d) bx[i].style.display=_d;\n   if(ver){ mostra.push([bx[i],nm]); n++; }\n  }\n  // ordem: ativas na ordem do efHub · anteriores da mais nova para a mais velha\n  mostra.sort(function(x,y){\n   if(modo===0) return (ORDEM[x[1]]===undefined?999:ORDEM[x[1]])-(ORDEM[y[1]]===undefined?999:ORDEM[y[1]]);\n   return (dt(y[1])||\"\").localeCompare(dt(x[1])||\"\");\n  });\n  var pai=mostra.length?mostra[0][0].parentNode:null;\n  var _ord=mostra.map(function(x){return x[1];}).join(\"|\");\n  if(pai && _ord!==window._t6ordBox){ window._t6ordBox=_ord;\n   for(var k=0;k<mostra.length;k++) pai.appendChild(mostra[k][0]); }\n  var sb=sec.querySelector(\".hsub\");\n  var _tx = modo\n   ? (n+\" box\"+(n===1?\"\":\"es\")+\" encerrada\"+(n===1?\"\":\"s\")+\" · top 3 de cada uma\")\n   : (n+\" box\"+(n===1?\"\":\"es\")+\" ativa\"+(n===1?\"\":\"s\")+\" · top 3 de cada uma\");\n  if(sb && sb.textContent!==_tx) sb.textContent=_tx;\n  var h2=sec.querySelector(\".htt h2\");\n  var _h2 = modo ? \"Boxes anteriores\" : \"Lançamentos\";\n  if(h2 && !window._t6abaBox && h2.textContent!==_h2) h2.textContent=_h2;\n  pinta();\n }\n function poe(){\n  if(document.getElementById(\"boxbt\")) return;\n  var alvo=document.getElementById(\"fbt\"); if(!alvo) return setTimeout(poe,250);\n  var b=document.createElement(\"button\"); b.id=\"boxbt\"; b.className=alvo.className;\n  b.style.cssText=\"display:inline-block;margin-left:8px\";\n  b.title=\"alterna entre as campanhas no ar e as ja encerradas\";\n  b.onclick=function(){ modo=modo?0:1; aplica();\n   var w=document.getElementById(\"homewrap\");\n   if(w) w.scrollIntoView({behavior:\"smooth\",block:\"start\"}); };\n  var ref=document.getElementById(\"condflut\")||alvo;\n  ref.parentNode.insertBefore(b, ref.nextSibling);\n  pinta();\n }\n setInterval(function(){ if(!document.getElementById(\"boxbt\")) poe(); },900);\n setInterval(aplica,1200);\n poe(); setTimeout(aplica,300);\n window.boxModo=function(m){ modo=m?1:0; window._t6box=!!modo; aplica(); };\n})();\n" + '</script>\n')
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    return html[:k] + sc + html[k:], ('OK (' + str(len(ativas)) + ' ativas de '
            + str(len(dtb)) + ', fonte: ' + fonte + ')')


def patch_contador(html, res):
    """Contador na barra de cima: LINHAS otimizadas e CARDS completos.

    Regra do Luis (10/08): "um card tem cinco linhas; se as cinco foram
    otimizadas ele conta um". Entao card so entra no contador quando TODAS
    as funcoes dele que estao na fila ja foram calculadas.
    """
    try:
        F = json.load(open('fila_v6.json', encoding='utf-8'))
    except Exception as e:
        return html, 'sem fila (' + str(e) + ')'
    # 16/08 — O CONTADOR PASSAVA DE 100%% (o cabecalho mostrou 12.365 de 11.889).
    # Medido: o numerador era `len(res)`, e o `res` nao e a fila. Ele traz
    #   a) as linhas de RESERVA tiradas dos backups `linhas.jsonl.ANTES-*`
    #      (marcadas `_velha`) — sao linhas que o motor esta REFAZENDO agora e
    #      que a tela mostra para nao ficar vazia. Estavam contando como feitas;
    #   b) linhas que sairam da fila e continuam no linhas.jsonl (medido em
    #      16/08 as 01h20: 31 chaves fora da fila);
    #   c) qualquer chave repetida, se houver.
    # Agora os dois lados contam O MESMO UNIVERSO: a fila. Isto e so o rotulo
    # do cabecalho — nao muda o `res`, nao muda a tela, nao muda o motor.
    esperado = {}
    fila = set()
    for r in F:
        b = str(r.get('card_id') or '').split('@')[0]
        if b:
            esperado[b] = esperado.get(b, 0) + 1
        fila.add((str(r.get('card_id') or ''), r.get('funcao')))
    feito, vistas = {}, set()
    for x in res:
        if x.get('_velha'):
            continue
        k = (str(x.get('card_id') or ''), x.get('funcao'))
        if k not in fila or k in vistas:
            continue
        vistas.add(k)
        b = k[0].split('@')[0]
        if b:
            feito[b] = feito.get(b, 0) + 1
    completos = sum(1 for b, n in esperado.items() if feito.get(b, 0) >= n)
    C = {'linhas': len(vistas), 'linhas_total': len(F),
         'cards': completos, 'cards_total': len(esperado)}
    sc = ('\n<script>\nconst CONT=' + json.dumps(C, ensure_ascii=False) + ';\n'
          + "(function(){\n function poe(){\n  if(document.getElementById(\"contbar\")) return;\n  var h=document.querySelector(\"header h1\"); if(!h) return setTimeout(poe,300);\n  var s=document.createElement(\"span\"); s.id=\"contbar\";\n  s.style.cssText=\"margin-left:14px;font-size:11.5px;font-weight:600;color:#8fa4c4;\"+\n   \"vertical-align:middle;letter-spacing:.2px;white-space:nowrap\";\n  var pl=CONT.linhas_total?Math.round(CONT.linhas*100/CONT.linhas_total):0;\n  var pc=CONT.cards_total?Math.round(CONT.cards*100/CONT.cards_total):0;\n  s.innerHTML='<span style=\"color:#22c58b\">'+CONT.linhas.toLocaleString(\"pt-BR\")+'</span>'+\n   ' de '+CONT.linhas_total.toLocaleString(\"pt-BR\")+' linhas ('+pl+'%)'+\n   ' &nbsp;·&nbsp; <span style=\"color:#22c58b\">'+CONT.cards.toLocaleString(\"pt-BR\")+'</span>'+\n   ' de '+CONT.cards_total.toLocaleString(\"pt-BR\")+' cards completos ('+pc+'%)';\n  s.title=\"card completo = todas as funcoes dele ja otimizadas\";\n  h.appendChild(s);\n }\n setInterval(function(){ if(!document.getElementById(\"contbar\")) poe(); },900);\n poe();\n})();\n" + '</script>\n')
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    return html[:k] + sc + html[k:], (str(C['linhas']) + '/' + str(C['linhas_total'])
                                      + ' linhas · ' + str(C['cards']) + '/'
                                      + str(C['cards_total']) + ' cards')


def patch_vaga_no_lugar(html):
    """O BLOCO DO IMPETO, do jeito que o Luis desenhou (10/08):

        IMPETO
          nativo
            Fantasia +2
          adicionado
            Criador de Jogadas +1

    Antes: o "SEM VAGA DE IMPETO" ficava perdido na linha de altura/peso/idade,
    e a tela NAO dizia o que o motor tinha posto na vaga livre — mostrava que a
    vaga existia e escondia o que entrou nela.
    """
    ok = 0
    velho = ("${c.slot===0?' \u00b7 <b style=\"color:#e46a6a\">SEM VAGA DE \u00cdMPETO</b>'"
             ":(c.slot===-1?' \u00b7 <span style=\"color:#c9a227\">vaga indefinida</span>':'')}")
    if velho in html:
        html = html.replace(velho, '', 1)
        ok += 1

    alvo = ("<div class=hbgrp><b>\u00cdmpeto nativo</b><ul class=hblist>"
            "${(function(){const f=(c.nmn&&c.nmn.length)?c.nmn:(c.imps||[])"
            ".filter(x=>x&&x.f).map(x=>x.n).filter(Boolean);"
            "return f.length?f.map(n=>`<li>${n}</li>`).join(''):'<li>n\u00e3o tem</li>';})()}"
            "</ul></div>`")
    novo = ("<div class=hbgrp><b>\u00cdmpeto</b>"
            "<div class=iasub>nativo</div><ul class=hblist>"
            "${(function(){const f=(c.nmn&&c.nmn.length)?c.nmn:(c.imps||[])"
            ".filter(x=>x&&x.f).map(x=>x.n).filter(Boolean);"
            "return f.length?f.map(n=>`<li>${n}</li>`).join(''):'<li>n\u00e3o tem</li>';})()}"
            "</ul>"
            "<div class=iasub>adicionado</div><ul class=hblist>"
            "${(function(){var _p=String(c.imp||'').split('o motor pos:');"
            "if(_p.length>1) return `<li>${_p[1].trim()}</li>`;"
            "if(c.slot===0) return '<li style=\"color:#8fa4c4\">n\u00e3o tem vaga</li>';"
            "if(c.slot) return '<li style=\"color:#8fa4c4\">vaga livre</li>';"
            "return '<li style=\"color:#8fa4c4\">vaga ainda n\u00e3o conferida</li>';})()}"
            "</ul></div>`")
    if alvo in html:
        html = html.replace(alvo, novo, 1)
        ok += 1

    css = ("\n<style>\n"
           ".iasub{font-size:10px;text-transform:uppercase;letter-spacing:.5px;"
           "color:#8fa4c4;margin:5px 0 1px}\n"
           "html[data-tema] .iasub{color:var(--txt2)!important}\n"
           "</style>\n")
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + html[k:]
    return html, ok



def guarda_historico_de_campanhas():
    """A ABA DE CAMPANHAS GUARDA TUDO QUE JA PASSOU.

    Pedido do Luis, aberto desde 10/08: "a aba de campanhas que a gente vai
    guardar todas as campanhas que foram feitas". A home do efHub e do efscout
    so mostram o que esta NO AR — quando a campanha sai, some da fonte.
    Entao a cada geracao a gente FUNDE o que esta no ar com o que ja foi visto,
    e nunca apaga. O arquivo cresce e vira a memoria das campanhas.

    campanhas_historico.json = { nome: {"visto": "AAAA-MM-DD", "ids": [...] } }
    """
    ARQ = 'campanhas_historico.json'
    H = {}
    if os.path.exists(ARQ):
        try:
            H = json.load(open(ARQ, encoding='utf-8')) or {}
        except Exception:
            H = {}
    hoje = __import__('datetime').date.today().isoformat()
    novos = 0

    def poe(nome, ids, quando):
        nonlocal novos
        if not nome:
            return
        r = H.get(nome)
        if r is None:
            H[nome] = {'visto': quando, 'ids': sorted({str(i) for i in (ids or [])})}
            novos += 1
        else:
            j = set(r.get('ids') or []) | {str(i) for i in (ids or [])}
            r['ids'] = sorted(j)
            if quando and quando > (r.get('visto') or ''):
                r['visto'] = quando

    try:
        e = json.load(open('campanhas_efhub.json', encoding='utf-8'))
        q = e.get('quando') or hoje
        for n in (e.get('ordem') or []):
            poe(n, (e.get('campanhas') or {}).get(n), q)
    except Exception:
        pass
    try:
        c = json.load(open('efscout_campanhas.json', encoding='utf-8'))
        for n, ids in (c.get('campanhas') or {}).items():
            poe(n, ids, hoje)
    except Exception:
        pass
    # ------------------------------------------------------------------
    # ⛔ AQUI NASCIA A BOX FALSA. ORDEM DO LUIS, 18/08:
    #    "Big Time e o TIPO da carta, um card lancado para comemorar uma
    #     partida — por isso vem com a data. BOX e onde voce roda as moedas."
    #
    #    O que este bloco fazia: pegava o campo `box` da fila_v6 e do
    #    box_por_card e CRIAVA uma campanha com esse nome. So que esses dois
    #    arquivos carregam a ETIQUETA DA CARTA, nao o nome da box. Resultado
    #    medido em 18/08 no campanhas_historico.json: 1.198 nomes, 600 deles
    #    com UMA carta so — "Big Time Argentina 15 Jul '26" (Messi) e
    #    "Big Time Portugal 23 Jun '26" (Cristiano) viraram duas prateleiras
    #    de um card, quando os dois estao dentro da mesma box de verdade,
    #    Living Legends 2026, que o efHub lista com 17 cartas.
    #
    #    ⛔ A REGRA, DAQUI PARA A FRENTE: SO QUEM VIU O efHub CRIA CAMPANHA.
    #       campanhas_efhub.json, efscout_campanhas.json e NOMES-DE-BOX.json
    #       (a memoria que o vigia acumula da lista de box do efHub) podem
    #       criar nome novo. A fila_v6 e o box_por_card so podem ACRESCENTAR
    #       CARTAS a um nome que ja existe — nunca inventar um.
    #
    #    ⛔ O QUE NAO ENTRA NAO SE PERDE: vai para
    #       ETIQUETAS-QUE-NAO-SAO-BOX.json, que e informacao boa (diz o tipo
    #       da carta e a partida que ela comemora), so nao e box.
    # ------------------------------------------------------------------
    de_verdade, dono_de_verdade = set(), {}
    try:
        for _r in REGRA.le_nomes_de_box().values():
            if _r.get('nome'):
                poe(_r['nome'], _r.get('cartas'), _r.get('visto') or hoje)
                de_verdade.add(_r['nome'])
                for _c in (_r.get('cartas') or []):
                    dono_de_verdade.setdefault(str(_c), set()).add(_r['nome'])
    except Exception:
        pass

    etiquetas = {}

    def so_acrescenta(nome, ids):
        """Nao cria campanha. Se o nome ja existe, junta as cartas nele."""
        if not nome:
            return
        if nome in H:
            r = H[nome]
            r['ids'] = sorted(set(r.get('ids') or []) | {str(i) for i in (ids or [])})
        else:
            etiquetas.setdefault(nome, set()).update(str(i) for i in (ids or []))

    try:
        porbox = {}
        for r in json.load(open('fila_v6.json', encoding='utf-8')):
            n = r.get('box')
            if n:
                porbox.setdefault(n, []).append(str(r.get('card_id') or '').split('@')[0])
        for n, ids in porbox.items():
            so_acrescenta(n, ids)
    except Exception:
        pass

    # o box_por_card.json e a memoria mais longa: nome da box + data de
    # lancamento de cada carta, incluindo campanhas que ja fecharam ha meses.
    try:
        BP = json.load(open('box_por_card.json', encoding='utf-8'))
        porbox, quando = {}, {}
        for b, r in BP.items():
            n = r.get('box')
            if not n:
                continue
            porbox.setdefault(n, []).append(str(b))
            d = r.get('dt')
            if d and (n not in quando or d < quando[n]):
                quando[n] = d
        for n, ids in porbox.items():
            so_acrescenta(n, ids)
    except Exception:
        pass

    # ⛔ E A LIMPEZA DO QUE JA ENTROU ERRADO — mas so o que da para PROVAR.
    #    Um nome sai do historico quando as duas coisas valem ao mesmo tempo:
    #      1. o efHub nunca chamou aquilo de box; e
    #      2. TODAS as cartas dele ja estao dentro de uma box de verdade.
    #    Nao provou, fica. Nao se apaga nome por parecer errado.
    if dono_de_verdade:
        tirados = {}
        for n in list(H):
            if n in de_verdade:
                continue
            ids = H[n].get('ids') or []
            if not ids:
                continue
            if all(dono_de_verdade.get(str(i)) for i in ids):
                tirados[n] = {'cartas': sorted(str(i) for i in ids),
                              'a_box_de_verdade': sorted(
                                  {x for i in ids for x in dono_de_verdade[str(i)]})}
                del H[n]
        if tirados:
            for n, r in tirados.items():
                etiquetas.setdefault(n, set()).update(r['cartas'])
            try:
                json.dump({'o_que_e': ('nomes que estavam no historico como campanha, o efHub nunca '
                                       'chamou de box, e todas as cartas deles ja estao dentro de '
                                       'uma box de verdade. Sairam do historico.'),
                           'quando': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
                           'quantas': len(tirados), 'itens': tirados},
                          open('BOX-FALSA-QUE-SAIU.json', 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=1)
            except Exception:
                pass

    # ⛔ E O QUE DA PARA PROVAR SAI SEM PRECISAR DE DONO. (18/08, tarde)
    #    A limpeza de cima so tira nome cujas cartas ja estao TODAS dentro de
    #    uma box de verdade — e as cartas velhas ("Big Time 13 Jul '94") nao
    #    estao em box nenhuma que o efHub ainda liste, entao elas ficavam.
    #    A regra prova sem precisar de dono: lixo, tipo de card e data anterior
    #    ao proprio jogo. Nada se perde: vai para o ETIQUETAS-QUE-NAO-SAO-BOX.
    provadas = {}
    try:
        _conh = REGRA.le_nomes_de_box()
    except Exception:
        _conh = {}
    for _n in list(H):
        try:
            if REGRA.e_etiqueta_provada(_n, _conh):
                provadas[_n] = sorted(str(i) for i in (H[_n].get('ids') or []))
                del H[_n]
        except Exception:
            pass
    if provadas:
        for _n, _ids in provadas.items():
            etiquetas.setdefault(_n, set()).update(_ids)
        print('historico · nomes provados etiqueta e retirados: %d' % len(provadas))

    if etiquetas:
        try:
            json.dump({'o_que_e': ('nomes que estavam no campo `box` de alguma carta mas que o '
                                   'efHub nunca chamou de box. Sao ETIQUETAS DE CARTA (o tipo do '
                                   'card e a partida que ele comemora). Nao criam campanha.'),
                       'quando': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
                       'quantas': len(etiquetas),
                       'itens': {k: sorted(v) for k, v in sorted(etiquetas.items())}},
                      open('ETIQUETAS-QUE-NAO-SAO-BOX.json', 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
        except Exception:
            pass

    try:
        json.dump(H, open(ARQ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    except Exception as ex:
        return 'nao gravei (%s)' % ex
    return '%d campanhas guardadas (%d novas)' % (len(H), novos)


def patch_limpa_tarjas(html):
    """LIMPEZA DA TELA — ordem do Luis, 10/08.

    1) MAX passa a ser o MAX da Konami (o numero do efHub), nao o OVR base.
       A etiqueta mostrava `sisOvr`, que e o OVR base — em 2.154 de 2.156 cards
       o rotulo dizia MAX e o numero era o base. O valor certo (`maxOvr`) ja
       estava no registro, sem uso.

    2) Morrem as cores que so confundem:
         borda dourada  = card na lista de METAS   -> serviu na epoca do molde
         faixa verde    = nativo                   -> nao aparecia
         roxo / azul    = tier S+ / S              -> "nessa altura ja foi"
       Fica UMA marca so, a unica que ele usa hoje: dentro da funcao, separar
       quem e DA FUNCAO de quem chegou MIGRADO (faixa ambar na lateral).

    3) As caixinhas meta / nativo / S+ / S saem do filtro — sem cor, nao servem.
    """
    ok = 0

    # a etiqueta aparece em duas formas na casca: template string e concatenacao
    for velho, novo in (
        ("${c.temMax?'MÁX '+c.sisOvr.toFixed(1):'OVR '+c.ovr}",
         "${(c.maxOvr&&c.maxOvr>c.ovr)?'MÁX '+Number(c.maxOvr).toFixed(1)"
         ":'OVR '+c.ovr}"),
        ("(c.temMax?'MÁX '+c.sisOvr.toFixed(1):'OVR '+c.ovr)",
         "((c.maxOvr&&c.maxOvr>c.ovr)?'MÁX '+Number(c.maxOvr).toFixed(1)"
         ":'OVR '+c.ovr)"),
    ):
        if velho in html:
            html = html.replace(velho, novo)
            ok += 1

    vc = ("const cls=c=>(mk&&isM(c)?' meta':'')+(HN&&!c.sec?' nat':'')"
          "+(HP&&c.tier==='S+'?' sp':'')+(HS&&c.tier==='S'?' ss':'');")
    nc = "const cls=c=>(c.MIG?' mig':'');"
    if vc in html:
        html = html.replace(vc, nc, 1)
        ok += 1

    css = ("\n<style>\n"
           "/* 10/08 — so uma marca: quem chegou MIGRADO leva faixa ambar. */\n"
           ".cd.mig{box-shadow:inset 3px 0 0 #f0a531!important}\n"
           ".cd.meta,.cd.nat,.cd.sp,.cd.ss{border-color:var(--line,#1f2733)!important;"
           "background:var(--surf,#121822)!important;box-shadow:none!important}\n"
           "#cmk,#cnat,#csp,#cs,#css{display:none!important}\n"
           "</style>\n")
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + html[k:]
    ok += 1
    return html, ok


# ------------------------------------------------------------ PE RUIM (11/08/2026)
# FECHADO PELO LUIS em 11/08/2026.
#
#   bonus = f x q          teto 1,00 ponto        IGUAL para as 18 funcoes
#   f (frequencia) = [0 , 0.35 , 0.70 , 1.00]
#   q (precisao)   = [0 , 0.40 , 0.75 , 1.00]
#
# Por que MULTIPLICA e nao soma: precisao nao vale nada se o card nunca usa o pe
# ruim, e frequencia nao vale nada se ele erra. O bonus mede jogada BOA de pe ruim.
#
# Por que NAO tem regra separada por funcao (ordem do Luis, 11/08):
#   "ninguem tem os dois pes... quem usa os dois e superior. E a realidade."
#   O goleiro tira 0,09 e o artilheiro 0,51 porque a Konami nao distribui pe ruim
#   pra goleiro — e isso e caracteristica real do card, nao defeito da regua.
#
# ESCALA 0-3 nos DOIS campos. PROVADA, nao suposta:
#   Rui Costa 88039045077725 -> no jogo "Raramente / Alta" -> no efHub 1 / 2
#   e nos 2.649 cards coletados nenhum passou de 3.
#   frequencia: 0 Quase nunca · 1 Raramente · 2 Ocasionalmente · 3 Regularmente
#   precisao  : 0 Baixa · 1 Media · 2 Alta · 3 Muito alta
#
# ACHADO: so existem 13 das 16 combinacoes. Nunca aparece frequencia alta com
# precisao baixa (2/0, 3/0, 3/1). Por isso o bonus nao precisa de punicao.
#
# FONTE: pe_ruim.json, campos weakFootUsage e weakFootAccuracy do efHub,
# coletados pelo Chrome (a API da 403 fora do navegador).
PE_RUIM_ARQ = 'pe_ruim.json'


def patch_pe_ruim(html):
    """Injeta a tabela de pe ruim e soma o bonus na nota(c)."""
    if 'PE RUIM - 11/08/2026' in html:
        return html, 'ja estava'
    if not os.path.exists(PE_RUIM_ARQ):
        return html, 'FALTA ' + PE_RUIM_ARQ
    try:
        PR = json.load(open(PE_RUIM_ARQ, encoding='utf-8')).get('dados') or {}
    except Exception as e:
        return html, 'nao li o %s: %s' % (PE_RUIM_ARQ, e)
    if not PR:
        return html, '%s vazio' % PE_RUIM_ARQ

    raw = ' '.join('%s:%x' % (k, v[0] * 4 + v[1]) for k, v in PR.items())

    bloco = (
        '  /* ===== PE RUIM - 11/08/2026 - injetado pelo gera_encaixe.py ===== */\n'
        '  /* 11/08 FECHADO PELO LUIS: bonus = f x q, teto 1,00, igual pra toda funcao. */\n'
        '  const PR_RAW="' + raw + '";\n'
        '  let PR_MAX = 1.0;\n'
        '  const PR_F=[0,0.35,0.70,1.00], PR_Q=[0,0.40,0.75,1.00];\n'
        '  const PR_ROT_F=["Quase nunca","Raramente","Ocasionalmente","Regularmente"];\n'
        '  const PR_ROT_Q=["Baixa","M\u00e9dia","Alta","Muito alta"];\n'
        '  const PR_TAB=(()=>{const R={};\n'
        '   for(const p of PR_RAW.split(" ")){const a=p.split(":");if(a.length!==2)continue;\n'
        '    const v=parseInt(a[1],16);R[a[0]]=[v>>2,v&3];}\n'
        '   return R;})();\n'
        '  function prPar(c){return PR_TAB[String(c.id).split("@")[0]]||null;}\n'
        '  function prBonus(c){const v=prPar(c); if(!v)return 0;\n'
        '   return PR_F[v[0]]*PR_Q[v[1]]*PR_MAX;}\n'
        '  (function(){let n=0,s=0;\n'
        '   for(const c of D){if(c.id==="MOLDE")continue; if(prPar(c)){n++;s+=prBonus(c);}}\n'
        '   const sem=D.filter(c=>c.id!=="MOLDE"&&!prPar(c)).length;\n'
        '   console.log("%cPE RUIM - "+n+" linhas com dado - "+sem+" sem dado - media +"\n'
        '    +(n?(s/n).toFixed(3):0)+" - PR_MAX="+PR_MAX,\n'
        '    "color:"+(sem?"#f0a531":"#22c58b")+";font-weight:700");})();\n'
        '  /* ===== FIM DO PE RUIM ===== */\n'
    )

    ok = 0
    # 1) o bloco entra logo antes da nota()
    alvo = 'function nota(c){const b=notaBase(c);'
    if alvo in html:
        html = html.replace(alvo, bloco + '  ' + alvo, 1); ok += 1
    # 2) calcula o _pr junto com o _ia
    v = ' if(c._ia===undefined)c._ia=iaBonus(c);'
    if v in html:
        html = html.replace(v, v + '\n if(c._pr===undefined)c._pr=prBonus(c);', 1); ok += 1
    # 3) soma na nota
    v = 'return piso(b+c._fb+c._ia-p,c.tipo);}'
    if v in html:
        html = html.replace(v, 'return piso(b+c._fb+c._ia+c._pr-p,c.tipo);}', 1); ok += 1
    # 4) o botao ACHATAR (ACH_BONUS) tem que desligar o pe ruim junto
    v = 'const _fis=fisBonus,_ia=iaBonus;'
    if v in html:
        html = html.replace(v, 'const _fis=fisBonus,_ia=iaBonus,_pr=prBonus;\n'
                               'prBonus=function(c){return ACH_BONUS?_pr(c):0;};', 1); ok += 1
    v = 'c._fb=undefined;c._ia=undefined;c._cp=undefined;'
    if v in html:
        html = html.replace(v, 'c._fb=undefined;c._ia=undefined;c._pr=undefined;c._cp=undefined;', 1); ok += 1
    # 5) a linha na ficha do card, logo depois do bloco do estilo da IA
    v = ":'este card n\u00e3o tem estilo de jogo da IA'}</div></div></div>"
    ficha = ("</div>"
             "<div class=sec style=margin-bottom:0><h3>P\u00e9 ruim</h3>"
             "<div class=mini>${prPar(c)?`frequ\u00eancia <b style=color:#8fb8ff>"
             "${PR_ROT_F[prPar(c)[0]]}</b> \u00b7 precis\u00e3o <b style=color:#8fb8ff>"
             "${PR_ROT_Q[prPar(c)[1]]}</b> \u00b7 b\u00f4nus <b style=color:#4f8cff>+"
             "${prBonus(c).toFixed(2)}</b> na nota`:'sem dado de p\u00e9 ruim'}</div>"
             "</div></div>")
    if v in html:
        html = html.replace(v, ":'este card n\u00e3o tem estilo de jogo da IA'}</div>" + ficha, 1); ok += 1

    return html, '%d de 6 (%d cards na tabela)' % (ok, len(PR))


# --------------------------------------------------- LAYOUT DO MEU TIME (11/08/2026)
# ORDEM DO LUIS, 11/08:
#   "o tecnico vai pra coluna da esquerda e embaixo do tecnico vem as reservas,
#    um em cada linha. E no meio, do lado direito, o campo. Embaixo disso tudo,
#    os fora do banco."
#   "esse numero ai... tem que estar a NOTA dele, do card. Voce tem que trazer
#    a carta JA OTIMIZADA. O 0/60 pts nao e importante, e pra sair."
#
# O QUE MUDA
#   1. a coluna da DIREITA acaba. O tecnico sobe para a esquerda, em cima do banco.
#   2. o elenco fora do banco sai da coluna e vai para BAIXO de tudo, em grade.
#   3. no card do jogador: sai o "0/60 pts", e o numero passa a ser a nota da
#      CARTA OTIMIZADA (mtRef(k).ideal = a build que o motor achou), no lugar da
#      nota da build crua do usuario — que dava numero negativo feio (-729 no
#      Rooney) so porque ele nunca distribuiu as barras daquele card.
#
# O clique no card JA abre o modal com as barrinhas (onclick="abrir(k)"). Nao
# precisou mexer — so nao pode perder isso ao mover o bloco de lugar.
MT_FILTRO_JS = """
<script>
/* FILTROS DO FORA DO BANCO - 11/08/2026 - injetado pelo gera_encaixe.py
   Ordem do Luis: "no fora do banco voce tem que colocar alguns filtros e
   classificadores, porque la fica muito dificil de organizar" (99 jogadores). */
window.MTF={q:"",ord:"nota",setor:""};
/* 11/08 - A MAIOR NOTA DO CARD. Ordem do Luis: "eu quero que pegue a maior nota
   do card. A maior nota que o card tiver e a que vai aparecer."
   Antes eu mostrava a nota da FUNCAO em que o card estava naquele lugar — que e
   menor quando ele nao esta na melhor funcao dele. Agora varre todas as linhas
   daquele card (mesmo id base) e pega a maior.
   O indice e refeito a cada mtRender, senao fica velho quando o usuario liga o
   ACHATAR ou troca o tecnico. A nota() ja tem cache proprio em c._n, entao a
   varredura so custa caro na primeira vez. */
window._MTMAX=null;
window.mtMaiorNota=function(c){
 if(!c) return 0;
 if(!_MTMAX){ _MTMAX={};
  for(var i=0;i<D.length;i++){ var x=D[i]; if(x.id==="MOLDE") continue;
   var b=String(x.id).split("@")[0]; var n;
   try{ n=nota(x); }catch(e){ continue; }
   if(_MTMAX[b]===undefined||n>_MTMAX[b]) _MTMAX[b]=n; } }
 var bb=String(c.id).split("@")[0];
 return (_MTMAX[bb]!==undefined)?_MTMAX[bb]:nota(c);};
/* 11/08 - ARRASTAR FICOU DIFICIL: o elenco foi para baixo do campo e os dois
   nao cabem na mesma tela. Ordem do Luis: "da um jeito de ficar mais facil".
   Duas coisas, sem mexer no drag&drop que ja existe:
   1. a pagina rola SOZINHA enquanto voce arrasta perto da borda de cima ou de baixo
   2. o campo fica grudado no topo, entao ele continua visivel quando voce desce
      ate o elenco (o CSS position:sticky faz isso) */
(function(){
 var ativo=false;
 document.addEventListener("dragstart",function(){ativo=true;},true);
 document.addEventListener("dragend",function(){ativo=false;},true);
 document.addEventListener("drop",function(){ativo=false;},true);
 document.addEventListener("dragover",function(e){
  if(!ativo)return;
  var y=e.clientY,h=window.innerHeight,z=110,d=0;
  if(y<z) d=-Math.ceil((z-y)/3);
  else if(y>h-z) d=Math.ceil((y-(h-z))/3);
  if(d) window.scrollBy(0,d);
 },true);
})();
window.mtForaSetor=function(t){t=String(t||"");
 if(/^(Goleiro|Zagueiro|Lateral)/.test(t))return "DEFESA";
 if(/^(Volante|Meia)/.test(t))return "MEIO";
 return "ATAQUE";};
window.mtForaSet=function(campo,v){MTF[campo]=v;mtRender();
 if(campo==="q"){const el=document.getElementById("mtfq");
  if(el){el.focus();el.setSelectionRange(el.value.length,el.value.length);}}};
window.mtForaLista=function(){
 const L=(MT.elenco||[]).map((k,i)=>({k,i,c:mtCard(k)})).filter(x=>x.c);
 const q=(MTF.q||"").trim().toLowerCase();
 let R=L.filter(x=>{
  if(q && String(x.c.nome||"").toLowerCase().indexOf(q)<0) return false;
  if(MTF.setor && mtForaSetor(x.c.tipo)!==MTF.setor) return false;
  return true;});
 const nt=x=>{try{return nota(x.c);}catch(e){return -9e9;}};
 if(MTF.ord==="nota") R.sort((a,b)=>nt(b)-nt(a));
 else if(MTF.ord==="nome") R.sort((a,b)=>String(a.c.nome).localeCompare(String(b.c.nome)));
 else if(MTF.ord==="funcao") R.sort((a,b)=>String(a.c.tipo).localeCompare(String(b.c.tipo))||nt(b)-nt(a));
 else if(MTF.ord==="ovr") R.sort((a,b)=>(b.c.ovr||0)-(a.c.ovr||0));
 return R;};
window.mtForaBarra=function(n,total){
 const op=(v,t)=>`<option value="${v}"${MTF.ord===v?" selected":""}>${t}</option>`;
 const se=(v,t)=>`<option value="${v}"${MTF.setor===v?" selected":""}>${t}</option>`;
 return `<div class=mtfbar>
  <input id=mtfq class=mtfin placeholder="buscar por nome..." value="${(MTF.q||"").replace(/"/g,'&quot;')}"
   oninput="mtForaSet('q',this.value)">
  <select class=mtfin onchange="mtForaSet('setor',this.value)">
   ${se("","todos os setores")}${se("DEFESA","defesa")}${se("MEIO","meio")}${se("ATAQUE","ataque")}</select>
  <select class=mtfin onchange="mtForaSet('ord',this.value)">
   ${op("nota","maior nota")}${op("ovr","maior OVR")}${op("nome","nome A-Z")}${op("funcao","função")}</select>
  ${(MTF.q||MTF.setor)?`<button class=btn onclick="MTF.q='';MTF.setor='';mtRender()">limpar filtro</button>
    <span class=mini>${n} de ${total}</span>`:`<span class=mini>${total} jogadores</span>`}
 </div>`;};
</script>
"""

MT_CSS = """
<style>
/* LAYOUT DO MEU TIME - 11/08/2026 - injetado pelo gera_encaixe.py
   #mtwrap na frente para ganhar dos !important das media queries da casca */
#mtwrap .mtgrid{grid-template-columns:320px minmax(0,1fr)!important}
#mtwrap .mtfora{background:var(--surf2,#131a24);border:1px solid var(--line,#1e2632);
 border-radius:10px;padding:10px 12px;margin-top:14px;max-width:none}
#mtwrap .mtforagrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));
 gap:2px 16px;align-items:start}
#mtwrap .mtforagrid .mtbc{padding:6px 0}
#mtwrap #mtesq .mtbanco{max-width:none}
#mtwrap .mtfbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0 10px}
#mtwrap .mtfin{background:var(--surf,#0d131b);color:inherit;border:1px solid var(--line,#1e2632);
 border-radius:7px;padding:5px 9px;font:inherit;font-size:12.5px}
#mtwrap .mtfin:focus{outline:1px solid #4f8cff}
#mtwrap .mtcampo{position:sticky;top:8px;align-self:start}
@media(max-height:820px){#mtwrap .mtcampo{position:static}}
@media(max-width:900px){#mtwrap .mtgrid{grid-template-columns:1fr!important}}

/* CONTRASTE DOS CHIPS "ESTE CARD NAS N FUNCOES" - 11/08/2026
   Ordem do Luis: "essa nota ai, 99.2, esta quase impossivel de ver por causa da
   tonalidade da cor". No tema CLARO o cinza do .ps2 e o verde #22c58b (que vem
   por estilo inline na funcao atual) somem no fundo branco.
   O seletor [style*="22c58b"] pega justamente a funcao atual, que e a unica que
   recebe a cor inline. */
html[data-tema=claro] .posl .ps2{color:#243044!important;background:#eef2f7!important;
 border-color:#b9c6d6!important}
html[data-tema=claro] .posl .ps2 b{color:#0b1220!important;font-weight:800}
html[data-tema=claro] .posl .ps2[style*="22c58b"]{color:#07603a!important;
 border-color:#07603a!important;background:#dff5e9!important}
html[data-tema=claro] .posl .ps2[style*="22c58b"] b{color:#07603a!important}
html[data-tema=claro] .pslb{color:#4a5668!important}
/* no escuro so engrossa o numero, que ja tinha contraste */
html[data-tema=escuro] .posl .ps2 b{color:#e8eef7;font-weight:800}
</style>
"""


def patch_mt_layout(html):
    """Tecnico+banco na esquerda, campo na direita, elenco embaixo em grade."""
    if 'LAYOUT DO MEU TIME - 11/08/2026' in html:
        return html, 'ja estava'
    ok = 0

    if '</head>' in html:
        html = html.replace('</head>', MT_CSS + MT_FILTRO_JS + '</head>', 1); ok += 1

    velho = ('<div class=mtlado id=mtdir>\n   ${mtPainelTec()}\n   '
             '<div class="mtbanco alvoelenco">')
    if velho in html:
        html = html.replace('<div class=mtlado id=mtesq>\n   <div class="mtbanco alvobanco">',
                            '<div class=mtlado id=mtesq>\n   ${mtPainelTec()}\n   '
                            '<div class="mtbanco alvobanco">', 1)
        html = html.replace(velho, '</div>\n <div class="mtfora alvoelenco">', 1)
        html = html.replace('${elenco}</div>\n  </div>\n </div>\n <div id=mtsaida>',
                            '<div class=mtforagrid>${elenco}</div></div>\n <div id=mtsaida>', 1)
        ok += 1

    # 11/08 CORRECAO: eu tinha usado mtRef(k).ideal, que recalcula a carta SEM
    # tecnico (passa bs=[]) e por isso dava 99,6 no Rio Ferdinand quando o
    # ranking mostra 104,54. O certo e a MESMA nota() do ranking. Medido rodando
    # a pagina no navegador, nao deduzido.
    velho_card = ("<div class=mini>${c.tipo} · ${mtGasto(k)}/${c.orc||0} pts</div></div>"
                  "<b style=\"color:${mtPct(k)>=90?'#22c58b':mtPct(k)>=50?'#f0a531':'#8b949e'}\">"
                  "${mtNotaReal(k).toFixed(1)}</b>")
    novo_card = ("<div class=mini>${c.tipo}</div></div>"
                 "<b title=\"nota da carta otimizada (a mesma do ranking)\" "
                 "style=\"color:${cor(nota(c),0)}\">${nota(c).toFixed(1)}</b>")
    n = html.count(velho_card)
    if n:
        html = html.replace(velho_card, novo_card); ok += n

    # 4) o FORA DO BANCO passa a ser filtravel e ordenavel (99 jogadores na grade)
    #    Reescreve a lista inteira: os botoes ++/x usam o indice ORIGINAL em
    #    MT.elenco, entao filtrar sem guardar o indice quebraria os botoes.
    velho_el = (' const elenco=(MT.elenco||[]).map((k,i)=>{const c=mtCard(k);if(!c)return"";')
    if velho_el in html:
        i0 = html.index(velho_el)
        i1 = html.index('\n document.getElementById("mtwrap").innerHTML=`', i0)
        novo_el = (
        ' const _foraL=mtForaLista();\n'
        ' const elenco=_foraL.map(({k,i,c})=>{\n'
        '  return `<div class=mtbc draggable=true data-key="${k}" data-de="elenco" data-i="${i}"'
        ' onclick="abrir(\'${k}\')"><img src="https://efimg.com/efootballhub22/images/player_cards/'
        '${String(c.id).split("@")[0]}_l.png" onerror="this.style.visibility=\'hidden\'">\n'
        '   <div style=flex:1><b>${c.nome}</b><div class=mini>${c.tipo}</div></div>'
        '<b title="nota da carta otimizada (a mesma do ranking)" style="color:${cor(nota(c),0)}">'
        '${nota(c).toFixed(1)}</b>\n'
        '   <button class=bbt title="ajustar barras" onclick="event.stopPropagation();mtAbreCfg(\'${k}\')">⚙</button>\n'
        '   <button class=bbt title="mandar pro banco" onclick="event.stopPropagation();mtProBanco(${i})">\\u2191</button>\n'
        '   <button class=bbt onclick="event.stopPropagation();mtTiraElenco(${i})">\\u00d7</button></div>`}).join("")\n'
        '  ||\'<div class=mini style="padding:6px 0">\'+((MT.elenco||[]).length?\'Nenhum jogador com esse filtro.\''
        ':\'Ninguém fora do banco ainda. <button class=btn style="margin-left:6px" onclick="mtAddElenco()">+ elenco</button>\')+\'</div>\';')
        html = html[:i0] + novo_el + html[i1:]
        ok += 1

    # 5) a barra de filtros entra no cabecalho do bloco de baixo
    velho_hd = ('<div class="mtfora alvoelenco"><div class=bhd><span>Elenco — fora do banco</span>'
                '<span style="display:flex;gap:6px;align-items:center">'
                '<span class=mini>${(MT.elenco||[]).length} jogadores</span>'
                '<button class=btn onclick="mtAddElenco()">+ elenco</button></span></div>')
    novo_hd = ('<div class="mtfora alvoelenco"><div class=bhd><span>Elenco — fora do banco</span>'
               '<span style="display:flex;gap:6px;align-items:center">'
               '<button class=btn onclick="mtAddElenco()">+ elenco</button></span></div>'
               '${mtForaBarra(_foraL.length,(MT.elenco||[]).length)}')
    if velho_hd in html:
        html = html.replace(velho_hd, novo_hd, 1); ok += 1

    # 6) a nota dos que estao NO CAMPO tambem passa a ser a da carta otimizada.
    #    Estava mostrando a build crua do usuario (Ronaldo 67,8 · Neuer 5,6 ·
    #    Romero -4,4) enquanto banco e elenco ja mostravam a otimizada. Ordem do
    #    Luis, 11/08: "os que estao dentro do campo esta dando a nota deles".
    #    A media do cabecalho vai junto, senao o numero de cima nao bate com os
    #    cards. O mtPct / "% do teto" do resumo NAO muda — aquilo mede outra
    #    coisa (o quanto ele ja tirou da propria carta).
    if '<div class=mtnt>${n.toFixed(1)}</div>' in html:
        html = html.replace('<div class=mtnt>${n.toFixed(1)}</div>',
                            '<div class=mtnt>${nota(c).toFixed(1)}</div>', 1); ok += 1
    v_med = 'med=tit.length?tit.reduce((a,x)=>a+mtNota(x.key),0)/tit.length:0;'
    if v_med in html:
        html = html.replace(v_med,
            'med=tit.length?tit.reduce((a,x)=>{const cc=mtCard(x.key);return a+(cc?nota(cc):0);},0)/tit.length:0;', 1)
        ok += 1

    # 7) a nota mostrada passa a ser a MAIOR do card (entre todas as funcoes dele)
    if 'function mtRender(){' in html:
        html = html.replace('function mtRender(){', 'function mtRender(){ _MTMAX=null;', 1); ok += 1
    trocas = [
        ('<div class=mtnt>${nota(c).toFixed(1)}</div>',
         '<div class=mtnt>${mtMaiorNota(c).toFixed(1)}</div>'),
        ('style="color:${cor(nota(c),0)}">${nota(c).toFixed(1)}</b>',
         'style="color:${cor(mtMaiorNota(c),0)}">${mtMaiorNota(c).toFixed(1)}</b>'),
        ('return a+(cc?nota(cc):0);', 'return a+(cc?mtMaiorNota(cc):0);'),
        ('const nt=x=>{try{return nota(x.c);}catch(e){return -9e9;}};',
         'const nt=x=>{try{return mtMaiorNota(x.c);}catch(e){return -9e9;}};'),
    ]
    for v, n in trocas:
        if v in html:
            html = html.replace(v, n); ok += 1

    return html, '%d de 13' % ok


# ------------------------------------------------ NOME DO IMPETO (11/08/2026)
# ORDEM DO LUIS, 11/08: "aqui tem que colocar o NOME do impeto MAIS o efeito.
# Nao e so o efeito."
#
# O que a tela mostrava:      NATIVO  Chute +2 · Chute +3
# O que ela passa a mostrar:  NATIVO  Striker's Instinct +3
#                                     Finalizacao · Cabeceio · Contato fisico +3
#
# DE ONDE VEM CADA PEDACO
#   nome  -> efscout_impeto_por_card.json (booster_id -> nome). E o nome DE
#            VERDADE do impeto no jogo. O `c.nmn` da casca e uma APROXIMACAO
#            montada a partir do const CAT, que so tem 87 assinaturas e nao tem
#            +4 nem +5 — por isso o Ronaldinho 89138288266704 aparecia como
#            "Tecnica +1 + Tecnica +3" quando na verdade e "Technique +4".
#            (confirmado pela sessao do impeto em 11/08)
#   efeito -> os pares [atributo, valor] do proprio efscout, escritos por extenso
#            com o const ATTRS da casca (os 26 nomes em portugues).
#            Conferido: Technique +4 = [[1,4],[2,4],[3,4],[4,4]] =
#            Controle de bola · Drible · Posse de bola · Passe rasteiro.
#
# LIMITE CONHECIDO: o efscout traz UM impeto por card. Card de DOIS nativos
# (nm de 8, 85 cards) mostra o principal pelo efscout e o resto pelo c.nmn.
# Sem dado do efscout, cai no comportamento antigo — nunca fica pior.
PIMP_ARQ = 'efscout_impeto_por_card.json'



def patch_tecnico_sugestao(html):
    """14/08: A SUGESTAO DE TECNICO CALCULADA NA TELA, nao gravada na linha.

    O `tecnicos_iguais` sai do motor e so muda quando a linha e refeita. Entao
    tecnico novo (Conte e Lampard, 14/08) nunca apareceria nas 11.918 linhas ja
    prontas — a menos que se refizesse tudo por causa de dois nomes.

    A regra do motor (roda_lote_v6.py) e reproduzivel na tela sem refazer nada:
    dois tecnicos dao nota IDENTICA se tem o mesmo multiplicador `m` e a
    diferenca entre os boosts cai so em atributo que a funcao NAO pesa.
    A tela tem as duas coisas — o `m` do tecnico e o peso de cada atributo.

    Se por qualquer motivo nao der para calcular, cai no que o motor gravou.
    """
    try:
        from equacao import carrega_tecnicos
        T = carrega_tecnicos('tecnicos.json')
    except Exception as e:
        return html, 'nao li tecnicos.json: %s' % e
    if not T:
        return html, 'lista vazia'

    # Mantem os tres indices historicos [nome, m, boost] e acrescenta o ID no
    # fim. Assim a casca antiga continua funcionando sem traducao de chave.
    dados = [[t['nome'], round(t['m'], 6), sorted(t['boost']), t.get('id')] for t in T]
    bloco = ('\n<script>\n'
             '/* SUGESTAO DE TECNICO - 14/08/2026 - injetado pelo gera_encaixe.py */\n'
             'window.TECS=' + json.dumps(dados, ensure_ascii=False,
                                         separators=(',', ':')) + ';\n'
             'window.tecIguais=function(c){\n'
             ' try{\n'
             '  var nm=(c._tecNome!==undefined?c._tecNome:c.TEC);\n'
             '  if(!nm||!window.TECS) return c.TECIG||[];\n'
             '  var t0=null,i,cur=[];\n'
             '  if(c.TECID!==undefined&&c.TECID!==null){for(i=0;i<TECS.length;i++) if(String(TECS[i][3])===String(c.TECID)){t0=TECS[i];break;}}\n'
             '  try{ (tecAtual(c)||[]).forEach(function(k){if(TECIDX[k]!==undefined)cur.push(TECIDX[k]);});cur.sort(function(a,b){return a-b;}); }catch(e){}\n'
             '  if(!t0) for(i=0;i<TECS.length;i++) if(TECS[i][0]===nm&&TECS[i][2].join(",")===cur.join(",")){t0=TECS[i];break;}\n'
             '  if(!t0){var un=TECS.filter(function(t){return t[0]===nm;});if(un.length===1)t0=un[0];}\n'
             '  if(!t0) return c.TECIG||[];\n'
             '  var pes={};\n'
             '  for(i=0;i<(c.arows||[]).length;i++) if(c.arows[i][1]) pes[c.arows[i][0]]=1;\n'
             '  var a={},j; for(j=0;j<t0[2].length;j++) a[t0[2][j]]=1;\n'
             '  var out=[];\n'
             '  for(i=0;i<TECS.length;i++){ var t=TECS[i];\n'
             '   if(t[3]===t0[3]||t[1]!==t0[1]) continue;\n'
             '   var b={},k,bate=true; for(j=0;j<t[2].length;j++) b[t[2][j]]=1;\n'
             '   for(k in a) if(!b[k]&&pes[k]){bate=false;break;}\n'
             '   if(bate) for(k in b) if(!a[k]&&pes[k]){bate=false;break;}\n'
             '   if(bate) out.push(t[0]);\n'
             '  }\n'
             '  out.sort();\n'
             '  return out.length?out.slice(0,5):(c.TECIG||[]);\n'
             ' }catch(e){ return c.TECIG||[]; }\n'
             '};\n'
             '</script>\n')
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + bloco + html[k:]

    ok = 0
    for a, b in (('c.TECIG&&c.TECIG.length', 'tecIguais(c).length'),
                 ('c.TECIG.slice(0,5).map', 'tecIguais(c).slice(0,5).map'),
                 ('c.TECIG.map(', 'tecIguais(c).map(')):
        if a in html:
            html = html.replace(a, b)
            ok += 1
    return html, '%d de 3 (%d tecnicos)' % (ok, len(dados))


def patch_nome_impeto(html):
    """Poe o NOME real do impeto e o efeito por extenso na ficha."""
    if 'NOME DO IMPETO - 11/08/2026' in html:
        return html, 'ja estava'
    if not os.path.exists(PIMP_ARQ):
        return html, 'FALTA ' + PIMP_ARQ
    try:
        IMP = json.load(open(PIMP_ARQ, encoding='utf-8'))
    except Exception as e:
        return html, 'nao li: %s' % e

    nomes, idx, card = [], {}, {}
    for b, e in IMP.items():
        if not e or not e.get('booster_id'):
            continue
        n = e.get('nome') or ''
        if n in ('', 'No Booster'):
            continue
        if n not in idx:
            idx[n] = len(nomes)
            nomes.append([n, e.get('efeito') or []])
        card[b] = idx[n]
    if not card:
        return html, 'sem impeto no arquivo'

    bloco = (
      '<script>\n'
      '/* NOME DO IMPETO - 11/08/2026 - injetado pelo gera_encaixe.py */\n'
      'window.PIMP=' + json.dumps({'n': nomes, 'c': card}, ensure_ascii=False,
                                  separators=(',', ':')) + ';\n'
      'window.pimpEfeito=function(pares){\n'
      ' if(!pares||!pares.length) return "";\n'
      ' var por={};\n'
      ' for(var i=0;i<pares.length;i++){var a=pares[i][0],v=pares[i][1];\n'
      '  var nm=(typeof ATTRS!=="undefined"&&ATTRS[a])?ATTRS[a]:("atributo "+a);\n'
      '  (por[v]=por[v]||[]).push(nm);}\n'
      ' var out=[];\n'
      ' Object.keys(por).sort(function(a,b){return b-a;}).forEach(function(v){\n'
      '  out.push(por[v].join(" \\u00b7 ")+" +"+v);});\n'
      ' return out.join(" \\u00b7 ");};\n'
      'window.pimpDoCard=function(c){\n'
      ' if(!c||!window.PIMP) return null;\n'
      ' var b=String(c.id).split("@")[0].split("|")[0];\n'
      ' var i=PIMP.c[b]; if(i===undefined) return null;\n'
      ' var e=PIMP.n[i]; return {nome:e[0],efeito:e[1]};};\n'
      # 14/08: OS DOIS IMPETOS NATIVOS. 115 cards tem DOIS e a tela mostrava
      # so o do efscout (que traz um por card). O `nm` do cards.json e a soma
      # dos dois; decompondo contra o const CAT os dois aparecem. So aceita
      # quando fecha EXATO — senao cai no antigo e nunca fica pior.
      'window.pimpNativos=function(c){\n'
      ' var nm=(c&&c.nm)||[]; if(!nm.length||nm.length>12) return null;\n'
      ' if(typeof CAT==="undefined") return null;\n'
      ' var d={},i,j,x; for(i=0;i<nm.length;i++) d[nm[i][0]]=(d[nm[i][0]]||0)+nm[i][1];\n'
      ' function sig(e){var o={},k;for(k=0;k<e.length;k++)o[e[k][0]]=(o[e[k][0]]||0)+e[k][1];return o;}\n'
      ' function eq(s){var a=Object.keys(s),b=Object.keys(d),k;\n'
      '  if(a.length!==b.length) return false;\n'
      '  for(k=0;k<a.length;k++) if(d[a[k]]!==s[a[k]]) return false; return true;}\n'
      # o CAT so vai ate +3. Os impetos +4 e +5 existem (Technique +4 do
      # Ronaldinho, os 6 cards Epic) e sao o MESMO impeto com o valor trocado —
      # entao as variantes saem do proprio +3, sem tabela nova.
      ' if(!window._CATX){var X=[];\n'
      '  for(i=0;i<CAT.length;i++){X.push([CAT[i][0],CAT[i][2]]);\n'
      '   if(/\\+3$/.test(CAT[i][0])){ [4,5].forEach(function(v){\n'
      '    X.push([CAT[i][0].replace(/\\+3$/,"+"+v),\n'
      '            CAT[i][2].map(function(pr){return [pr[0],v];})]);});}}\n'
      '  window._CATX=X; window._CATS=X.map(function(e){return sig(e[1]);});}\n'
      ' var S=window._CATS, X=window._CATX;\n'
      ' for(i=0;i<X.length;i++) if(eq(S[i])) return [{nome:X[i][0],efeito:X[i][1]}];\n'
      ' for(i=0;i<X.length;i++) for(j=i+1;j<X.length;j++){var t={};\n'
      '  for(x in S[i]) t[x]=S[i][x];\n'
      '  for(x in S[j]) t[x]=(t[x]||0)+S[j][x];\n'
      '  if(eq(t)) return [{nome:X[i][0],efeito:X[i][1]},{nome:X[j][0],efeito:X[j][1]}];}\n'
      ' return null;};\n'
      '</script>\n'
      '<style>\n'
      '.impef{font-size:10.5px;color:#8fa4c4;line-height:1.35;margin:0 0 3px}\n'
      'html[data-tema] .impef{color:var(--txt2)!important}\n'
      'html[data-tema=claro] .impef{color:#5a6675!important}\n'
      '.hblist li b{font-weight:700}\n'
            '</style>\n')

    ok = 0
    if '</head>' in html:
        html = html.replace('</head>', bloco + '</head>', 1); ok += 1

    # o NATIVO: nome do efscout + efeito por extenso; sem dado, cai no antigo
    velho = ("${(function(){const f=(c.nmn&&c.nmn.length)?c.nmn:(c.imps||[])"
             ".filter(x=>x&&x.f).map(x=>x.n).filter(Boolean);"
             "return f.length?f.map(n=>`<li>${n}</li>`).join(''):'<li>não tem</li>';})()}")
    novo = ("${(function(){const L=(typeof pimpNativos==='function')?pimpNativos(c):null;"
            "if(L&&L.length>1) return L.map(x=>{const ef=pimpEfeito(x.efeito);"
            "return `<li><b>${pimpPT(x.nome,x.efeito)}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}).join('');"
            "const P=(typeof pimpDoCard==='function')?pimpDoCard(c):null;"
            "const f=(c.nmn&&c.nmn.length)?c.nmn:(c.imps||[])"
            ".filter(x=>x&&x.f).map(x=>x.n).filter(Boolean);"
            "if(P){const ef=pimpEfeito(P.efeito);"
            "return `<li><b>${pimpPT(P.nome,P.efeito)}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}"
            "if(L&&L.length===1){const ef=pimpEfeito(L[0].efeito);"
            "return `<li><b>${pimpPT(L[0].nome,L[0].efeito)}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}"
            "return f.length?f.map(n=>`<li><b>${n}</b></li>`).join(''):'<li>não tem</li>';})()}")
    if velho in html:
        html = html.replace(velho, novo, 1); ok += 1

    # o ADICIONADO: o motor ja da o nome; o efeito sai do const CAT da casca
    v2 = ("${(function(){var _p=String(c.imp||'').split('o motor pos:');"
          "if(_p.length>1) return `<li>${_p[1].trim()}</li>`;")
    n2 = ("${(function(){var _p=String(c.imp||'').split('o motor pos:');"
          "if(_p.length>1){var nm=_p[1].trim();var ef='';"
          "try{var h=(typeof CAT!=='undefined')?CAT.filter(function(x){return x[0]===nm;})[0]:null;"
          "if(h)ef=pimpEfeito(h[2]);}catch(e){}"
          "return `<li><b>${nm}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}")
    if v2 in html:
        html = html.replace(v2, n2, 1); ok += 1

    return html, '%d de 3 (%d cards com nome)' % (ok, len(card))


def patch_fecha_pesos(html):
    """FECHADO PELO LUIS EM 10/08/2026 — os dois bonus somados por fora.

    ESTILO DE JOGO DA IA .... teto 1 ponto
        A conta continua a mesma: 1 x (quantos estilos / 5).
        1 estilo = +0,2 · 3 = +0,6 · 5 = +1,0
        Por que 1 e nao 2: varredura em 10/08 nas comunidades EN, ES, PT, TR,
        ID, JP e CHINESA (incluindo os 90 episodios do 实况实验室 do
        珠海amadeusz, a unica fonte do mundo que faz teste de bancada) —
        NINGUEM pontua AI playing style, e ele nunca dedicou um episodio ao
        tema em 365 videos. Alem disso 83% das nossas linhas estao com zero
        estilo coletado. Peso alto premiaria quem por acaso foi coletado.

    FISICO (molde do corpo) .. de -1,5 a +1,5  (CORPO_MAX = 1.5)
        Amplitude total de 3 pontos. O bonus e o % de cumprimento do molde da
        funcao aplicado nesse teto: 100% do molde = +1,5 · -100% = -1,5.
    """
    ok = 0
    for velho, novo in (('let IA_PT=2;', 'let IA_PT=1;'),
                        # 15/08 ORDEM DO LUIS: o teto do estilo de IA era 5,
                        # mas o maximo que existe na base e 4 (medido nas 12.161
                        # linhas: 1->2.069  2->3.010  3->1.865  4->282  5->ZERO).
                        # Com teto 5 ninguem chegava ao +1,00. Agora 4 = +1,00.
                        ('let IA_MAX=5;', 'let IA_MAX=4;'),
                        ('let IA_I=4;', 'let IA_I=2;'),
                        # 14/08: o rotulo mostrava +2 (valor da casca) enquanto a
                        # conta usava +1 (valor trocado aqui). Confundiu o Luis.
                        ('>estilo IA: +2</button>', '>estilo IA: +1</button>'),
                        ('let CORPO_MAX = 1;', 'let CORPO_MAX = 1.5;'),
                        ('let CORPO_MAX = 1.5;', 'let CORPO_MAX = 1.5;')):
        if velho in html:
            html = html.replace(velho, novo, 1)
            ok += 1
    return html, ok


def patch_falso_nove(html):
    """FALSO NOVE — a 19a funcao. Decisao do Luis, 12/08.

    CA/SA + estilo "Atacante Pivo" deixa de ser Centroavante movel e vira
    Falso nove. Molde proprio (64 representantes) no dados/molde.json v5.

    Aqui so a TELA: o terceiro destino no funcDaPos, a funcao nas 8 tabelas
    indexadas por nome (copiadas do Centroavante movel) e o lugar na barra.
    """
    import re, json as _j
    ok = 0
    FN = 'Falso nove'
    CM = 'Centroavante m\u00f3vel'

    # 1) funcDaPos ganha o terceiro destino
    a = ("if(p==='SA'||p==='SS')p=TJ_SA[modelo]||'MO';\n const r=TJ_REGRA[p];"
         "if(!r)return null;\n return (r[0]||[]).indexOf(modelo)>=0?r[1]:r[2];")
    b = ("if(p==='SA'||p==='SS')p=TJ_SA[modelo]||'MO';\n"
         " if(p==='CA'&&modelo==='Atacante Piv\u00f4')return 'Falso nove';\n"
         " const r=TJ_REGRA[p];if(!r)return null;\n"
         " return (r[0]||[]).indexOf(modelo)>=0?r[1]:r[2];")
    if a in html:
        html = html.replace(a, b); ok += 1

    # 2) as 8 tabelas indexadas por nome: copia a entrada do Centroavante movel
    for tab in ('REGUA', 'FX_ANC', 'FX_K', 'FIS_KON', 'FIS_P', 'MF_TIPO', 'MF_FAIXA',
                'FILA', 'MED', 'B5V', 'ESTV', 'MF_DIRF'):
        m = re.search(tab + r'=\{', html)
        if not m: continue
        i = m.end() - 1
        d = 0
        for j in range(i, len(html)):
            if html[j] == '{': d += 1
            elif html[j] == '}':
                d -= 1
                if d == 0: break
        bloco = html[i:j+1]
        if '"' + FN + '"' in bloco: continue
        alvo = None
        for cand in (CM, 'Centroavante m' + chr(92) + 'u00f3vel'):
            kk = bloco.find('"' + cand + '":')
            if kk >= 0: alvo = cand; k = kk; break
        if alvo is None: continue
        p = k + len('"' + alvo + '":')
        dd = 0; fim = None
        for t in range(p, len(bloco)):
            ch = bloco[t]
            if ch in '[{': dd += 1
            elif ch in ']}':
                dd -= 1
                if dd == 0: fim = t + 1; break
            elif ch == ',' and dd == 0: fim = t; break
        if fim is None: continue
        valor = bloco[p:fim]
        novo = bloco[:1] + '"' + FN + '":' + valor + ',' + bloco[1:]  # FN e ascii
        html = html[:i] + novo + html[j+1:]
        ok += 1

    # 3) rotulo curto e lugar na barra lateral, dentro de CENTROAVANTE
    html = html.replace('"Centroavante fixo":"fixo"',
                        '"Falso nove":"falso nove","Centroavante fixo":"fixo"')
    a = '["CENTROAVANTE",["Centroavante fixo","Centroavante m\u00f3vel"]]'
    b = '["CENTROAVANTE",["Falso nove","Centroavante fixo","Centroavante m\u00f3vel"]]'
    if a in html:
        html = html.replace(a, b); ok += 1
    else:
        a2 = '["CENTROAVANTE",["Centroavante fixo","Centroavante móvel"]]'
        b2 = '["CENTROAVANTE",["Falso nove","Centroavante fixo","Centroavante móvel"]]'
        if a2 in html:
            html = html.replace(a2, b2); ok += 1

    # MT_FUNCS: a chave e a POSICAO. O CA ganha a terceira funcao.
    for a, b2 in (
        ('CA:["Centroavante fixo","Centroavante m\u00f3vel"]',
         'CA:["Falso nove","Centroavante fixo","Centroavante m\u00f3vel"]'),
        ('CA:["Centroavante fixo","Centroavante móvel"]',
         'CA:["Falso nove","Centroavante fixo","Centroavante móvel"]'),
        ('SA:["Segundo atacante"]',
         'SA:["Segundo atacante","Falso nove"]'),
    ):
        if a in html:
            html = html.replace(a, b2); ok += 1

    return html, ok



def patch_edicao_viva(html):
    """A NOTA PASSA A SE REFAZER SOZINHA — e o condicional do card funciona.

    Achado em 14/08, medido na casca e no HTML gerado:

    1) TODA edição da ficha (barra, técnico, habilidade, ímpeto) termina em
       `_grava` / `_trocaHabs`. As duas refazem `c.b1` e param aí — não
       refazem o `c.b1n` (o b1 na régua, que é o que entra na nota) nem
       apagam o cache `c._n`. Resultado: os atributos mudam na tela e a nota
       fica congelada. Todo OUTRO ponto do código faz o trio completo
       (ver `notaComTec`, linha ~2705 da casca): b1, b1n e `delete _n`.

    2) O botão do condicional NA FICHA (`toggleCondCard`) depende de
       `c.cdelta`, que o gerador nunca montou — clicar não fazia nada.
       O dado certo já existe e é o `CD`, a build INTEIRA que o motor
       refez para os degraus 2 e 3 (763 registros no HTML de 14/08).
       ⛔ Aqui NÃO se soma por fora: troca a build guardada, como em 10/08.

    Tudo entra como script no fim do arquivo, sobrescrevendo as funções da
    casca. A casca de 3,1 MB não é editada.
    """
    if 'EDICAO_VIVA_1408' in html:
        return html, 0
    ok = 0

    # ---- o seletor solto de FABRICAR IMPETO sai de cena ------------------
    # Ele lia a lista `c.imps` (furada) e mostrava "(nenhum)" com o card
    # tendo impeto. O controle agora vive no quadro do impeto, ao lado do
    # nome — ordem do Luis, 14/08: "deixa la onde esta o Sem Bola".
    ai = "const imp=(c.sl&&(c.sl[0]||c.sl[1]))?`<div class=imp>"
    bi = "const imp=false?`<div class=imp>"
    if ai in html:
        html = html.replace(ai, bi)
        ok += 1

    # ---- nunca mais "IMPETO NATIVO: nao tem" em card que tem -------------
    an = "return f.length?f.map(n=>`<li><b>${n}</b></li>`).join(''):'<li>n\u00e3o tem</li>';"
    bn = ("return f.length?f.map(n=>`<li><b>${n}</b></li>`).join(''):"
          "((typeof _natDoVetor==='function')?_natDoVetor(c):'<li>n\u00e3o tem</li>');")
    if an in html:
        html = html.replace(an, bn)
        ok += 1

    # ---- AS TRES ABAS DO BLOCO ATRIBUTOS ---------------------------------
    am = 'return `<div class="bpan bptrio">'
    bm = ('return `${(typeof _modoBar===' + chr(39) + 'function' + chr(39)
          + ')?_modoBar(K):' + chr(39) + chr(39) + '}<div class="bpan bptrio">')
    if am in html:
        html = html.replace(am, bm)
        ok += 1


    # ---- O BOTAO DAS BARRAS SAI DO MODO ADMINISTRADOR --------------------
    # Ordem do Luis, 14/08: o usuario poe os insumos que ELE TEM (as poucas
    # habilidades que conseguiu, o tecnico que tem, o impeto que tem) e as
    # barrinhas se redistribuem sozinhas para a maior nota com aquilo.
    # O botao ja fazia exatamente isso — so estava escondido no modo admin.
    ab = ('<button class=admonly onclick="otimizarBarras(\'${K}\')"')
    bb = ('<button onclick="otimizarBarras(\'${K}\')"')
    if ab in html:
        html = html.replace(ab, bb)
        ok += 1
    for _a, _b in ((chr(34)+'administrador: redistribui as barras',
                    chr(34)+'distribui os 66 pontos das barras'),
                   ('recalcular as barras (admin)',
                    'ajustar as barras ao que est'+chr(92)+'u00e1 na tela')):
        if _a in html:
            html = html.replace(_a, _b)
            ok += 1


    # ---- O TETO 99 QUE APAGAVA O ORIGINAL (achado 14/08) ------------------
    # `valsDeLvl` refaz os atributos a partir do ORIGINAL mais o delta da
    # barra, e travava tudo em 99. Mas o valor original de um card forte JA
    # PASSA de 99 (Messi: Drible 113, Finalizacao 107 — impeto e habilidade
    # somam por cima). Entao baixar a barra cortava 113 -> 99, e voltar a
    # barra devolvia min(99, 113) = 99. O corte era PERMANENTE: o Luis via
    # 111,53 virar 108,49 e nunca mais voltar.
    # Conserto: o teto passa a ser o MAIOR entre 99 e o valor original —
    # quem ja estava acima nao e mais rebaixado, e a conta volta a ser
    # reversivel. Nada sobe alem do que subia antes.
    # mesmo teto no caminho das HABILIDADES (`_trocaHabs`): tirar e devolver
    # a habilidade deixava a nota no chao porque o valor acima de 99 era
    # cortado na ida e nao voltava na volta.
    ah = 'const vals=(c.sis||v0).map((x,i)=>Math.max(0,Math.min(99,Math.round(x+(v1[i]-v0[i])))));'
    bh = 'const vals=(c.sis||v0).map((x,i)=>Math.max(0,Math.min(Math.max(99,x),Math.round(x+(v1[i]-v0[i])))));'
    if ah in html:
        html = html.replace(ah, bh)
        ok += 1

    a = 'v[i]=Math.max(0,Math.min(99,o.v[k]+(cn[i]-cb[i])+(tn[i]-tb[i])));'
    b = 'v[i]=Math.max(0,Math.min(Math.max(99,o.v[k]),o.v[k]+(cn[i]-cb[i])+(tn[i]-tb[i])));'
    if a in html:
        html = html.replace(a, b)
        ok += 1

    # o botao da ficha so aparece se o card TEM os degraus do motor
    a = 'const _cond=(c.imps||[]).some(x=>x.c)||c.cdelta;'
    b = 'const _cond=!!(c.CD&&(c.CD["2"]||c.CD["3"]));'
    if a in html:
        html = html.replace(a, b)
        ok += 1

    # ---- O CONTROLE DO IMPETO VAI PARA O QUADRO DO IMPETO ----------------
    # Ordem do Luis, 14/08: "deixa la onde esta o Sem Bola, e so mudar la".
    # O seletor solto embaixo do tecnico (FABRICAR IMPETO) lia a lista
    # `c.imps`, que esta furada — por isso mostrava "(nenhum)" com o card
    # tendo impeto. Aqui o controle nasce ao lado do nome, lendo a string.
    a = ("return `<li><b>${nm}</b>${ef?`<div class=impef>${ef}</div>`:''}</li>`;}"
         "if(c.slot===0) return '<li style=\"color:#8fa4c4\">n\u00e3o tem vaga</li>';"
         "if(c.slot) return '<li style=\"color:#8fa4c4\">vaga livre</li>';")
    b = ("return `<li><b>${nm}</b> <b style=\"cursor:pointer;color:#e46a6a;margin-left:4px\" "
         "title=\"tirar este \u00edmpeto\" onclick=\"editImp('${K}','')\">\u00d7</b>"
         "${ef?`<div class=impef>${ef}</div>`:''}"
         "${(typeof _impSel==='function')?_impSel(c,K,nm):''}</li>`;}"
         "if(c.slot===0) return '<li style=\"color:#8fa4c4\">n\u00e3o tem vaga</li>';"
         "if(c.slot) return `<li><span style=\"color:#8fa4c4\">vaga livre</span>"
         "${(typeof _impSel==='function')?_impSel(c,K,''):''}</li>`;")
    if a in html:
        html = html.replace(a, b)
        ok += 1

    sc = """
<script>
/* ===== EDICAO_VIVA_1408 ===== */
(function(){
 /* A nota de hoje NAO vem mais do b1 pela regua: vem da % DO MOLDE
    (patch ACH, funcao achPct), que tem cache proprio em c._cp e reescreve
    o c.b1n de todos os cards a cada traducaoViva(). Medido em 14/08 no
    Chromium: apos editar, _renota punha o b1n certo e o traducaoViva
    seguinte devolvia o valor antigo, porque o _cp continuava no cache.
    Entao apaga-se o _cp ANTES — e o traducaoViva faz o resto.
    O b1nDe fica de reserva, para quando o ACH estiver desligado. */
 function _renota(c){
  if(!c||c.id==="MOLDE")return;
  delete c._cp;
  delete c._n;
  try{
   var A=c.arows||[], n2=0, d2=0, q, w2;
   for(q=0;q<A.length;q++){ w2=A[q][1]; if(!w2) continue;
    n2+=w2*A[q][3]; d2+=w2*A[q][2]; }
   if(d2){ c.b1n=100*n2/d2; return; }
  }catch(e){}
  try{ c.b1n=b1nDe(c.tipo,c.b1); }catch(e){}
 }
 function _pinta(){ try{traducaoViva();}catch(e){} try{render();}catch(e){} }
 window._renota=_renota;

 var _g=window._grava;
 if(_g) window._grava=function(c,lvl){ _g(c,lvl); _renota(c); _pinta(); };

 var _th=window._trocaHabs;
 if(_th) window._trocaHabs=function(key,novas){ _th(key,novas); _renota(_card(key)); _pinta(); };

 var _rm=window.restaurarMotor;
 if(_rm) window.restaurarMotor=function(key){
  var c=_card(key); if(c){ delete c._cdOrig; c.cmode=1; }
  _rm(key); _renota(_card(key)); _pinta();
 };

 var _df=window._desfaz;
 if(_df) window._desfaz=function(){
  _df();
  try{ for(var i=0;i<D.length;i++) _renota(D[i]); }catch(e){}
  _pinta();
 };

 /* ---- IMPETO CONDICIONAL NA FICHA DO CARD ----------------------------
    Degraus lidos do videogame em 31/07 e refeitos INTEIROS pelo motor:
      1 a 7 jogadores da condicao -> degrau 1 (o padrao, e o do ranking)
      8 a 10                      -> degrau 2
      11 a 23                     -> degrau 3
    Nao existe degrau 4 nem 5: o motor so calcula 2 e 3. */
 function _tem(c){ return !!(c&&c.CD&&(c.CD["2"]||c.CD["3"])); }
 function _guarda(c){
  if(c._cdOrig)return;
  c._cdOrig={b1:c.b1,b1n:c.b1n,bar:c.sisBar,TEC:c.TEC,TECB:c.TECB,
             HAB:c.HAB,adds:c.adds,sobra:c.sobra,
             v:(c.arows||[]).map(function(r){return r[3];})};
 }
 function _aplica(c){
  if(!_tem(c))return;
  _guarda(c);
  var n=c.cmode||1, o=c._cdOrig, a,
      f=(n>1&&c.CD[String(n)])?c.CD[String(n)]:null;
  c.b1    = f? f.b1    : o.b1;
  c.b1n   = f? f.b1n   : o.b1n;
  c.sisBar= f? f.bar   : o.bar;
  c.TEC   = f? f.TEC   : o.TEC;
  c.TECB  = f? f.TECB  : o.TECB;
  c.HAB   = f? f.HAB   : o.HAB;
  c.adds  = f? f.HAB   : o.adds;
  c.sobra = f? f.sobra : o.sobra;
  var vv = f? f.v : o.v;
  if(c.arows&&vv) for(a=0;a<c.arows.length;a++){
   if(vv[a]===undefined)continue;
   c.arows[a][3]=vv[a];
   c.arows[a][4]=Math.round((vv[a]-c.arows[a][2])*100)/100;
   c.arows[a][5]=vv[a];
  }
  delete c._cp;
  delete c._n;
 }
 window.recalcCard=function(c){ if(_tem(c)) _aplica(c); };

 /* ---- IMPETO ADICIONADO: editavel no proprio quadro -------------------
    A verdade do impeto e a STRING `c.imp` — o proprio codigo da casca diz
    isso num comentario, e a lista `c.imps` do banco esta desencontrada dela
    desde 05/08 (caderninho, item 24: "seletor pleno dos impetos fica pro
    pacotao real"). O formato real e:

       "de fabrica: Conducao Tecnica +3 · o motor pos: Sem Bola +1"

    O `editImp` da casca reescrevia a string INTEIRA ("Precisao +3 ⚒"),
    APAGANDO o impeto de fabrica junto. Aqui so a parte depois de
    "o motor pos:" e trocada; o nativo nunca e tocado.

    E o `valsDeLvl` nao conhecia impeto — so barra e tecnico. Entao trocar
    o impeto nao mexia em atributo nenhum. Agora entra pelo mesmo caminho
    do tecnico: delta entre o impeto original e o de agora. */
 /* Reotimizar as barras depois de trocar habilidade ou impeto (ordem do
    Luis, 14/08). Com uma trava: se a escolha voltou a ser EXATAMENTE a que o
    motor tinha posto, devolve a build do motor em vez de reotimizar — o
    otimizador que roda no navegador e mais fraco que o motor de verdade, e
    sem isso desfazer uma troca nunca voltava a nota de origem. */
 function _igualAoMotor(c){
  var o=_oriDe(c);
  if(String(c.imp||'')!==String(o.imp||'')) return false;
  var h=(c._habs!==undefined)?c._habs:(c.HAB||[]), h0=(c.HAB||[]), i;
  if(h.length!==h0.length) return false;
  for(i=0;i<h.length;i++) if(h0.indexOf(h[i])<0) return false;
  return true;
 }
 /* Se a composicao voltou a ser EXATAMENTE a que o motor escolheu, o card
    volta a ser o do motor — pelo mesmo caminho do botao verde, que ja devolve
    o numero exato. Nao se reotimiza no navegador nesse caso: o otimizador
    daqui e mais fraco que o motor e devolveria nota menor.
    (A primeira tentativa montava a restauracao na mao e devolvia 110,5 no
    lugar de 108,57 — por isso agora chama o `restaurarMotor` de verdade.) */
 function _igualAoMotor(c){
  var o=_oriDe(c);
  if(String(c.imp||'')!==String(o.imp||'')) return false;
  var h=(c._habs!==undefined)?c._habs:(c.HAB||[]), h0=(c.HAB||[]), i;
  if(h.length!==h0.length) return false;
  for(i=0;i<h.length;i++) if(h0.indexOf(h[i])<0) return false;
  var t=(c._tec!==undefined)?c._tec:(c.TECB||[]), t0=(o.tec||[]);
  if(t.length!==t0.length) return false;
  for(i=0;i<t.length;i++) if(t0.indexOf(t[i])<0) return false;
  return true;
 }
 function _reOtim(c,key){
  if(window.ENC_MODO==='livre') return;
  if(_igualAoMotor(c)){
   if(typeof restaurarMotor==='function') restaurarMotor(key);
   return;
  }
  if(typeof otimizarBarras==='function') otimizarBarras(key);
 }
 /* trocar o TECNICO tambem redistribui as barras (ordem do Luis, 14/08:
    o usuario poe os insumos que ELE tem — habilidade, tecnico, impeto — e
    as barrinhas se acertam sozinhas para a maior nota com aquilo). */
 var _tc=window.trocaTec;
 if(_tc) window.trocaTec=function(key,idx){
  var c=_card(key); try{ _oriDe(c); }catch(e){}
  _tc(key,idx);
  try{ _reOtim(_card(key),key); }catch(e){}
  _pinta(); try{ reabrir(key); }catch(e){}
 };
 /* ===== AS ABAS DO BLOCO ATRIBUTOS — REMOVIDAS DAQUI EM 16/08/2026 =====
    ⛔ NAO REPOR. Este bloco definia `window.encModo` e `window._modoBar` — e o
    CONTA-DO-MOTOR.js define OS DOIS DE NOVO. Duas versoes da mesma coisa no
    mesmo HTML, e quem mandava era a que carregasse por ultimo.

    O que isso custou, medido em 16/08: na tela gerada as 02h25 venceu ESTA
    versao, que chamava `otimizarBarras` ao entrar na aba em vez de `zeraInsumos`.
    Resultado: a aba abria com tecnico, impeto fabricado e habilidades
    adicionadas ja preenchidos com a build do motor. E os nomes das abas que o
    Luis fechou em 15/08 (MAXIMO POSSIVEL / MEU CARD / LIVRE) nunca chegaram a
    aparecer — esta versao os sobrescrevia com os nomes de 14/08.

    Ordem do Luis, 16/08: *"por que que tem duas versoes? A gente nao pode
    trabalhar com coisa pela metade, so da problema. Voce tem que colocar o que
    a gente vai usar mesmo."*

    Fica UMA versao so, a do CONTA-DO-MOTOR.js. O gancho que insere a barra de
    abas (`_modoBar(K)` antes do `<div class="bpan bptrio">`) CONTINUA aqui em
    cima — ele so chama quem existir. */
 /* ---- "IMPETO NATIVO: nao tem" em card que TEM (14/08) ----------------
    O nome do impeto nativo vem do `nmn` / do efscout. Quando nenhum dos dois
    tem o nome, a tela escrevia "nao tem" — mas o EFEITO esta no vetor `nm`,
    que o motor usa e que nunca esta vazio nesses cards (Hazard e o exemplo
    do Luis). Aqui o nome e DEDUZIDO do proprio vetor: procura-se no catalogo
    o impeto cujos atributos e valores batem exatamente com o que sobrou.
    Se nenhum bate, mostra-se o efeito por extenso — nunca mais "nao tem"
    num card que tem. */
 window._natDoVetor=function(c){
  var v, i, j, k, sobra=[], usados=[], f, ok2, achou;
  var _AVISO='<li><b>TEM ímpeto — efeito por conferir</b>'
      +'<div class=impef>o card veio com ímpeto de fábrica, mas o catálogo não '
      +'conhece esse código'+((c.boostIds&&c.boostIds.length)?' ('+c.boostIds.join(' e ')+')':'')
      +'. O motor calculou SEM ele: a nota está por baixo. '
      +'Conferir a ficha no jogo resolve todos os cards que usam o mesmo.</div></li>';
  try{ v=expand(c.nm).slice(); }catch(e){ return c.impDesc?_AVISO:'<li>não tem</li>'; }
  var soma=0; for(i=0;i<26;i++) soma+=v[i];
  if(!soma) return c.impDesc?_AVISO:'<li>não tem</li>';
  /* tira do vetor o que ja foi identificado como fabricado (a string) */
  try{ var im=_impVetStr(c.imp); for(i=0;i<26;i++) v[i]=Math.max(0,v[i]-im[i]); }catch(e){}
  soma=0; for(i=0;i<26;i++) soma+=v[i];
  if(!soma) return c.impDesc?_AVISO:'<li>não tem</li>';
  for(k=0;k<3;k++){
   achou=null;
   for(j=0;j<CAT.length;j++){
    f=expand(CAT[j][2]); ok2=false;
    for(i=0;i<26;i++){ if(f[i]>v[i]){ ok2=false; break; } if(f[i]) ok2=true; }
    if(ok2){ if(!achou || _peso(f)>_peso(expand(achou[2]))) achou=CAT[j]; }
   }
   if(!achou) break;
   usados.push(achou[0]);
   f=expand(achou[2]); for(i=0;i<26;i++) v[i]-=f[i];
   soma=0; for(i=0;i<26;i++) soma+=v[i];
   if(!soma) break;
  }
  if(usados.length){
   return usados.map(function(n){
    var h=null,z; for(z=0;z<CAT.length;z++) if(CAT[z][0]===n){h=CAT[z];break;}
    var ef=''; try{ if(h) ef=pimpEfeito(h[2]); }catch(e){}
    return '<li><b>'+n+'</b>'+(ef?'<div class=impef>'+ef+'</div>':'')+'</li>';
   }).join('');
  }
  var txt=[]; try{ v=expand(c.nm);
   for(i=0;i<26;i++) if(v[i]) txt.push(ATTRS[i]+' +'+v[i]);
  }catch(e){}
  return txt.length? '<li><b>ímpeto nativo</b><div class=impef>'+txt.join(' · ')+'</div></li>'
                   : (c.impDesc?_AVISO:'<li>não tem</li>');
 };
 function _peso(f){ var t=0,i; for(i=0;i<26;i++) t+=f[i]; return t; }
 var MARCA='o motor pos:';
 function _impPartes(c){
  var s=String(c.imp||''), i=s.indexOf(MARCA);
  if(i<0) return {fab:s.replace(/\\s*\u2692\\s*$/,'').trim(), add:''};
  return {fab:s.slice(0,i).replace(/[·\\s]+$/,'').trim(),
          add:s.slice(i+MARCA.length).replace(/\\s*\u2692\\s*$/,'').trim()};
 }
 function _impMonta(fab,add){
  var a=[]; if(fab)a.push(fab); if(add)a.push(MARCA+' '+add);
  return a.join(' · ');
 }
 function _impNome(n){
  if(!n)return null;
  for(var i=0;i<CAT.length;i++) if(CAT[i][0]===n) return CAT[i];
  return null;
 }
 function _impVetStr(s){
  var v=new Array(26); for(var i=0;i<26;i++)v[i]=0;
  var P=_impPartes({imp:s});
  [P.fab.replace(/^de f[aá]brica:\\s*/i,''), P.add].forEach(function(bloco){
   String(bloco||'').split(/\\s+[·+]\\s+/).forEach(function(n){
    var f=_impNome(n.trim()); if(f) expand(f[2]).forEach(function(q,j){v[j]+=q;});
   });
  });
  return v;
 }
 window.impVet=function(c){ return _impVetStr(c&&c.imp); };

 var _vl=window.valsDeLvl;
 if(_vl) window.valsDeLvl=function(c,lvl){
  var v=_vl(c,lvl);
  try{
   var o=_oriDe(c), ib=_impVetStr(o.imp), inn=_impVetStr(c.imp);
   c.arows.forEach(function(r,k){ var i=r[0], d=inn[i]-ib[i];
    if(d) v[i]=Math.max(0,Math.min(Math.max(99,o.v[k]),v[i]+d)); });
  }catch(e){}
  return v;
 };

 window.editImp=function(key,nome){
  var c=_card(key); if(!c)return;
  /* o retrato do original TEM de ser tirado antes de mexer na string:
     o _oriDe guarda na primeira chamada, e quem chamava primeiro era o
     _grava — ja com o impeto novo, o que zerava o delta. */
  try{ _oriDe(c); _marca(key); }catch(e){}
  var P=_impPartes(c), add=(!nome||nome==='(nenhum)')?'':nome;
  c.imp=_impMonta(P.fab,add);
  c.imps=(c.imps||[]).filter(function(x){return !x.f;});
  if(add)c.imps.push({n:add,c:0,f:1});
  _grava(c,_lvlDe(c));
  try{ _reOtim(c,key); }catch(e){}
  _pinta();
  try{ reabrir(key); }catch(e){}
 };
/* ---- HABILIDADE: o efeito parava de aparecer por saturacao ------------
    O `_trocaHabs` mede o efeito da habilidade pela `cadeia()`, que trava em
    99. O Messi tem Drible 113 e Finalizacao 107 no motor; na cadeia os dois
    viram 99, e ai as habilidades de drible dele "nao tem onde subir" —
    tirar as CINCO adicionadas mexia 0,5% na nota. Medido em 14/08.
    Aqui o efeito e medido SEM a trava, sobre o valor pre-habilidade, e o
    delta e aplicado em cima do numero do motor. */
 function _preHab(c,lvl){
  var nm=expand(c.nm), tec=tecVet(tecAtual(c)), im=_impVetStr(c.imp);
  var cb=_contrib(lvl), v=new Array(26), i;
  for(i=0;i<26;i++){ v[i]=Math.min(99,(c.base?c.base[i]:0)+cb[i]) + nm[i]+im[i]+tec[i]; }
  return v;
 }
 function _buffSemTeto(v,b){
  if(!b) return v;
  return v + Math.max(0, Math.ceil(v*b[0]/100) + b[1]);
 }
 window._trocaHabs=function(key,novas){
  var c=_card(key); if(!c)return;
  try{ _oriDe(c); _marca(key); }catch(e){}
  var lvl=_lvlDe(c), pre=_preHab(c,lvl);
  var b0=buffDe(habsDe(c));
  c._habs=novas;
  var b1=buffDe(habsDe(c));
  var o=_oriDe(c), sis=(c.sis&&c.sis.length)?c.sis.slice():c.arows.map(function(r){return r[3];});
  c.arows.forEach(function(r,k){
   var i=r[0], d=_buffSemTeto(pre[i],b1[i])-_buffSemTeto(pre[i],b0[i]);
   var teto=Math.max(99,o.v[k]);
   var x=Math.max(0,Math.min(teto,Math.round(sis[i]+d)));
   sis[i]=x; r[3]=x; r[4]=Math.round((x-r[2])*100)/100; r[5]=x;
  });
  c.sis=sis;
  c.b1=notaDe(sis,c.arows);
  _renota(c);
  _pinta();
  try{ reabrir(key); }catch(e){}
 };
 window.impAdicionado=function(c){ return _impPartes(c).add; };
 window._impSel=function(c,K,atual){
  var ops=window.impOpcoes(c), h="", i, q=String.fromCharCode(39);
  h+="<select style=\\"max-width:200px;margin-top:5px;font-size:11px\\" onchange=\\"editImp("+q+K+q+",this.value)\\">";
  h+="<option value=\\"\\""+(atual?"":" selected")+">(nenhum)</option>";
  for(i=0;i<ops.length;i++) h+="<option"+(ops[i]===atual?" selected":"")+">"+ops[i]+"</option>";
  return h+"</select>";
 };
 window.impOpcoes=function(c){
  var fora={}, P=_impPartes(c);
  String(P.fab).split(/\\s+[·+]\\s+/).forEach(function(n){fora[n.trim()]=1;});
  return CAT.filter(function(x){ return !fora[x[0]]; }).map(function(x){return x[0];});
 };
 window.toggleCondCard=function(key){
  var c=_card(key); if(!c||!_tem(c))return;
  try{ _marca(key); }catch(e){}
  var d=(c.cmode||1)+1;
  while(d<=3 && !c.CD[String(d)]) d++;
  c.cmode = (d>3)?1:d;
  _aplica(c);
  _pinta();
  try{ reabrir(key); }catch(e){}
 };
})();
</script>
"""
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    return html[:k] + sc + html[k:], ok + 1


_JS_CONTA_DO_MOTOR = r'''/* ===================================================================
   A CONTA DO MOTOR NA TELA — 15/08/2026
   Ordem do Luis: "tem que calcular de acordo com o que mexe, da mesma
   forma que o motor calcula". E o desenho, na palavra dele:
     "o motor e essa equacao com alteracao a exaustao das variaveis para
      achar a soma maxima; a tela e a aplicacao dela pontualmente."
   Uma equacao so, dois usos.

   A Equacao 1 (AS-DUAS-EQUACOES-NAO-MEXER + equacao.py):
     pre = min(99, base + niveis das barras)      <- referencia da habilidade
     x   = pre + trunc(pre*(m-1))   piso 40, teto 99
     x  += +1 do tecnico (2 atributos)            passa de 99
     x  += impeto nativo (c.nm) + o que o motor pos    passa de 99
     x  += ceil(pre*pct/100 + flat)               habilidade, SEM TRAVA
   =================================================================== */
(function(){
  if (window.CONTA_DO_MOTOR_1508) return;
  window.CONTA_DO_MOTOR_1508 = true;

  var HABM = __HABM__;      /* nome PT -> [rara?1:0, {idx:[pct,flat]}]  (65) */
  var TECM = __TECM__;      /* nome do tecnico -> [multiplicadores possiveis] */
  var MS   = [1.036,1.0365,1.0355,1.034091,1.03275,1.03];

  function mult(x,m){ if(!m||m===1) return x;
    return Math.min(99, Math.max(40, x + Math.trunc(x*(m-1)))); }

  /* a regra da metade: comum vencedora inteira, cada perdedora metade;
     RARA soma por cima, inteira. (equacao.py buff_de) */
  function buff(hs){
    var pcC={},pcR={},flC={},flR={},i,h,v,k,d;
    for(i=0;i<(hs||[]).length;i++){ h=hs[i]; v=HABM[h]; if(!v) continue;
      var rara=v[0]===1, ef=v[1];
      for(k in ef){ d=ef[k];
        if(d[0]){ var A=rara?pcR:pcC; A[k]=(A[k]||[]).concat(d[0]); }
        if(d[1]){ var B=rara?flR:flC; B[k]=(B[k]||[]).concat(d[1]); } } }
    var meia=function(a){ if(!a||!a.length) return 0;
      var v2=a.slice().sort(function(x,y){return y-x;});
      return v2[0]+v2.slice(1).reduce(function(s,x){return s+x/2;},0); };
    var out={}, ids={}, o;
    [pcC,pcR,flC,flR].forEach(function(O){ for(o in O) ids[o]=1; });
    for(o in ids){
      var pct = meia(pcC[o]) + (pcR[o]||[]).reduce(function(a,b){return a+b;},0);
      var flat= meia(flC[o]) + (flR[o]||[]).reduce(function(a,b){return a+b;},0);
      if(pct||flat) out[+o]=[pct,flat];
    }
    return out;
  }

  /* SO o que o motor pos entra pela string. O NATIVO ja vem pelo c.nm —
     ler a string inteira conta o de fabrica DUAS VEZES (erro pego em 15/08). */
  function impDoMotor(s){
    var v=new Array(26).fill(0), dep=String(s||'').split('o motor pos:');
    if(dep.length<2) return v;
    dep.slice(1).join(' ').split('·').forEach(function(p){
      var t=p.replace(' (cond.)','').replace(' ⚒','').trim(); if(!t) return;
      var f=(typeof CAT!=='undefined') ? CAT.find(function(y){return y[0]===t;}) : null;
      if(f) expand(f[2]).forEach(function(x,i){ v[i]+=x; });
    });
    return v;
  }

  /* TODAS as habilidades que contam: fabrica + RARAS + as escolhidas.
     A tela esquecia as raras. */
  function todasHabs(c, escolhidas){
    return (c.fab||[]).concat(c.raras||[], escolhidas||[]);
  }

  /* a Equacao 1, uma vez, com o estado que vier */
  function conta(c, st){
    var base=c.base||[], cb=_contrib(st.lvl), tec=tecVet(st.tecb||[]),
        nm=expand(c.nm), imp=impDoMotor(st.imp), bf=buff(todasHabs(c, st.habs)),
        out=[], i, pre, x;
    for(i=0;i<26;i++){
      pre = Math.min(99,(base[i]||0)+cb[i]);
      x   = mult(pre, st.m);
      x  += tec[i] + nm[i] + imp[i];
      if(bf[i]) x += Math.ceil(pre*bf[i][0]/100 + bf[i][1]);
      out[i]=x;
    }
    return out;
  }

  /* o multiplicador do card: o que REPRODUZ o que o motor gravou.
     Sem chute — e a propria prova que escolhe. */
  function achaM(c, b){
    if(c._m!==undefined) return c._m;
    /* compara sempre contra o RETRATO do que o motor gravou, nunca contra um
       estado que ja foi mexido na tela */
    b = b || c._anc0 || {lvl:_lvlDe(c), tecb:(c.TECB||[]), imp:c.imp,
                         habs:(c._habs0||c.HAB||[]), v:(c.sis||[])};
    var st0={lvl:b.lvl, tecb:b.tecb, imp:b.imp, habs:b.habs}, i, k, v, ok;
    for(k=0;k<MS.length;k++){
      st0.m=MS[k]; v=conta(c,st0); ok=true;
      for(i=0;i<26;i++) if(Math.round(v[i])!==Math.round(b.v[i])){ ok=false; break; }
      if(ok){ c._m=MS[k]; return c._m; }
    }
    var L=TECM[c.TEC]; c._m = (L&&L.length)? L[L.length-1] : 1.036; c._mAprox=true;
    return c._m;
  }
  function mDoNome(nome, atual){
    var L=TECM[nome]; if(!L||!L.length) return atual;
    if(L.length===1) return L[0];
    var melhor=L[0], i;                 /* nome repetido: fica o mais perto do atual */
    for(i=1;i<L.length;i++) if(Math.abs(L[i]-atual)<Math.abs(melhor-atual)) melhor=L[i];
    return melhor;
  }

  /* ---- a ANCORA: o retrato do que o motor gravou ---- */
  function anc(c){
    if(!c._anc){
      var b = c._anc0 || { v:(c.sis||[]).slice(), lvl:_lvlDe(c), tecb:(c.TECB||[]).slice(),
                           imp:c.imp, habs:(c._habs0||c.HAB||[]).slice(),
                           sisBar:(c.sisBar||[]).map(function(r){return r.slice();}), sobra:c.sobra };
      c._anc = { v:b.v.slice(), lvl:b.lvl, tecb:b.tecb.slice(), imp:b.imp, habs:b.habs.slice(),
                 sisBar:b.sisBar.map(function(r){return r.slice();}), sobra:b.sobra, m:0 };
      c._anc.m = achaM(c, b);
    }
    return c._anc;
  }

  /* ---- o estado que esta na tela agora ---- */
  function agora(c, lvl){
    var a=anc(c), tecb = (c._tec!==undefined? c._tec : a.tecb);
    var nomeTec = (c._tecNome!==undefined? c._tecNome : c.TEC);
    return { lvl: lvl||_lvlDe(c), tecb: tecb, imp: c.imp,
             habs: (c._habs!==undefined? c._habs : a.habs),
             m: mDoNome(nomeTec, a.m) };
  }

  /* =========== o valor final: gravado + o delta da EQUACAO ===========
     Ancorar no gravado faz o card nunca escorregar do que o motor calculou,
     e o delta e a conta do motor. */
  function valores(c, lvl){
    var a=anc(c), v0=conta(c,{lvl:a.lvl,tecb:a.tecb,imp:a.imp,habs:a.habs,m:a.m}),
        v1=conta(c, agora(c,lvl)), out=[], i;
    for(i=0;i<26;i++) out[i] = Math.max(0, a.v[i] + (v1[i]-v0[i]));
    return out;
  }

  window.valsDeLvl = function(c,lvl){ try{ return valores(c,lvl); }catch(e){ return (c.sis||[]).slice(); } };

  window._trocaHabs = function(key,novas){
    var c=_card(key); if(!c) return;
    try{ _marca(key); }catch(e){}
    try{ _oriDe(c); }catch(e){}
    anc(c);
    c._habs = novas;
    var vals = valores(c, _lvlDe(c));
    c.sis = vals;
    c.arows.forEach(function(r){ r[3]=vals[r[0]]; r[4]=r[3]-r[2]; r[5]=r[3]; });
    c.b1 = notaDe(vals, c.arows);
    try{ c.b1n = (function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); }catch(e){}
    delete c._cp; delete c._n;
    traducaoViva(); render();
    try{ reabrir(key); }catch(e){}
  };


  /* ===== O BOTAO OTIMIZAR — ele RESTAURA, nao recalcula ====================
     Handoff de 03/08, ordem do Luis:
        "⚡ OTIMIZAR — a build do motor: RESTAURA, nao recalcula.
         ⚙ recalcular as barras (admin): redistribui com o que esta na tela."
     Medido em 15/08 (e o defeito e ANTERIOR a este patch): o botao estava
     redistribuindo as barras na hora, com o guloso da tela, e devolvendo build
     PIOR que a do motor em 3 de 3 cards:
        Bergkamp 102,83 -> 100,79 · Barcola 104,46 -> 102,85 · 103,78 -> 102,66
     Faz sentido que perca: o motor varre a exaustao, a tela nao.
     Agora ele devolve o retrato inteiro do que o motor gravou — barras, sobra,
     impeto, tecnico, habilidades e os 26 atributos. */
  window.otimizar = function(key){
    var c=_card(key); if(!c) return;
    var a=anc(c);
    delete c._habs; delete c._tec; delete c._tecNome; delete c._ori;
    c.imp = a.imp;
    c.sisBar = a.sisBar.map(function(r){ return r.slice(); });
    if(a.sobra!==undefined) c.sobra = a.sobra;
    c.sis = a.v.slice();
    if(c.arows) c.arows.forEach(function(r){ r[3]=c.sis[r[0]]; r[4]=r[3]-r[2]; r[5]=r[3]; });
    c.b1 = notaDe(c.sis, c.arows);
    try{ c.b1n = (function(A){var n=0,d=0,i,w;A=A||[];for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;n+=w*A[i][3];d+=w*A[i][2];}return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows); }catch(e){}
    delete c._cp; delete c._n;
    try{ traducaoViva(); }catch(e){}
    render(); try{ reabrir(key); }catch(e){}
  };

  /* guarda o retrato das habilidades ANTES de qualquer edicao */
  try{ for(var q=0;q<D.length;q++){ var _c=D[q]; if(!_c) continue;
    if(_c.HAB) _c._habs0 = _c.HAB.slice();
    if(_c.sis && _c.arows) _c._anc0 = { v:_c.sis.slice(), lvl:_lvlDe(_c), tecb:(_c.TECB||[]).slice(),
      imp:_c.imp, habs:(_c.HAB||[]).slice(),
      sisBar:(_c.sisBar||[]).map(function(r){return r.slice();}), sobra:_c.sobra };
  } }catch(e){}



  /* ===== RECALCULAR AS BARRAS — com a conta do motor ======================
     O botao "recalcular as barras" (o admin) chama a distOtima da casca, que
     decide onde por cada ponto JA CONTANDO o efeito da habilidade. Duas coisas
     estavam erradas ali, medidas em 15/08:
       1. o `bf` vinha do buffDe da casca — 62 habilidades e SEM as raras
       2. dentro da distOtima o efeito e aplicado pela aplicaBuff VELHA
          (% sobre o valor ja somado com impeto/tecnico, e travando em 99)
     Resultado: ele gastava ponto onde a habilidade ja cobria, e deixava de
     gastar onde ela nao chegava.

     Conserto: a mesma distOtima, com UMA linha trocada — a do efeito — e o
     buff certo (65 habilidades, com as raras). Se o trecho nao for encontrado,
     nada e alterado: fica como estava. */
  try{
    if (typeof distOtima === 'function') {
      var _src = distOtima.toString();
      var _velho = "const f=(v)=>{let w=Math.min(99,v)+A; if(B)w=aplicaBuff(w,B[0],B[1]);";
      var _novo  = "const f=(v)=>{const pre=Math.min(99,v); let w=pre+A; if(B)w=w+Math.ceil(pre*B[0]/100+B[1]);";
      if (_src.indexOf(_velho) >= 0) {
        window.distOtima = eval('(' + _src.split(_velho).join(_novo) + ')');
        window.DIST_OTIMA_CERTA = true;
      } else {
        window.DIST_OTIMA_CERTA = false;
      }
    }
  }catch(e){ window.DIST_OTIMA_CERTA = false; }

  window.otimizarBarras = function(key){
    var c=_card(key); if(!c||!c.base) return;
    try{ _marca(key); }catch(e){}
    var a=anc(c), st=agora(c, _lvlDe(c)), i;
    var nm=expand(c.nm), imp=impDoMotor(st.imp), tc=tecVet(st.tecb||[]);
    var add=new Array(26).fill(0);
    for(i=0;i<26;i++) add[i]=nm[i]+imp[i]+tc[i];
    var bf=buff(todasHabs(c, st.habs));           /* 65 habilidades, COM as raras */
    var orc=c.orc||0;
    var lvl=distOtima(c.base, c.arows, orc, add, bf);
    /* a regra de ouro do motor: nunca sobra ponto — o resto vai pro maior peso */
    var g=orc-gastoDe(lvl);
    if(g>0){
      var pw={}; MBK.forEach(function(b){
        pw[b]=Math.max.apply(null,[0].concat(c.arows.filter(function(r){return MB[b].indexOf(r[0])>=0;})
                                                    .map(function(r){return r[1];})));});
      var ordem=MBK.slice().sort(function(x,y){return pw[y]-pw[x];});
      for(var z=0;z<ordem.length;z++){
        var b=ordem[z];
        while((lvl[b]||0)<25){ var cst=ACCU[(lvl[b]||0)+1]-ACCU[lvl[b]||0];
          if(cst>g) break; lvl[b]=(lvl[b]||0)+1; g-=cst; }
        if(g<=0) break;
      }
    }
    _grava(c,lvl);
    try{ reabrir(key); }catch(e){}
  };

  /* ===== A PROVA — as duas contas ainda dao o mesmo resultado? =============
     Os casos abaixo foram calculados pelo PROPRIO equacao.py na hora de gerar
     esta tela. A conta daqui roda nos mesmos casos e compara.
     Mudou a formula do motor -> o esperado muda junto -> a tela acusa sozinha.
     (ordem do Luis, 15/08: "deixa pronto pra atualizar juntos") */
  var PROVA = __PROVA__;
  try{
    var falhou=[];
    (PROVA||[]).forEach(function(p,ix){
      var cf={ base:p.base, nm:p.nm, fab:[], raras:[], TECB:p.tecb };
      var v=conta(cf, {lvl:p.lvl, tecb:p.tecb, imp:'', habs:p.habs, m:p.m});
      for(var i=0;i<26;i++){
        if(Math.round(v[i])!==Math.round(p.esperado[i])){
          falhou.push({caso:ix, atributo:i, tela:Math.round(v[i]), motor:p.esperado[i]});
          break; }
      }
    });
    window.CONTA_DESALINHADA = falhou.length;
    window.CONTA_PROVAS = (PROVA||[]).length;
    if(falhou.length){
      console.warn('A CONTA DA TELA ESTA DESALINHADA DO MOTOR — '+falhou.length+
                   ' de '+PROVA.length+' casos de prova falharam', falhou);
      var aviso=document.createElement('div');
      aviso.style.cssText='position:fixed;left:8px;bottom:8px;z-index:99999;background:#a00;'+
        'color:#fff;font:12px system-ui;padding:6px 10px;border-radius:4px;max-width:320px';
      aviso.textContent='A conta da tela está desalinhada do motor ('+falhou.length+' de '+
        PROVA.length+' provas). O que você editar aqui pode não bater com a nota. '+
        'Detalhe no Console (F12).';
      if(document.body) document.body.appendChild(aviso);
      else document.addEventListener('DOMContentLoaded',function(){document.body.appendChild(aviso);});
    }
  }catch(e){ }

  window._contaDoMotor = { conta:conta, valores:valores, buff:buff, achaM:achaM,
                           impDoMotor:impDoMotor, anc:anc, agora:agora, mDoNome:mDoNome };
})();
'''




def _provas_da_equacao():
    """OS CASOS DE PROVA — calculados pelo PROPRIO equacao.py, na hora de gerar.

    Ordem do Luis (15/08): "deixa pronto pra atualizar juntos quando ir pra
    internet". Isto e a metade que nao precisa esperar a internet.

    A conta esta escrita duas vezes (Python no motor, JavaScript na tela). Em vez
    de confiar que as duas continuam iguais, o gerador CALCULA aqui, com as
    funcoes de verdade do equacao.py, o resultado de alguns casos — e manda os
    casos junto. A tela roda a conta dela nos mesmos casos quando carrega.

    Se as duas contas divergirem, o navegador avisa sozinho:
        - console.warn com o caso que falhou
        - window.CONTA_DESALINHADA com quantos falharam

    Mudou a formula do motor? O esperado muda junto — porque sai das funcoes
    dele. A tela acusa na hora, sem ninguem precisar lembrar.
    """
    try:
        import equacao as E
    except Exception:
        return []
    CASOS = [
        # base, niveis de barra, multiplicador, +1 do tecnico, impeto nativo, habilidades
        ([80]*26, {'shooting': 5},                  1.036,  ['finishing'],            [], []),
        ([95]*26, {'dribbling': 10},                1.0365, ['dribbling'],            [[2, 3]], ['Elástico']),
        ([70]*26, {'passing': 20, 'dribbling': 3},  1.0355, ['lowPass', 'stamina'],   [[4, 4]], ['Passe na medida']),
        ([99]*26, {},                               1.036,  ['speed'],                [[15, 5]], ['Chutes com decolagem']),
        ([88]*26, {'defending': 12},                1.03,   ['ballWinning'],          [], ['Interceptação', 'Carrinho']),
        ([60]*26, {'lowerBodyStrength': 25},        1.0341, [],                       [[17, 2]], []),
        ([97]*26, {'shooting': 8, 'passing': 8},    1.0365, ['finishing', 'curl'],    [[6, 4]], ['Folha seca', 'Malícia']),
        ([40]*26, {},                               1.03,   [],                       [], []),
    ]
    out = []
    for base, lvl, m, tecb, nm, habs in CASOS:
        try:
            pre = E.base_barras(list(base), lvl)
            v = [E._mult(x, m) for x in pre]
            # o +1 do tecnico: o indice sai do mapa POS do proprio equacao.py
            # (o `AM` e a ordem do efHub, NAO a ordem do vetor — usar AM.index
            #  aqui poe o +1 no atributo errado em 21 dos 26. Medido em 15/08.)
            for k in tecb:
                i = E.POS.get(k, -1)
                if i >= 0: v[i] += 1
            for i, x in nm: v[i] += x
            for i, (pct, flat) in E.buff_de(habs).items():
                v[i] = E.aplica_buff(v[i], pct, flat, pre[i])
            out.append({'base': list(base), 'lvl': lvl, 'm': m, 'tecb': tecb,
                        'nm': nm, 'habs': habs, 'esperado': [int(x) for x in v]})
        except Exception:
            continue
    return out


def patch_conta_do_motor(html):
    """15/08 — A TELA PASSA A CALCULAR COM A EQUACAO DO MOTOR.

    Ordem do Luis: *"tem que calcular de acordo com o que mexe, da mesma forma
    que o motor calcula"*. E o desenho, na palavra dele:
      "o motor e essa equacao com alteracao a exaustao das variaveis para achar
       a soma maxima; a tela e a aplicacao dela pontualmente."

    OS CINCO FUROS MEDIDOS EM 15/08 (12.163 linhas, Chromium headless):

      1. a habilidade usava a formula VELHA — % sobre o valor pos-tecnico e
         TRAVANDO em 99. O equacao.py (MUDANCA F) le BASE+BARRAS e NAO trava.
      2. as habilidades RARAS ficavam de fora da conta (`habsDe` esquece `c.raras`)
      3. o impeto nao era lido: procura " + " e o formato e " · " com os prefixos
         `de fabrica:` / `o motor pos:`   (5.313 linhas)
      4. o MULTIPLICADOR do tecnico nao existe na tela — trocar tecnico so
         trocava o +1 de dois atributos
      5. a tela conhece 62 habilidades; o HAB_EFEITOS_FINAL tem 65. Faltavam
         Desencadeador de ataques (73 cards), Impeto de Ataque (25), Sombra
         veloz (14) — por elas a tela nao fazia NADA

    O QUE MUDA, medido antes x depois:
      tirar habilidade .... 6 de 300 casos mudam
      trocar tecnico ..... 103 de 200 casos mudam   <- o multiplicador entrando
      as 3 fantasma ...... nao faziam nada; agora valem (Salah 100,37 -> 101,06)

    A ANCORA: valor = o que o MOTOR GRAVOU + (equacao com o insumo novo −
    equacao com o insumo de agora). Sem mexer em nada, a tela devolve
    exatamente o que o motor gravou — provado nas 12.163 linhas, 26 de 26.

    O multiplicador de cada linha e descoberto pela PROVA (qual dos 6 valores
    reproduz o que o motor gravou), nao por chute: fecha em 9.832 linhas; nas
    outras usa o do nome e marca `_mAprox`.

    ⛔ A casca de 3,1 MB nao e editada. ⛔ O motor nao e tocado.
    """
    if 'CONTA_DO_MOTOR_1508' in html:
        return html, 0
    try:
        import equacao as _E
        _H = json.load(open('HAB_EFEITOS_FINAL.json', encoding='utf-8'))
        habm = {}
        for v in _H.values():
            ef = {}
            for k, d in (v.get('efeito') or {}).items():
                ef[int(k)] = [float(d.get('pct', 0)), float(d.get('flat', 0))]
            habm[v['arquivo']] = [1 if v['tipo'] == 'rara' else 0, ef]
        _T = _E.carrega_tecnicos('tecnicos.json')
        tecm = {}
        for t in _T:
            tecm.setdefault(t['nome'], [])
            if round(t['m'], 6) not in tecm[t['nome']]:
                tecm[t['nome']].append(round(t['m'], 6))
        for n in tecm: tecm[n].sort()
    except Exception as e:
        print('CONTA DO MOTOR: nao consegui montar as tabelas (%s) — a tela fica como estava' % e)
        # 16/08 — o console tem milhares de linhas e o Luis nao acha nada la
        # dentro. A razao da falha passa a ficar num arquivo de uma linha.
        try:
            open('POR-QUE-A-CONTA-NAO-ENTROU.txt', 'w', encoding='utf-8').write(
                'A conta do motor NAO entrou na tela.\r\n\r\n'
                'motivo: %s: %s\r\n' % (type(e).__name__, e))
        except Exception:
            pass
        return html, 0

    # ---- A TRAVA DA EQUACAO REPETIDA -----------------------------------
    # A conta esta escrita DUAS VEZES: em Python (equacao.py, que o motor usa)
    # e em JavaScript (aqui). As TABELAS acompanham sozinhas — sao lidas do
    # arquivo a cada geracao. A CONTA nao.
    #
    # Foi assim que nasceu o defeito de 15/08: tiraram a trava do 99 do
    # equacao.py e a tela ficou para tras, calada, por dias.
    #
    # Entao: se o equacao.py mudar, esta geracao GRITA. Nao conserta sozinha —
    # avisa que alguem tem que vir aqui conferir a conta em JS.
    # 16/08 — md5 atualizado depois do conserto de ENCODING no equacao.py
    # (linhas 72 e 154 ganharam `encoding='utf-8'`). ⛔ A CONTA nao mudou —
    # so a forma de ler dois arquivos. O md5 velho era b35e1e3c...
    EQ_MD5 = '838cd5204a1193e4c93a3c5d0e2d06cc'
    try:
        import hashlib
        _md5 = hashlib.md5(open('equacao.py','rb').read()).hexdigest()
        if _md5 != EQ_MD5:
            print()
            print('=' * 64)
            print('  ATENCAO — O equacao.py MUDOU.')
            print('=' * 64)
            print('  md5 de agora .:', _md5)
            print('  md5 esperado .:', EQ_MD5)
            print()
            print('  A conta da TELA esta escrita em JavaScript aqui dentro')
            print('  (patch_conta_do_motor) e NAO muda sozinha.')
            print('  Confira se a mudanca do motor tem que entrar la tambem,')
            print('  e depois atualize o EQ_MD5 desta funcao.')
            print('=' * 64)
            print()
    except Exception:
        pass

    # ---- A FONTE DA CONTA DA TELA --------------------------------------
    # Ordem do Luis (15/08): "deixa pronto pra atualizar juntos quando ir pra
    # internet". Entao a conta da tela mora num ARQUIVO SO:
    #
    #     CONTA-DO-MOTOR.js   <- a fonte. E ele que vira o arquivo servido
    #                            pelo servidor quando o sistema for pra web:
    #                            a tela busca <script src="/conta-do-motor.js">
    #                            em vez de receber embutido, e ai passa a
    #                            atualizar junto, sem regerar HTML nenhum.
    #
    # Enquanto e HTML solto (disco e Drive), o arquivo e LIDO e embutido aqui.
    # Se ele nao existir, cai na copia que mora dentro deste .py — nunca falha.
    _fonte = 'CONTA-DO-MOTOR.js'
    if os.path.exists(_fonte):
        js_src = open(_fonte, encoding='utf-8').read()
        print('conta da tela ...........: %s (a FONTE)' % _fonte)
    else:
        js_src = _JS_CONTA_DO_MOTOR
        try:
            open(_fonte, 'w', encoding='utf-8').write(_JS_CONTA_DO_MOTOR)
            print('conta da tela ...........: criei o %s (agora ele e a FONTE)' % _fonte)
        except Exception:
            pass

    js = js_src \
        .replace('__HABM__', json.dumps(habm, ensure_ascii=False)) \
        .replace('__TECM__', json.dumps(tecm, ensure_ascii=False)) \
        .replace('__PROVA__', json.dumps(_provas_da_equacao(), ensure_ascii=False))
    tag = '<script>\n' + js + '\n</script>\n'
    if '</body>' in html:
        html = html.replace('</body>', tag + '</body>', 1)
    else:
        html = html + tag
    return html, len(habm)



# ============================================================================
#  O CABECALHO DO MODAL — O CAMPINHO   ·   15/08/2026
#
#  Ordem do Luis, com as fotos da ficha do jogo na mao:
#    "todos os cards tem esse campinho. A gente precisa implementar esse
#     campinho no nosso modal, ele tem que ir no topo, no cabecalho. E ai a
#     gente consegue tirar essa POSICAO NATIVA: se a gente poe o campinho, a
#     posicao nativa a gente poe EM CIMA do campinho, e do campinho as
#     posicoes que ele pode atuar. Ai a gente fica so com o 'nas funcoes'.
#     E ai a gente coloca botoes MAIORES que estao ai hoje, e a cor deles de
#     acordo com a PROFICIENCIA dessa posicao — no Pepe, botao de Zagueiro de
#     saida fica uma cor mais forte que o de combate, que e 108. E ai embaixo
#     vem tudo num bloquinho pequeno, o restante das informacoes, que e uma
#     informacao redundante: vem o estilo, vem os votos e tal."
#
#  O QUE MUDA
#    1  o `posLinha` inteiro e trocado: sai a linha "POSICAO NATIVA / TAMBEM
#       JOGA", entra o CAMPINHO (o mesmo desenho da ficha do jogo) com a
#       nativa marcada em azul e as de tambem-joga em verde, com as estrelas.
#    2  o nome da posicao nativa vai EM CIMA do campinho.
#    3  os botoes das funcoes ficam grandes, e a cor de cada um sai da
#       proficiencia: o melhor da carta em verde forte, os outros descendo.
#    4  as duas linhas `.mini` do cabecalho viram um BLOQUINHO pequeno.
#    5  some a linha grande "% DO TOPO DA FUNCAO" (o numero ja esta logo
#       abaixo, junto do bruto) — ordem dele: "so vou colocar 100% do topo".
#    6  o menu de habilidades passa a oferecer o POOL REAL da carta
#       (pool_disponivel do motor, 4.435 linhas tem), e nao so o que falta do
#       ideal da funcao — era por isso que "nao dava pra adicionar algumas".
#
#  ⛔ Nao toca em nota, em motor nem na casca de 3,1 MB.
# ============================================================================

_CSS_CAMPINHO = """
<script>
/* 15/08 — ESTE BLOCO SALVA O MODAL.
   O `_tecRep` (quais nomes de tecnico se repetem) e chamado pelo
   painelBuild ao montar a ficha. Estando so no fim do <body>, qualquer
   tropeco antes dele deixava a funcao sem existir — e ai o template do
   modal lancava ReferenceError e A FICHA NAO ABRIA EM CARD NENHUM.
   Agora ele e declarado aqui, sozinho, sem depender de nada: se o
   catalogo ainda nao existir, ele so devolve false. */
function _tecRep(n){
  try{
    if(!window._TR){
      if(typeof TECS === "undefined") return false;
      window._TR = {}; var v = {}, i;
      for(i=0;i<TECS.length;i++) v[TECS[i][0]] = (v[TECS[i][0]]||0)+1;
      for(i in v) if(v[i] > 1) window._TR[i] = 1;
    }
    return !!window._TR[n];
  }catch(e){ return false; }
}
if(typeof window.HABRARAS === "undefined") window.HABRARAS = {};
</script>
<style>
/* o que subiu para o painel de build nao se repete no grid abaixo.
   So some quando o painel existe — card sem orcamento nao tem painel. */
#box:has(.bpan) .secdup{display:none}
/* ---- o campinho ---- */
.cbwrap{display:flex;gap:14px;align-items:flex-start;margin:6px 0 2px;flex-wrap:wrap}
.cbcampo{width:100%;height:100%;box-sizing:border-box;display:flex;
 flex-direction:column;padding:10px 11px;border-radius:10px;
 background:linear-gradient(180deg,#1f7a4d,#14603b);border:1px solid #223429}
.cbnv{font-size:10.5px;font-weight:800;letter-spacing:.5px;color:#eafff3;text-align:center;
 margin-bottom:6px;text-transform:uppercase;line-height:1.3}
.cbnv b{color:#ffffff}
.cbl{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;margin-bottom:4px;
 align-items:stretch}
.cbp{display:block;text-align:center;font-size:11.5px;font-weight:800;border-radius:5px;
 padding:5px 0;border:1px solid transparent;line-height:1.25}
.cbv{display:block}
.cboff{color:#d8f0e2;background:#ffffff1f;border-color:#ffffff2e}
.cbsec{color:#0b2717;background:#e9f7ef;border-color:#ffffff}
.cbnat{color:#fff;background:#1553c8;border-color:#ffffff;box-shadow:0 0 0 2px #ffffff66}
.cbfab{box-shadow:inset 0 0 0 2px #ffd75e}
/* ---- os botoes das funcoes ---- */
.cbfns{flex:1 1 240px;min-width:210px}
.cbfnl{display:flex;flex-direction:column;gap:6px;margin-top:5px;align-items:flex-start}
.cbfn{display:flex;align-items:center;gap:10px;border-radius:9px;width:100%;max-width:330px;
 border:1px solid;font-weight:700;cursor:pointer;line-height:1.15}
.cbfn i{font-style:normal;flex:1 1 auto;text-align:left}
.cbfn u{text-decoration:none;font-size:10px;opacity:.85;font-weight:800;flex:0 0 76px;text-align:center}
.cbfn b{font-weight:800;letter-spacing:-.3px;flex:0 0 58px;text-align:right}
.cbfn:hover{filter:brightness(1.18)}
/* a funcao ABERTA fica AZUL — o MESMO azul da posicao acesa no campinho.
   Azul quer dizer "e esta aqui", nos dois lugares (Luis, 15/08). */
.cbfnq{background:#1553c8!important;border-color:#ffffff!important;
 color:#ffffff!important;box-shadow:0 0 0 2px #ffffff55}
.cbfnq i,.cbfnq u,.cbfnq b{color:#ffffff!important}
/* ---- o estilo de jogo, em destaque embaixo da foto ---- */
.fhdcol{flex:0 0 auto;width:158px;display:flex;flex-direction:column;
 align-items:stretch;gap:7px}
.fhdcol .fhdimg{width:100%}
.fhdmeio{flex:1 1 300px;min-width:250px;display:flex;flex-direction:column;gap:6px}
.fhd{align-items:stretch}
/* 15/08: o campo ocupa a COLUNA INTEIRA, de cima a baixo (Luis) */
.fhdcampo{flex:1 1 260px;min-width:230px;max-width:360px;display:flex;
 align-self:stretch}
.cbcampo .cbl{flex:1 1 0;min-height:0}
.cbcampo .cbp{height:100%;display:flex;align-items:center;
 justify-content:center;padding:0}
.cbcampo .cbv{height:100%}
.fhdbts{margin-top:2px}
.fhdnome{font-size:23px;font-weight:800;line-height:1.1;letter-spacing:-.4px;text-align:center}
.fhdcol>.mini{background:var(--surf2,#10161d);border:1px solid var(--line,#1e2732);
 border-radius:8px;padding:6px 9px;font-size:10.5px;line-height:1.55}
.fhdestbox{align-self:flex-start;padding:5px 14px;text-align:center;font-size:11.5px;font-weight:800;
 line-height:1.3;color:#0f3325;background:#8fd6b4;border:1px solid #4fae83;
 border-radius:7px;padding:4px 5px;box-sizing:border-box}
html[data-tema=escuro] .fhdestbox{color:#eaf2ff;background:#1e3a63;border-color:#4f7bbf}
@media(max-width:820px){.fhdcol{width:150px}.fhdcol .fhdimg{width:84px}.fhdnome{font-size:17px}.fhdestbox{font-size:10px}}
.secoff{display:none}
/* ---- o corpo e o pe ruim dentro do bloco Corpo ---- */
.corpotop{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 8px}
.corpotop span,.corpopr span{font-size:13px;font-weight:700;padding:7px 13px;
 border-radius:8px;background:var(--surf2,#141a22);line-height:1.2;
 border:1px solid var(--line,#2b3543)}
.corpopr{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:9px;padding-bottom:9px;
 border-bottom:1px dashed var(--line,#2b3543)}
.fhdbasico{margin-top:5px;padding-top:5px;border-top:1px solid #ffffff55;
 font-size:9.5px;font-weight:800;line-height:1.25;letter-spacing:.2px}
/* ---- o % do topo, logo abaixo da nota final ---- */
.fhddt{color:#1f7a52}
html[data-tema=escuro] .fhddt{color:#7fd1a0}
.fhdtopo{font-size:14px;font-weight:800;margin-top:1px;letter-spacing:-.2px}
/* ---- o bloquinho pequeno de baixo ---- */
.fhdid>.mini{background:var(--surf2,#10161d);border:1px solid var(--line,#1e2732);
 border-radius:8px;padding:6px 10px;font-size:10.5px;line-height:1.6}
/* ---- as abas do bloco de atributos, com o balaozinho ---- */
.encabas{display:flex;gap:6px;margin-bottom:10px;position:relative}
.encaba{flex:1;cursor:pointer;border-radius:7px;padding:7px 4px;font-size:11px;font-weight:800;
 background:transparent;border:1px solid var(--line,#2a3441);color:var(--txt3,#7d8794)}
.encaba:hover{border-color:#22c58b;color:var(--txt2,#c8d4e2)}
.encabaon{background:#17402f;border-color:#22c58b;color:#fff}
.encaba[data-tip]:hover::after{content:attr(data-tip);position:absolute;left:0;right:0;top:100%;
 margin-top:7px;z-index:70;background:#0d1218;border:1px solid #33445a;border-radius:9px;
 padding:10px 13px;font-size:11.5px;font-weight:500;line-height:1.6;color:#d3dde9;
 text-align:left;white-space:normal;box-shadow:0 10px 26px #000a}
/* o seletor do tecnico dentro do bloco "tecnico utilizado" */
.hbgrp .imp{display:block;margin-top:4px;padding-top:0;border-top:none}
.hbgrp .imp label{display:none}
.hbgrp .imp select{width:100%;max-width:100%}
.tecmais{font-size:10.5px;line-height:1.4;margin-top:3px;color:var(--txt3,#8fa4c4)}
/* as tres colunas de controle (alvo · vs alvo · pontos) num cinza mais
   escuro, para separar do que e do card (Luis, 15/08) */
.atgc>*:nth-child(n+10){color:#5f6b78}
.athead.atgc>*:nth-child(n+10){color:#4d5866}
/* o botao do ESTILO em azul — nao pode se confundir com o verde das funcoes */
.fhdestbox,.fhdmeio .fhdestbox{align-self:stretch;width:100%;box-sizing:border-box;min-height:52px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:10px 16px;font-size:15.5px;border-radius:9px;color:#ffffff!important;background:#1553c8!important;border:1px solid #ffffff!important}
html[data-tema=escuro] .fhdestbox{background:#1553c8!important}
.fhdnat b{font-size:14.5px;line-height:1.25}
.fhdnat .pslb{font-size:8.5px;opacity:.75}
.fhdnat .fhddt{font-size:11px;font-weight:700}
.fhdovr{line-height:1.75}
.fhdovr b{font-size:14px;margin-left:3px;color:inherit}
.fhdbtstt{font-size:10px;font-weight:800;letter-spacing:.6px;
 color:var(--txt3,#7d8794);margin:8px 0 5px;line-height:1.35}
.fhdbtstt span{display:block;font-size:9.5px;font-weight:600;
 letter-spacing:0;opacity:.8;text-transform:none}
.fhdnat{line-height:1.35}
.fhdsig{font-size:19px;font-weight:800;letter-spacing:-.3px;
 color:#1553c8;line-height:1.15;margin-top:1px}
html[data-tema=escuro] .fhdsig{color:#7fb0ff}
.fhdpos{font-size:12.5px;font-weight:700;line-height:1.3}
.fhdnat .fhddt{font-size:10.5px;font-weight:700;margin-top:2px}
/* ---- as travas de cada aba ---- */
[data-encmodo=motor] #box .brow,
[data-encmodo=insumos] #box .brow{pointer-events:none;opacity:.5}
[data-encmodo=motor] #box .bpan select,
[data-encmodo=motor] #box .bpan .chip b,
[data-encmodo=motor] #box .bpan .bbt{pointer-events:none;opacity:.5}
[data-encmodo=motor] #box .bpan button[onclick^="otimizarBarras"],
[data-encmodo=insumos] #box .bpan button[onclick^="otimizarBarras"],
[data-encmodo=motor] #box .bpan button[onclick^="restaurarMotor"],
[data-encmodo=insumos] #box .bpan button[onclick^="restaurarMotor"]{display:none}
[data-encmodo=insumos] #box .bpc1 .hbgrp:last-child{display:none}
</style>
"""

_JS_CAMPINHO = """
<script>
/* O CAMPINHO NO CABECALHO — 15/08. So apresentacao: nao encosta em nota. */
(function(){
 if(window.CAMPINHO_1508) return; window.CAMPINHO_1508 = true;
 /* o mesmo desenho da ficha do jogo, de cima (ataque) para baixo */
 var CAMPO=[["PE","CA","PD"],["","SA",""],["MLE","MO","MLD"],["","MC",""],
            ["","VOL",""],["LE","ZC","LD"],["","GK",""]];
 function irmAll(c){var b=String(c.id).split("@")[0];
  return D.filter(function(x){return x.id!=="MOLDE"&&String(x.id).split("@")[0]===b;});}
 function sig(p){ return (typeof SIGJ!=="undefined"&&SIGJ[p])?SIGJ[p]:p; }
 function nomeP(p){ return (typeof POSN!=="undefined"&&POSN[p])?POSN[p]:p; }
 /* A COR E O TAMANHO saem da PROFICIENCIA (ordem do Luis, 15/08):
    o de mais pontos vem maior e no verde mais forte; os outros vao clareando.
    *"nao e porque tem zagueiro de saida que o outro vai ser preto — pode ser
    um verde mais claro"* — a escala vai do verde medio ao verde CLARO, nunca
    ao escuro. E eles ficam um EMBAIXO do outro, nao lado a lado. */
 function cores(p){
  /* 15/08, 2o ajuste: a escala ia a um verde tao claro que o ultimo botao
     sumia no fundo. Agora vai do verde forte ao verde MEDIO, texto branco
     em todos e borda mais escura — nenhum se confunde com o fundo. */
  var l=Math.round(80-56*p), sat=Math.round(30+45*p);
  return {bg:"hsl(152 "+sat+"% "+l+"%)",
          bd:"hsl(152 "+(sat+16)+"% "+Math.round(l-15)+"%)",
          tx:"#ffffff",
          pad:(5+4*p).toFixed(1)+"px "+(9+4*p).toFixed(1)+"px",
          fn:(11+2.5*p).toFixed(1)+"px",
          fb:(13.5+4.5*p).toFixed(1)+"px"};
 }
 /* O NOME DO IMPETO NATIVO EM PORTUGUES (Luis, 15/08: "ele esta puxando o
    nome em ingles, tem que puxar o nome em portugues"). O efscout devolve
    "Stealing +3"; o `const CAT` da casca fala portugues. Casando o EFEITO
    atributo a atributo sai o nome certo — sem tabela de traducao a manter. */
 /* 15/08: a POSICAO NATIVA e do CARD, nao da linha. Em linha migrada ou
    de 2a posicao o `np` vem diferente, e o bloquinho mudava quando o
    Luis trocava de funcao. Aqui ela sai do irmao nativo — e nunca muda. */
 window.npFixo=function(c){
  try{
   var b=String(c.id).split("@")[0];
   var irm=D.filter(function(x){return x.id!=="MOLDE"&&String(x.id).split("@")[0]===b;});
   var nat=irm.find(function(x){return !x.MIG && !x.sec;});
   return (nat&&nat.np)||c.np;
  }catch(e){ return c.np; }
 };
 window.pimpPT=function(n,ef){
  try{
   if(!n) return n;
   if(CAT.some(function(x){return x[0]===n;})) return n;
   var v=expand(ef), i, j, f, ok, idx=[], nivel=0;
   /* 1) o nome exato, quando o efeito bate atributo a atributo */
   for(j=0;j<CAT.length;j++){ f=expand(CAT[j][2]); ok=true;
    for(i=0;i<26;i++) if(f[i]!==v[i]){ ok=false; break; }
    if(ok) return CAT[j][0]; }
   /* 2) o impeto nativo pode vir em nivel que nao existe no catalogo
         (o catalogo so tem +1/+2/+3 e o nativo chega a +5). Ai casa-se pelo
         CONJUNTO DE ATRIBUTOS e leva-se o nivel junto:
         "Technique +5" -> Tecnica (mesmos 4 atributos) -> "Tecnica +5". */
   for(i=0;i<26;i++) if(v[i]){ idx.push(i); if(v[i]>nivel) nivel=v[i]; }
   if(idx.length){
    for(j=0;j<CAT.length;j++){
     f=expand(CAT[j][2]); ok=true;
     for(i=0;i<26;i++) if((f[i]>0)!==(v[i]>0)){ ok=false; break; }
     if(ok) return String(CAT[j][0]).replace(/\\s*\\+\\d+\\s*$/,'')+' +'+nivel;
    }
   }
  }catch(e){}
  return n;
 };
 /* as duas pecas do cabecalho, cada uma na sua coluna (Luis, 15/08) */
 window.selPos=function(p,key){
  window._SELPOS=(window._SELPOS===p)?null:p;   /* clicar de novo desmarca */
  try{ reabrir(key); }catch(e){}
 };
 /* abrir uma ficha nova zera a escolha de posicao */
 try{ var _rb=window.reabrir;
  window.reabrir=function(k){ if(window._ULTK!==k){ window._SELPOS=null; window._ULTK=k; }
   return _rb.apply(this, arguments); }; }catch(e){}
 window.cbFuncoes=function(c){ posLinha(c); return window._cbFuncoes; };
 window.cbCampo  =function(c){ posLinha(c); return window._cbCampo;   };
 window.posLinha=function(c){
  var np=c.np, est={}, i;
  /* 15/08: o campinho segue a FUNCAO ABERTA, nao a nativa. Ordem do Luis:
     "quando eu clicar em Segundo atacante ele vai pro SA; quando eu clicar
      em Meia lateral atacante, la no campinho muda pra MLE ou MLD".
     As estrelinhas sairam. */
  var np=c.np, est={}, i, daFuncao={};
  (c.sp||[]).forEach(function(x){ if(x[0]!==np) est[x[0]]=x[1]; });
  /* 15/08: a posicao acesa. O `funcDaPos` depende do ESTILO do card, e por
     isso deixava o campinho apagado em card cujo estilo remapeia a posicao
     (o Luis pegou no Ruud Gullit "Armador criativo", em Segundo atacante).
     CONFERIDO no regra.json: cada posicao tem DUAS funcoes possiveis —
     REGRA["MO"] = [estilos, "Segundo atacante", "Meia ofensivo armador"].
     Entao a posicao desta ficha e: a que o estilo aponta OU, se nenhuma,
     qualquer posicao que tenha esta funcao entre as duas dela. */
  ["PE","CA","PD","SA","MLE","MO","MLD","MC","VOL","LE","ZC","LD","GK"]
   .forEach(function(p){ var f=null;
    try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
    /* 15/08 — CONFERIDO na base: o Hazard 88035823751302 tem np=MO e
       sec="MC/MLE/PD/PE/SA". MLD NAO esta la. O campinho acendia MLD ao abrir
       "Meia lateral atacante" so porque a REGRA diz que MLD gera essa funcao —
       mas a regra e da posicao, nao do card. So acende o que o card exerce. */
    if(!(p===np || est[p]!==undefined)) return;
    if(f && f===c.tipo){ daFuncao[p]=1; return; }
    try{ var r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null;
     if(r && (r[1]===c.tipo || r[2]===c.tipo)) daFuncao[p]=1;
     if(!daFuncao[p] && p==="SA" && typeof TJ_SA!=="undefined"){
      var q=TJ_SA[c.modelo]||"MO", r2=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[q]:null;
      if(r2 && (r2[1]===c.tipo || r2[2]===c.tipo)) daFuncao[p]=1; }
    }catch(e){}
   });
  if(!Object.keys(daFuncao).length){
   ["PE","CA","PD","SA","MLE","MO","MLD","MC","VOL","LE","ZC","LD","GK"]
    .forEach(function(p){ var f=null;
     try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
     if(f && f===c.tipo) daFuncao[p]=1;
     try{ var r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null;
      if(r && (r[1]===c.tipo||r[2]===c.tipo)) daFuncao[p]=1; }catch(e){}
    });
  }
  var _minhas=[np].concat(Object.keys(est));
  /* ===== A REGRA SIMETRICA DO CAMPINHO (Luis, 15/08) ====================
       clicou na FUNCAO  ->  acende as POSICOES onde ela pode ser exercida
       clicou na POSICAO ->  acende as FUNCOES que ela pode exercer
     O azul quer dizer sempre "isto corresponde ao que voce clicou". Um lado
     e a pergunta, o outro e a resposta.
       clica em Atacante infiltrador -> acendem SA e MAT no campo
       clica em SA -> acendem Atacante infiltrador e Meia ofensivo na lista
     Clicar numa POSICAO nao abre ficha: so mostra as opcoes. Quem abre e o
     clique na FUNCAO — assim quem entra pela posicao escolhe qual quer ver. */
  function funcsDaPos(p){
   var out=[], f=null, r=null;
   try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
   try{ r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null; }catch(e){}
   irmAll(c).forEach(function(y){
    if(y.tipo===f || (r && (r[1]===y.tipo || r[2]===y.tipo))){
     if(out.indexOf(y.tipo)<0) out.push(y.tipo); }
   });
   return out;
  }
  var _sel = (window._SELPOS && _minhas.indexOf(window._SELPOS)>=0) ? window._SELPOS : null;
  var _funcsSel = _sel ? funcsDaPos(_sel) : null;
  if(_sel){ daFuncao={}; daFuncao[_sel]=1; }
  var cel=function(p){
   if(!p) return "<i class=cbv></i>";
   var aqui=(daFuncao[p]===1), nat=(p===np), sec=(est[p]!==undefined), f=null, alvo=null;
   try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
   if(f) alvo=irmAll(c).find(function(y){return y.tipo===f;});
   var cls="cbp "+(aqui?"cbnat":((nat||sec)?"cbsec":"cboff"))+(nat?" cbfab":"");
   var t=aqui?("esta ficha: "+c.tipo):(nat?("posicao de fabrica: "+nomeP(p)):
        (sec?("tambem joga: "+nomeP(p)+(f?" — "+f:"")):nomeP(p)));
   var cl=(_minhas.indexOf(p)>=0)?(" onclick=\\"selPos('"+p+"','"+c.id+"|"+c.tipo+"')\\""
           +" style=\\"cursor:pointer\\""):"";
   return "<span class=\\""+cls+"\\""+cl+" title=\\""+t+"\\">"+sig(p)+"</span>";
  };
  var campo=CAMPO.map(function(l){return "<div class=cbl>"+l.map(cel).join("")+"</div>";}).join("");
  var irm=irmAll(c);
  irm.forEach(function(x){ if(x._n===undefined) x._n=nota(x); });
  irm.sort(function(a,b){ return b._n-a._n; });
  var mx=irm.length?irm[0]._n:0, mn=irm.length?irm[irm.length-1]._n:0;
  /* 15/08 — a sigla do botao e a POSICAO QUE ESTE CARD EXERCE, nao a da
     funcao. Luis: "ele so pode ser MLE, entao nao poe MLE/MLD". */
  function sigsDoCard(tipo){
   var out=[];
   _minhas.forEach(function(p){
    var f=null, r=null;
    try{ f=(typeof funcDaPos==="function")?funcDaPos(p,c.modelo):null; }catch(e){}
    try{ r=(typeof TJ_REGRA!=="undefined")?TJ_REGRA[p]:null; }catch(e){}
    if((f===tipo)||(r&&(r[1]===tipo||r[2]===tipo))){
     if(out.indexOf(sig(p))<0) out.push(sig(p)); }
   });
   if(!out.length) return (typeof sigDe==="function")?sigDe(tipo):"";
   return out.join("/");
  }
  var bts=irm.map(function(x,ix){
   /* o tom vem da POSICAO NA LISTA, nao da diferenca de nota: com oito
      funcoes, oito tons — a 1a no verde escuro e a ultima bem clara. */
   var p=(irm.length>1)?(1-(ix/(irm.length-1))):1, k=cores(p),
       aq=_funcsSel?(_funcsSel.indexOf(x.tipo)>=0):(x.tipo===c.tipo);
   return "<span class=\\"cbfn"+(aq?" cbfnq":"")+"\\" style=\\"background:"+k.bg+
    ";border-color:"+(aq?"#ffffff":k.bd)+";color:"+k.tx+";padding:"+k.pad+
    "\\" onclick=\\"reabrir('"+x.id+"|"+x.tipo+"')\\" title=\\""+x.tipo+
    (aq?" — e esta ficha":"")+"\\"><i style=\\"font-size:"+k.fn+"\\">"+x.tipo+
    "</i><u>"+sigsDoCard(x.tipo)+"</u><b style=\\"font-size:"+
    k.fb+"\\">"+x._n.toFixed(1).replace(".",",")+"</b></span>";
  }).join("");
  var titulo=irm.length>1?("ESTE CARD NAS "+irm.length+" FUN\\u00c7\\u00d5ES"):"A FUN\\u00c7\\u00c3O DESTE CARD";
  /* 15/08: primeiro as FUNCOES, e o campinho ao lado delas — ordem do
     Luis: "em vez de voce colocar o campo, voce coloca as funcoes; ai
     depois do lado das funcoes voce coloca o campo". */
  window._cbFuncoes="<div class=cbfnl>"+bts+"</div>";
  window._cbCampo="<div class=cbcampo><div class=cbnv>"+
   (_sel ? (nomeP(_sel)+" <b>"+sig(_sel)+"</b>")
         : (function(){var k=Object.keys(daFuncao);
            if(!k.length) return nomeP(np)+" <b>"+sig(np)+"</b>";
            return nomeP(k[0])+" <b>"+k.map(sig).join(" \u00b7 ")+"</b>";})())+
   "</div>"+campo+"</div>";
  return "<div class=cbwrap><div class=cbfns>"+
   "<div class=cbfnl>"+bts+"</div></div>"+
   "<div class=cbcampo><div class=cbnv>"+
   (function(){var k=Object.keys(daFuncao);
    if(!k.length) return nomeP(np)+" <b>"+sig(np)+"</b>";
    return nomeP(k[0])+" <b>"+k.map(sig).join(" \u00b7 ")+"</b>";})()+
   "</div>"+campo+"</div></div>";
 };
})();
</script>
"""



_JS_VISUAL_1508B = r"""<script>
/* ===================================================================
   O VISUAL DO MODAL — 15/08/2026, 2a leva (ordens do Luis)
   ⛔ SO APARENCIA. Nao encosta em nota, motor, banco nem chave de funcao.
      Ordem dele: "isso ai e so o visual, so o que aparece na tela".

    1  o nome do card maior
    2  a coluna da nota em BLOQUINHOS: "pontuacao total" no lugar de
       "nota final", "% do topo" no lugar de "% top", "Pode Melhorar"
    3  a aba "DO MEU JEITO" vira "LIVRE"
    4  o titulo ATRIBUTOS centralizado
    5  o FISICO num bloco so, medidas em TRES COLUNAS, e o ESTILO DE
       JOGO DA IA na quarta coluna
    6  o titulo do campinho: o nome da posicao por extenso e sem negrito,
       so a sigla em negrito
    7  as tres colunas do painel com a MESMA largura (a distribuicao dos
       pontos ocupava o espaco das outras duas)
    8  IMPETO: quem nao tem vaga (sl 0/0) nao mostra mais o campo
       ADICIONADO — nao ha o que adicionar
    9  o botao do condicional vira hexagono + os tres degraus (+1/+2/+3),
       com o degrau atual aceso. Clicar vai DIRETO no degrau (antes o
       botao ciclava 1->2->3->1, e parecia que apagava coisa).
       ⚠️ o rotulo antigo dizia `degrau ${cmode||1}` e o cmode interno e
       0/1/2 — degrau 1 e 2 mostravam os DOIS o numero 1. Agora bate.
   10  o condicional passa a funcionar tambem na aba MAXIMO — e so ele
   11  TECNICO: a caixa fechada mostra so o NOME; a lista aberta continua
       com os atributos (senao os tres Koeman viram um so). O +1 vai
       para uma linha por atributo
   12  o efeito do impeto: um atributo por linha

   Feito por JS depois que a ficha monta (e nao por replace na casca)
   porque a ficha e REMONTADA a cada abrir / trocar de aba. Tudo dentro
   de try/catch: se algo aqui falhar, a ficha continua de pe.
   =================================================================== */
(function(){
 if(window.VISUAL_1508B) return; window.VISUAL_1508B = true;

 var st = document.createElement('style');
 st.textContent =
  '.fhdnome>div{font-size:27px!important}'
 +'.cbnv{font-weight:600!important}.cbnv b{font-weight:800!important}'
 +'.fhdnota{display:flex;flex-direction:column;gap:7px;align-items:stretch}'
 +'.pvbox{background:var(--surf2,#dae3de);border:1px solid var(--line,#bfcec7);'
 +'border-radius:10px;padding:8px 10px;text-align:center}'
 +'.pvbox .fhdl{display:block}'
 +'h3.pvcentro{text-align:center}'
 /* 15/08: as duas primeiras colunas sobravam espaco a direita e a
    distribuicao dos pontos ficava espremida, ruim de arrastar a barra.
    Agora elas ficam do tamanho do conteudo e o que sobra vai todo para
    a distribuicao. */
 +'@media(min-width:1101px){#box .bptrio,body .bptrio{'
 +'grid-template-columns:fit-content(250px) fit-content(235px) minmax(0,1fr)!important}}'
 +'.pvfis{grid-column:1/-1!important;display:grid!important;'
 +'grid-template-columns:1fr 1fr 1fr 0.85fr;gap:16px;align-items:start}'
 +'.pvfis .pvtopo{grid-column:1/-1}.pvfis .pvtotal{grid-column:1/4}'
 +'.pvcol{min-width:0}'
 +'.pvcol .fzh,.pvcol .fzr{grid-template-columns:1fr 32px 30px 34px 44px!important;'
 +'gap:5px!important;font-size:11px!important}'
 +'.pvcol .fzh{font-size:8.5px!important;letter-spacing:0!important;line-height:1.25}'
 +'.pvfis .sec{margin:0!important;padding:0!important;background:none!important;border:none!important}'
 +'.pvcond{margin-top:8px;padding-top:8px;border-top:1px dashed var(--line,#bfcec7)}'
 +'.pvcondtt{display:flex;align-items:center;gap:6px;font-size:10px;letter-spacing:.5px;'
 +'text-transform:uppercase;color:var(--txt2,#4a6159);margin-bottom:6px}'
 +'.pvhex{width:17px;height:19px;display:block;flex:none}'
 +'.pvdeg{display:flex;gap:5px}'
 +'.pvdeg button{flex:1;padding:5px 0;border-radius:7px;font-size:12px;font-weight:800;'
 +'background:var(--surf2,#dae3de);border:1px solid var(--line,#bfcec7);'
 +'color:var(--txt2,#4a6159);cursor:pointer;line-height:1.1}'
 +'.pvdeg button.on{background:#f0a531;border-color:#d38c1c;color:#3a2500}'
 +'[data-encmodo] #box .pvdeg button{pointer-events:auto!important;opacity:1!important}'
 +'.pvtec select{width:100%;font-weight:800}'
 +'.pvtecl{font-size:11px;color:var(--txt2,#4a6159);margin-top:4px;line-height:1.5}'
 +'.pvtecl b{color:var(--txt,#16302a)}'
 +'.impef .pvef{display:block}'
 +'#box.pvtrava .sec,#box.pvtrava .bpan{opacity:.28;pointer-events:none;filter:grayscale(.5)}'
 +'#box.pvtrava .fhdestbox .fhdbasico{display:none!important}'
 +'.pvpede{background:var(--surf2,#dae3de);border:1px solid var(--line,#bfcec7);'
 +'border-radius:12px;padding:14px 16px;margin:10px 0 14px;text-align:center}'
 +'.pvpedet{font-size:13.5px;font-weight:800;color:var(--txt,#16302a)}'
 +'.pvpedes{font-size:11.5px;color:var(--txt2,#4a6159);margin-top:3px}'
 +'.pvpedeb{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:11px}'
 +'.pvpedeb button{padding:9px 16px;border-radius:9px;font-size:13px;font-weight:800;'
 +'background:#17402f;color:#fff;border:1px solid #0f2c20;cursor:pointer}'
 +'.pvpedeb button b{font-weight:900;margin-left:8px}'
 +'.pvbas{display:inline-block;font-size:8.5px;font-weight:800;letter-spacing:.4px;'
 +'background:#0000002e;color:inherit;padding:1px 5px;border-radius:5px;margin-left:6px;'
 +'vertical-align:middle;opacity:.9}'
 /* 16/08 — a etiqueta vira COLUNA dentro do botao da funcao: largura fixa
    para as quatro colunas (nome · basico · posicao · nota) baterem em todas
    as linhas, e invisivel quando o estilo liga. */
 +'.cbfn .pvbas{flex:0 0 54px;margin-left:0;text-align:center;padding:1px 0}'
 +'.cbfn .pvbasvazio{background:transparent;opacity:0}'
 +'@media(max-width:1100px){.pvfis{grid-template-columns:1fr 1fr}.pvfis .pvtotal{grid-column:1/-1}}'
 /* ================= O CELULAR — 15/08 =========================
    Medido em 390x844: a 3a coluna do painel ficava com LARGURA ZERO
    (a regra do desktop matava o responsivo da casca), o campinho
    colapsava com as posicoes uma por cima da outra, e a coluna da
    nota gastava 158px de altura. Aqui vai o pacote do celular. */
 +'@media(max-width:820px){'
   /* o painel empilha, e a distribuicao dos pontos ocupa a largura toda */
 +'#box .bptrio,body .bptrio{grid-template-columns:minmax(0,1fr)!important;gap:12px}'
 +'.bptrio .bpc3{grid-column:auto!important}'
   /* o campinho para de colapsar: cada linha com altura minima */
 +'.fhdcampo{align-self:auto!important;max-width:none!important;width:100%}'
 +'.cbcampo{height:auto!important}'
 +'.cbcampo .cbl{flex:none!important;min-height:32px}'
 +'.cbcampo .cbp{height:32px!important;font-size:11px}'
   /* a nota vira uma faixa de tres, em vez de tres blocos empilhados */
 +'.fhdnota{flex-direction:row!important;align-items:stretch;gap:6px}'
 +'.fhdnota .pvbox{flex:1;padding:7px 4px}'
 +'.fhdnota .fhdn{font-size:26px}'
 +'.fhdnota .fhdl{font-size:8.5px}'
   /* a coluna do nome ocupa a largura toda e nao deixa buraco do lado */
 +'.fhdcol{width:100%!important;flex-direction:row;align-items:center;gap:10px;flex-wrap:wrap}'
 +'.fhdnome{text-align:left;flex:1 1 100%}'
 +'.fhdnome>div{font-size:22px!important}'
 +'.fhdcol>.mini{flex:1 1 auto}'
   /* o fisico em duas colunas e o resto respirando */
 +'.pvfis{grid-template-columns:1fr 1fr!important;gap:10px}'
 +'.pvfis .pvtotal{grid-column:1/-1!important}'
 +'.pvcol .fzh,.pvcol .fzr{grid-template-columns:1fr 26px 26px 30px 40px!important;font-size:10.5px!important}'
   /* as tres abas cabem sem quebrar */
 +'.encabas{display:grid!important;grid-template-columns:1fr 1fr 1fr;gap:5px}'
 +'.encaba{padding:8px 2px!important;font-size:10px!important;line-height:1.2}'
 +'.pvpedeb{flex-direction:column}'
 +'.pvpedeb button{width:100%}'
 +'}';
 document.head.appendChild(st);

 var HEX = '<svg class=pvhex viewBox="0 0 24 27" aria-hidden="true">'
         + '<polygon points="12,1 23,7.5 23,19.5 12,26 1,19.5 1,7.5" fill="#f0a531" '
         + 'stroke="#8a5a10" stroke-width="1.4"/></svg>';

 /* A CHAVE DA FICHA ABERTA.
    ⚠️ 15/08: o `CUR` da casca e um `let` no topo do script — ele NAO vira
    `window.CUR`, e ler dali devolvia undefined. Aqui se tenta o proprio
    `CUR` (visivel no escopo global) e, se falhar, tira a chave do onclick
    dos botoes das abas, que sempre a carregam. */
 function chave(){
  try{ if(typeof CUR !== 'undefined' && CUR) return CUR; }catch(e){}
  if(window.CUR) return window.CUR;
  var b = document.querySelector('.encaba[onclick]');
  if(b){
   var m = String(b.getAttribute('onclick') || '').match(/,\s*'([^']+)'\s*\)/);
   if(m) return m[1];
  }
  return null;
 }
 function cardAberto(){
  var k = chave();
  if(!k) return null;
  try{ return (typeof _card === 'function') ? _card(k) : null; }catch(e){ return null; }
 }

 /* ---- 3 · a aba ------------------------------------------------- */
 /* ⛔ 16/08 — ESTE RENOMEADOR FOI REMOVIDO. NAO REPOR.
    Ele reescrevia o texto dos botoes DEPOIS de desenhados, para trocar
    "COM O QUE EU TENHO" por "MEU CARD" e "DO MEU JEITO" por "LIVRE".
    Era o TERCEIRO lugar mexendo na mesma barra de abas — junto com a
    definicao do `_modoBar` no patch_edicao_viva (removida hoje) e a do
    CONTA-DO-MOTOR.js.

    Ordem do Luis, 16/08: *"por que que tem duas versoes? A gente nao pode
    trabalhar com coisa pela metade, so da problema."*

    Agora QUEM DECIDE O ROTULO DA ABA E UM LUGAR SO: o `window._modoBar`
    do `patch_modal_1608b`, que desenha as DUAS abas
    (⚡ MAXIMO POSSIVEL e ⚙ MEU CARD) ja com o nome certo. */
 function abas(){ /* sem efeito: o rotulo nasce certo no _modoBar */ }

 /* ---- 2 · a coluna da nota -------------------------------------- */
 function nota(){
  var nt = document.querySelector('.fhdnota');
  if(!nt || nt.dataset.pv === '1') return;
  var num = nt.querySelector('.fhdn'), lab = nt.querySelector('.fhdl'),
      top = nt.querySelector('.fhdtopo'), mel = nt.querySelector('.fhdmel');
  if(!num || !lab) return;
  lab.textContent = 'pontuação total';
  if(top) top.innerHTML = top.innerHTML.replace('% top', '% do topo');
  if(mel) mel.innerHTML = mel.innerHTML.replace('pode melhorar', 'Pode Melhorar');
  var cx = function(a, b2){ var d = document.createElement('div'); d.className = 'pvbox';
                            if(a) d.appendChild(a); if(b2) d.appendChild(b2); return d; };
  nt.appendChild(cx(num, lab));
  if(top) nt.appendChild(cx(top));
  if(mel) nt.appendChild(cx(mel));
  nt.dataset.pv = '1';
 }

 /* ---- 4 · o titulo ---------------------------------------------- */
 function titulos(){
  var h = document.querySelectorAll('.sec>h3'), i;
  for(i=0;i<h.length;i++)
   if(/^Atributos$/i.test(h[i].textContent.trim())) h[i].classList.add('pvcentro');
 }

 /* ---- 5 · o FISICO em tres colunas + o ESTILO DE JOGO DA IA ------
    A coluna DIRECAO sai: a "nota da medida" (+1 / -2 / 0) ja da o
    resultado, e sem ela cada medida cabe numa linha so. */
 function fisico(){
  var secs = document.querySelectorAll('.sec'), fis = null, ia = null, i, t;
  for(i=0;i<secs.length;i++){
   t = secs[i].querySelector('h3'); if(!t) continue;
   t = t.textContent.trim();
   if(/^F[ií]sico$/i.test(t)) fis = secs[i];
   if(/Estilo de jogo da IA/i.test(t)) ia = secs[i];
  }
  if(!fis || fis.dataset.pv === '1') return;
  var h3 = fis.querySelector('h3'),
      topo = fis.querySelectorAll('.corpotop,.corpopr'),
      head = fis.querySelector('.fzh'),
      rows = [].slice.call(fis.querySelectorAll('.fzr'));
  if(!h3 || !head || rows.length < 4) return;
  var total = rows.pop();
  var tira = function(el){ var c = el.children; if(c[1]) c[1].remove(); };
  tira(head); rows.forEach(tira);
  fis.dataset.pv = '1'; fis.classList.add('pvfis');
  var wt = document.createElement('div'); wt.className = 'pvtopo';
  wt.appendChild(h3);
  for(i=0;i<topo.length;i++) wt.appendChild(topo[i]);
  fis.innerHTML = ''; fis.appendChild(wt);
  var per = Math.ceil(rows.length / 3), j, col;
  for(i=0;i<3;i++){
   col = document.createElement('div'); col.className = 'pvcol';
   col.appendChild(head.cloneNode(true));
   for(j=i*per;j<(i+1)*per && j<rows.length;j++) col.appendChild(rows[j]);
   fis.appendChild(col);
  }
  if(ia){ col = document.createElement('div'); col.className = 'pvcol';
          col.appendChild(ia); fis.appendChild(col); }
  if(total){ total.classList.add('pvtotal'); fis.appendChild(total); }
 }

 /* ---- 9 e 10 · O DEGRAU DO CONDICIONAL --------------------------
    ⚠️ MEDIDO EM 15/08 — a tela aplicava a build ERRADA, deslocada de um.
    O motor grava as builds em `c.CD` nas chaves "2" e "3" (o degrau 1 e a
    propria build base). A tela procurava CD[cmode] com cmode 0/1/2:
        degrau 1 -> base        certo
        degrau 2 -> CD["1"] nao existe -> caia na base   ERRADO
        degrau 3 -> CD["2"]                              ERRADO
        CD["3"] nunca era usada
    Medido no Can Uzun / Meia ofensivo:  111,6 · 111,6 · 132,2
    quando o gravado e                   111,6 · 132,2 · 151,7

    E o motor esta CERTO: ele roda `build_completo2` de novo para cada
    degrau (roda_lote_v6.py, `for _grau in (2,3)`) — reotimiza barras,
    tecnico e habilidades. Medido nas 653 linhas com CD: 635 tem b1
    diferente por degrau, 81 mudam de barra, 69 de tecnico, 39 de
    habilidade. So 18 dao o mesmo b1 (o condicional nao pega atributo com
    peso naquela funcao) — e foi num desses que eu tropecei primeiro.

    ⛔ O RANKING continua no degrau 1, sempre. Isto so vale quando o Luis
    clica no degrau dentro da ficha. */
 function _cdBuild(c, degrau){
  if(degrau > 1 && c.CD && c.CD[String(degrau)]) return c.CD[String(degrau)];
  return c._cdBase || null;
 }
 window.setCondCard = function(key, degrau){
  try{
   var c = (typeof _card === 'function') ? _card(key) : null;
   if(!c) return;
   if(typeof _marca === 'function') _marca(key);
   /* guarda a build de fabrica na primeira troca, para poder voltar ao 1 */
   if(!c._cdBase) c._cdBase = { b1:c.b1, b1n:c.b1n, v:(c.sis||[]).slice(),
     bar:JSON.parse(JSON.stringify(c.sisBar||[])), TEC:c.TEC, TECB:c.TECB,
     HAB:(c.adds||[]).slice(), sobra:c.sobra };
   var s = _cdBuild(c, degrau);
   if(s){
    if(s.v)   c.sis    = s.v.slice();
    if(s.bar) c.sisBar = JSON.parse(JSON.stringify(s.bar));
    if(s.HAB) c.adds   = s.HAB.slice();
    if(s.TEC !== undefined)  c.TEC  = s.TEC;
    if(s.TECB !== undefined) c.TECB = s.TECB;
    if(s.sobra !== undefined) c.sobra = s.sobra;
    if(s.b1  !== undefined) c.b1  = s.b1;
    if(s.b1n !== undefined) c.b1n = s.b1n;
    /* a nota e a tabela leem do arows. ⚠️ a linha e
       [indice, peso, alvo, valor, valor-alvo] — o 1o campo e o INDICE do
       atributo, NAO o nome (tentei pelo nome e nunca casava). */
    if(c.arows && s.v) c.arows.forEach(function(r){
      var at = r[0];
      if(typeof at === 'string' && typeof ATTRS !== 'undefined') at = ATTRS.indexOf(at);
      if(typeof at === 'number' && at >= 0 && s.v[at] !== undefined){
        r[3] = s.v[at]; r[4] = r[3] - r[2];
      }
    });
   }
   c.cmode = degrau - 1;              /* o campo antigo segue coerente */
   ['_n','_cp','_fb','_ia','_pr','_ESC','_notaMot'].forEach(function(k){ delete c[k]; });
   if(typeof traducaoViva === 'function') traducaoViva();
   if(typeof render === 'function') render();
   if(typeof reabrir === 'function') reabrir(key);
  }catch(e){ console.warn('setCondCard', e); }
 };

 /* ---- 8 · 9 · 12 · o bloco do IMPETO ----------------------------- */
 function impeto(){
  var K = chave(), c = null;
  c = cardAberto();

  /* 8 — sem vaga, sem campo "adicionado" */
  if(c && c.sl && c.sl[0] === 0 && c.sl[1] === 0){
   var subs = document.querySelectorAll('.iasub'), i, s;
   for(i=0;i<subs.length;i++){
    s = subs[i];
    if(/adicionado/i.test(s.textContent) && s.dataset.pv !== '1'){
     var ul = s.nextElementSibling;
     s.remove(); if(ul && ul.tagName === 'UL') ul.remove();
    }
   }
  }

  /* 12 — o efeito do impeto, um atributo por linha */
  var efs = document.querySelectorAll('.impef'), k, e, partes;
  for(k=0;k<efs.length;k++){
   e = efs[k];
   if(e.dataset.pv === '1') continue;
   e.dataset.pv = '1';
   partes = e.textContent.split(' · ');
   if(partes.length > 1)
    e.innerHTML = partes.map(function(x){
     return '<span class=pvef>' + x + '</span>'; }).join('');
  }

  /* 9 — o botao do condicional */
  var bts = document.querySelectorAll('button.bbt'), b, box, grau, j, h = '', K2;
  for(j=0;j<bts.length;j++){
   b = bts[j];
   if(!/condicional/i.test(b.textContent)) continue;
   box = b.parentElement;
   if(box.dataset.pv === '1') continue;
   box.dataset.pv = '1';
   /* a chave sai do onclick do proprio botao: o window.CUR ainda vem
      nulo quando a ficha esta sendo montada */
   K2 = (String(b.getAttribute('onclick')||'').match(/'([^']+)'/) || [])[1] || K;
   if(!c){ try{ c = _card(K2); }catch(e){} }
   grau = ((c && c.cmode) || 0) + 1;
   h = '<div class=pvcondtt>' + HEX + '<span>ímpeto condicional</span></div><div class=pvdeg>';
   for(var n=1;n<=3;n++)
    h += '<button class="' + (n === grau ? 'on' : '') + '" title="degrau ' + n
       + ' do ímpeto condicional" onclick="setCondCard(\'' + K2 + '\',' + n + ')">+'
       + n + '</button>';
   h += '</div>';
   box.className = 'hbgrp pvcond';
   box.innerHTML = h;
  }
 }

 /* ---- 11 · o TECNICO --------------------------------------------- */
 function tecnico(){
  var sel = null, ss = document.querySelectorAll('#box select'), i;
  for(i=0;i<ss.length;i++)
   if(/trocaTec/.test(ss[i].getAttribute('onchange') || '')){ sel = ss[i]; break; }
  if(!sel) return;
  var grp = sel.closest('.hbgrp');
  if(!grp || grp.dataset.pv === '1') return;
  grp.dataset.pv = '1'; grp.classList.add('pvtec');

  var op = sel.options[sel.selectedIndex];
  if(op && op.value !== ''){
   var cheio = op.text, corte = cheio.split(' · ');
   /* fechado mostra so o nome; ao abrir, a lista volta inteira —
      senao os tres Koeman viram um so */
   op.dataset.cheio = cheio;
   op.text = corte[0];
   var volta = function(){ if(op.dataset.cheio) op.text = op.dataset.cheio; };
   var corta = function(){ if(op.dataset.cheio) op.text = op.dataset.cheio.split(' · ')[0]; };
   sel.addEventListener('mousedown', volta);
   sel.addEventListener('focus', volta);
   sel.addEventListener('blur', corta);
   sel.addEventListener('change', corta);
  }

  /* o "+1 X · Y" vira uma linha por atributo */
  var kids = grp.querySelectorAll('div,span'), e, attrs = null, velha = null;
  for(i=0;i<kids.length;i++){
   e = kids[i];
   if(e.children.length === 0 && /^\+1\s+\S/.test(e.textContent.trim())){ velha = e; break; }
  }
  if(velha){
   attrs = velha.textContent.trim().replace(/^\+1\s*/, '').split(' · ');
   var alvo = velha.parentElement, html = '';
   for(i=0;i<attrs.length;i++)
    if(attrs[i].trim()) html += '<div class=pvtecl>+1 em <b>' + attrs[i].trim() + '</b></div>';
   velha.remove();
   if(html){ var d = document.createElement('div'); d.innerHTML = html; alvo.appendChild(d); }
  }
 }

 /* ---- 13 · CLICOU NUMA POSICAO: A FICHA TRAVA E PEDE A FUNCAO ----
    Ordem do Luis, 15/08: *"se ele clicar em MAT, ele pode ser Meia
    ofensivo ou Atacante infiltrador. O que nao pode e ele olhar la
    embaixo e achar que aquela ficha e a de MAT"*. Antes, clicar numa
    posicao acendia as funcoes mas deixava a ficha da funcao ANTERIOR
    montada embaixo — induzindo ao erro.
    Agora a ficha esmaece e aparece o aviso com as funcoes daquela
    posicao, cada uma com a sua nota. So volta quando ele escolher.
    ⛔ So apresentacao: nada de nota, nem de motor.
    As funcoes saem dos BOTOES JA ACESOS pelo campinho (classe cbfnq) —
    mesma fonte da tela, para o aviso nunca discordar do que esta ali. */
 /* escolheu a funcao: a marcacao da posicao sai e a ficha abre inteira */
 window._pvEscolhe = function(k){
  window._SELPOS = null;
  var b = document.querySelector('#box');
  if(b) b.classList.remove('pvtrava');
  var a = document.querySelector('.pvpede');
  if(a) a.remove();
  try{ abrir(k); }catch(e){}
 };

 function pedeFuncao(){
  var box = document.querySelector('#box') || document.body;
  var velho = document.querySelector('.pvpede');
  if(velho) velho.remove();
  box.classList.remove('pvtrava');
  var sel = window._SELPOS;
  if(!sel) return;
  var fhd = document.querySelector('.fhd');
  if(!fhd || !fhd.parentElement) return;
  var acesos = document.querySelectorAll('.cbfn.cbfnq'), i, b, nome, nota_, sig, out = [];
  for(i=0;i<acesos.length;i++){
   b = acesos[i];
   nome = (b.querySelector('i') || {}).textContent || '';
   nota_ = (b.querySelector('b') || {}).textContent || '';
   if(nome) out.push([nome.trim(), nota_.trim(), !!b.querySelector('.pvbas')]);
  }
  if(!out.length) return;
  /* uma funcao so nessa posicao: nao ha o que escolher — abre direto
     (Luis, 15/08: "quando o cara faz uma funcao so nao precisa escolher") */
  if(out.length === 1){
   var c1 = cardAberto();
   if(c1 && c1.tipo !== out[0][0]){ window._pvEscolhe(c1.id + '|' + out[0][0]); return; }
   window._SELPOS = null;
   return;
  }
  sig = (typeof SIGJ !== 'undefined' && SIGJ[sel]) || sel;
  var c = null;
  c = cardAberto();
  var id = c ? c.id : '';
  var d = document.createElement('div');
  d.className = 'pvpede';
  d.innerHTML = '<div class=pvpedet>' + sig + ' — '
    + (out.length > 1 ? ('aqui ele pode fazer ' + out.length + ' funções')
                      : 'aqui ele faz uma função')
    + '</div><div class=pvpedes>'
    + (out.length > 1 ? 'cada uma tem build e nota própria. Escolha qual você quer ver:'
                      : 'clique para ver a ficha dela:')
    + '</div><div class=pvpedeb>'
    + out.map(function(x){
        return '<button onclick="_pvEscolhe(\'' + id + '|' + x[0].replace(/'/g, "\\'")
             + '\')">' + x[0] + (x[1] ? '<b>' + x[1] + '</b>' : '')
             + (x[2] ? '<span class=pvbas>BÁSICO</span>' : '') + '</button>';
      }).join('')
    + '</div>';
  fhd.parentElement.insertBefore(d, fhd.nextSibling);
  box.classList.add('pvtrava');
 }

 /* ---- 14 · A MARCA "BASICO" NA LISTA DAS FUNCOES -----------------
    Luis, 15/08: para saber em quais funcoes o estilo nao liga ele tinha
    de abrir uma por uma, porque a tarja so fala da ficha aberta. Agora
    cada botao da lista leva a marca, e ele ve todas de uma vez.
    ⛔ So etiqueta: a nota nao muda (o +1 continua onde ja estava). */
 function basicoNaLista(){
  var bts = document.querySelectorAll('.cbfn'), i, b, nome, irm, c = null;
  if(!bts.length) return;
  c = cardAberto();
  if(!c || typeof D === 'undefined' || typeof estiloAtiva !== 'function') return;
  var base = String(c.id).split('@')[0];
  for(i=0;i<bts.length;i++){
   b = bts[i];
   if(b.querySelector('.pvbas')) continue;
   nome = (b.querySelector('i') || {}).textContent;
   if(!nome) continue;
   nome = nome.trim();
   irm = null;
   for(var j=0;j<D.length;j++)
    if(D[j].id !== 'MOLDE' && String(D[j].id).split('@')[0] === base && D[j].tipo === nome){
     irm = D[j]; break; }
   /* 16/08 — ORDEM DO LUIS: a etiqueta era ANEXADA no fim do botao, depois
      da nota, e desalinhava a lista inteira: o que era tres colunas virava
      quatro so nas linhas que tinham BASICO, e o nome quebrava em duas
      linhas. *"agora vai ficar o nome na primeira da esquerda, basico ou
      vazio na segunda, na terceira a posicao e na quarta a nota."*
      Entao a coluna existe SEMPRE — vazia quando o estilo liga — e entra
      ANTES da posicao, nao no fim. */
   var s = document.createElement('span');
   if(irm && !estiloAtiva(irm)){
    s.className = 'pvbas';
    s.textContent = 'BÁSICO';
    s.title = 'o estilo de jogo dele não liga nesta posição';
   } else {
    s.className = 'pvbas pvbasvazio';
   }
   var u = b.querySelector('u');
   if(u) b.insertBefore(s, u); else b.appendChild(s);
  }
 }

 /* ---- 15 · O NOME DO ESTILO POR EXTENSO --------------------------
    Luis, 15/08: *"tem espaco suficiente pra escrever Jogador de
    infiltracao e voce abreviou sem necessidade"*.
    A abreviacao vem do DADO (c.modelo). Aqui so o TEXTO NA TELA e
    trocado — o `c.modelo` continua igual, senao quebra o `funcDaPos`,
    o `SA_FAMILIA` e o `EST_POS`, que casam pelo nome do banco. */
 var ESTPT = { 'Jog. de infiltração': 'Jogador de infiltração',
               'Especialista em cruz.': 'Especialista em cruzamento' };
 function nomeEstilo(){
  var b = document.querySelector('.fhdestbox');
  if(!b) return;
  var no = b.firstChild;
  while(no){
   if(no.nodeType === 3 && ESTPT[no.nodeValue.trim()])
    no.nodeValue = ESTPT[no.nodeValue.trim()];
   no = no.nextSibling;
  }
 }

 function arruma(){
  try{ abas(); }catch(e){}
  try{ nota(); }catch(e){}
  try{ titulos(); }catch(e){}
  try{ fisico(); }catch(e){}
  try{ impeto(); }catch(e){}
  try{ tecnico(); }catch(e){}
  try{ pedeFuncao(); }catch(e){}
  try{ basicoNaLista(); }catch(e){}
  try{ nomeEstilo(); }catch(e){}
  try{ tiraBotaoBonus(); }catch(e){}
 }
 /* ---- 16 · O CLIQUE NA POSICAO ESTAVA SENDO ENGOLIDO -------------
    ⚠️ Medido em 15/08: o `selPos` da casca marca a posicao e chama o
    `reabrir`; so que o `reabrir` foi envolvido para ZERAR o `_SELPOS`
    quando a chave muda — e na primeira vez o `_ULTK` ainda esta vazio,
    entao ele zerava a marcacao que acabara de ser feita. Resultado: o
    primeiro clique numa posicao nao fazia nada.
    Aqui o `_ULTK` e acertado ANTES, e a marcacao e reposta depois. */
 (function(){
  var orig = window.selPos;
  if(typeof orig !== 'function') return;
  window.selPos = function(p, key){
   var novo = (window._SELPOS === p) ? null : p;
   window._ULTK = key;
   window._SELPOS = novo;
   try{ if(typeof reabrir === 'function') reabrir(key); }catch(e){}
   window._SELPOS = novo;
   setTimeout(arruma, 0);
  };
 })();

 /* ---- 17 · OS BONUS ENTRAM NA NOTA, E O BOTAO SAI ----------------
    ORDEM DO LUIS, 15/08: *"e pra colocar direto na nota já esses valores.
    Físico ±1,5 · estilo de IA 0 a +1 · pé ruim 0 a +1 · estilo ativo +1.
    Já não tem nada de botão mais não."*

    ⚠️ O QUE ESTAVA ACONTECENDO: a casca tem `let ACH_BONUS=0` e envolve
    os tres bonus:
        prBonus  = function(c){ return ACH_BONUS ? _pr(c)  : 0; };
        fisBonus = function(c){ return ACH_BONUS ? _fis(c) : 0; };
        iaBonus  = function(c){ return ACH_BONUS ? _ia(c)  : 0; };
    Com a chave em 0, FISICO, PE RUIM e ESTILO DE IA ficavam TODOS zerados
    no ranking — era isso o "bonus +0.0" que o Luis viu no estilo de IA e o
    "bonus +0.00" do bloco Fisico. A conta por tras estava certa: medido,
    o _ia de um card com 2 COM devolve 0,4 certinho.

    Medido ao ligar, nas 12.161 linhas: 11.223 mudam de nota (92%),
    media +0,389, maior ganho +2,30, maior perda -1,50. No top 20 do
    Zagueiro de combate so 2 dos 20 ficam na mesma posicao.

    O estilo ativo (+1) nunca esteve na chave — esse ja entrava. */
 try{ ACH_BONUS = 1; }catch(e){}
 function tiraBotaoBonus(){
  var bs = document.querySelectorAll('button'), i;
  for(i=0;i<bs.length;i++)
   if(/nota = % do molde/.test(bs[i].textContent||'')) bs[i].remove();
 }
 try{ tiraBotaoBonus(); }catch(e){}
 try{ if(typeof _achGo === 'function') _achGo(); }catch(e){}

 window._visual1508B = arruma;

 function envolve(nome){
  var f = window[nome];
  if(typeof f !== 'function') return;
  window[nome] = function(){
   var r = f.apply(this, arguments);
   setTimeout(arruma, 0);
   return r;
  };
 }
 envolve('abrir'); envolve('encModo'); envolve('reabrir');
 if(document.readyState === 'loading')
  document.addEventListener('DOMContentLoaded', function(){ setTimeout(arruma, 0); });
 else setTimeout(arruma, 0);
})();
</script>
"""



def patch_nota_1508c(html):
    """OS BONUS ENTRAM NA NOTA — 15/08, ordem do Luis.

    *"e pra colocar direto na nota já esses valores. Físico ±1,5 · estilo de
    IA 0 a +1 · pé ruim 0 a +1 · estilo ativo +1. Já não tem nada de botão."*

    Tres coisas, todas MEDIDAS antes de mexer:

    1) `let ACH_BONUS=0` desligava os TRES bonus de uma vez (a casca envolve
       fisBonus/iaBonus/prBonus com `return ACH_BONUS ? _x(c) : 0`). Era isso
       o "bonus +0.0" do estilo de IA e o "+0.00" do bloco Fisico — a conta
       por tras estava certa (o _ia de um card com 2 COM devolve 0,4).

    2) o PE RUIM era calculado e JOGADO FORA:
           if(c._pr===undefined) c._pr = prBonus(c);   <- calcula
           return piso(b + c._fb + c._ia - p + bo, c.tipo);   <- nao usa
       Medido no Bradley Barcola: b1n 104,4613 + IA 0,4 + estilo 1 = 105,8613,
       que era exatamente a nota — o 0,28 do pe ruim ficava de fora.

    3) o botao "nota = % do molde" do canto sai (quem tira e o bloco visual).

    ⚠️ ISTO MUDA NOTA — de proposito. Medido ao ligar, nas 12.161 linhas:
       11.223 mudam (92%), media +0,389, maior ganho +2,30, maior perda -1,50.
    """
    ok = 0
    a = 'let ACH_BONUS=0;'
    if a in html:
        html = html.replace(a, 'let ACH_BONUS=1;', 1)
        ok += 1
    a = 'return piso(b+c._fb+c._ia-p+bo,c.tipo);}'
    if a in html:
        html = html.replace(a, 'return piso(b+c._fb+c._ia+c._pr-p+bo,c.tipo);}', 1)
        ok += 1
    return html, ok


# ==================================================================== #
#  O BONUS VEM PRONTO DO MOTOR — 15/08/2026
#
#  ORDEM DO LUIS, 15/08:
#    "O motor de atributos vai puxar do banco de dados, cuspir o resultado
#     e a gente vai colar na porra do encaixe."
#    "Hoje ele puxa da maquina. Quando for pra internet, puxa do banco.
#     E assim que tem que ser."
#
#  Ate aqui a tela CALCULAVA os quatro bonus por conta propria, com as
#  tabelas cravadas dentro dela. Agora quem calcula e o motor_bonus.py, que
#  cospe o saida_v6/bonus.jsonl. Este patch COLA esses numeros dentro do
#  HTML — exatamente como o gerador ja faz com o resultado dos atributos.
#
#  Se o arquivo nao existir, nada muda: a tela calcula como sempre calculou.
#  E rede de seguranca de proposito — nunca deixar o encaixe sem nota.
# ==================================================================== #
BONUS_ARQ = 'saida_v6/bonus.jsonl'


# ==================================================================== #
#  OS NOMES DA BARRA LATERAL — 15/08/2026
#
#  ORDEM DO LUIS, 15/08: "atualiza os nomes dessa barra lateral".
#
#  As funcoes foram renomeadas em 15/08, mas o menu da esquerda continuava
#  com os rotulos curtos antigos: o VOLANTE mostrava "de contencao" certo,
#  mas o MEIO ainda dizia "de chegada", "por dentro", "por fora" e
#  "segundo atacante" — nomes que nao existem mais em lugar nenhum.
#
#  Sao duas tabelas na casca:
#     ROT  o rotulo curto de cada funcao (o item clicavel do menu)
#     SIG  a sigla de cada grupo (o subtitulo do grupo)
#  O RENOMEIA_FUNCAO nao pega nenhuma das duas: ele troca o NOME da funcao,
#  e aqui o que esta errado e o APELIDO dela dentro do menu.
# ==================================================================== #
ROTULO_BARRA = [
    # (funcao ja com o nome novo, rotulo curto que aparece no menu)
    ('Meia de arranque',     'de arranque'),      # era "de chegada"
    ('Ala finalizador',      'finalizador'),      # era "por dentro"
    ('Ala cruzador',         'cruzador'),         # era "por fora"
    ('Meia ofensivo',        'ofensivo'),         # era "armador" (repetia com o Meia armador)
    ('Atacante infiltrador', 'infiltrador'),      # era "segundo atacante"
    ('Meia armador',         'armador'),
]

# o subtitulo do grupo tambem: a sigla continua, mas por extenso quando cabe
SIGLA_BARRA = [
    ('"MEIA LATERAL":"MLE · MLD"', '"MEIA LATERAL":"MLE · MLD"'),
]


# ==================================================================== #
#  APAGAR A PUNICAO DE MIGRACAO — 15/08/2026
#
#  ORDEM DO LUIS, 15/08:
#    "esquece negocio de punicao de migracao, isso e coisa de seculos atras,
#     ja foi superada ha anos. O que a gente usa hoje e BONUS pra quem e da
#     funcao e ponto final. Tem que apagar essas desgraca ai."
#
#  Ja estava ABOLIDA por decisao dele em 05/08 (`MIG_PUN = 0`) e reconfirmada
#  em 14/08 quando ele mandou tirar os botoes — "toda nota esta definida ja".
#  Mas o CODIGO MORTO continuou: o termo `-p` seguia na formula da nota, com
#  toda a maquinaria por tras (PUN_ESTILO, punEstilo, MIG_ESCALA, o botao).
#  Zerado nao e apagado: enquanto o termo esta la, um clique errado no botao
#  volta a punir 12 mil linhas em silencio.
#
#  Fica de pe o que substituiu a punicao: o BONUS de estilo ativo (+1 para
#  quem tem o estilo ligado na posicao da funcao).
# ==================================================================== #
def patch_apaga_punicao(html):
    """Tira o termo da punicao de migracao da formula da nota, e o botao."""
    ok = 0

    # 1) o termo sai da conta da nota
    a = 'return piso(b+c._fb+c._ia+c._pr-p+bo,c.tipo);}'
    b = ('return piso(b+c._fb+c._ia+c._pr+bo,c.tipo);}   '
         '/* 15/08: o -p (punicao de migracao) SAIU. Abolida em 05/08. */')
    if a in html:
        html = html.replace(a, b, 1); ok += 1

    # 2) a chamada tambem, senao fica variavel declarada e nao usada
    a = ' const p=punEstilo(c);'
    b = (' /* 15/08: punEstilo APAGADO. Nao existe mais punicao de migracao —\n'
         '    o que vale e o bonus de quem E da funcao. */')
    if a in html:
        html = html.replace(a, b, 1); ok += 1

    # 3) a funcao vira casca, para nao quebrar quem ainda a chame
    a = ('function punEstilo(c){\n'
         ' if(!c.MIG) return 0;                    '
         '/* o card está na função DELE — não paga nada */\n'
         ' return PUN_ESTILO*(1-comportamento(c)/100);}')
    b = ('function punEstilo(c){ return 0; }   '
         '/* 15/08: ABOLIDA. Sempre zero. */')
    if a in html:
        html = html.replace(a, b, 1); ok += 1

    # 4) o botao nao pode mais ligar nada
    a = 'function toggleMigPun(){'
    b = ('function toggleMigPun(){ return; }   '
         '/* 15/08: o botao da punicao nao faz mais nada */\n'
         'function _toggleMigPun_morto(){')
    if a in html:
        html = html.replace(a, b, 1); ok += 1

    # 5) a escala nao pode ter valor diferente de zero
    import re as _re
    m = _re.search(r'const MIG_ESCALA=\[[^\]]*\];', html)
    if m:
        html = html.replace(m.group(0), 'const MIG_ESCALA=[0];', 1); ok += 1

    return html, ok


def patch_barra_lateral(html):
    """Poe no menu da esquerda os nomes novos das funcoes."""
    import re as _re
    ok = 0
    for funcao, rotulo in ROTULO_BARRA:
        for nome in (funcao, _esc(funcao)):
            # so dentro do ROT={...}: e la que mora o rotulo do menu
            for velho in _re.findall(r'"%s":"[^"]*"' % _re.escape(nome), html):
                novo = '"%s":"%s"' % (nome, rotulo)
                if velho != novo and ':"' in velho:
                    # nao mexer em par que nao seja rotulo (valor com numero, lista...)
                    html = html.replace(velho, novo)
                    ok += 1
    return html, ok


def _molde_do_corpo_js():
    """O molde do corpo, por funcao, no formato que a ficha usa.

    Le o mesmo `dados/insumos_bonus.json` que o motor_bonus.py le, e resolve
    aqui o que a classe `Molde` dele resolve em tempo de execucao. Assim a
    tela nao precisa reimplementar a regra — so aplicar a tabela.
    """
    import json as _j
    caminho = os.path.join('dados', 'insumos_bonus.json')
    if not os.path.exists(caminho):
        return 'const CORPO_MOLDE={};const CORPO_ORDEM=[];\n'
    try:
        ins = _j.load(open(caminho, encoding='utf-8'))
        c = ins['corpo']
    except Exception:
        return 'const CORPO_MOLDE={};const CORPO_ORDEM=[];\n'

    ordem = c['ordem']
    cortes = c['cortes']
    cortes_gk = c['cortes_altura_goleiro']
    direcao = c['direcao']
    tipo = c['tipo_de_corpo']
    excecoes = c['excecoes']
    goleiro = c['goleiro']
    porte = c['bloco_porte']
    proporcao = c['bloco_proporcao']
    ombros = c['bloco_ombros']
    peso_altura = c.get('peso_altura', 5)
    peso_demais = c.get('peso_demais', 1)

    def _peso(m):
        return peso_altura if m == 'Altura' else peso_demais

    def _dir(m, f):
        d = direcao.get(f)
        if d and m in d:
            return d[m]
        e = excecoes.get(f + '|' + m)
        if e is not None:
            return e
        t = tipo.get(f)
        if not t:
            return 0
        if t[0] == 'GK':
            return goleiro.get(m, 0)
        if m in porte:
            return 1 if t[0] == 'G' else -1
        if m in proporcao:
            return 1 if t[1] == 'L' else -1
        return ombros.get(m, 0)

    def _corte(m, f):
        t = tipo.get(f)
        if t and t[0] == 'GK' and m == 'Altura':
            return cortes_gk
        return cortes[m]

    def _alvo(m, f):
        d = _dir(m, f)
        if not d:
            return '—'
        k = _corte(m, f)
        return ('≥' + str(k[3] + 1)) if d > 0 else ('≤' + str(k[0]))

    funcoes = set(list(direcao.keys()) + list(tipo.keys()))
    saida = {}
    for f in sorted(funcoes):
        teto = 0
        medidas = {}
        for m in ordem:
            d = _dir(m, f)
            if d:
                teto += _peso(m) * 2
            medidas[m] = [d, _peso(m), _alvo(m, f), _corte(m, f)]
        saida[f] = {'teto': teto or 1, 'm': medidas}

    return ('const CORPO_ORDEM=' + _j.dumps(ordem, ensure_ascii=False,
                                            separators=(',', ':')) + ';\n'
            'const CORPO_MOLDE=' + _j.dumps(saida, ensure_ascii=False,
                                            separators=(',', ':')) + ';\n'
            '/* a MESMA conta do motor_bonus.nota_da_medida: -2 a +2 */\n'
            'function notaDaMedida(v,k){ if(v<=k[0])return -2; if(v<=k[1])return -1;\n'
            ' if(v<=k[2])return 0; if(v<=k[3])return 1; return 2; }\n'
            '/* as 12 linhas do corpo de um card numa funcao, no formato do frows:\n'
            '   [nome, peso, alvo, valor, nota, direcao, pontos] */\n'
            'function corpoLinhas(c){\n'
            ' try{\n'
            '  var base=String(c.id).split("@")[0];\n'
            '  var v=CORPO_MOTOR[base], M=CORPO_MOLDE[c.tipo];\n'
            '  if(!v||!M) return [];\n'
            '  var out=[],i,m,e,val,n,pts;\n'
            '  for(i=0;i<CORPO_ORDEM.length;i++){\n'
            '   m=CORPO_ORDEM[i]; e=M.m[m]; val=v[i];\n'
            '   if(!e||typeof val!=="number") continue;\n'
            '   n=notaDaMedida(val,e[3]); pts=n*e[0]*e[1];\n'
            '   out.push([m, e[0]?e[1]:0, e[2], val, n, e[0],\n'
            '             Math.round(pts*100)/100]);\n'
            '  }\n'
            '  return out;\n'
            ' }catch(e){ return []; }\n'
            '}\n'
            'window.corpoLinhas=corpoLinhas;\n')


def patch_bonus_pronto(html):
    """Cola os quatro bonus ja calculados pelo motor dentro da tela."""
    import json as _j
    if not os.path.exists(BONUS_ARQ):
        return html, 'SEM ' + BONUS_ARQ + ' (a tela calcula sozinha, como antes)'

    T = {}
    CORPO = {}
    try:
        with open(BONUS_ARQ, encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    d = _j.loads(linha)
                except Exception:
                    continue
                cid, fun = d.get('card_id'), d.get('funcao')
                if not cid or not fun:
                    continue
                def _n(v):
                    # None = o motor NAO sabe. Vai como null e a tela calcula
                    # como sempre calculou. Nunca piora o que ja estava certo.
                    return round(float(v), 4) if isinstance(v, (int, float)) else None
                T['%s|%s' % (cid, fun)] = [_n(d.get('b_corpo')),
                                           _n(d.get('b_pe_ruim')),
                                           _n(d.get('b_estilo')),
                                           _n(d.get('b_ia')),
                                           d.get('faltou') or 0]
                #  o corpo medido pelo motor, na ordem do `detalhe`. Um por
                #  CARD (nao por funcao) — as medidas do corpo nao mudam com a
                #  funcao, so o alvo e o peso mudam.
                if cid not in CORPO:
                    det = d.get('detalhe') or []
                    if det:
                        CORPO[cid] = [x.get('valor') for x in det]
    except Exception as e:
        return html, 'ERRO lendo o %s: %s' % (BONUS_ARQ, e)
    if not T:
        return html, BONUS_ARQ + ' esta vazio'

    # ⛔ ensure_ascii=False de proposito: a chave carrega o NOME DA FUNCAO, e o
    #    RENOMEIA_FUNCAO roda depois, por cima do HTML inteiro. Escapado, o
    #    renomeio nao casaria e a tabela ficaria com o nome velho enquanto a
    #    linha ja veio com o novo — o mesmo defeito que zerou o fisico de 1.439
    #    linhas em 15/08. (O _renomeia() cobre as duas formas, mas aqui e melhor
    #    nem criar a forma escapada.)
    js = ('\n<script>\n'
          '/* ===== O BONUS VEM PRONTO DO MOTOR - 15/08/2026 =====\n'
          '   Quem calculou foi o motor_bonus.py. A tela so usa o numero.\n'
          '   [ corpo , pe ruim , estilo ativo , estilo da IA , o que faltou ]\n'
          '   null = o motor NAO SABE. Nao e zero, e falta de dado. O 5o campo\n'
          '   diz o nome do que faltou, para a ficha poder AVISAR em vez de\n'
          '   fingir que o card tirou zero. */\n'
          'const BONUS_PRONTO=' + _j.dumps(T, ensure_ascii=False,
                                           separators=(',', ':')) + ';\n'
          #  ⛔ O CORPO DE CADA CARD, MEDIDO PELO MOTOR. A ordem e a do
          #  `detalhe` do bonus.jsonl e bate com o MF_ARQIDX:
          #    Altura, Coxa, Panturrilha, Cintura, Peito, Tam. braco,
          #    Tam. pescoco, Compr. perna, Compr. braco, Compr. pescoco,
          #    Larg. ombro, Alt. ombro
          'const CORPO_MOTOR=' + _j.dumps(CORPO, separators=(',', ':')) + ';\n'
          #  ⛔ 19/08 — O MOLDE DO CORPO, POR FUNCAO.
          #  Ordem do Luis: *"as medidas do corpo saem do motor de bonus e sao
          #  gravadas no supabase"*. Estavam — mas so os NUMEROS do card
          #  (CORPO_MOTOR). Faltava o molde: direcao, peso, alvo e os quatro
          #  cortes de cada medida em cada funcao. Sem ele a ficha nao tinha
          #  como montar a tabela, e o bloco MEDIDAS DO CORPO saia vazio
          #  (`soma 0 · peso 0 · 0%`), porque o `frows` do gerador e `[]`.
          #  Sao 19 funcoes x 12 medidas — cabe inteiro, e a conta e a MESMA
          #  do motor_bonus (nota_da_medida: -2 a +2 pelos quatro cortes).
          + _molde_do_corpo_js()
          + '/* ⛔ 19/08 — O BANCO MANDA. A TELA NAO CALCULA BONUS.\n'
          '   Ordem do Luis, 19/08: *"a gente alterou a fonte de dados que estava\n'
          '   dispersa para uma unica fonte. Se o banco fala que o bonus e x, o\n'
          '   bonus e x."*\n'
          '   Antes havia uma "rede de seguranca": quando a chave nao era achada,\n'
          '   a tela CALCULAVA sozinha. Isso criou dois enderecos para o mesmo\n'
          '   numero — e a sessao do encaixe mediu a conta disso: 1.567 linhas\n'
          '   divergindo no estilo da IA e 250 no corpo, com a NOTA usando um\n'
          '   valor e o TEXTO ao lado mostrando outro.\n'
          '   Agora a rede sai. Sem o numero do banco o bonus e ZERO para a conta\n'
          '   e fica REGISTRADO como falta — nao como medida. E a mesma regra do\n'
          '   Luis de 15/08: nao se inventa zero no lugar de nao sei.\n'
          '   Quem quiser ver quanto ficou sem: window.BONUS_SEM_BANCO. */\n'
          + 'window.BONUS_SEM_BANCO={n:0,chaves:{}};\n'
          + 'function bonusPronto(c,i,calcula){\n'
          ' try{ var k=String(c.id).split("@")[0]+"|"+c.tipo;\n'
          '  var b=BONUS_PRONTO[k];\n'
          '  if(b && typeof b[i]==="number") return b[i];\n'
          '  if(!BONUS_SEM_BANCO.chaves[k]){ BONUS_SEM_BANCO.chaves[k]=1;\n'
          '                                  BONUS_SEM_BANCO.n++; }\n'
          ' }catch(e){}\n'
          ' return 0;\n'
          '}\n'
          '</script>\n')

    #  ⛔ 19/08 — A TRAVA DA CHAVE DO BONUS.
    #  Nasceu de um defeito medido pela sessao do encaixe na instalacao DELES:
    #  a chave do BONUS_PRONTO vem do bonus.jsonl com o nome do BANCO, e o
    #  `c.tipo` da linha la sai RENOMEADO. Resultado: 57% das linhas nao achavam
    #  o proprio bonus e a tela recalculava sozinha, em silencio, por quatro
    #  dias. Aqui as duas usam o nome do banco e casam — mas isso e uma
    #  coincidencia de arquitetura, nao uma garantia: basta alguem mexer na
    #  ordem dos patches ou no RENOMEIA_FUNCAO para descasar.
    #  ⛔ A LICAO DO ACHADO DELES NAO E "renomeie a chave" — e que COMENTARIO
    #     NAO E PROVA. La havia um comentario garantindo a ordem de execucao, e
    #     ele estava errado. Entao aqui nao ha comentario garantindo nada: ha
    #     uma contagem, impressa a cada geracao.
    try:
        _chaves = CHAVES_DA_TELA
    except NameError:
        _chaves = None
    if _chaves:
        _acham = sum(1 for k in _chaves if k in T)
        _pct = 100.0 * _acham / len(_chaves) if _chaves else 0
        print('   linhas que acham o proprio bonus: %d de %d (%.1f%%)%s'
              % (_acham, len(_chaves), _pct,
                 '' if _pct >= 90 else '   <<< CAIU. A CHAVE DESCASOU.'))
        if _pct < 90:
            _faltam = [k for k in _chaves if k not in T][:5]
            print('   exemplos de chave que nao achou:')
            for _k in _faltam:
                print('      %s' % _k)
            print('   ⛔ a tela vai mostrar bonus ZERO nessas linhas — o banco')
            print('      manda, e sem chave nao ha o que ler. Conferir se o')
            print('      RENOMEIA_FUNCAO passou por cima da chave.')

    # o script entra ANTES da nota(), senao a funcao nao existe na hora da chamada
    alvo = '<script>'
    i = html.find(alvo)
    if i < 0:
        return html, 'nao achei onde por o script'
    html = html[:i] + js + html[i:]

    # ⛔ 15/08 ORDEM DO LUIS: "quando nao souber, tem que AVISAR que nao foi
    #    possivel puxar, senao a gente nao vai saber nunca". A tarja na ficha.
    js2 = ('\n<script>\n'
           '/* ===== A TARJA DO NAO SEI - 15/08/2026 ===== */\n'
           '(function(){\n'
           ' if(window.__NAOSEI)return; window.__NAOSEI=1;\n'
           ' var CSS="#box .naosei{margin:8px 0 2px;padding:8px 12px;border-radius:8px;'
           'background:#3a2a12;border:1px solid #7a5a1c;color:#f0c060;font-size:13px;'
           'line-height:1.45}#box .naosei b{color:#ffd479}";\n'
           ' var st=document.createElement("style"); st.textContent=CSS;\n'
           ' document.head.appendChild(st);\n'

           ' function poe(){\n'
           '  var bx=document.getElementById("box"); if(!bx)return;\n'
           '  var v=bx.querySelector(".naosei"); if(v)v.remove();\n'
           '  var k=null;\n'
           '  var bt=bx.querySelector(".encaba[onclick]");\n'
           '  if(bt){ var m=String(bt.getAttribute("onclick")||"").match('
           '/\x27([^\x27]+\\|[^\x27]+)\x27/); if(m)k=m[1]; }\n'
           '  if(!k){ var r=bx.querySelector("[onclick^=\\"reabrir(\\"]");\n'
           '   if(r){ var m2=String(r.getAttribute("onclick")||"").match('
           '/\x27([^\x27]+\\|[^\x27]+)\x27/); if(m2)k=m2[1]; } }\n'
           '  if(!k)return; var f=null;\n'
           '  try{ var bb=BONUS_PRONTO[k]; f=(bb&&bb[4])?bb[4]:null; }catch(e){}\n'
           '  if(!f||!f.length)return;\n'
           '  var d=document.createElement("div"); d.className="naosei";\n'
           '  d.innerHTML="\\u26a0 <b>N\\u00c3O SEI</b> \\u2014 este card est\\u00e1 '
           'sendo julgado <b>sem</b> "+f.join(" · ")+". O dado n\\u00e3o existe na base, '
           'ent\\u00e3o o b\\u00f4nus n\\u00e3o foi calculado \\u2014 e <b>n\\u00e3o '
           '\\u00e9 zero</b>, \\u00e9 falta de coleta. A lista completa est\\u00e1 no '
           '<b>NAO-SEI.txt</b> da pasta.";\n'
           '  var alvo=bx.querySelector(".fhdestbox")||bx.querySelector(".bptrio")||'
           'bx.firstElementChild;\n'
           '  if(alvo&&alvo.parentNode) alvo.parentNode.insertBefore(d,alvo);\n'
           ' }\n'

           ' ["abrir","reabrir","encModo"].forEach(function(n){\n'
           '  var o=window[n]; if(typeof o!=="function")return;\n'
           '  window[n]=function(){ var r=o.apply(this,arguments);\n'
           '   setTimeout(poe,0); return r; };\n'
           ' });\n'
           ' setTimeout(poe,300);\n'
           '})();\n'
           '</script>\n')
    i2 = html.rfind('</body>')
    if i2 > 0:
        html = html[:i2] + js2 + html[i2:]

    ok = 0
    for velho, novo in (
            ('if(c._fb===undefined)c._fb=fisBonus(c);',
             'if(c._fb===undefined)c._fb=bonusPronto(c,0,fisBonus);'),
            ('if(c._pr===undefined)c._pr=prBonus(c);',
             'if(c._pr===undefined)c._pr=bonusPronto(c,1,prBonus);'),
            ('if(c._ia===undefined)c._ia=iaBonus(c);',
             'if(c._ia===undefined)c._ia=bonusPronto(c,3,iaBonus);'),
            ('const bo=bonEstilo(c);',
             'const bo=bonusPronto(c,2,bonEstilo);')):
        if velho in html:
            html = html.replace(velho, novo, 1)
            ok += 1
    return html, '%d de 4 · %d pares colados' % (ok, len(T))


def patch_visual_1508b(html):
    """A 2a leva de ajustes visuais do modal — 15/08 (ordens do Luis).

    Vai como UM bloco de <script> no fim do body, e nao como replace de
    string na casca, porque a ficha e REMONTADA a cada abrir / trocar de
    aba: o bloco se pendura no `abrir`, no `encModo` e no `reabrir` e
    refaz o visual sempre que a ficha volta. Tudo em try/catch.

    ⛔ Nao encosta em nota, motor, banco nem chave de funcao.
    """
    if 'VISUAL_1508B' in html:
        return html, 0
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    return html[:k] + _JS_VISUAL_1508B + html[k:], 1

def patch_modal_cabecalho(html):
    ok = 0

    # ---- 1. o CSS + o campinho ---------------------------------------------
    if 'CAMPINHO_1508' not in html:
        k = html.find('</head>')
        if k > 0:
            html = html[:k] + _CSS_CAMPINHO + html[k:]
            ok += 1
        k = html.rfind('</body>')
        if k < 0:
            k = len(html)
        html = html[:k] + _JS_CAMPINHO + html[k:]
        ok += 1

    # ---- 2. some a linha grande do "% do topo da funcao" -------------------
    a = ('<span class=fhdl style="font-size:13px;font-weight:800;margin-top:2px">'
         '${pctTopo(c)} do topo da fun\u00e7\u00e3o</span>')
    if a in html:
        html = html.replace(a, '')
        ok += 1

    # ---- 4. o que subiu para o painel sai do grid (Luis, 15/08) ---------
    #  As tres secoes viram `secdup` e somem POR CSS quando o painel de
    #  build existe (`#box:has(.bpan) .secdup{display:none}`). Em card sem
    #  orcamento o painel nao existe — e ai elas continuam aparecendo, que e
    #  o unico lugar onde a informacao estaria.
    for velho, nvo in (
        ("<div class=sec><h3>${MODO_ADM?'Habilidades':'Habilidades'}</h3>",
         '<div class="sec secdup"><h3>${MODO_ADM?\'Habilidades\':\'Habilidades\'}</h3>'),
        ("<div class=sec><h3>${MODO_ADM?'Habilidades especiais':'Habilidades especiais'}</h3>",
         '<div class="sec secdup"><h3>${MODO_ADM?\'Habilidades especiais\':\'Habilidades especiais\'}</h3>'),
        ('<div class=sec style=margin-bottom:0><h3>P\u00e9 ruim</h3>',
         '<div class="sec secdup" style=margin-bottom:0><h3>P\u00e9 ruim</h3>'),
    ):
        if velho in html:
            html = html.replace(velho, nvo)
            ok += 1

    # ---- 7. O TOPO DA FICHA, 2a leva de ordens do Luis (15/08) ---------
    #  a) "% do topo" sai da linha comprida e vai LOGO ABAIXO da nota final,
    #     escrito curto: "100,00% top". O bruto sai.
    #  b) embaixo da FOTO entra o ESTILO DE JOGO em destaque ("O destruidor") —
    #     *"o estilo tem que ficar destacado, nao pode ficar no meio daqueles
    #      outros ali, que a informacao nao e tao importante"*.
    #  c) o OVR fica auto-explicativo: "OVR base 86 · OVR máximo 102,46".
    a = ('${(function(){if(c._notaMot===undefined)return \'\';const na=nota(c);'
         'const p=na>0?(c._notaMot-na)/na*100:0;')
    i = html.find('<span class=fhdl>nota final</span>')
    j = html.find('</div></div>\n <div class=duo>', i)
    if i > 0 and j > i:
        fim = i + len('<span class=fhdl>nota final</span>')
        topo = ("<span class=fhdtopo>${(function(){var t=topoDoTipo(c.tipo);"
                "var n=nota(c);var p=t>0?100*n/t:0;"
                "return '<b style=\"color:'+(p>=99.5?'#22c58b':(p>=90?'#c98a1f':'inherit'))"
                "+'\">'+p.toFixed(2).replace('.',',')+'% top</b>';})()}</span>")
        melhor = ("${(function(){if(c._notaMot===undefined)return '';const na=nota(c);"
                  "const p=na>0?(c._notaMot-na)/na*100:0;"
                  "return '<span class=fhdmel>pode melhorar <b>'"
                  "+(p>0.05?'+'+p.toFixed(1).replace('.',','):'0')+'%</b></span>';})()}")
        html = html[:fim] + topo + melhor + html[j:]
        ok += 1

    #  15/08, refino: a foto EM CIMA e o estilo EMBAIXO dela, um sobre o
    #  outro — *"voce vai colocar a foto em cima e jogador de infiltracao
    #  embaixo"*. Para isso os dois entram numa coluna so.
    a = '<img class=fhdimg src='
    if a in html and '<div class=fhdcol>' not in html:
        html = html.replace(a, '<div class=fhdcol>' + a, 1)
        ok += 1
    a = ('_l.png" onerror="this.style.display=\'none\'">')
    if a in html:
        html = html.replace(
            a, a + "<div class=fhdestbox>${(c.modelo||c.tipo||'')}</div></div>", 1)
        ok += 1

    a = "OVR base ${c.ovr} \u2192 M\u00c1X ${(c.maxOvr||c.sisOvr||0)}"
    b = ("<b>OVR base ${c.ovr}</b> \u00b7 OVR m\u00e1ximo <b>${(c.maxOvr||c.sisOvr||0)}</b>")
    if a in html:
        html = html.replace(a, b, 1)
        ok += 1

    # o estilo sai do bloquinho (subiu para baixo da foto)
    a = ("${(c.modelo&&c.modelo!==c.tipo)?' <span class=cdmdl><i>estilo</i> '"
         "+c.modelo+'</span>':''}")
    if a in html:
        html = html.replace(a, '', 1)
        ok += 1

    # ---- 8. o PE RUIM e o corpo entram no bloco CORPO (Luis, 15/08) ----
    #  *"o pe ruim pode junto com o bloco de habilidades fisicas"* — e a
    #  altura/peso/idade tambem: *"sem tudo voce pode colocar junto do bloco
    #  de atributos fisicos, que nao da nada nao"*.
    a = "':'Corpo'}</h3>${fz}</div>"
    if a in html:
        b = ("':'Corpo'}</h3>"
             "<div class=corpotop>"
             "<span>${c.h}cm</span><span>${c.w}kg</span><span>${c.age} anos</span>"
             "<span>${c.foot||'\u2014'}</span>"
             "<span>les\u00e3o ${c.inj||'\u2014'}</span></div>"
             "<div class=corpopr>${prPar(c)?`"
             "<span>p\u00e9 ruim <b>${PR_ROT_F[prPar(c)[0]]}</b></span>"
             "<span>precis\u00e3o <b>${PR_ROT_Q[prPar(c)[1]]}</b></span>"
             "<span>b\u00f4nus <b style=color:#4f8cff>+${prBonus(c).toFixed(2)}</b></span>`"
             ":'<span>p\u00e9 ruim sem dado</span>'}</div>"
             "${fz}</div>")
        html = html.replace(a, b, 1)
        ok += 1

    # o bloco solto do Pe ruim some de vez (ele agora mora no Corpo)
    a = '<div class="sec secdup" style=margin-bottom:0><h3>P\u00e9 ruim</h3>'
    if a in html:
        html = html.replace(a, '<div class="sec secoff" style=margin-bottom:0>'
                               '<h3>P\u00e9 ruim</h3>', 1)
        ok += 1

    # e o corpo sai do bloquinho de cima (subiu para o bloco Corpo)
    a = (" \u00b7 ${c.foot||'\u2014'} (p\u00e9 ruim ${c.wfu??'\u2014'}/${c.wfa??'\u2014'})"
         " \u00b7 ${c.h}cm / ${c.w}kg \u00b7 ${c.age} anos"
         " \u00b7 les\u00e3o ${c.inj||'\u2014'}")
    if a in html:
        html = html.replace(a, '', 1)
        ok += 1

    # ---- 9. O BLOCO DO FISICO (Luis, 15/08) ----------------------------
    #  a) o titulo vira so "Físico": *"pode tirar esse tanto de explicacao que
    #     tem; isso ai e so fisico, ou atributos fisicos, so isso"*.
    #  b) TODAS as medidas na lista: *"ele esta com 8 medidas indiferentes
    #     nessa funcao; todas agora estao sendo consideradas, entao coloca
    #     todas"*. O "+ N medidas indiferentes" escondido sai.
    #     ⚠ As que o molde ainda nao usa continuam com alvo "—" e 0.00 — quem
    #       decide se elas pesam e o MF_DIRF do molde, que e motor, nao tela.
    a = ("'F\u00edsico \u2014 molde da fun\u00e7\u00e3o (alvo = elite) \u00b7 "
         "b\u00f4nus somado por fora: \u226590% +4 \u00b7 \u226570% +2 \u00b7 "
         "\u226420% \u22122':'Corpo'")
    if a in html:
        html = html.replace(a, "'F\u00edsico':'F\u00edsico'", 1)
        ok += 1

    a = "const fz=MODO_ADM?(FH+c.frows.filter(r=>r[1]>0).slice()"
    if a in html:
        html = html.replace(a, "const fz=MODO_ADM?(FH+c.frows.slice()", 1)
        ok += 1

    # medida que o molde nao usa nao tem direcao — escrever "menor melhor"
    # nela seria dizer uma coisa que o molde nao diz
    a = "<span class=mini>${r[5]>0?'maior melhor':'menor melhor'}</span>"
    if a in html:
        html = html.replace(
            a, "<span class=mini>${!r[5]?'\u2014':(r[5]>0?'maior melhor':'menor melhor')}"
               "</span>", 1)
        ok += 1

    a = ("+(c.frows.filter(r=>r[1]===0).length?`<details class=zr><summary>+ "
         "${c.frows.filter(r=>r[1]===0).length} medidas indiferentes nesta "
         "fun\u00e7\u00e3o</summary><div class=mini style=\"padding:5px 0\">"
         "${c.frows.filter(r=>r[1]===0).map(r=>r[0]).join(' \u00b7 ')}</div>"
         "</details>`:'')")
    if a in html:
        html = html.replace(a, '', 1)
        ok += 1

    # ---- 10. A COLUNA DA ESQUERDA (Luis, 15/08) ------------------------
    #  *"voce vai colocar o nome, embaixo a foto e embaixo o estilo. Do lado,
    #   em vez de voce colocar o campo, voce coloca as funcoes; ai depois do
    #   lado das funcoes voce coloca o campo. Ai esse aqui, onde esta escrito
    #   segundo atacante e o overall base, voce coloca embaixo de onde esta
    #   escrito jogador de infiltracao."*
    #  Fica: NOME · FOTO · ESTILO · posicao/votos · overall  numa coluna so;
    #  ao lado dela as FUNCOES; e ao lado das funcoes o CAMPINHO.
    i = html.find('<div class=fhdcol>')
    j = html.find('<div class=fhdid>', i)
    k = html.find('${posLinha(c)}', j)
    m = html.find('<div class=fhdnota>', k)
    if i > 0 and j > i and k > j and m > k:
        col   = html[i:j]                                   # a coluna com a foto
        nome  = html[j + len('<div class=fhdid>'):k]         # o nome e as tarjas
        minis = html[k + len('${posLinha(c)}'):m]            # posicao/votos + overall
        minis = minis.rstrip()
        if minis.endswith('</div>'):
            minis = minis[:-len('</div>')]                   # o </div> era do fhdid
        col = col.replace('<div class=fhdcol>',
                          '<div class=fhdcol><div class=fhdnome>' + nome.strip() + '</div>', 1)
        col = col.rstrip()
        if col.endswith('</div>'):
            col = col[:-len('</div>')] + minis + '</div>'
        # 15/08, refino do Luis: QUATRO colunas.
        #   1 foto + nome
        #   2 estilo + posicao/votos + overall  E, embaixo, os BOTOES
        #   3 o campinho, maior
        #   4 a nota (como estava)
        _i2 = col.find('<img class=fhdimg')
        _i3 = col.find('<div class=fhdestbox>')
        _nome = col[col.find('<div class=fhdcol>') + len('<div class=fhdcol>'):_i2]
        _img = col[_i2:_i3]
        _resto = col[_i3:]
        if _resto.rstrip().endswith('</div>'):
            _resto = _resto.rstrip()[:-len('</div>')]
        # o ESTILO sobe para o topo da coluna 2; os dois bloquinhos ficam
        # na coluna 1, debaixo da foto (dica do Luis, 15/08)
        _fe = _resto.find('</div>', _resto.find('fhdestbox'))
        _est = _resto[:_fe + len('</div>')]
        _minis = _resto[_fe + len('</div>'):]
        html = (html[:i]
                + '<div class=fhdcol>' + _nome + _img + _minis + '</div>'
                + '<div class=fhdmeio>' + _est
                + '<div class=fhdbts><div class=fhdbtstt>'
                  'FUN\u00c7\u00d5ES QUE ELE PODE EXERCER EM CAMPO'
                  '<span>clique para ver o build</span>'
                  '</div>${cbFuncoes(c)}</div></div>'
                + '<div class=fhdcampo>${cbCampo(c)}</div>'
                + html[m:])
        ok += 1

    # o OVR vira OVERALL por extenso, em DUAS linhas e com o numero em
    # destaque — a informacao que importa e o numero (Luis, 15/08)
    a = "<b>OVR base ${c.ovr}</b> \u00b7 OVR m\u00e1ximo <b>${(c.maxOvr||c.sisOvr||0)}</b>"
    if a in html:
        html = html.replace(
            # 15/08, 2a leva: o numero e o da KONAMI — o rotulo diz isso.
            a, "<div class=fhdovr>Base Konami: <b>${c.ovr}</b></div>"
               "<div class=fhdovr>M\u00e1ximo Konami: "
               "<b>${(c.maxOvr||c.sisOvr||0)}</b></div>", 1)
        ok += 1

    # ---- 11. AS ETIQUETAS DO NOME (Luis, 15/08) ------------------------
    #  *"essas etiquetas tem que sair. Esse `meta` pode sair, a gente nao
    #   precisa disso mais. A de `migrado` pode ficar, mas em outro lugar, nao
    #   do lado do nome. E o BASICO tem que vir perto de onde informa que ele
    #   e jogador de infiltracao"* — porque e o estilo que nao liga naquela
    #   posicao; a informacao so faz sentido colada no estilo.
    TAG_META = "${isM(c)?' <span class=\"tg m\">meta</span>':''}"
    TAG_BAS = ('${estiloAtiva(c)?\'\':\' <span class="tg se" title="o estilo de jogo '
               'dele n\u00e3o liga nesta posi\u00e7\u00e3o \u2014 aqui ele joga como '
               'B\u00c1SICO">B\u00c1SICO \u00b7 sem estilo nesta posi\u00e7\u00e3o'
               '</span>\'}')
    TAG_MIG = ("${c.MIG?' <span class=\"tg mg\">migrado \u00b7 nativo: '"
               "+(POSN[c.np]||c.np||'\u2014')+' ('+(c.np||'\u2014')+')</span>':''}")
    for t in (TAG_META, TAG_BAS, TAG_MIG):
        if t in html:
            html = html.replace(t, '', 1)
            ok += 1

    # o BASICO cola no bloco do estilo; o MIGRADO desce para o bloquinho
    a = "<div class=fhdestbox>${(c.modelo||c.tipo||'')}</div>"
    if a in html:
        html = html.replace(a,
            "<div class=fhdestbox>${(c.modelo||c.tipo||'')}"
            "${estiloAtiva(c)?'':'<div class=fhdbasico title=\"o estilo de jogo dele "
            "n\u00e3o liga nesta posi\u00e7\u00e3o\">B\u00c1SICO \u2014 este estilo "
            "n\u00e3o liga nesta posi\u00e7\u00e3o</div>'}</div>", 1)
        ok += 1
    a = "<div class=mini><b>${(POSN[npFixo(c)]||npFixo(c)||'\u2014')}</b> <b>(${(SIGJ&&SIGJ[c.np])||c.np||'\u2014'})</b>"
    if a in html:
        # ⚠️ 15/08 — AQUI JA QUEBROU A TELA UMA VEZ: `${...}` dentro de uma
        #    string de aspas simples NAO interpola, e o travessao de dentro
        #    fechava a string. Erro de sintaxe -> o `const D` inteiro nao
        #    carregava. Dentro de string, concatena; nunca `${}`.
        html = html.replace(a, a + "${c.MIG?' \u00b7 <b style=\"color:#c98a1f\">"
                                   "migrado</b> (nativo '+(POSN[c.np]||c.np||'\u2014')+')':''}", 1)
        ok += 1

    # ---- 12. O SELETOR DO TECNICO (Luis, 15/08) ------------------------
    #  *"voce coloca o nome dele na caixinha, e embaixo voce coloca o mais um
    #   que ele aumenta"* — o `<option>` levava nome + os dois atributos e
    #   ficava cortado dentro da caixa. Agora a caixa mostra so o NOME e os
    #   atributos do +1 ficam numa linha abaixo dela.
    a = "${t[0]} \u00b7 +1 ${t[1].map(tecPT).join(' \u00b7 ')}"
    if a in html:
        html = html.replace(a, "${t[0]}", 1)
        ok += 1
    a = "</li></ul>${tecSel}</div>`"
    if a in html:
        html = html.replace(a, "</li></ul>${tecSel}"
                               "<div class=tecmais>+1 ${(tecAtual(c)||[]).map(tecPT)"
                               ".join(' \u00b7 ')||'\u2014'}</div></div>`", 1)
        ok += 1
    a = "</b>${tecSel}</div>`"
    if a in html:
        html = html.replace(a, "</b>${tecSel}"
                               "<div class=tecmais>+1 ${(tecAtual(c)||[]).map(tecPT)"
                               ".join(' \u00b7 ')||'\u2014'}</div></div>`", 1)
        ok += 1

    # ---- 13. na aba COM O QUE EU TENHO as "boas opcoes" nao servem -------
    #  *"nao precisa dessas boas opcoes; isso aqui e o cara que vai colocar a
    #   habilidade dele"*. Some so nessa aba; nas outras continua.
    ok += 1

    # ---- 14. O BLOCO FISICO MOSTRAVA A REGUA VELHA (Luis, 15/08) -------
    #  *"esse fisico eu acho que esta um pouco defasado; o maior melhor, o
    #   menor melhor, eu acho que nao e mais desse jeito. Tem que aparecer na
    #   tela o que a gente realmente esta considerando atualmente."*
    #
    #  CONFERIDO no proprio HTML (so leitura):
    #     mfNota(v,c) = v<=c[0]?-2 : v<=c[1]?-1 : v<=c[2]?0 : v<=c[3]?1 : 2
    #     MF_PESO     = Altura vale 5, as outras valem 1
    #     CORPO_MAX   = 1,5  (o bonus final na nota)
    #  Ou seja: desde 10/08 cada medida vale de -2 a +2 POR FAIXA (ETAPA 2).
    #  A tela ainda mostrava "ALVO ≥9" e "maior melhor" — a leitura de
    #  passa/nao-passa do modelo ANTERIOR, que nao pontua mais assim.
    #  Agora a coluna mostra a NOTA DA MEDIDA (-2 a +2), que e o que conta.
    a = ("<div class=fzh><span>Medida</span><span>Dire\u00e7\u00e3o</span>"
         "<span>Alvo</span><span>No card</span><span>Pontos</span></div>")
    if a in html:
        html = html.replace(a, "<div class=fzh><span>Medida</span>"
                               "<span>Dire\u00e7\u00e3o</span><span>Nota da medida</span>"
                               "<span>No card</span><span>Pontos</span></div>", 1)
        ok += 1
    a = "<span class=mini>${r[2]}</span><b>${r[3]}</b>"
    if a in html:
        html = html.replace(
            a, "<span class=mini><b style=\"color:${r[4]>0?'#22c58b':"
               "(r[4]<0?'#e0533d':'inherit')}\">${r[4]>0?'+':''}${r[4]}</b>"
               "</span><b>${r[3]}</b><span class=mini>${r[2]}</span>", 1)
        ok += 1
    a = "<span class=mini>soma ${(c.b4r||0).toFixed(0)} de \u00b1${MF_FAIXA[c.tipo]?MF_FAIXA[c.tipo][1]:32}</span>"
    if a in html:
        html = html.replace(a, "<span class=mini>soma ${(c.b4r||0).toFixed(0)}</span>", 1)
        ok += 1

    # ---- 15. TECNICO COM NOME REPETIDO (Luis, 15/08) -------------------
    #  *"eu tenho tres Ronald Koeman e eu nao sei qual e qual"* — o catalogo
    #  tem o mesmo nome com boosts diferentes. Quem repete passa a mostrar os
    #  dois atributos do +1 na propria opcao; quem e unico continua so o nome.
    a = "<option value=\"${i}\"${i===sel?' selected':''}>${t[0]}</option>"
    if a in html:
        html = html.replace(
            a, "<option value=\"${i}\"${i===sel?' selected':''}>${t[0]}"
               "${_tecRep(t[0])?' \u00b7 '+t[1].map(tecPT).join(' + '):''}</option>", 1)
        ok += 1

    # ---- 16. A COLUNA 1: SO A POSICAO NATIVA (Luis, 15/08) -------------
    #  *"posicao nativa, so, nao muda nunca. Nao e a funcao. Nao precisa
    #   desses votos. A data de lancamento pode ficar."*
    i = html.find("<div class=mini>${c.tipo} <b>(${sigDe(c.tipo)})</b>")
    if i > 0:
        j = html.find('</div>', i)
        if j > i:
            html = (html[:i]
                    + "<div class=\"mini fhdnat\">"
                      "<span class=pslb>POSI\u00c7\u00c3O NATIVA</span>"
                      "<div class=fhdsig>${(typeof SIGJ!=='undefined'&&SIGJ[npFixo(c)])||npFixo(c)||'\u2014'}</div>"
                      "<div class=fhdpos>${(POSN[npFixo(c)]||npFixo(c)||'\u2014')}</div>"
                      "${c.dt?`<div class=fhddt>${c.dt.split('-').reverse().join('/')}</div>`:''}"
                    + html[j:])
            ok += 1

    # o GRUPO da barra lateral acompanha a posicao: MAT e "Meia atacante".
    # Enquanto ele dizia "MEIA OFENSIVO", esse termo estava ocupado por uma
    # POSICAO e nao podia nomear uma funcao.
    for velho, nvo in (('"MEIA OFENSIVO":"MAT"', '"MEIA ATACANTE":"MAT"'),
                       ('"MEIA OFENSIVO"', '"MEIA ATACANTE"'),
                       ("'MEIA OFENSIVO'", "'MEIA ATACANTE'")):
        if velho in html:
            html = html.replace(velho, nvo)
            ok += 1

    # ---- 17. O RENOMEIO PASSA DE NOVO, POR ULTIMO (15/08) --------------
    #  ⚠️ O `RENOMEIA_FUNCAO` roda no patch_interface_p1, mas o MOLDE DO
    #  FISICO (MF_DIRF) e injetado DEPOIS — e entrava com os nomes antigos.
    #  Como ele casa pelo nome da funcao (`MF_DIRF[c.tipo]`), o corpo deixaria
    #  de pontuar em Atacante finalizador e Atacante criador, em silencio.
    #  Aqui o renomeio passa outra vez, ja com tudo montado.
    html = _renomeia(html)
    ok += 1

    # ---- 6. o rodape do painel enxuga (Luis, 15/08) --------------------
    #  o seletor do tecnico e o do impeto subiram para a coluna do meio;
    #  e o botao laranja sai de vez: *"isso ajusta as barras ao que esta na
    #  tela, o que que e isso? qual a diferenca dele pro otimizar? esse
    #  ajustar as barras nao tem muito sentido nao"*. Com as tres abas ele
    #  virou redundante: no MAXIMO e leitura, em COM O QUE EU TENHO as barras
    #  ja se ajustam sozinhas a cada insumo, e em DO MEU JEITO e na mao.
    a = '${tecSel}${imp}<button onclick="restaurarMotor('
    if a in html:
        html = html.replace(a, '<button onclick="restaurarMotor(', 1)
        ok += 1
    i = html.find('<button onclick="otimizarBarras(')
    if i > 0:
        j = html.find('</button>', i)
        if j > i:
            html = html[:i] + html[j + len('</button>'):]
            ok += 1

    # ---- 5. as etiquetas do nome que perderam o sentido (Luis, 15/08) ---
    #  *"esse + NOVA ja perdeu o sentido: a ideia era o card que entrou essa
    #   semana; agora ele marca o que o NOSSO MOTOR rodou agora, e ai carta
    #   antiga aparece como nova. E esse `nativo` nao tem necessidade aqui —
    #   nativo do que? La embaixo ja diz a posicao nativa dele. A etiqueta de
    #   nativo so faz sentido quando a gente ve em LISTA."*
    #  Sai so do cabecalho da ficha; nas listas as duas continuam.
    for velho in (
        '${c.NOVO?\' <span class="tg nv">\u2726 NOVA</span>\':\'\'}',
        '${c.MIG?\'\':(c.sec?\' <span class="tg s2">2\u00aa posi\u00e7\u00e3o</span>\''
        ':\' <span class="tg n">nativo</span>\')}',
    ):
        if velho in html:
            html = html.replace(velho, '', 1)
            ok += 1

    # ---- 3. o "+ adicionar" oferece TODAS as habilidades -------------------
    #  Ordem do Luis, 15/08: *"eu imagino que essa lista seja so aquela que o
    #  nosso motor esta autorizado a utilizar. So que no jogo o cara pode
    #  utilizar a que quiser. Entao tem que ter TODAS aqui — se ele quiser
    #  usar uma que nao da conta, o problema e dele."*
    #  Antes vinha so `c.falta` (o que falta do ideal da funcao): dava 8 ou 9
    #  opcoes num catalogo de 65. Agora vem tudo que a tela sabe calcular,
    #  em ordem alfabetica, menos o que o card ja tem.
    a = ('const _pool=(c.falta||[]).filter(s=>!_hab.includes(s)'
         '&&HABEF[s]!==undefined);')
    #  ⛔ HABILIDADE ESPECIAL (rara) NAO entra: *"Xerifao nao e pra
    #     adicionar, ela e especial — ou vem com a carta ou nao vem"*
    b = ("const _pool=Object.keys(HABEF).filter(function(s){"
         "return _hab.indexOf(s)<0&&_nat.indexOf(s)<0"
         "&&!(typeof HABRARAS!=='undefined'&&HABRARAS[s]);})"
         ".sort(function(x,y){return x.localeCompare(y,'pt');});")
    if a in html:
        html = html.replace(a, b)
        ok += 1

    return html, ok


def patch_setores(html):
    """SETORES DA BARRA LATERAL — decisao do Luis, 12/08. SO APARENCIA.

    Antes: GOLEIRO 2 · DEFESA 4 · MEIO 8 · ATAQUE 4
    Agora: GOLEIRO 2 · DEFESA 6 · MEIO 5 · ATAQUE 5

      VOLANTE ............ sai do MEIO, vai para a DEFESA
                           (o molde dele ja e defensivo: peso 55 em defesa, 16 em bola)
      SEGUNDO ATACANTE ... sai da familia MEIA OFENSIVO e vira familia propria,
                           no ATAQUE. O "Meia ofensivo armador" fica no MEIO.

    Nenhum nome de funcao muda. Nao encosta em molde, banco nem motor.
    """
    ok = 0
    a = ('SET=[["GOLEIRO",["GOLEIRO"]],["DEFESA",["ZAGUEIRO","LATERAL"]],'
         '["MEIO",["VOLANTE","MEIA DE LIGAÇÃO","MEIA LATERAL","MEIA OFENSIVO"]],'
         '["ATAQUE",["PONTA","CENTROAVANTE"]]]')
    b = ('SET=[["GOLEIRO",["GOLEIRO"]],["DEFESA",["ZAGUEIRO","LATERAL","VOLANTE"]],'
         '["MEIO",["MEIA DE LIGAÇÃO","MEIA LATERAL","MEIA OFENSIVO"]],'
         '["ATAQUE",["SEGUNDO ATACANTE","PONTA","CENTROAVANTE"]]]')
    if a in html:
        html = html.replace(a, b); ok += 1

    a = ('["MEIA OFENSIVO",["Meia ofensivo armador","Segundo atacante"]],["PONTA",')
    b = ('["MEIA OFENSIVO",["Meia ofensivo armador"]],'
         '["SEGUNDO ATACANTE",["Segundo atacante"]],["PONTA",')
    if a in html:
        html = html.replace(a, b); ok += 1

    for velho, novo in (('"MEIA OFENSIVO":"MAT · SA"',
                         '"MEIA OFENSIVO":"MAT","SEGUNDO ATACANTE":"SA"'),
                        ('"MEIA OFENSIVO":"MO · SA"',
                         '"MEIA OFENSIVO":"MAT","SEGUNDO ATACANTE":"SA"')):
        if velho in html:
            html = html.replace(velho, novo); ok += 1; break
    return html, ok


def patch_meu_time(html):
    """SEMEIA O MODULO "MEU TIME" com o elenco real do Luis.

    Fonte: meu_time.json — os cards reconhecidos nas fotos do elenco no PS5
    (10/08/2026). O modulo guarda o time no localStorage (MT_v1) com
    {form, slots, banco, elenco}. Aqui a gente so ACRESCENTA ao `elenco` o que
    ainda nao esta la — nunca apaga escalacao nem banco que o Luis montou.

    Ordem dele: "coloca todos eles fora do banco" (ou seja, no elenco) e
    "conforme for rodando voce vai colocando" — por isso o semeador roda a cada
    geracao: card que o motor acabou de calcular entra sozinho no elenco.
    Para cada card entra a MELHOR funcao dele (maior nota).
    """
    try:
        MT = json.load(open('meu_time.json', encoding='utf-8'))
    except Exception as e:
        return html, 'sem meu_time.json (' + str(e) + ')'
    ids = [str(i) for i in (MT.get('ids') or [])]
    if not ids:
        return html, 'meu_time.json vazio'
    sc = ('\n<script>\nconst MEU_TIME=' + json.dumps({'ids': ids}, ensure_ascii=False)
          + ';\n' + "(function(){\n var IDS = new Set((typeof MEU_TIME!==\"undefined\" && MEU_TIME.ids)||[]);\n if(!IDS.size) return;\n function semeia(){\n  if(typeof MT===\"undefined\" || typeof D===\"undefined\") return setTimeout(semeia,500);\n  try{ if(typeof MTdb!==\"undefined\" && MTdb.load) MTdb.load(); }catch(e){}\n  MT.elenco = MT.elenco || [];\n  MT.banco  = MT.banco  || [];\n  var ja = new Set();\n  (MT.slots||[]).forEach(function(x){ if(x && x.key) ja.add(String(x.key).split(\"|\")[0]); });\n  MT.banco.forEach(function(k){ ja.add(String(k).split(\"|\")[0]); });\n  MT.elenco.forEach(function(k){ ja.add(String(k).split(\"|\")[0]); });\n  var melhor = {};\n  for (var i=0;i<D.length;i++){\n   var c=D[i];\n   if(!c || c.id===\"MOLDE\") continue;\n   var id=String(c.id);\n   if(!IDS.has(id) || ja.has(id)) continue;\n   var n = (typeof nota===\"function\") ? nota(c) : (c.b1n||0);\n   if(!melhor[id] || n > melhor[id].n) melhor[id] = {n:n, k:id+\"|\"+c.tipo};\n  }\n  var novos = Object.keys(melhor);\n  if(!novos.length) return;\n  novos.forEach(function(id){ MT.elenco.push(melhor[id].k); });\n  try{ if(typeof MTdb!==\"undefined\" && MTdb.save) MTdb.save(); }catch(e){}\n  try{ if(typeof mtRender===\"function\") mtRender(); }catch(e){}\n  console.log(\"%cMEU TIME · \"+novos.length+\" cards novos entraram no elenco (\"+\n    MT.elenco.length+\" no total; \"+IDS.size+\" cards do elenco reconhecidos nas fotos)\",\n    \"background:#22c58b;color:#08120c;font-weight:700;padding:2px 7px\");\n }\n setTimeout(semeia, 900);\n window.meuTimeSemeia = semeia;\n})();\n" + '</script>\n')
    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    return html[:k] + sc + html[k:], '%d cards do elenco' % len(ids)


# ============================================================================
#  A ABA MEU TIME MEDIA NA REGUA — 16/08/2026 (sessao "EF Meu Time 4")
#
#  A casca tem DUAS funcoes que calculam a nota de um card numa configuracao
#  hipotetica, e as duas reescreviam o c.b1n com o b1nDe antes de chamar
#  nota(c):
#
#     notaComTec(c,bs)      linha 2700 da casca   ->  mtN, e o ranking de
#                                                      tecnicos (linhas 2889-2894)
#     notaCfg(c,lvl,bs)     linha 2785 da casca   ->  mtNotaReal, mtN, mtPct
#
#  Juntas elas desenham a ABA MEU TIME INTEIRA: a nota de cada titular, o
#  percentual do chip de cada carta e o ganho de cada tecnico. Sem editar nada.
#
#  E o b1nDe (linha 2698) NAO e a nota:
#
#     escalaDe(tipo) -> {sa: 20/maior_b1_da_funcao, sb: ...}
#     b1nDe(tipo,b1) -> 92 + b1*sa        (ou b1*sb quando b1 < 0)
#
#  Isso e a REGUA reescalada para a faixa 92-112. A nota e o percentual do
#  molde — 100 * soma(peso*valor) / soma(peso*alvo) — que e o que o motor
#  grava e o que o achPct da tela calcula.
#
#  E chega na nota TODA, nao num cantinho: com SUG=[100,0,0,0,0] o
#  notaBase(c) E o b1n e mais nada; os bonus entram todos depois dele.
#
#  MEDIDO no encaixe_v6_NOVO.html de 16/08, 12.203 cards, as duas contas
#  rodadas lado a lado:
#
#     o b1n GRAVADO confere com a formula do motor .... desvio maximo 0,000000
#
#     MOTOR x b1nDe
#       diferenca mediana ...... 13,88 pontos de nota
#       acima de 1 ponto ....... 11.136 cards (91%)
#       maior diferenca ........ 1.603,53
#       Jaroensak Wonggorn · Ala cruzador   gravado 86,03   b1nDe -1517,50
#
#  ⛔ E A ORDEM MUDA, nao e so o numero. O b1nDe e monotono no b1, entao
#     preserva o ranking DO b1 — que nao e o ranking da nota. E a decisao de
#     06/08: ESCOLHER NAO E MEDIR. Contando os pares de cards da mesma funcao:
#
#       pares comparados ................................ 38.494
#       discordam (a regua diz um, a nota diz o outro) ... 2.286 = 5,9%
#
#     Um em cada dezessete. No ranking de tecnicos isso e apontar o tecnico
#     errado em torno de 6% das vezes — e apontar CALADO.
#
#  ⚠️ NAO DA PARA USAR O achPct AQUI. Ele grava em c._cp, e nem o notaComTec
#     nem o notaCfg restauram o _cp no fim (eles restauram arows, b1 e b1n).
#     O cache do card REAL ficaria com o valor da simulacao. Por isso a conta
#     vai inline, sem cache — e o _cp continua intocado.
#
#  A string trocada aparece exatamente 2 vezes na casca (uma em cada funcao),
#  entao um replace so pega as duas. O contador confere isso.
# ============================================================================
#  A TELA DE INICIO EM BLOCOS — 16/08/2026
#
#  Tres ordens do Luis, no mesmo pedido, olhando a tela de inicio:
#
#  1) *"a barra de rolagem esta quase bulinando as cartas. Arruma isso aqui,
#     da espaco entre elas."*
#     A lateral (#filtros) e fixa, tem 252px e overflow-y:auto — a barra de
#     rolagem dela nasce colada na borda dourada, e o main comecava no pixel
#     seguinte. Agora o main tem folga a esquerda e a lateral tem folga a
#     direita.
#
#  2) *"voce colocou como se fosse linhas cada box... esse espaco aqui todo,
#     desperdicado. Coloca como box, so com os tres mais bem colocados, e voce
#     pode clicar e abrir como se fosse uma nova pagina mesmo."*
#     Cada campanha era uma LINHA de largura inteira com 3 cards a esquerda e
#     dois tercos de vazio a direita. Agora sao BLOCOS lado a lado num grid, e
#     o "ver os N cards" abre a campanha em tela cheia, com um voltar.
#
#  3) *"na previa do card — isso aqui e so pras box — voce esta priorizando a
#     nota maior. Vai colocar o contrario, o percentual do topo maior, e vai
#     classificar elas pelo percentual do topo. A etiqueta de NOVA pode sumir,
#     a de MIGRADO tambem. A de BASICO voce vai colocar na frente do estilo, e
#     na linha do estilo tira a palavra 'estilo'. O valor bruto tambem nao
#     precisa. O OVR tambem nao tem necessidade."*
#
#  ⛔ SO NA BOX. O podio do "Top 3 de cada funcao", logo abaixo, continua com o
#     _hcd original da casca — nao foi tocado. Por isso existe um _hcdBox
#     separado em vez de mexer no _hcd.
#
#  Como entra: redefine window.homeRender por cima da que a casca declarou. O
#  bloco vai no fim do body, entao roda depois da declaracao e antes do
#  DOMContentLoaded que chama o homeToggle(1). Nada da casca foi apagado — se
#  este bloco cair, a casca volta a valer sozinha.
#
#  ⚠️ O script das "boxes anteriores" (patch_boxes_anteriores) varre
#     sec.getElementsByClassName("hbox") e reordena com appendChild no pai.
#     Os .hbox agora moram dentro do .hgrid, e o pai passa a ser o .hgrid —
#     o appendChild continua valendo. Na tela cheia nao existe .hbox, e ele
#     sai no `if(!bx.length) return`.
# ============================================================================
def patch_home_blocos_1608(html):
    if 'HOME_EM_BLOCOS_1608' in html:
        return html, 'ja estava'
    if 'function homeRender()' not in html:
        return html, 'NAO ACHEI o homeRender da casca'

    css = (
      '<style>\n'
      '/* HOME_EM_BLOCOS_1608 */\n'
      '@media(min-width:840px){\n'
      ' html[data-lay=cmp] main,main{margin-left:252px!important;\n'
      '  padding-left:22px!important}\n'
      '}\n'
      '.hgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(600px,1fr));\n'
      ' gap:14px;align-items:start}\n'
      '.hgrid>.hbox{margin:0!important}\n'
      '.gradebx{grid-template-columns:repeat(3,minmax(0,1fr))!important}\n'
      '.hvolta{cursor:pointer;font:inherit;font-size:11px;font-weight:800;\n'
      ' padding:5px 12px;border-radius:7px;border:1px solid var(--line,#1f2733);\n'
      ' background:transparent;color:inherit}\n'
      '.hvolta:hover{border-color:var(--dourado,#f0a531)}\n'
      '/* o card da box usa as MESMAS areas do grid do tema (foto/nota/nome/sub).\n'
      '   So o conteudo muda: na area da nota entra o % do topo. */\n'
      'html[data-tema] .cdbx .nt:before{content:"% do topo"!important}\n'
      '.cdbx .bxsg{font-size:17px;font-weight:800;margin-left:1px;letter-spacing:0}\n'
      'html[data-tema] .cdbx .ntsub{margin-top:6px!important;display:block}\n'
      '.cdbx .ntsub b{font-size:11.5px;font-weight:800;letter-spacing:0}\n'
      '.cdbx .ntsub b .ndec{font-size:9px}\n'
      '/* a palavra "estilo" sai da linha do modelo (ordem do Luis).\n'
      '   ⚠️ CORRIGIDO 15h40: eu tinha restringido a regra ao .cdbx e ao .cdpd,\n'
      '      e o card da PAGINA DE POSICOES nao tem nenhuma das duas classes —\n'
      '      la a palavra continuou. So dava para ver num card BASICO sem estilo\n'
      '      proprio (o Thibaut Courtois), porque nos outros a linha nem aparece.\n'
      '      Agora vale para QUALQUER .cd, que e o que ele pediu. */\n'
      'html[data-tema] .cd .mi .cdmdl:before{content:""!important}\n'
      'html[data-tema] .cdbx .mi .cdmdl:before{content:""!important}\n'
      '.cdbx .mi .cdmdl .tg.se{margin-right:5px}\n'
      '</style>\n')

    js = (
      '<script>\n'
      '/* ===== HOME_EM_BLOCOS_1608 — a tela de inicio em blocos ===== */\n'
      '(function(){\n'
      ' if(typeof homeRender!=="function") return;\n'
      ' if(typeof topoDoTipo!=="function"||typeof nota!=="function") return;\n'
      '\n'
      ' function pctDo(c){ var t=topoDoTipo(c.tipo), n=nota(c); return t>0?100*n/t:0; }\n'
      '\n'
      ' /* a ordem da box passa a ser pelo % do topo, nao pela nota (ordem do Luis) */\n'
      ' function melhoresPct(cs){\n'
      '  var b={};\n'
      '  cs.forEach(function(c){ var k=c.nome, v=pctDo(c);\n'
      '   if(!b[k]||v>b[k][1]) b[k]=[c,v]; });\n'
      '  return Object.keys(b).map(function(k){return b[k];})\n'
      '   .sort(function(x,y){return y[1]-x[1];}).map(function(p){return p[0];});\n'
      ' }\n'
      '\n'
      ' /* a previa do card DA BOX. O _hcd da casca continua intocado, e e ele\n'
      '    que o podio das funcoes usa. */\n'
      ' function cdBox(c,i){\n'
      '  var n=nota(c), p=pctDo(c), ref=notaMed(c.tipo);\n'
      '  var cr = p>=99.5?"#8fd694":(p>=90?"#f0a531":"var(--txt3)");\n'
      '  var bas = estiloAtiva(c) ? "" :\n'
      '   "<span class=\\"tg se\\" title=\\"o estilo dele nao liga nesta posicao — aqui ele joga como BASICO\\">BÁSICO</span> ";\n'
      '  var mdl = (c.modelo&&c.modelo!==c.tipo) ? c.modelo : "";\n'
      '  var est = (bas||mdl) ? ("<span class=cdmdl>"+bas+mdl+"</span>") : "";\n'
      '  var refaz = c.velha ?\n'
      '   " <span class=\\"tg vl\\" title=\\"o motor esta recalculando esta linha — esta e a nota anterior\\">↻ refazendo</span>" : "";\n'
      '  var pc = p.toFixed(2).split(".");\n'
      '  return "<div class=\\"cd cdbx\\" data-k=\\""+c.id+"|"+c.tipo+"\\">"\n'
      '   + "<div class=rk>"+(i+1)+"º</div>"\n'
      '   + "<img src=\\"https://efimg.com/efootballhub22/images/player_cards/"\n'
      '     + String(c.id).split("@")[0]\n'
      '     + "_l.png\\" loading=lazy onerror=\\"this.style.visibility=&quot;hidden&quot;\\">"\n'
      '   + "<div class=nt style=\\"color:"+cr+"\\">"\n'
      '     + pc[0] + "<span class=ndec>,"+pc[1]+"</span><span class=bxsg>%</span>"\n'
      '     + "<span class=ntsub><b style=\\"color:"+cor(n,ref)+"\\">nota "+_nd(n)+"</b></span>"\n'
      '     + "</div>"\n'
      '   + "<div class=nm>"+c.nome+refaz+"</div>"\n'
      '   + "<div class=mi><b>"+c.tipo+"</b> <span class=hpos>"+(c.np||"")+"</span>"\n'
      '     + est + "</div>"\n'
      '   + "</div>";\n'
       ' }\n'
      '\n'
      ' /* a box em tela cheia — "abrir como se fosse uma nova pagina" */\n'
      ' window.HOME_CHEIA=null;\n'
      ' window.abreBoxCheia=function(n){ window.HOME_CHEIA=n; homeRender();\n'
      '  window.scrollTo(0,0); };\n'
      ' window.fechaBoxCheia=function(){ window.HOME_CHEIA=null; homeRender();\n'
      '  window.scrollTo(0,0); };\n'
      '\n'
      ' window.homeRender=function(){\n'
      '  var w=document.getElementById("homewrap"); if(!w) return;\n'
      '  var cx={};\n'
      '  D.forEach(function(c){ if(c.id==="MOLDE"||!c.pacote) return;\n'
      '   (cx[c.pacote]=cx[c.pacote]||[]).push(c); });\n'
      '\n'
      '  /* ---- a box aberta em tela cheia ---- */\n'
      '  var ch=window.HOME_CHEIA;\n'
      '  if(ch && cx[ch]){\n'
      '   var todos=melhoresPct(cx[ch]);\n'
      '   w.innerHTML = "<section class=hbloco><div class=htt>"\n'
      '    + "<button class=hvolta onclick=\\"fechaBoxCheia()\\">← voltar</button>"\n'
      '    + "<h2>"+ch+"</h2><span class=hsub>"+todos.length+" card"\n'
      '    + (todos.length===1?"":"s")+" · na ordem do % do topo</span></div>"\n'
      '    + "<div class=grade>"\n'
      '    + todos.map(function(c,i){return cdBox(c,i);}).join("")\n'
      '    + "</div></section>";\n'
      '   w.querySelectorAll("[data-k]").forEach(function(el){\n'
      '    el.onclick=function(){ abrir(el.dataset.k); }; });\n'
      '   return;\n'
      '  }\n'
      '\n'
      '  /* ---- os lancamentos, um bloco por campanha ---- */\n'
      '  var nomes=Object.keys(cx).map(function(n){ return [n,melhoresPct(cx[n])]; })\n'
      '   .sort(function(a,b){ return pctDo(b[1][0])-pctDo(a[1][0]); });\n'
      '  var h="<section class=hbloco><div class=htt><h2>Lançamentos</h2>"\n'
      '   + "<span class=hsub>"+nomes.length+" box"+(nomes.length===1?"":"es")\n'
      '   + " · top 3 de cada um</span></div>";\n'
      '  h += "<div class=hgrid>" + nomes.map(function(par){\n'
      '   var n=par[0], cs=par[1], mo=cs.slice(0,3);\n'
      '   return "<div class=hbox><div class=hboxt><span class=hboxn>"+n+"</span>"\n'
      '    + "<span class=hboxc>"+cs.length+" card"+(cs.length===1?"":"s")+"</span>"\n'
      '    + (cs.length>3 ? ("<button class=hmais data-box=\\""+n+"\\">ver os "\n'
      '        + cs.length + " cards</button>") : "")\n'
      '    + "</div><div class=\\"grade gradebx\\">"\n'
      '    + mo.map(function(c,i){ return cdBox(c,i); }).join("")\n'
      '    + "</div></div>";\n'
      '  }).join("") + "</div></section>";\n'
      '\n'
      '  /* ---- o Top 3: quem monta e o homeTop3, do bloco PODIO_E_BLOCOS_1608 ---- */\n'
      '  h += (typeof homeTop3==="function") ? homeTop3() : "";\n'
      '\n'
      '  w.innerHTML=h;\n'
      '  w.querySelectorAll("[data-k]").forEach(function(el){\n'
      '   el.onclick=function(){ abrir(el.dataset.k); }; });\n'
      '  w.querySelectorAll(".hmais").forEach(function(b){\n'
      '   b.onclick=function(e){ e.stopPropagation(); abreBoxCheia(b.dataset.box); }; });\n'
      ' };\n'
      '})();\n'
      '</script>\n')

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + js + html[k:]
    return html, 'entrou'


# ============================================================================
#  A PALAVRA "PONTUACAO", O TOP 3 EM QUATRO BLOCOS E O PODIO NOVO — 16/08/2026
#
#  Ordens do Luis, na sequencia em que ele falou:
#
#  A) *"a nomenclatura nota nao existe mais, ela agora e pontuacao. E isso em
#     qualquer parte do sistema, qualquer pagina que aparecer, qualquer
#     visualizacao."*
#     ⚠️ So o ROTULO. Nome de variavel (nota(), notaMed, b1n, notaDe) fica —
#     trocar isso quebraria a tela inteira e nao muda nada para ele.
#     ⚠️ A palavra "nota" em cima do numero grande do card NAO esta no HTML:
#     ela e um `content:"nota"` do CSS. Quem procurar no gerador nao acha.
#
#  B) *"o top 3 de cada funcao... nao estou gostando desse design. A linha do
#     goleiro so tem defensivo e ofensivo, entao sobra espaco. Voce vai colocar
#     um bloco pra goleiro, um bloco pra defesa, um bloco de campo e um bloco
#     pra ataque."*
#
#  C) *"cada funcao tem tipo um podio, o primeiro no meio... vamos colocar o
#     primeiro do lado esquerdo, o segundo do lado direito num card um pouco
#     menor, o terceiro do lado do segundo um pouco menor."*
#
#  D) O card do podio: *"aqui nos vamos mostrar em evidencia a pontuacao,
#     embaixo o topo. O bruto tem que sair, qualquer etiqueta que tiver aí tem
#     que sair — nova, migrado, meta, qualquer uma. E o estilo voce coloca so o
#     nome. Se for algum que e basico, voce coloca a etiqueta basico na frente."*
#
#  E) *"voce ja aproveita pra inserir essas alteracoes na pagina de posicoes,
#     porque tem as mesmas informacoes da pagina inicial so por posicoes."*
#
#  ⚠️ INVERSAO PROPOSITAL, confirmada por ele: nos LANCAMENTOS o numero grande e
#     o % do topo; no PODIO e na PAGINA DE POSICOES o numero grande e a
#     PONTUACAO. Nao e engano — ele confirmou com estas palavras: *"e isso
#     mesmo, e o contrario."*
# ============================================================================
def patch_pontuacao_e_podio_1608(html):
    fora = []

    # ------------------------------------------------------------------ (A)
    #  A palavra. Cada par e um rotulo que o olho dele le na tela.
    #  Nao entra aqui nada que seja nome de variavel, chave de ordenacao
    #  (data-s=nota) ou comentario de codigo.
    # ------------------------------------------------------------------
    pares = [
        # o rotulo em cima do numero grande do card — mora no CSS, nao no HTML
        ('content:"nota"',                      'content:"pontuação"'),
        # o cabecalho da tabela
        ('<th data-s=nota>Nota</th>',           '<th data-s=nota>Pontuação</th>'),
        # a ficha
        ('<span class=fhdl>nota final</span>',  '<span class=fhdl>pontuação final</span>'),
        # textos corridos
        ('): nota ',                            '): pontuação '),
        ('as notas do campo estão',             'as pontuações do campo estão'),
        ('buscando a maior nota',               'buscando a maior pontuação'),
        ('esta \u00e9 a nota anterior',           'esta é a pontuação anterior'),
        ('esta e a nota anterior',               'esta e a pontuacao anterior'),
        ('e a nota N\u00c3O muda',              'e a pontuação NÃO muda'),
        ('a nota está por baixo',               'a pontuação está por baixo'),
        ('pode não bater com a nota',           'pode não bater com a pontuação'),
        ('cada uma tem build e nota própria',   'cada uma tem build e pontuação própria'),
        ('a nota sai só com o que já é certo',  'a pontuação sai só com o que já é certo'),
        ('A nota que aparece na tela',          'A pontuação que aparece na tela'),
        ('NOTA 0-10',                           'PONTUAÇÃO 0-10'),
        # o que o meu proprio bloco dos lancamentos escreve
        ('>nota "+_nd(n)+"<',                   '>pontuação "+_nd(n)+"<'),
    ]
    trocas = 0
    for a, b in pares:
        n = html.count(a)
        if n:
            html = html.replace(a, b)
            trocas += n
        else:
            fora.append(a[:34])

    # ------------------------------------------------------------------ (E)
    #  O CARD DA PAGINA DE POSICOES — o template do render() da casca.
    #  Sai: o MAX/OVR do topo, o + NOVA, o MIGRADO, o bruto e a fileira
    #  inteira de etiquetas. Fica: o "refazendo" (e aviso de estado, nao
    #  enfeite) e o BASICO, que desce para a frente do nome do estilo.
    # ------------------------------------------------------------------
    pos = 0

    #  ⚠️ NAO da para mirar na casca aqui: outro patch ja reescreveu este trecho
    #     antes de mim (o c.temMax/sisOvr virou c.maxOvr). Vai por padrao, e so
    #     no card do RANKING — o <div class=ovx>MOLDE</div> nao pode ser tocado.
    padrao = re.compile(r"<div class=ovx>\$\{[^{}]*?OVR '\+c\.ovr\}</div>\n?")
    html, k = padrao.subn('', html)
    if k:
        pos += 1
    else:
        fora.append('o MAX/OVR do card do ranking')

    a = ("<div class=nm>${c.NOVO?'<span class=\"tg nv\">\u2726 NOVA</span> ':''}${c.nome}"
         "${c.MIG?' <span class=\"tg mg\">MIGRADO</span>':''}")
    b = "<div class=nm>${c.nome}"
    if a in html:
        html = html.replace(a, b); pos += 1
    else:
        fora.append('o NOVA/MIGRADO do card do ranking')

    a = ("${estiloAtiva(c)?'':' <span class=\"tg se\" title=\"o estilo de jogo dele n\u00e3o "
         "liga nesta posi\u00e7\u00e3o \u2014 aqui ele joga como B\u00c1SICO\">B\u00c1SICO</span>'}</div>")
    if a in html:
        html = html.replace(a, '</div>'); pos += 1
    else:
        fora.append('o BASICO sair do nome, no card do ranking')

    #  o BASICO entra na frente do nome do estilo, e o estilo perde a palavra
    #  "estilo" (que tambem vem do CSS, no :before do .cdmdl)
    a = ("${(c.modelo&&c.modelo!==c.tipo)?' <span class=cdmdl>'+c.modelo+'</span>':''}</div>")
    b = ("${(function(){var bs=estiloAtiva(c)?'':'<span class=\"tg se\" title=\"o estilo de "
         "jogo dele nao liga nesta posicao - aqui ele joga como BASICO\">B\u00c1SICO</span> ';"
         "var md=(c.modelo&&c.modelo!==c.tipo)?c.modelo:'';"
         "return (bs||md)?(' <span class=cdmdl>'+bs+md+'</span>'):'';})()}</div>")
    if a in html:
        html = html.replace(a, b); pos += 1
    else:
        fora.append('o BASICO ir para a linha do estilo, no card do ranking')

    a = "<i>bruto ${(c.b1||0).toFixed(1)}</i>"
    if a in html:
        html = html.replace(a, ''); pos += 1
    else:
        fora.append('o bruto do card do ranking')

    #  a fileira de etiquetas inteira
    i = html.find('<div class=tags>${c._org&&VP()?')
    if i >= 0:
        j = html.find('</div>', i)
        if j > 0:
            html = html[:i] + '<div class=tags></div>' + html[j + 6:]
            pos += 1
    else:
        fora.append('a fileira de etiquetas do card do ranking')

    # ------------------------------------------------------------------ (B+C+D)
    #  O TOP 3: quatro blocos, e o podio virado.
    #  So CSS + a segunda metade da homeRender, que este gerador ja redefine.
    # ------------------------------------------------------------------
    css = (
      '<style>\n'
      '/* PODIO_E_BLOCOS_1608 */\n'
      '/* CORRIGIDO 15h30 — o bloco por SETOR espremia o podio (o nome do card\n'
      '   quebrava letra a letra). Ordem do Luis: "pode deixar cada um no seu\n'
      '   bloco mesmo, ai voce divide eles em duas colunas".\n'
      '   Cada FUNCAO e um bloco. Duas colunas. E cada area do campo tem o seu\n'
      '   proprio grid, entao NUNCA sobra uma funcao de outra area do lado —\n'
      '   se o meio tem 3, ficam 2 em cima e 1 embaixo, e a linha acaba ali. */\n'
      '.hfns{grid-template-columns:repeat(2,minmax(0,1fr))!important;\n'
      ' gap:20px 20px!important;margin-bottom:26px!important}\n'
      '.hfn{border:1px solid var(--line,#1f2733);border-radius:9px;padding:13px 14px 15px}\n'
      'html[data-tema] .hfn{background:var(--surf2)!important;border-radius:14px!important}\n'
      '.hfn>.hfnt{margin:0 0 11px!important}\n'
      '@media(max-width:1180px){ .hfns{grid-template-columns:1fr!important} }\n'
      '/* o podio deixa de ser 2-1-3 e passa a ser 1-2-3, decrescente.\n'
      '   CORRIGIDO 15h30: era 1.28 / 1 / .86 e o 1o ficou desproporcional\n'
      '   demais ao lado dos outros dois. Ordem do Luis: "da uma aumentadinha\n'
      '   nos outros cards tambem". */\n'
      '.pod{grid-template-columns:1.13fr 1fr .94fr!important}\n'
      '.podc.p1{order:1!important}.podc.p2{order:2!important}.podc.p3{order:3!important}\n'
      '.podc.p1 .ped{border-radius:0 0 0 6px!important}\n'
      '.podc.p2 .ped{border-radius:0!important}\n'
      '.podc.p3 .ped{border-radius:0 0 6px 0!important}\n'
      '/* o card do podio: a pontuacao em evidencia, o % do topo embaixo.\n'
      '\n'
      '   🔴 CORRIGIDO 15h30 — A FOTO VIRA COLUNA.\n'
      '   O 1o colocado leva a classe .cdbig, e o tema da a ela um grid\n'
      '   proprio: "nota nota" na primeira linha. Resultado: a pontuacao\n'
      '   atravessava o card inteiro e a foto ficava EMBAIXO dela — nas\n'
      '   palavras do Luis, "a nota esta em cima da cabeca deles".\n'
      '   Ordem: *"a foto do card do lado esquerdo como se fosse uma coluna,\n'
      '   e na coluna da direita voce coloca o resto — nota em cima, embaixo\n'
      '   o nome, e o restante das informacoes."*\n'
      '   Entao os TRES cards do podio usam o mesmo desenho, e o 1o e maior\n'
      '   so na largura da coluna da foto. */\n'
      'html[data-tema] .cdpd,html[data-tema] .cdpd.cdbig{\n'
      ' grid-template-columns:62px minmax(0,1fr)!important;\n'
      ' grid-template-areas:"foto nota" "foto nome" "foto sub"!important;\n'
      ' column-gap:10px!important;align-content:start}\n'
      'html[data-tema] .cdpd.cdbig{grid-template-columns:74px minmax(0,1fr)!important}\n'
      'html[data-tema] .cdpd>img{align-self:start!important}\n'
      'html[data-tema] .cdpd .nm{margin:7px 0 0!important}\n'
      'html[data-tema] .cdpd .mi{margin:4px 0 0!important}\n'
      'html[data-tema] .cdpd .nt:before{content:"pontuação"!important}\n'
      'html[data-tema] .cdpd .ntsub{margin-top:6px!important;display:block}\n'
      '.cdpd .ntsub b{font-size:11.5px;font-weight:800}\n'
      'html[data-tema] .cdpd .mi .cdmdl:before{content:""!important}\n'
      '.cdpd .mi .cdmdl .tg.se{margin-right:5px}\n'
      '.cdpd .tags{display:none!important}\n'
      '</style>\n')

    js = (
      '<script>\n'
      '/* ===== PODIO_E_BLOCOS_1608 ===== */\n'
      '(function(){\n'
      ' if(typeof window.homeRender!=="function") return;\n'
      '\n'
      ' /* o card do podio. Mesmas areas do grid do tema — so o conteudo muda. */\n'
      ' window.cdPodio=function(c,i,ref){\n'
      '  var n=nota(c), t=topoDoTipo(c.tipo), p=t>0?100*n/t:0;\n'
      '  var cr = p>=99.5?"#8fd694":(p>=90?"#f0a531":"var(--txt3)");\n'
      '  var bas = estiloAtiva(c) ? "" :\n'
      '   "<span class=\\"tg se\\" title=\\"o estilo dele nao liga nesta posicao — aqui ele joga como BASICO\\">BÁSICO</span> ";\n'
      '  var mdl = (c.modelo&&c.modelo!==c.tipo) ? c.modelo : "";\n'
      '  var est = (bas||mdl) ? ("<span class=cdmdl>"+bas+mdl+"</span>") : "";\n'
      '  var refaz = c.velha ?\n'
      '   " <span class=\\"tg vl\\" title=\\"o motor esta recalculando esta linha — esta e a pontuacao anterior\\">↻ refazendo</span>" : "";\n'
      '  return "<div class=\\"cd cdpd"+((i===0)?" cdbig":"")+"\\" data-k=\\""+c.id+"|"+c.tipo+"\\">"\n'
      '   + "<img src=\\"https://efimg.com/efootballhub22/images/player_cards/"\n'
      '     + String(c.id).split("@")[0]\n'
      '     + "_l.png\\" loading=lazy onerror=\\"this.style.visibility=&quot;hidden&quot;\\">"\n'
      '   + "<div class=nt style=\\"color:"+cor(n,ref)+"\\">"+_nd(n)\n'
      '     + "<span class=ntsub><b style=\\"color:"+cr+"\\">"\n'
      '     + p.toFixed(2).replace(".",",") + "%</b> do topo</span></div>"\n'
      '   + "<div class=nm>"+c.nome+refaz+"</div>"\n'
      '   + "<div class=mi><b>"+c.tipo+"</b> <span class=hpos>"+(c.np||"")+"</span>"\n'
      '     + est + "</div>"\n'
      '   + "</div>";\n'
      ' };\n'
      '\n'
      ' /* a segunda metade da home: os quatro setores viram quatro blocos */\n'
      ' window.homeTop3=function(){\n'
      '  var porTipo={};\n'
      '  D.forEach(function(c){ if(c.id==="MOLDE") return;\n'
      '   (porTipo[c.tipo]=porTipo[c.tipo]||[]).push(c); });\n'
      '  var h="<section class=hbloco><div class=htt><h2>Top 3 de cada função</h2>"\n'
      '   + "<span class=hsub>18 funções</span></div>";\n'
      '  SET.forEach(function(par){\n'
      '   var sn=par[0], fams=par[1], dentro="";\n'
      '   fams.forEach(function(fm){\n'
      '    var fx=(FAM.find(function(z){return z[0]===fm;})||[0,[]])[1];\n'
      '    fx.forEach(function(fn){\n'
      '     var cs=_hmelhores(porTipo[fn]||[]).slice(0,3); if(!cs.length) return;\n'
      '     var ref=notaMed(fn);\n'
      '     dentro += "<div class=hfn><div class=hfnt>"+fn+" <span>"+(SIG[fm]||"")\n'
      '      + "</span></div><div class=pod>"\n'
      '      + cs.map(function(c,i){ return "<div class=\\"podc p"+(i+1)+"\\">"\n'
      '         + cdPodio(c,i,ref) + "<div class=ped><b>"+(i+1)+"º</b></div></div>";\n'
      '        }).join("") + "</div></div>";\n'
      '    });\n'
      '   });\n'
      '   /* um grid por area: o proximo setor sempre comeca em linha nova */\n'
      '   if(dentro) h += "<div class=hset>"+sn+"</div><div class=hfns>"+dentro+"</div>";\n'
      '  });\n'
      '  return h + "</section>";\n'
      ' };\n'
      '})();\n'
      '</script>\n')

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + js + html[k:]

    msg = '%d rotulos · %d de 6 no card do ranking' % (trocas, pos)
    if fora:
        msg += ' · NAO ACHEI (%d): %s' % (len(fora), ' | '.join(fora))
    return html, msg


# ============================================================================
#  O CABECALHO, OS FILTROS E O ALCANCE DA BUSCA — 16/08/2026
#
#  8) *"essa parte aí de ficha do sistema, escala, isso tudo que eu printei,
#     voce vai tirar. Voce vai colocar lá no lugar essa aí que tem a quantidade
#     de linhas e de completos. E do lado de boxes anteriores voce vai colocar o
#     campo de busca — voce vai tirar ele de onde ele esta e vai colocar la."*
#
#  9) *"o resto das ferramentas de busca voce pode refazer tudo porque tem um
#     monte de coisa que nao serve pra nada. O que a gente tem que ter ali e
#     busca e filtro: filtrar por posicao, por funcao, por estilo de jogo, e um
#     jeito de filtrar tambem por minimo e maximo de nota e de percentual."*
#
# 11) *"na pagina inicial a busca e por todo mundo; na pagina de posicoes a
#     busca e so por quem esta na posicao escolhida."*
#
#  ⛔ NADA E APAGADO — o que sai fica com display:none.
#     O render() da casca le #tier, #posfab, #orig, #vm, #mx e #ps toda vez que
#     roda. Removendo os elementos do DOM, ele quebra na primeira linha. Escondidos,
#     continuam valendo "Todos" e a tela nao sente. E devolver qualquer um deles
#     e apagar uma linha de CSS.
#
#  ⛔ E O QUE NAO E FILTRO CONTINUA: ver por · vista · destacar · os dois
#     recalcular. Ele falou de FILTROS; esses cinco sao ferramenta. So sairam do
#     meio dos filtros e foram para um bloco proprio embaixo. Apagar botao que
#     funciona sem ordem expressa ja custou caro nesta tela.
# ============================================================================
def patch_cabecalho_e_filtros_1608(html):
    if 'CABECALHO_E_FILTROS_1608' in html:
        return html, 'ja estava'

    css = (
      '<style>\n'
      '/* CABECALHO_E_FILTROS_1608 */\n'
      '/* 8a · o bloco da direita sai (escondido, nao apagado) */\n'
      'header #subtxt,header #fichasis{display:none!important}\n'
      '/* 8b · o contador vai para a direita */\n'
      'header h1{display:flex!important;align-items:center;gap:7px;flex-wrap:wrap;\n'
      ' width:100%;box-sizing:border-box;padding-right:12px}\n'
      '#contbar{margin-left:auto!important}\n'
      '/* 8c · a busca no cabecalho, do lado do boxes anteriores */\n'
      '#qtopo{display:flex;align-items:center;gap:0;position:relative}\n'
      '#qtopo input{width:230px!important;padding-left:26px!important;font-size:12px}\n'
      '#qtopo:before{content:"\\2315";position:absolute;left:8px;top:50%;\n'
      ' transform:translateY(-50%);opacity:.55;pointer-events:none;font-size:13px}\n'
      '#qtopo .qesc{position:absolute;right:7px;top:50%;transform:translateY(-50%);\n'
      ' cursor:pointer;opacity:.5;font-size:13px;line-height:1;display:none}\n'
      '#qtopo.tem .qesc{display:block}\n'
      '/* 9 · os filtros que sairam */\n'
      '#filtros .ctl .fld.saiu{display:none!important}\n'
      '/* 9 · o bloco das ferramentas, separado dos filtros */\n'
      '#ferrag{border-top:1px solid var(--line,#1f2733);margin-top:12px;padding-top:11px}\n'
      'html[data-tema] #ferrag{border-top-color:rgba(255,255,255,.16)!important}\n'
      '#ferrag>.ftit{font-size:9px;letter-spacing:1.4px;font-weight:800;\n'
      ' margin:0 0 9px;opacity:.66}\n'
      '/* a barra lateral: grupo VAZIO nao aparece.\n'
      '   O SEGUNDO ATACANTE (SA) sobrou de quando essa funcao virou\n'
      '   "Atacante infiltrador" e foi para o grupo MEIA ATACANTE. O botao\n'
      '   ficou la, sem nada dentro. A regra e geral, nao e o caso isolado:\n'
      '   grupo que nao tem nenhuma funcao dentro nao tem por que existir. */\n'
      '#filtros .famg.vazio{display:none!important}\n'
      '/* 9 · a faixa de pontuacao e de percentual */\n'
      '.faixa{display:flex;align-items:center;gap:6px}\n'
      '.faixa input{width:100%!important;min-width:0}\n'
      '.faixa em{font-style:normal;opacity:.5;font-size:11px}\n'
      '</style>\n')

    js = (
      '<script>\n'
      '/* ===== CABECALHO_E_FILTROS_1608 ===== */\n'
      '(function(){\n'
      ' function achou(){ return document.getElementById("q")\n'
      '   && document.querySelector("header h1")\n'
      '   && document.querySelector("#filtros .ctl"); }\n'
      '\n'
      ' function monta(){\n'
      '  if(document.getElementById("qtopo")) return true;\n'
      '  if(!achou()) return false;\n'
      '  var h1=document.querySelector("header h1");\n'
      '  var q=document.getElementById("q");\n'
      '  var ctl=document.querySelector("#filtros .ctl");\n'
      '\n'
      '  /* --- 8c · a busca sobe. Mover o proprio elemento preserva os\n'
      '         ouvintes que a casca ja pendurou nele. --- */\n'
      '  var cx=document.createElement("span"); cx.id="qtopo";\n'
      '  var velhoPai=q.parentNode;\n'
      '  cx.appendChild(q);\n'
      '  var esc=document.createElement("span"); esc.className="qesc"; esc.textContent="\\u00d7";\n'
      '  esc.title="limpar a busca";\n'
      '  cx.appendChild(esc);\n'
      '  if(velhoPai && velhoPai.className==="fld") velhoPai.style.display="none";\n'
      '  var ref=document.getElementById("boxbt")||document.getElementById("condflut")\n'
      '        ||document.getElementById("fbt");\n'
      '  if(ref&&ref.parentNode===h1) h1.insertBefore(cx, ref.nextSibling);\n'
      '  else h1.appendChild(cx);\n'
      '\n'
      '  /* --- 11 · o alcance da busca muda com a pagina --- */\n'
      '  /* ⚠️ o HOME da casca e `let`, e `let` no topo de um script NAO vira\n'
      '     propriedade de window. Tem de ler pelo escopo lexico. */\n'
      '  function naHome(){ try{ return !!HOME; }catch(e){ return false; } }\n'
      '  function ajustaPlaceholder(){\n'
      '   q.placeholder = naHome() ? "buscar em todos os cards"\n'
      '                            : "buscar nesta posição";\n'
      '  }\n'
      '  ajustaPlaceholder();\n'
      '  setInterval(ajustaPlaceholder, 700);\n'
      '  esc.onclick=function(){ q.value=""; cx.classList.remove("tem");\n'
      '   try{ if(naHome()){ var w=document.getElementById("gbWrap");\n'
      '        if(w) w.style.display="none"; } else render(); }catch(e){} };\n'
      '  q.addEventListener("input", function(){\n'
      '   cx.classList.toggle("tem", !!q.value);\n'
      '   /* na inicial, quem responde e a busca global — ela varre o D inteiro,\n'
      '      todas as funcoes. Na pagina de posicoes o render() ja filtra dentro\n'
      '      da funcao aberta, e nao se mexe nele. */\n'
      '   if(!naHome()) return;\n'
      '   var w=document.getElementById("gbWrap"), gi=document.getElementById("gbIn");\n'
      '   if(!w||!gi) return;\n'
      '   if(!q.value){ w.style.display="none"; return; }\n'
      '   w.style.display="";\n'
      '   gi.value=q.value;\n'
      '   gi.dispatchEvent(new Event("input",{bubbles:true}));\n'
      '  });\n'
      '\n'
      '  /* --- a barra lateral: esconde grupo sem nenhuma funcao dentro --- */\n'
      '  function limpaGrupos(){\n'
      '   var n=0;\n'
      '   Array.prototype.slice.call(document.querySelectorAll("#fam .famg"))\n'
      '    .forEach(function(g){\n'
      '      var tem=g.querySelectorAll(".tabs .tab").length;\n'
      '      if(!tem){ g.classList.add("vazio"); n++; }\n'
      '      else g.classList.remove("vazio");\n'
      '    });\n'
      '   /* e o setor que ficou sem nenhum grupo visivel some junto */\n'
      '   Array.prototype.slice.call(document.querySelectorAll("#fam .setor"))\n'
      '    .forEach(function(st){\n'
      '      var vis=Array.prototype.slice.call(st.querySelectorAll(".famg"))\n'
      '        .filter(function(g){ return !g.classList.contains("vazio"); }).length;\n'
      '      st.style.display = vis ? "" : "none";\n'
      '    });\n'
      '   window._GRUPOS_VAZIOS = n;\n'
      '  }\n'
      '  limpaGrupos();\n'
      '  setTimeout(limpaGrupos, 1200);\n'
      '\n'
      '  /* --- os nomes de GRUPO que o Luis trocou, 16/08 15h35 ---\n'
      '     Ordem dele, com estas palavras: "meia lateral nao e mais meia\n'
      '     lateral, e ALA. Ponta nao e mais ponta, e ATACANTE."\n'
      '     Acompanha o rotulo longo, que ja era Ala finalizador / Ala cruzador\n'
      '     e Atacante criador / Atacante finalizador.\n'
      '     ⚠️ So o que aparece na tela. O data-g continua o nome antigo, porque\n'
      '        e ele que o FAM e o resto do codigo usam para achar o grupo. */\n'
      '  var NOMEGRUPO = { "MEIA LATERAL":"ALA", "PONTA":"ATACANTE" };\n'
      '  function renomeiaGrupos(){\n'
      '   var n=0;\n'
      '   Array.prototype.slice.call(document.querySelectorAll("#fam .famt[data-g]"))\n'
      '    .forEach(function(t){\n'
      '      var g=t.getAttribute("data-g"), novo=NOMEGRUPO[g];\n'
      '      if(!novo) return;\n'
      '      var b=t.querySelector("b");\n'
      '      if(b && b.textContent!==novo){ b.textContent=novo; n++; }\n'
      '    });\n'
      '   window._GRUPOS_RENOMEADOS = n;\n'
      '  }\n'
      '  renomeiaGrupos();\n'
      '  setTimeout(renomeiaGrupos, 1200);\n'
      '\n'
      '  /* --- 9 · os filtros que saem, escondidos um a um pelo id --- */\n'
      '  ["tier","posfab","orig","vm","mx","ps"].forEach(function(id){\n'
      '   var e=document.getElementById(id); if(!e) return;\n'
      '   var f=e.closest(".fld"); if(f) f.classList.add("saiu");\n'
      '  });\n'
      '\n'
      '  /* --- 9 · a faixa de pontuacao e a de percentual --- */\n'
      '  function faixa(id,rot,ph1,ph2){\n'
      '   var d=document.createElement("div"); d.className="fld";\n'
      '   d.innerHTML="<span>"+rot+"</span><div class=faixa>"\n'
      '    +"<input type=number id="+id+"min placeholder=\\""+ph1+"\\">"\n'
      '    +"<em>até</em>"\n'
      '    +"<input type=number id="+id+"max placeholder=\\""+ph2+"\\"></div>";\n'
      '   return d;\n'
      '  }\n'
      '  var alvo=document.getElementById("mdl");\n'
      '  var dep=alvo?alvo.closest(".fld"):ctl.firstChild;\n'
      '  var f1=faixa("pnt","pontuação","mín","máx");\n'
      '  var f2=faixa("pct","% do topo","mín","máx");\n'
      '  if(dep&&dep.nextSibling) { ctl.insertBefore(f1,dep.nextSibling);\n'
      '                             ctl.insertBefore(f2,f1.nextSibling); }\n'
      '  else { ctl.appendChild(f1); ctl.appendChild(f2); }\n'
      '\n'
      '  /* --- 9 · o que nao e filtro desce para um bloco proprio --- */\n'
      '  var g=document.createElement("div"); g.id="ferrag";\n'
      '  g.innerHTML="<div class=ftit>FERRAMENTAS</div>";\n'
      '  ctl.appendChild(g);\n'
      '  ["verpor","view"].forEach(function(id){\n'
      '   var e=document.getElementById(id); if(!e) return;\n'
      '   var f=e.closest(".fld"); if(f) g.appendChild(f);\n'
      '  });\n'
      '  var dst=ctl.querySelector(".dst"); if(dst) g.appendChild(dst);\n'
      '  Array.prototype.slice.call(ctl.querySelectorAll("button.hb"))\n'
      '   .forEach(function(b){ g.appendChild(b); });\n'
      '  var cnt=document.getElementById("cnt"); if(cnt) g.appendChild(cnt);\n'
      '\n'
      '  /* --- 9 · a faixa filtra depois do render, sem tocar no render --- */\n'
      '  var IDX=null;\n'
      '  function indice(){\n'
      '   if(IDX) return IDX;\n'
      '   IDX={};\n'
      '   D.forEach(function(c){ IDX[c.id+"|"+c.tipo]=c; });\n'
      '   return IDX;\n'
      '  }\n'
      '  function num(id){ var e=document.getElementById(id);\n'
      '   if(!e||e.value==="") return null; var v=parseFloat(e.value.replace(",","."));\n'
      '   return isNaN(v)?null:v; }\n'
      '  function aplicaFaixa(){\n'
      '   var pmin=num("pntmin"), pmax=num("pntmax"),\n'
      '       cmin=num("pctmin"), cmax=num("pctmax");\n'
      '   var out=document.getElementById("out"); if(!out) return;\n'
      '   var lig=(pmin!==null||pmax!==null||cmin!==null||cmax!==null);\n'
      '   var I=indice(), fora=0, dentro=0;\n'
      '   Array.prototype.slice.call(out.querySelectorAll("[data-k]")).forEach(function(el){\n'
      '    /* ⚠️ o tema poe display:grid!important no .cd — um display:none\n'
      '       inline SEM important perde para ele e o card continua na tela.\n'
      '       Tem de ser setProperty com a prioridade. */\n'
      '    if(!lig){ el.style.removeProperty("display"); return; }\n'
      '    var c=I[el.getAttribute("data-k")]; if(!c) return;\n'
      '    var n=nota(c), t=topoDoTipo(c.tipo), p=t>0?100*n/t:0, ok=true;\n'
      '    if(pmin!==null&&n<pmin) ok=false;\n'
      '    if(pmax!==null&&n>pmax) ok=false;\n'
      '    if(cmin!==null&&p<cmin) ok=false;\n'
      '    if(cmax!==null&&p>cmax) ok=false;\n'
      '    if(ok) el.style.removeProperty("display");\n'
      '    else   el.style.setProperty("display","none","important");\n'
      '    if(ok) dentro++; else fora++;\n'
      '   });\n'
      '   var av=document.getElementById("faixaav");\n'
      '   if(!av){ av=document.createElement("div"); av.id="faixaav";\n'
      '    av.style.cssText="font-size:10.5px;font-weight:700;margin-top:7px;opacity:.8";\n'
      '    var p2=document.getElementById("pctmax");\n'
      '    if(p2) p2.closest(".fld").appendChild(av); }\n'
      '   av.textContent = lig ? (dentro+" na faixa · "+fora+" escondidos") : "";\n'
      '  }\n'
      '  window.aplicaFaixa=aplicaFaixa;\n'
      '  ["pntmin","pntmax","pctmin","pctmax"].forEach(function(id){\n'
      '   var e=document.getElementById(id); if(e) e.addEventListener("input",aplicaFaixa);\n'
      '  });\n'
      '  if(typeof window.render==="function"){\n'
      '   var _r=window.render;\n'
      '   window.render=function(){ var v=_r.apply(this,arguments);\n'
      '    try{ aplicaFaixa(); }catch(e){} return v; };\n'
      '  }\n'
      '  return true;\n'
      ' }\n'
      '\n'
      ' /* o contador e o boxes anteriores nascem depois, por setInterval —\n'
      '    entao a montagem tambem insiste ate os dois existirem. */\n'
      ' if(!monta()){ var t=setInterval(function(){ if(monta()) clearInterval(t); }, 300); }\n'
      ' setTimeout(function(){ monta(); }, 1500);\n'
      '})();\n'
      '</script>\n')

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + js + html[k:]
    return html, 'entrou'


# ============================================================================
#  A ABA DO ELENCO — 16/08/2026
#
#  O Luis explicou primeiro PARA QUE serve, e isso muda tudo:
#
#    *"esse programa vai virar site. O usuario vai colocar os jogadores que ele
#     tem na conta dele do videogame aqui, e poder manipular eles. Vamos ter
#     dois tipos: o que usa esporadicamente e nao salva nada, e o LOGADO, que
#     a gente tem que salvar as coisas dele — principalmente o elenco."*
#
#  Os 114 cards dele nao sao a ficha dele: sao a massa de teste da ferramenta.
#
#  O QUE ELE PEDIU, na ordem em que falou:
#
#   1  a barra lateral nao aparece nesta aba — *"aqui nos estamos tratando do
#      time dele"*. O campo e a estrela e fica com a tela toda.
#   2  saem os blocos DEFESA / MEIO / ATAQUE / PARA A VAGA DE GK — *"nao precisa"*
#   3  🔴 as vagas estavam FORA do campo (causa raiz abaixo)
#   4  a foto do card na lista esta pequena demais
#   5  o card mostra nome · POSICAO · funcao · ESTILO DE JOGO
#   6  a pontuacao e a da POSICAO NATIVA — a maior funcao que usa aquela
#      posicao — com DUAS casas (Messi: SA -> Falso nove -> 112,00)
#   7  botoes de mover em cada lugar, sem precisar arrastar
#   8  o × pede confirmacao antes de excluir
#   9  teto de 11 titulares e 12 reservas
#  10  os tecnicos reservas saem do painel de jogo e vao para a area do
#      fora do banco — *"ali sao so os que vao pro jogo"*
#
#  ⛔ FICA PARA DEPOIS: a foto do tecnico. O tecnicos.json tem 1.664 tecnicos
#     com id, nome, pais, idade e habilidades, e NENHUM campo de imagem. Nao
#     invento endereco.
#
#  ⛔ E NAO APAGUEI os 114 dele. O botao de escolher entra ao lado; quem quiser
#     comecar do zero tem o `limpar` que ja existia.
#
#  COMO ENTRA: quase tudo e pos-processamento do DOM depois do mtRender(), em
#  vez de reescrever o mtRender inteiro (que e enorme e faz muita coisa). Se
#  este bloco cair, a aba volta ao que era sozinha.
# ============================================================================
def patch_elenco_1608(html):
    """A ABA DO ELENCO — o layout de 16/08 e o card unico.

    ORDEM DO LUIS, 16/08, com desenho a mao dele por cima da tela:
      *"tem que ser assim o design de cada card no elenco"* — foto em cima,
      nome, POSICAO · funcao, estilo de jogo, pontuacao, e os botoes empilhados
      na direita com o x no fim.
      *"as visualizacoes estao diferentes umas das outras... o ideal e que elas
      nao ficassem diferentes"* — o MESMO card no campo, no banco e fora dele.
      *"o campo em cima, do lado direito o tecnico escolhido e a formacao,
      embaixo os reservas de seis em seis... aliais de dois em dois, seis
      linhas, e embaixo o fora do banco de seis em seis"*.
      *"diminui o campo, coloca o goleiro colado no fim, e em cima poe o nome
      do time e o nome do usuario"*.

    ⛔ NENHUMA CONTA NOVA. Este patch le `mtNotaReal`, `nota`, `cor`, `notaMed`
    e `estiloAtiva`, que ja existiam, e nao escreve em banco nenhum.
    """
    if 'ELENCO_1608' in html:
        return html, 'ja estava'
    if 'mtRender' not in html:
        return html, 'NAO ACHEI o mtRender'

    css = (
      '<style>\n'
      '/* ELENCO_1608 — o design que o Luis fechou no base44, 17/08 */\n'
      '@media(max-height:820px){#mtwrap .mtcampo{position:relative!important}}\n'
      'body.naelenco #filtros{display:none!important}\n'
      '@media(min-width:840px){\n'
      ' body.naelenco header,body.naelenco main{margin-left:0!important}\n'
      ' body.naelenco main{padding-left:16px!important;padding-right:16px!important;\n'
      '  max-width:none!important;width:auto!important}\n'
      '}\n'
      '#mtwrap .mtresumo,#mtwrap .mtres,#mtwrap .mtfora{display:none!important}\n'
      #  duas médias na mesma tela, de contas diferentes: a de cima é a da casca
      'body.naelenco #mtwrap .mthd .mini{display:none!important}\n'
      '\n'
      '/* ---------- a paleta, medida no CSS do base44 ---------- */\n'
      #  🔴 MEDIDO na tela gerada: as variaveis entraram mas ninguem pintou o
      #  fundo — o cabecalho branco do tema claro engolia o nome do time.
      #  A aba do elenco e escura por desenho; aqui ela pinta o proprio fundo.
      #  🔴 MEDIDO: `body.naelenco{background:...!important}` PERDEU. O tema da
      #  casca pinta com `html[data-tema=claro] body` — especificidade (0,1,2)
      #  contra a minha (0,1,1). Empatar em !important nao basta; quem decide e
      #  a especificidade. Com `html[data-tema] body.naelenco` vai a (0,2,2).
      'html[data-tema] body.naelenco,body.naelenco{background:#101812!important;\n'
      ' color:#f2f6ec}\n'
      'body.naelenco main,body.naelenco #tela,body.naelenco #mtwrap{\n'
      ' background:transparent!important}\n'
      'body.naelenco{--elbg:#101812;--elpane:#17231c;--elbox:#1b2820;--ellinha:#243329;\n'
      ' --elfg:#f2f6ec;--elmudo:#9ca3af;--ellima:#bef264;--elverm:#e0533d;\n'
      ' --elrisco:rgba(226,255,238,.20);\n'
      ' --elcond:"Arial Narrow","Roboto Condensed",ui-sans-serif,system-ui,sans-serif}\n'
      'body.naelenco #elwrap{color:var(--elfg)}\n'
      '#elwrap{max-width:1400px;margin:0 auto;width:100%;padding:4px 0 0}\n'
      '@media(min-width:1700px){#elwrap{max-width:1560px}}\n'
      '\n'
      '/* ---------- o cabeçalho ---------- */\n'
      '#elfaixa{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;\n'
      ' gap:16px;padding-bottom:16px;margin-bottom:20px;border-bottom:1px solid var(--ellinha)}\n'
      '.eleyebrow{font-size:11px;letter-spacing:.3em;text-transform:uppercase;\n'
      ' color:var(--elmudo);margin:0 0 2px}\n'
      '.eltime{font-family:var(--elcond);font-size:48px;line-height:1;font-weight:700;\n'
      ' letter-spacing:-1.2px;cursor:text;outline:none;min-width:120px;display:inline-block;\n'
      ' border-bottom:1px dashed transparent}\n'
      '.eltime:hover{border-bottom-color:var(--ellinha)}\n'
      '.eltime:focus{border-bottom-color:var(--ellima)}\n'
      '.eldono{font-size:11px;color:var(--elmudo);margin-top:6px}\n'
      '.elstats{display:flex;gap:26px;flex-wrap:wrap}\n'
      '.elstat p{margin:0}\n'
      '.elstat p:first-child{font-size:10px;letter-spacing:.2em;text-transform:uppercase;\n'
      ' color:var(--elmudo)}\n'
      '.elstat p:last-child{font-family:var(--elcond);font-size:20px;font-weight:700;\n'
      ' font-variant-numeric:tabular-nums}\n'
      '\n'
      '/* ---------- as duas colunas ---------- */\n'
      '#elgrid{display:grid;gap:20px;grid-template-columns:1fr}\n'
      '@media(min-width:1024px){#elgrid{grid-template-columns:340px minmax(0,1fr)}}\n'
      '.elpane{border-radius:12px;border:1px solid var(--ellinha);background:var(--elpane);\n'
      ' padding:12px;align-self:start;min-width:0}\n'
      '.elpane.pousa{box-shadow:0 0 0 2px var(--ellima)}\n'
      '.elhd{display:flex;align-items:baseline;justify-content:space-between;gap:8px;\n'
      ' flex-wrap:wrap;font-size:12px;font-weight:700;letter-spacing:.2em;\n'
      ' text-transform:uppercase;margin:0}\n'
      '.elhd em{font-style:normal;font-size:10px;font-weight:400;color:var(--elmudo);\n'
      ' letter-spacing:.02em;text-transform:none}\n'
      '\n'
      '/* ---------- a placa da formação: ELA É O SELETOR ---------- */\n'
      #  ORDEM DO LUIS, 17/08: *"em cima tem duas formação — a placa e um
      #  seletor embaixo dizendo a mesma coisa. Tem que ter só uma, só a
      #  grandona."* Então o seletor virou uma camada transparente por cima da
      #  placa: clica na placa, abre a lista.
      '.elbadge{position:relative;display:flex;align-items:center;\n'
      ' justify-content:space-between;padding:14px 16px;border-radius:10px;\n'
      ' border:1px solid var(--ellinha);background:var(--elbox);margin-bottom:10px;\n'
      ' cursor:pointer;transition:border-color .12s}\n'
      '.elbadge:hover{border-color:var(--ellima)}\n'
      '.elbadge select{position:absolute;inset:0;width:100%;height:100%;opacity:0;\n'
      ' cursor:pointer;font-size:16px;border:none;background:transparent}\n'
      '.elbadge .elseta{position:absolute;right:14px;bottom:9px;font-size:10px;\n'
      ' color:var(--elmudo);pointer-events:none}\n'
      '.elbadge .ellbl{font-size:10px;letter-spacing:.2em;text-transform:uppercase;\n'
      ' color:var(--elmudo);margin:0}\n'
      '.elbadge .elnum{font-family:var(--elcond);font-size:44px;font-weight:700;\n'
      ' line-height:1;margin:0;letter-spacing:-1px;color:var(--ellima)}\n'
      '.eldots{display:flex;gap:4px;align-items:flex-end;height:28px}\n'
      '.eldots i{width:4px;border-radius:1px;background:var(--ellima);opacity:.85}\n'
      '.elcoach{display:flex;align-items:center;gap:12px;padding:12px;border-radius:10px;\n'
      ' border:1px solid var(--ellinha);background:var(--elbox);margin:10px 0}\n'
      '.elavatar{width:44px;height:44px;border-radius:50%;flex-shrink:0;background:#22332a;\n'
      ' border:1px solid var(--ellinha);display:flex;align-items:center;\n'
      ' justify-content:center;font-size:16px;font-weight:700;color:#9fc08a}\n'
      '.elcinfo{min-width:0}\n'
      '.elcinfo .elrole{font-size:10px;color:var(--elmudo);letter-spacing:.12em;\n'
      ' text-transform:uppercase;margin:0}\n'
      '.elcinfo .elcname{font-size:14px;font-weight:700;margin:0;white-space:nowrap;\n'
      ' overflow:hidden;text-overflow:ellipsis}\n'
      '.elsel{width:100%;font:inherit;font-size:12px;font-weight:700;padding:7px 9px;\n'
      ' border-radius:8px;border:1px solid var(--ellinha);background:var(--elbox);\n'
      ' color:inherit}\n'
      '.elnota2{font-size:10px;color:var(--elmudo);margin:6px 0 0;line-height:1.45}\n'
      '\n'
      '/* ---------- O CARD ---------- */\n'
      '.elcard{position:relative;width:150px;padding:9px;border-radius:10px;\n'
      ' border:1px solid var(--ellinha);background:var(--elbox);cursor:pointer;\n'
      ' user-select:none;text-align:left;overflow:hidden;\n'
      ' transition:transform .12s,border-color .12s}\n'
      '.elcard:hover{transform:translateY(-2px);border-color:var(--ellima)}\n'
      '.eltop{display:flex;align-items:flex-start;justify-content:space-between;gap:4px}\n'
      '.elpt{font-family:var(--elcond);font-weight:700;font-size:30px;line-height:.92;\n'
      ' letter-spacing:-.5px;font-variant-numeric:tabular-nums}\n'
      '.elpt i{font-style:normal;font-size:17px;letter-spacing:-.5px}\n'
      '.elpt.elzero{color:var(--elverm)!important}\n'
      #  🔴 a pílula saía "S" em vez de "SA": o flex encolhia ela para a
      #  pontuação caber. Agora quem cede é o número, não a sigla.
      '.eltop>*{min-width:0}\n'
      '.elpt{flex:0 1 auto;overflow:hidden}\n'
      '.elpos,.elpsel{flex:0 0 auto;border-radius:5px;background:rgba(242,246,236,.10);padding:2px 6px;\n'
      ' font:inherit;font-size:9.5px;font-weight:700;letter-spacing:.08em;\n'
      ' text-transform:uppercase;white-space:nowrap;color:var(--elfg);border:none;\n'
      ' line-height:1.5;margin-top:2px}\n'
      '.elpsel{cursor:pointer;-webkit-appearance:none;appearance:none;padding-right:6px}\n'
      '.elpsel:hover{background:var(--ellima);color:#101812}\n'
      #  ⛔ A FOTO É QUADRADA — ordem dele. E tem TETO: sem o teto ela cresce
      #  junto com o card e o card do campo vira um poste de 340px, onde não
      #  cabem quatro linhas no gramado. Medido.
      '.elfoto{margin:8px auto 0;width:min(100%,104px);aspect-ratio:1/1;border-radius:8px;\n'
      ' overflow:hidden;background:rgba(242,246,236,.06);\n'
      ' border:1px solid rgba(242,246,236,.07);display:flex;align-items:center;\n'
      ' justify-content:center}\n'
      '.elfoto img{width:100%;height:100%;object-fit:contain;object-position:50% 50%;\n'
      ' display:block}\n'
      #  ORDEM DO LUIS: *"o nome tem que estar centralizado"*. O bloco de texto
      #  inteiro embaixo da foto vai centrado — com só o nome centrado e o resto
      #  à esquerda o card fica torto.
      '.elnm{margin-top:8px;font-size:12.5px;font-weight:700;line-height:1.2;\n'
      ' overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;\n'
      ' -webkit-box-orient:vertical;min-height:2.4em;text-align:center}\n'
      '.elfn{font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;\n'
      ' color:var(--elmudo);font-weight:700;line-height:1.25;margin-top:3px;\n'
      ' overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;\n'
      ' -webkit-box-orient:vertical;text-align:center}\n'
      '.eles{font-size:9.5px;color:var(--elmudo);opacity:.75;line-height:1.25;\n'
      ' margin-top:1px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;\n'
      ' -webkit-box-orient:vertical;text-align:center}\n'
      '.elorig{font-size:8.5px;font-weight:700;letter-spacing:.08em;color:var(--elmudo);\n'
      ' opacity:.7;text-transform:uppercase;margin-top:5px;white-space:nowrap;\n'
      ' overflow:hidden;text-overflow:ellipsis;text-align:center}\n'
      '.elorig.temb{color:var(--ellima);opacity:1}\n'
      '.elforapos{margin-top:6px;font-size:9px;line-height:1.3;border-radius:6px;\n'
      ' padding:4px 5px;background:rgba(224,83,61,.14);\n'
      ' border:1px solid rgba(224,83,61,.35);color:#ff9d8c;font-weight:700;\n'
      ' text-align:center}\n'
      '\n'
      '/* a faixa dos botões: só no hover, só no rodapé, e atravessável */\n'
      #  🔴 Se ela cobrir o card inteiro o arrasto MORRE: medido no navegador,
      #  o Chrome não inicia arrasto nativo a partir de um <button> e o evento
      #  `dragstart` não chega a nascer.
      '.elacts{position:absolute;left:0;right:0;bottom:0;top:auto;padding:16px 7px 7px;\n'
      ' background:linear-gradient(to top,rgba(10,16,12,.97) 58%,rgba(10,16,12,0));\n'
      ' display:flex;flex-wrap:wrap;gap:4px;opacity:0;pointer-events:none;\n'
      ' border-radius:0 0 9px 9px;transition:opacity .12s}\n'
      '.elcard:hover .elacts{opacity:1}\n'
      '.elbt{font:inherit;font-size:10px;font-weight:700;padding:5px 4px;border-radius:6px;\n'
      ' border:1px solid var(--ellinha);background:transparent;color:inherit;\n'
      ' cursor:pointer;white-space:nowrap;line-height:1.2;text-align:center;\n'
      ' overflow:hidden;text-overflow:ellipsis}\n'
      '.elbt:hover{border-color:var(--ellima);color:var(--ellima)}\n'
      '.elacts .elbt{color:var(--elfg);border-color:rgba(242,246,236,.22);\n'
      ' background:rgba(16,24,18,.7);flex:1 1 40%;min-width:0;pointer-events:none}\n'
      '.elcard:hover .elacts .elbt{pointer-events:auto}\n'
      '.elacts .elbt.elx{flex:0 0 26px;padding:5px 2px;border-color:transparent;opacity:.6}\n'
      '.elacts .elbt.elx:hover{opacity:1;border-color:var(--elverm);color:var(--elverm)}\n'
      '@media(hover:none){\n'
      ' .elacts{position:static;inset:auto;background:none;opacity:1;\n'
      '  pointer-events:auto;padding:8px 0 0}\n'
      ' .elacts .elbt{background:transparent;pointer-events:auto}\n'
      '}\n'
      '\n'
      '/* ---------- as duas listas ---------- */\n'
      '#elreservas .elgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));\n'
      ' gap:9px;margin-top:12px}\n'
      '#elreservas .elcard{width:100%}\n'
      '#elfora .elgrid{display:flex;flex-wrap:wrap;gap:9px;margin-top:12px}\n'
      '.elvazia{border:1px dashed var(--ellinha);border-radius:8px;padding:22px 12px;\n'
      ' text-align:center;font-size:11px;color:var(--elmudo);width:100%;margin-top:12px}\n'
      '#elbarra{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0 0}\n'
      '#elbarra .elsel2{font:inherit;font-size:11.5px;font-weight:700;padding:6px 9px;\n'
      ' border-radius:8px;border:1px solid var(--ellinha);background:var(--elbox);\n'
      ' color:inherit;cursor:pointer;max-width:190px}\n'
      '#elbusca{flex:1;min-width:170px;font:inherit;font-size:12.5px;padding:7px 11px;\n'
      ' border-radius:8px;border:1px solid var(--ellinha);background:var(--elbox);\n'
      ' color:inherit}\n'
      '#elbarra .elcont{font-size:11px;color:var(--elmudo);white-space:nowrap}\n'
      '\n'
      '/* ---------- O CAMPO ---------- */\n'
      #  ⛔ A casca já desenha um gramado, mas o dela é claro e tem `!important`
      #  em `html[data-tema]`. Aqui a grama é a do base44 — escura, em faixas de
      #  6,25% — e as LINHAS são desenhadas por divs (`.risco`), não pelos
      #  pseudo-elementos: os `:before`/`:after` da casca têm
      #  `background:rgba(255,255,255,.55)!important` e virariam um retângulo
      #  branco em cima de qualquer caixa desenhada no mesmo lugar.
      '#mtwrap .mtcampo{position:relative!important;aspect-ratio:3/4;\n'
      ' max-height:1280px;width:100%!important;max-width:none!important;\n'
      ' height:auto!important;min-height:0!important;overflow:hidden;\n'
      ' border-radius:12px;margin:12px 0 0!important;padding:0!important;\n'
      ' border:none!important;touch-action:none;box-shadow:none!important;\n'
      ' background:repeating-linear-gradient(to bottom,\n'
      '  #245c3d 0 6.25%, #296746 6.25% 12.5%)!important}\n'
      '#mtwrap .mtcampo::before,#mtwrap .mtcampo::after{display:none!important;\n'
      ' content:none!important}\n'
      '.risco{position:absolute;pointer-events:none;border:1px solid var(--elrisco)}\n'
      '.r-borda{inset:2.2%;border-radius:3px}\n'
      '.r-meio{left:2.2%;right:2.2%;top:50%;height:0;border-width:1px 0 0 0}\n'
      '.r-circulo{left:50%;top:50%;width:20%;aspect-ratio:1;\n'
      ' transform:translate(-50%,-50%);border-radius:999px}\n'
      '.r-areaG{left:22%;right:22%;height:16%;border-radius:2px}\n'
      '.r-areaP{left:35%;right:35%;height:6.5%;border-radius:2px}\n'
      '.r-cima{top:2.2%;border-top:none}\n'
      '.r-baixo{bottom:2.2%;border-bottom:none}\n'
      '.r-pena{width:8px;height:8px;border-radius:50%;background:var(--elrisco);\n'
      ' border:none;left:50%;transform:translateX(-50%)}\n'
      '\n'
      '#mtwrap .mtsl{width:var(--elcw,170px)!important;text-align:left!important;\n'
      ' background:transparent!important;border:none!important;padding:4px!important;\n'
      ' backdrop-filter:none!important;border-radius:12px;box-shadow:none!important;\n'
      ' transition:background .15s,box-shadow .15s}\n'
      '#mtwrap .mtsl:hover{background:transparent!important;\n'
      ' border-color:transparent!important}\n'
      '#mtwrap .mtsl.vaz{background:transparent!important;border:none!important}\n'
      '#mtwrap .mtsl.pousa{background:rgba(190,242,100,.22)!important;\n'
      ' box-shadow:0 0 0 2px var(--ellima)!important}\n'
      '#mtwrap .mtsl .elcard{width:100%;box-shadow:0 10px 26px -14px rgba(0,0,0,.95)}\n'
      '#mtwrap .mtsl .elfoto{width:min(100%,124px)}\n'
      '#mtwrap .mtsl .elpt{font-size:34px}\n'
      '#mtwrap .mtsl .elpt i{font-size:19px}\n'
      '#mtwrap .mtsl .elpos,#mtwrap .mtsl .elpsel{font-size:10.5px;padding:2px 7px}\n'
      '#mtwrap .mtsl .elnm{font-size:13.5px}\n'
      '#mtwrap .mtsl .elfn{font-size:10px}\n'
      '#mtwrap .mtsl .eles{font-size:10px}\n'
      '#mtwrap .mtsl.vaz .elvazio{display:flex;flex-direction:column;align-items:center;\n'
      ' justify-content:center;gap:5px;width:100%;\n'
      ' height:calc(var(--elcw,170px) * 1.28);\n'
      ' border:1px dashed rgba(226,255,238,.45);border-radius:10px;cursor:pointer;\n'
      ' background:rgba(9,26,17,.4)}\n'
      '#mtwrap .mtsl.vaz .elvazio:hover{border-color:var(--ellima);\n'
      ' background:rgba(9,26,17,.65)}\n'
      '#mtwrap .mtsl .elvmais{font-family:var(--elcond);font-size:26px;font-weight:700;\n'
      ' line-height:1;color:#eafaf0!important;opacity:.8}\n'
      '#mtwrap .mtsl .elvpos{font-size:10px;letter-spacing:.18em;font-weight:700;\n'
      ' text-transform:uppercase;color:#eafaf0!important}\n'
      '#mtwrap .mtsl .elvfn{font-size:8.5px;text-align:center;line-height:1.25;\n'
      ' padding:0 4px;color:#cfe8da!important;opacity:.85}\n'
      '\n'
      '/* o nome da posição, embaixo do bloco — e ele é o botão de trocar */\n'
      '.elvagapos{position:absolute;left:50%;bottom:-12px;transform:translateX(-50%);\n'
      ' z-index:15;display:flex;align-items:center;gap:2px;padding:0 4px 0 2px;\n'
      ' border-radius:20px;border:1px solid rgba(190,242,100,.45);background:#111c15;\n'
      ' box-shadow:0 3px 10px -4px rgba(0,0,0,.9);transition:border-color .12s}\n'
      '.elvagapos:hover{border-color:var(--ellima)}\n'
      '.elvagaseta{font-size:9px;color:var(--ellima);pointer-events:none;\n'
      ' line-height:1;padding-right:2px}\n'
      '#mtwrap .mtsl .elvagapos .elpsel{background:transparent!important;\n'
      ' color:var(--ellima)!important;font-size:11px;letter-spacing:.12em;\n'
      ' padding:4px 2px 4px 9px;margin:0;font-weight:700}\n'
      '#mtwrap .mtsl .elvagapos .elvagafixa{font-size:11px;letter-spacing:.12em;\n'
      ' font-weight:700;color:var(--ellima);padding:4px 7px 4px 9px}\n'
      '#mtwrap .mtsl .elvagapos .elvagafixa+.elvagaseta{display:none}\n'
      '\n'
      '/* a alça: botão redondo com o ✥ — arrasta a VAGA */\n'
      '.elalca{position:absolute;top:-9px;right:-9px;z-index:20;display:flex;\n'
      ' align-items:center;justify-content:center;width:24px;height:24px;padding:0;\n'
      ' border-radius:999px;border:1px solid rgba(190,242,100,.35);background:#111c15;\n'
      ' color:var(--ellima);cursor:grab;touch-action:none;font-size:11px;line-height:1;\n'
      ' opacity:.85;transition:opacity .15s,transform .15s}\n'
      '.elalca:hover{opacity:1;transform:scale(1.12)}\n'
      '#mtwrap .mtsl.arr{z-index:99;opacity:.9}\n'
      '#mtwrap .mtsl.arr .elalca{cursor:grabbing}\n'
      '.elmove{position:absolute;left:50%;top:8px;transform:translateX(-50%);z-index:60;\n'
      ' background:var(--ellima);color:#101812;font-size:11px;font-weight:700;\n'
      ' padding:5px 12px;border-radius:20px;pointer-events:none}\n'
      '.elaviso{margin-top:5px;font-size:8.5px;line-height:1.3;border-radius:6px;\n'
      ' padding:4px 5px;background:rgba(190,242,100,.10);\n'
      ' border:1px solid rgba(190,242,100,.30);color:#d6f79a;font-weight:700}\n'
      '.elaviso button{display:block;width:100%;margin-top:3px;font:inherit;font-size:8.5px;\n'
      ' font-weight:700;padding:2px 4px;border-radius:5px;border:1px solid currentColor;\n'
      ' background:transparent;color:inherit;cursor:pointer}\n'
      '</style>\n')

    js = (
      '<script>\n'
      '/* ===== ELENCO_1608 — o layout e o card unico ===== */\n'
      '(function(){\n'
      ' if(typeof mtRender!=="function") return;\n'
      ' var TETO_TIT=11, TETO_BANCO=12;\n'
      ' window.EL_TETO={titulares:TETO_TIT, banco:TETO_BANCO};\n'
      '\n'
      ' /* ---------- 1 · A PONTUACAO QUE O CARD MOSTRA ----------\n'
      '    Ordem do Luis, 16/08: *"descarta a pontuacao da posicao original.\n'
      '    Ele vai aparecer com a pontuacao que esta no MEU CARD do modal."*\n'
      '    O `mtNotaReal` ja e exatamente isso: a nota com as barras que o\n'
      '    usuario pos (`mtCfg`) e o tecnico do time. Quando a FAZER MINHA BUILD\n'
      '    entrar, ela substitui esta funcao por cima — por isso ela esta no\n'
      '    window e num lugar so. */\n'
      #  🔴 17/08 — DEFEITO DE FUNDO, achado medindo a vaga do goleiro: o card no
      #  campo mostrava "GK · Zagueiro de saida" — a posicao da vaga certa e a
      #  funcao do card errada.
      #  A CAUSA nao estava na conta: os tres blocos de script entram no HTML
      #  com `rfind('</body>')`, e a ORDEM DELES NAO E GARANTIDA. Medido no HTML
      #  gerado: BUILD em 38.611.894, SELETOR em 38.628.766 e ELENCO em
      #  38.639.337 — o do elenco caiu POR ULTIMO e sobrescreveu a `elPontuacao`
      #  boa (a que aceita a funcao da vaga) por esta versao simples.
      #  ⛔ A REGRA QUE FICA: quando dois blocos definem a mesma funcao, o que
      #  tem a versao POBRE so define se ninguem tiver definido antes. Assim
      #  qualquer ordem funciona.
      ' if(typeof window.elPontuacao!=="function")\n'
      '  window.elPontuacao=function(k, funcDaVaga){\n'
      '   var c=null; try{ c=mtCard(k); }catch(e){}\n'
      '   if(!c) return null;\n'
      '   var n=0; try{ n=mtNotaReal(k); }catch(e){ try{ n=nota(c); }catch(e2){ n=0; } }\n'
      '   return {n:n, func:funcDaVaga||c.tipo, nome:null};\n'
      '  };\n'
      '\n'
      ' function doisDec(v){\n'
      '  var s=(+v||0).toFixed(2).split(".");\n'
      '  return s[0]+"<i>,"+s[1]+"</i>";\n'
      ' }\n'
      ' function esc(t){ return String(t==null?"":t)\n'
      '  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")\n'
      '  .replace(/"/g,"&quot;"); }\n'
      '\n'
      ' /* ---------- 2 · AS TRAVAS ----------\n'
      '    Ordem do Luis: *"o time titular e o reserva, os dois juntos sao vinte\n'
      '    e tres jogadores, e esses vinte e tres nao aceitam cards do mesmo\n'
      '    jogador."*\n'
      '    ⚠️ A casca ja tinha essa trava no comeco do mtRender, so que ela ia\n'
      '    longe demais: derrubava o repetido do FORA DO BANCO tambem, calada.\n'
      '    Fora do banco pode ter os tres Haaland — o desligamento esta abaixo. */\n'
      ' function quantosTit(){\n'
      '  var n=0, s=MT.slots||[];\n'
      '  for(var i=0;i<s.length;i++) if(s[i]&&s[i].key) n++;\n'
      '  return n;\n'
      ' }\n'
      ' function jogadorDe(k){ try{ return _jog(k); }catch(e){ return String(k); } }\n'
      ' function jaEstaNosVinteETres(k, ignora){\n'
      '  var j=jogadorDe(k), s=MT.slots||[], i;\n'
      '  for(i=0;i<s.length;i++){\n'
      '   if(!s[i]||!s[i].key||s[i].key===ignora) continue;\n'
      '   if(jogadorDe(s[i].key)===j) return true;\n'
      '  }\n'
      '  var b=MT.banco||[];\n'
      '  for(i=0;i<b.length;i++){\n'
      '   if(b[i]===ignora) continue;\n'
      '   if(jogadorDe(b[i])===j) return true;\n'
      '  }\n'
      '  return false;\n'
      ' }\n'
      ' function podeEntrarNosVinteETres(k){\n'
      '  if(!jaEstaNosVinteETres(k,k)) return true;\n'
      '  var c=null; try{ c=mtCard(k); }catch(e){}\n'
      '  alert("Voc\\u00ea j\\u00e1 tem um card do "+((c&&c.nome)||"mesmo jogador")\n'
      '   +" entre os titulares e os reservas.\\n\\nO time de 23 n\\u00e3o aceita dois "\n'
      '   +"cards do mesmo jogador. Fora do banco pode.");\n'
      '  return false;\n'
      ' }\n'
      ' function cabeNoBanco(){\n'
      '  if((MT.banco||[]).length < TETO_BANCO) return true;\n'
      '  alert("O banco de reservas j\\u00e1 est\\u00e1 cheio \\u2014 s\\u00e3o "+TETO_BANCO\n'
      '   +" vagas.\\n\\nTire algu\\u00e9m do banco antes de p\\u00f4r mais um.");\n'
      '  return false;\n'
      ' }\n'
      ' function cabeNoCampo(){\n'
      '  if(quantosTit() < TETO_TIT) return true;\n'
      '  alert("O time j\\u00e1 est\\u00e1 com os "+TETO_TIT+" titulares.\\n\\n"\n'
      '   +"Tire algu\\u00e9m do campo antes de p\\u00f4r mais um.");\n'
      '  return false;\n'
      ' }\n'
      '\n'
      ' /* ---------- 3 · MOVER DE UM LUGAR PARA O OUTRO ----------\n'
      '    ⚠️ CORRIGIDO no teste de 16/08: a primeira versao caia no "primeiro\n'
      '    slot livre qualquer" e mandou o Messi para o GOLEIRO. Escalar no lugar\n'
      '    errado e pior que nao escalar. */\n'
      ' function achaVaga(c){\n'
      '  var s=MT.slots||[], pos=c?(c.np||c.pos):null, i, j;\n'
      '  for(i=0;i<s.length;i++) if(s[i]&&!s[i].key&&s[i].pos===pos) return i;\n'
      '  var fd=[]; try{ fd=MT_FUNCS[pos]||[]; }catch(e){}\n'
      '  for(i=0;i<s.length;i++){\n'
      '   if(!s[i]||s[i].key) continue;\n'
      '   var fv=[]; try{ fv=MT_FUNCS[s[i].pos]||[]; }catch(e){}\n'
      '   for(j=0;j<fd.length;j++) if(fv.indexOf(fd[j])>=0) return i;\n'
      '  }\n'
      '  return -1;\n'
      ' }\n'
      ' function soltaDe(k, fica){\n'
      '  if(fica!=="fora")  MT.elenco=(MT.elenco||[]).filter(function(x){return x!==k;});\n'
      '  if(fica!=="banco") MT.banco =(MT.banco ||[]).filter(function(x){return x!==k;});\n'
      '  if(fica!=="campo"){ var s=MT.slots||[];\n'
      '   for(var i=0;i<s.length;i++) if(s[i]&&s[i].key===k) s[i].key=null; }\n'
      ' }\n'
      ' function paraOCampo(k){\n'
      '  var c=null; try{ c=mtCard(k); }catch(e){}  if(!c) return;\n'
      '  var jaEsta=false, s=MT.slots||[], i;\n'
      '  for(i=0;i<s.length;i++) if(s[i]&&s[i].key===k) jaEsta=true;\n'
      '  if(jaEsta) return;\n'
      '  if(!cabeNoCampo()) return;\n'
      '  if(!podeEntrarNosVinteETres(k)) return;\n'
      #  ⚠️ 16/08 — A RECUSA SAIU. Ordem do Luis: *"se eu quero colocar o
      #  centroavante de meio de campo, voce nao permite. Mas no jogo e
      #  permitido. Se o cara quer fazer errado o problema e dele."*
      #  O botao agora prefere a vaga da posicao dele; nao tendo, usa a primeira
      #  vaga livre qualquer — e a pontuacao dele cai sozinha, porque passa a ser
      #  medida contra o molde da vaga. A tela conta a verdade em vez de proibir.
      '  var v=achaVaga(c);\n'
      '  if(v<0){\n'
      '   var s2=MT.slots||[], q;\n'
      '   for(q=0;q<s2.length;q++) if(s2[q] && !s2[q].key && s2[q].pos!=="GK"){ v=q; break; }\n'
      '   if(v<0) for(q=0;q<s2.length;q++) if(s2[q] && !s2[q].key){ v=q; break; }\n'
      '  }\n'
      '  if(v<0) return;\n'
      '  MT.slots[v].key=k;\n'
      '  /* ⚠️ 16/08 — DEFEITO QUE O LUIS PEGOU NO MESSI: a vaga guardava a funcao\n'
      '     antiga dela (Atacante infiltrador, 102,7) em vez da funcao do card que\n'
      '     acabou de entrar (Falso nove, 112,03). A vaga passa a receber a funcao\n'
      '     do proprio card sempre que a posicao dela aceita essa funcao. */\n'
      '  MT.slots[v].func=funcaoDaVaga(MT.slots[v], k);\n'
      '  soltaDe(k,"campo");\n'
      '  MTdb.save(); mtRender();\n'
      ' }\n'
      ' function paraOBanco(k){\n'
      '  if((MT.banco||[]).indexOf(k)>=0) return;\n'
      '  if(!cabeNoBanco()) return;\n'
      '  if(!podeEntrarNosVinteETres(k)) return;\n'
      '  MT.banco=MT.banco||[]; MT.banco.push(k);\n'
      '  soltaDe(k,"banco");\n'
      '  MTdb.save(); mtRender();\n'
      ' }\n'
      ' function paraForaDoBanco(k){\n'
      '  MT.elenco=MT.elenco||[];\n'
      '  if(MT.elenco.indexOf(k)<0) MT.elenco.unshift(k);\n'
      '  soltaDe(k,"fora");\n'
      '  MTdb.save(); mtRender();\n'
      ' }\n'
      ' function tiraDoElenco(k){\n'
      '  var c=null; try{ c=mtCard(k); }catch(e){}\n'
      '  if(!confirm("Tirar "+((c&&c.nome)||"este card")+" do seu elenco?\\n\\n"\n'
      '   +"Ele sai da lista inteira \\u2014 do campo, do banco e de fora do banco.\\n"\n'
      '   +"Isso n\\u00e3o apaga nada do seu jogo, s\\u00f3 daqui.")) return;\n'
      '  soltaDe(k,null);\n'
      '  MTdb.save(); mtRender();\n'
      ' }\n'
      ' window.elParaCampo=paraOCampo; window.elParaBanco=paraOBanco;\n'
      ' window.elParaFora=paraForaDoBanco; window.elExclui=tiraDoElenco;\n'
      '\n'
      ' /* ---------- 4 · A TRAVA DA CASCA, QUE IA LONGE DEMAIS ----------\n'
      '    O mtRender da casca comeca filtrando repetidos das TRES listas. A do\n'
      '    fora do banco esta errada pela regra do Luis, e o estrago era mudo: o\n'
      '    segundo Haaland sumia sem aviso. Aqui a lista de fora do banco e\n'
      '    guardada antes e devolvida depois. */\n'
      ' var _mr=window.mtRender;\n'
      ' window.mtRender=function(){\n'
      '  var guardado=(MT.elenco||[]).slice();\n'
      '  var v=_mr.apply(this,arguments);\n'
      '  var perdeu=guardado.filter(function(k){ return (MT.elenco||[]).indexOf(k)<0; });\n'
      '  if(perdeu.length){\n'
      '   /* so devolve o que nao foi para o campo nem para o banco */\n'
      '   var nosVinte={}, s=MT.slots||[], i;\n'
      '   for(i=0;i<s.length;i++) if(s[i]&&s[i].key) nosVinte[s[i].key]=1;\n'
      '   (MT.banco||[]).forEach(function(k){ nosVinte[k]=1; });\n'
      '   var volta=perdeu.filter(function(k){ return !nosVinte[k]; });\n'
      '   if(volta.length){\n'
      '    MT.elenco=(MT.elenco||[]).concat(volta);\n'
      '    try{ MTdb.save(); }catch(e){}\n'
      '    return _mr.apply(this,arguments);\n'
      '   }\n'
      '  }\n'
      '  return v;\n'
      ' };\n'
      '\n'
      #  ---------- 🔴 O mtSlots DA CASCA DESFAZIA TUDO ----------
      #  ACHADO EM 17/08, com o Luis no seletor de posicao: *"quando eu clico pra
      #  passar de VOL pra MO, MC ou MLE, nao passa. Esse botao nao esta
      #  funcionando."*
      #  Nao era o botao. O `mtSlots()` da casca roda no comeco de TODO
      #  `mtRender` e faz:
      #      f.forEach((x,i)=>{ MT.slots[i].pos = x[0];
      #                         if(!MT.slots[i].mv){ ...x, ...y } });
      #  ou seja, ele REESCREVE a posicao de cada vaga com a da formacao de
      #  fabrica, sempre. O clique mudava para MO, o mtRender rodava logo em
      #  seguida e devolvia VOL antes de a tela desenhar.
      #  ⚠️ Isto derrubava tambem o ARRASTAR DA VAGA — que muda a posicao pela
      #  regiao onde ela para. Os dois pediam o mesmo conserto.
      #  Aqui o que o Luis decidiu na mao (`posFixa`) e onde ele largou a vaga
      #  (`mv`) sao guardados antes e repostos depois. O resto do `mtSlots`
      #  continua fazendo o que sempre fez.
      ' (function(){\n'
      '  var _ms=window.mtSlots; if(typeof _ms!=="function") return;\n'
      '  window.mtSlots=function(){\n'
      '   var g=(MT.slots||[]).map(function(x){\n'
      '    return x?{pos:x.pos, func:x.func, posFixa:!!x.posFixa, mv:!!x.mv,\n'
      '              x:x.x, y:x.y}:null; });\n'
      '   var r=_ms.apply(this,arguments);\n'
      '   var s=MT.slots||[], i;\n'
      '   for(i=0;i<s.length;i++){\n'
      '    if(!s[i]||!g[i]) continue;\n'
      '    if(g[i].mv){ s[i].x=g[i].x; s[i].y=g[i].y; s[i].mv=1; }\n'
      '    if(g[i].posFixa || g[i].mv){\n'
      '     if(g[i].pos){ s[i].pos=g[i].pos; }\n'
      '     if(g[i].func){ s[i].func=g[i].func; }\n'
      '     if(g[i].posFixa) s[i].posFixa=1;\n'
      '    }\n'
      '   }\n'
      '   return r;\n'
      '  };\n'
      ' })();\n'
      '\n'
      ' /* ---------- 5 · O CARD UNICO ---------- */\n'
      ' function botao(fn,k,tit,rot,cls){\n'
      '  return \'<button class="elbt \'+(cls||"")+\'" title="\'+esc(tit)+\'" \'\n'
      '   +\'onclick="event.stopPropagation();\'+fn+\'(\\\'\'+k+\'\\\')">\'+rot+\'</button>\';\n'
      ' }\n'
      #  ---------- O SELETOR DE POSICAO DA VAGA ----------
      #  ORDEM DO LUIS, 17/08: *"algumas posicoes do campo podem ser duas. Por
      #  exemplo o SA, ele pode ser PTE ou PTD tambem. Tem que dar um jeito de
      #  escolher aqui o que o cara quer que seja."*
      #  A regiao onde a vaga esta continua mandando no palpite — mas ele tem a
      #  ultima palavra, e o que ele escolher fica. As opcoes sao as posicoes da
      #  MESMA FAIXA do campo (o SA fica na faixa do ataque, junto de CA, PTE e
      #  PTD), porque so essas fazem sentido para onde a vaga esta parada.
      ' var FAIXA={\n'
      '  ata:["CA","SA","PE","PD"],\n'
      '  mei:["MO","MC","VOL","MLE","MLD"],\n'
      '  def:["ZC","LE","LD"],\n'
      '  gol:["GK"]\n'
      ' };\n'
      ' function faixaDe(pos){\n'
      '  for(var f in FAIXA) if(FAIXA[f].indexOf(pos)>=0) return f;\n'
      '  return "mei";\n'
      ' }\n'
      ' function seletorDePosicao(sl){\n'
      '  if(!sl) return "";\n'
      '  if(sl.pos==="GK") return \'<b class=elvagafixa>GK</b>\';\n'
      '  var ix=(MT.slots||[]).indexOf(sl);\n'
      '  var ops=FAIXA[faixaDe(sl.pos)]||[], h, i;\n'
      '  if(ops.indexOf(sl.pos)<0) ops=ops.concat([sl.pos]);\n'
      '  h=\'<select class=elpsel onclick="event.stopPropagation()" \'\n'
      '   +\'onchange="event.stopPropagation();elTrocaPos(\'+ix+\',this.value)" \'\n'
      '   +\'title="a posi\\u00e7\\u00e3o desta vaga \\u2014 a pontua\\u00e7\\u00e3o \'\n'
      '   +\'\\u00e9 medida contra o molde dela">\';\n'
      '  for(i=0;i<ops.length;i++)\n'
      '   h+=\'<option\'+(ops[i]===sl.pos?" selected":"")+\'>\'+esc(ops[i])+\'</option>\';\n'
      '  return h+"</select>";\n'
      ' }\n'
      ' window.elTrocaPos=function(ix, pos){\n'
      '  var sl=(MT.slots||[])[ix]; if(!sl) return;\n'
      '  sl.pos=pos; sl.posFixa=1;\n'
      '  sl.func=funcaoDaVaga(sl, sl.key);\n'
      '  window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '  try{ MTdb.save(); }catch(e){}\n'
      '  try{ mtRender(); }catch(e){}\n'
      ' };\n'
      '\n'
      #  ---------- AS POSICOES QUE O CARD JOGA ----------
      #  ORDEM DO LUIS, 17/08: *"todo card tem as posicoes que ele joga. Quando
      #  ele for pro campo, se for arrastado pra alguma outra posicao voce pode
      #  ate aceitar ele la, so que com a chance ZERADA — zero — e tem que dar
      #  uma mensagem que ele nao joga nessa posicao."*
      #  ⚠️ E POSICAO, nao funcao — ele foi explicito. A funcao se resolve
      #  sozinha: *"as builds sao construidas por funcoes, entao se voce jogar
      #  ele na posicao que ele atua ja vai mostrar a funcao dele."*
      #  ⛔ A LISTA E DO PROPRIO CARD, nao inventada: `c.np` e a posicao nativa
      #  e `c.sp` traz as secundarias — sao as mesmas que o campinho do modal
      #  acende (o `_minhas` de la e exatamente `[np].concat(as do sp)`).
      ' function posDoCard(c){\n'
      '  var out=[];\n'
      '  if(!c) return out;\n'
      '  if(c.np) out.push(c.np);\n'
      '  try{ (c.sp||[]).forEach(function(x){\n'
      '   if(x && x[0] && out.indexOf(x[0])<0) out.push(x[0]); }); }catch(e){}\n'
      '  if(!out.length && c.pos) out.push(c.pos);\n'
      '  return out;\n'
      ' }\n'
      ' function jogaNaPos(c, pos){\n'
      '  if(!c || !pos) return true;\n'
      '  var L=posDoCard(c);\n'
      '  if(!L.length) return true;\n'
      '  return L.indexOf(pos)>=0;\n'
      ' }\n'
      ' window.elPosDoCard=posDoCard; window.elJogaNaPos=jogaNaPos;\n'
      '\n'
      #  ---------- O CARD, no formato do arquivo que ele mandou ----------
      #  A pontuacao grande em cima com a sigla da posicao ao lado, a foto, o
      #  nome e a funcao embaixo. Os botoes de mover saem da frente: eles ficam
      #  numa capa que so aparece com o mouse em cima. O card fica limpo e
      #  IGUAL nos tres lugares — campo, banco e fora dele — que foi o pedido
      #  de 16/08: *"o ideal e que elas nao ficassem diferentes"*.
      ' function montaCard(k, de, sl){\n'
      '  var c=null; try{ c=mtCard(k); }catch(e){}\n'
      '  if(!c) return "";\n'
      '  var fv=(sl&&sl.func)?sl.func:null;\n'
      '  var foraDePosicao = !!(sl && sl.pos && !jogaNaPos(c, sl.pos));\n'
      '  var p=window.elPontuacao(k, fv) || {n:0, func:fv||c.tipo};\n'
      '  if(foraDePosicao) p={n:0, func:p.func, nome:p.nome, zero:1};\n'
      '  var posMostra=(sl&&sl.pos)?sl.pos:(c.np||c.pos||"");\n'
      '  var idb=String(c.id).split("@")[0];\n'
      '  var est=(c.modelo&&c.modelo!==c.tipo)?c.modelo:"";\n'
      '  var bas="";\n'
      '  try{ if(typeof estiloAtiva==="function" && !estiloAtiva(c))\n'
      '    bas="B\\u00c1SICO \\u00b7 "; }catch(e){}\n'
      '  var cr="inherit";\n'
      '  try{ cr=cor(p.n, notaMed(p.func)); }catch(e){}\n'
      #  fora de posicao: ZERO, e vermelho, com o motivo escrito. Ordem dele.
      #  E quando ele JOGA ali mas o motor nao tem a carta naquela funcao, vale
      #  o traco — que e outra coisa: nao e "ele nao serve", e "nao da para
      #  medir".
      '  var pt = foraDePosicao\n'
      '   ?(\'<div class="elpt elzero" title="joga de \'\n'
      '     +esc(posDoCard(c).join(", "))+\'">0<i>,00</i></div>\')\n'
      '   :((p.n>0)\n'
      '     ?(\'<div class=elpt style="color:\'+cr+\'">\'+doisDec(p.n)+\'</div>\')\n'
      '     :(\'<div class=elpt style="opacity:.45" title="o motor n\\u00e3o mede \'\n'
      '       +esc(c.nome)+\' como \'+esc(p.func)+\' \\u2014 esta carta n\\u00e3o existe \'\n'
      '       +\'nessa fun\\u00e7\\u00e3o no banco">\\u2014</div>\'));\n'
      #  a sigla e a DA VAGA quando o card esta no campo, e la ela e um seletor:
      #  *"algumas posicoes do campo podem ser duas. O SA pode ser PE ou PD
      #  tambem."* Nas listas e a nativa do card, so leitura.
      #  no campo a sigla mora embaixo do bloco (o `refazVaga` a desenha);
      #  aqui em cima ela sairia repetida.
      '  var tag = sl ? "" : (\'<span class=elpos>\'+esc(posMostra)+\'</span>\');\n'
      '  var bts="";\n'
      '  if(de==="fora")       bts = botao("elParaCampo",k,"escalar como titular","\\u2191 titular")\n'
      '                            + botao("elParaBanco",k,"mandar pro banco","\\u2193 reserva");\n'
      '  else if(de==="banco") bts = botao("elParaCampo",k,"escalar como titular","\\u2191 titular")\n'
      '                            + botao("elParaFora",k,"tirar do banco","\\u2193 fora");\n'
      '  else                  bts = botao("elParaBanco",k,"mandar pro banco","\\u2193 reserva")\n'
      '                            + botao("elParaFora",k,"tirar do time","\\u2193 fora");\n'
      '  var extra="";\n'
      '  try{ if(typeof window.elBotoesExtra==="function") extra=window.elBotoesExtra(k,de)||""; }catch(e){}\n'
      #  ⚠️ 16/08 — ORDEM DO LUIS: *"quando a gente clica no card e ele esta
      #  dentro do campo aparece essa janela ai [o 'Quem joga de MO'], nao tem
      #  por que. Tem que aparecer o modal do card."*
      #  A causa era o clique borbulhando: a vaga da casca tem
      #  `onclick="mtAbreSel(i)"` e o meu card mora dentro dela. O
      #  stopPropagation resolve — e a VAGA VAZIA continua abrindo o seletor,
      #  que la e o certo. A capa dos botoes tambem abre o modal quando o
      #  clique cai fora dos botoes.
      '  var abre=\'onclick="event.stopPropagation();\'\n'
      '   +\'(window.elAbreCard||abrir)(\\\'\'+k+\'\\\')"\';\n'
      '  return \'<div class=elcard data-k="\'+esc(k)+\'" \'+abre+\'>\'\n'
      '   +\'<div class=eltop>\'+pt+tag+\'</div>\'\n'
      '   +\'<div class=elfoto><img loading=lazy src="https://efimg.com/efootballhub22\'\n'
      '    +\'/images/player_cards/\'+idb+\'_l.png" \'\n'
      '    +\'onerror="this.style.visibility=&quot;hidden&quot;"></div>\'\n'
      '   +\'<div class=elnm title="\'+esc(c.nome)+\'">\'+esc(c.nome)+\'</div>\'\n'
      '   +\'<div class=elfn title="\'+esc(p.func)+\'">\'+esc(p.func)+\'</div>\'\n'
      '   +\'<div class=eles title="\'+esc(est||"")+\'">\'+esc(bas+(est||"\\u2014"))+\'</div>\'\n'
      '   +\'<div class="elorig\'+(p.nome?" temb":"")+\'" title="\'\n'
      '     +(p.nome?("build sua, salva como \\u201c"+esc(p.nome)+"\\u201d")\n'
      '            :"voc\\u00ea ainda n\\u00e3o salvou build deste card \\u2014 "\n'
      '             +"este \\u00e9 o card como ele sai do pacote")\n'
      '     +\' \\u00b7 j\\u00e1 com o t\\u00e9cnico do time">\'\n'
      '     +(p.nome?esc(p.nome):"carta base")+\'</div>\'\n'
      #  ⚠️ 17/08 — ORDEM DO LUIS: *"nao precisa escrever uma frase tao grande. So
      #  coloca que ele joga de volante, MC ou MO e pronto."*
      '   +(foraDePosicao?(\'<div class=elforapos>joga de \'\n'
      '     +esc(posDoCard(c).slice(0,4).join(" \\u00b7 "))\n'
      '     +(posDoCard(c).length>4?" \\u2026":"")+\'</div>\'):"")\n'
      '   +\'<div class=elacts \'+abre+\'>\'+bts+extra\n'
      '    +botao("elExclui",k,"tirar do elenco","\\u00d7","elx")+\'</div>\'\n'
      '   +\'</div>\';\n'
      ' }\n'
      ' window.elMontaCard=montaCard;\n'
      '\n'
      #  ---------- 6 · O CAMPO VIVO ----------
      #  ORDEM DO LUIS, 16/08, com a foto do mapa de posicoes do jogo na mao:
      #    *"a gente precisa dar um jeito de movimentar essas posicoes, elas nao
      #    podem ser fixas, porque no jogo o cara movimenta ela se ele quiser.
      #    Quando ele faz isso deixa de ser uma 4-3-3 e vira uma 4-4-2. Como o
      #    jogo faz isso? Ele define pedacos do campo que sao do ataque, pedacos
      #    que sao do meio."*
      #    *"se o cara quer fazer errado o problema e dele"* — qualquer jogador
      #    em qualquer vaga, sem recusa.
      #
      #  A MALHA, lida do mapa do proprio jogo:
      #
      #             ESQUERDA        CENTRO                 DIREITA
      #    ATAQUE      PE          CA  /  SA                 PD
      #    MEIO        MLE      MO / MC / VOL                MLD
      #    DEFESA      LE          ZC  /  GK                  LD
      #
      #  ⚠️ O DESENHO DO JOGO E DESPROPORCIONAL, e o Luis avisou: as colunas de
      #  fora aparecem largas mas comportam UMA vaga por faixa (um LE, um MLE,
      #  um PE). Quem precisa de largura e a coluna do meio — la cabem tres
      #  zagueiros lado a lado. Por isso 18% / 64% / 18%, e nao um terco cada.
      ' var MALHA={\n'
      '  colE:18, colD:82,\n'
      '  centro:[ {ate:17,pos:"CA"}, {ate:29,pos:"SA"}, {ate:41,pos:"MO"},\n'
      '           {ate:55,pos:"MC"}, {ate:68,pos:"VOL"}, {ate:88,pos:"ZC"},\n'
      '           {ate:101,pos:"GK"} ],\n'
      '  lados:[ {ate:29,e:"PE",d:"PD"}, {ate:60,e:"MLE",d:"MLD"},\n'
      '          {ate:101,e:"LE",d:"LD"} ]\n'
      ' };\n'
      ' function posDaRegiao(x,y){\n'
      '  var i;\n'
      '  if(x<MALHA.colE || x>MALHA.colD){\n'
      '   for(i=0;i<MALHA.lados.length;i++) if(y<=MALHA.lados[i].ate)\n'
      '    return (x<MALHA.colE)?MALHA.lados[i].e:MALHA.lados[i].d;\n'
      '   return (x<MALHA.colE)?"LE":"LD";\n'
      '  }\n'
      '  for(i=0;i<MALHA.centro.length;i++) if(y<=MALHA.centro[i].ate)\n'
      '   return MALHA.centro[i].pos;\n'
      '  return "GK";\n'
      ' }\n'
      ' window.elPosDaRegiao=posDaRegiao;\n'
      '\n'
      #  A FORMACAO E CONSEQUENCIA, nao escolha: ela e lida de onde as vagas
      #  estao. Conta por faixa, de tras para a frente, pulando o goleiro.
      ' function formacaoLida(){\n'
      '  var s=MT.slots||[], f={def:0,mei:0,ata:0}, i, y, p;\n'
      '  for(i=0;i<s.length;i++){\n'
      '   if(!s[i]) continue;\n'
      '   p=s[i].pos; if(p==="GK") continue;\n'
      '   y=+s[i].y||0;\n'
      '   if(y>=62) f.def++; else if(y>=30) f.mei++; else f.ata++;\n'
      '  }\n'
      '  if(!f.def && !f.mei && !f.ata) return MT.form||"";\n'
      '  return f.def+"-"+f.mei+"-"+f.ata;\n'
      ' }\n'
      ' window.elFormacaoLida=formacaoLida;\n'
      '\n'
      #  A FUNCAO DA VAGA. Ordem do Luis, e o raciocinio e dele:
      #  *"se a gente puxar a melhor, ele vai olhar e falar 'que nota boa' — e
      #  vai estar tudo errado, porque no videogame dele vai estar outra. Tem que
      #  considerar a que ele esta utilizando na hora, mas da um aviso de que ele
      #  tem uma melhor pra aquela posicao."*
      #  Entao: entre as funcoes da posicao, vale a da BUILD dele se ela couber.
      #  So quando nao couber e que a vaga pega a melhor para a carta.
      ' function funcaoDaVaga(sl, k){\n'
      '  var fs=[]; try{ fs=MT_FUNCS[sl.pos]||[]; }catch(e){}\n'
      '  if(!fs.length) return sl.func||null;\n'
      '  if(k && typeof window.elBuildAtiva==="function"){\n'
      '   var b=window.elBuildAtiva(String(k).split("|")[0].split("@")[0]);\n'
      '   if(b && b.func && fs.indexOf(b.func)>=0) return b.func;\n'
      '  }\n'
      '  if(k){\n'
      '   var base=String(k).split("|")[0].split("@")[0], melhor=null;\n'
      '   try{\n'
      '    D.forEach(function(x){\n'
      '     if(!x || x.id==="MOLDE") return;\n'
      '     if(String(x.id).split("@")[0]!==base) return;\n'
      '     if(fs.indexOf(x.tipo)<0) return;\n'
      '     var n=nota(x); if(!melhor||n>melhor.n) melhor={n:n,tipo:x.tipo};\n'
      '    });\n'
      '   }catch(e){}\n'
      '   if(melhor) return melhor.tipo;\n'
      '  }\n'
      '  if(fs.indexOf(sl.func)>=0) return sl.func;\n'
      '  return fs[0];\n'
      ' }\n'
      '\n'
      #  Depois de a vaga mudar de lugar: recalcula posicao, funcao e formacao.
      ' function religaVaga(ix){\n'
      '  var sl=(MT.slots||[])[ix]; if(!sl) return;\n'
      '  if(sl.pos==="GK") return;  /* o goleiro nao sai do gol — ordem do Luis */\n'
      #  se ele escolheu a posicao na mao, arrastar dentro da MESMA faixa nao
      #  desfaz a escolha. Mudou de faixa, a regiao volta a mandar.
      '  var p=posDaRegiao(+sl.x||50, +sl.y||50);\n'
      '  if(sl.posFixa && faixaDe(p)===faixaDe(sl.pos)){\n'
      '   sl.func=funcaoDaVaga(sl, sl.key);\n'
      '   var nv=formacaoLida(); if(nv) MT.form_lida=nv;\n'
      '   return;\n'
      '  }\n'
      '  sl.posFixa=0;\n'
      '  if(p==="GK") p="ZC";       /* nenhuma outra vaga vira goleiro */\n'
      '  sl.pos=p;\n'
      '  sl.func=funcaoDaVaga(sl, sl.key);\n'
      '  var nova=formacaoLida();\n'
      '  if(nova) MT.form_lida=nova;\n'
      ' }\n'
      ' window.elReligaVaga=religaVaga;\n'
      '\n'
      #  O TAMANHO DO CARD NO CAMPO sai de duas contas, e vale a menor:
      #    pela LARGURA .. a linha mais cheia da formacao (cinco na zaga e o
      #                    caso mais apertado que existe no jogo)
      #    pela ALTURA ... as faixas ocupadas tem de caber de cima a baixo
      #  A foto 3:4 e o que come altura, e por isso ela entra na conta.
      #  ---------- ONDE CADA VAGA FICA NO GRAMADO ----------
      #  ⛔ A ALTURA DO CAMPO SAIU DO JAVASCRIPT. No arquivo que ele mandou o
      #  gramado e `aspect-ratio:3/4` — a propria proporcao resolve, e some com
      #  a conta circular que em 16/08 colapsou o card em 96px e com o campo
      #  gigante que ele reprovou em 17/08 (*"essa porra desse campo gigante"*).
      #  Aqui sobra so o que o CSS nao sabe fazer: a largura do card, tirada da
      #  linha mais cheia da formacao (cinco na zaga e o caso mais apertado que
      #  existe), e o desempate quando duas vagas se tocam.
      ' function arrumaCampo(){\n'
      '  var campo=document.querySelector("#mtwrap .mtcampo"); if(!campo) return;\n'
      '  var W=campo.clientWidth; if(!W) return;\n'
      '  var H=campo.clientHeight||Math.round(W*4/3);\n'
      '  var sls=[].slice.call(campo.querySelectorAll(".mtsl"));\n'
      '  if(!sls.length) return;\n'
      '  var slots=MT.slots||[], pts=[], i, j;\n'
      '  for(i=0;i<sls.length;i++){\n'
      '   var ix=+sls[i].getAttribute("data-i"); var sl=slots[ix]; if(!sl) continue;\n'
      '   pts.push({el:sls[i], x:+sl.x||50, y:+sl.y||50, ix:ix});\n'
      '  }\n'
      '  if(!pts.length) return;\n'
      #  as linhas sao agrupadas por vizinhanca (10%), nao por faixa fixa: o CA
      #  em y=14 e o PE em y=22 sao a MESMA linha aos olhos, e arredondar por
      #  faixa transformava uma 4-3-3 em seis linhas.
      '  pts.sort(function(a,b){ return a.y-b.y; });\n'
      '  var linhas=[], atual=null;\n'
      '  for(i=0;i<pts.length;i++){\n'
      '   if(!atual || (pts[i].y-atual.y0)>10){ atual={y0:pts[i].y, itens:[]}; linhas.push(atual); }\n'
      '   atual.itens.push(pts[i]);\n'
      '  }\n'
      '  var n=linhas.length, maior=1;\n'
      '  for(i=0;i<n;i++) if(linhas[i].itens.length>maior) maior=linhas[i].itens.length;\n'
      #  ---------- A LARGURA DO CARD ----------
      #  *"os que estao dentro do campo tem que estar maiores que os outros."*
      #  Duas contas, vale a menor:
      #    pela LARGURA . a linha mais cheia da formacao (cinco na zaga e o pior
      #                   caso que existe no jogo)
      #    pela ALTURA .. as faixas ocupadas tem de caber de cima a baixo. A foto
      #                   e quadrada, entao a altura do card fica ~ largura + 125.
      #  a LARGURA sai da linha mais cheia da formação (cinco na zaga é o pior
      #  caso que existe no jogo). O piso de 150px é a informação falando mais
      #  alto que a moldura.
      '  var PISO=150;\n'
      '  var porLarg=Math.floor((W-18)/maior)-10;\n'
      '  var larg=Math.max(PISO, Math.min(196, porLarg));\n'
      '  campo.style.setProperty("--elcw", larg+"px");\n'
      #  desenha uma vez no lugar de fábrica para poder MEDIR o card de verdade
      '  for(i=0;i<pts.length;i++){\n'
      '   pts[i].el.style.left=pts[i].x.toFixed(2)+"%";\n'
      '   pts[i].el.style.top =pts[i].y.toFixed(2)+"%";\n'
      '  }\n'
      '  var altMax=0;\n'
      '  for(i=0;i<pts.length;i++) altMax=Math.max(altMax, pts[i].el.offsetHeight||0);\n'
      '  if(!altMax) altMax=larg+118;\n'
      #  ---------- e agora quem cede é o CAMPO, não o card ----------
      #  Se as N linhas não cabem na altura do gramado, o gramado cresce. Antes
      #  eu encolhia o card e a escrita cortava — foi o que ele viu.
      #  o rótulo da posição pendura 12px para fora do bloco — ele não entra no
      #  `offsetHeight` e encostaria no card de baixo sem esta folga.
      '  var precisa=n*(altMax+16) + (n+1)*6;\n'
      #  🔴 e o `max-height:1280px` do CSS trava a altura que eu ponho aqui —
      #  medido: o JS pedia 1842px e o campo continuava em 1280, com cinco
      #  pares de cards um em cima do outro. Quem cresce solta o teto junto.
      #  🔴 DUAS TRAVAS, as duas minhas, achadas medindo:
      #  1. o `max-height:1280px` do CSS segurava a altura nova
      #  2. o `height:auto!important` do MEU CSS vencia o `style.height` inline
      #     — inline sem `!important` perde para `!important` de folha.
      #     Medido: o inline dizia 1878px e o clientHeight continuava 1352.
      '  if(precisa > H+2){\n'
      '   campo.style.setProperty("max-height","none","important");\n'
      '   campo.style.setProperty("height",Math.round(precisa)+"px","important");\n'
      '   H=campo.clientHeight||precisa;\n'
      '  } else if(campo.style.height){\n'
      '   campo.style.removeProperty("height");\n'
      '   campo.style.removeProperty("max-height");\n'
      '   H=campo.clientHeight||H;\n'
      '  }\n'
      #  sobrando altura, o card pode voltar a crescer até o teto
      '  var sobra=Math.floor(H/n)-(altMax-larg);\n'
      '  if(sobra>larg+6 && porLarg>larg){\n'
      '   larg=Math.min(196, porLarg, sobra);\n'
      '   campo.style.setProperty("--elcw", larg+"px");\n'
      '   altMax=0;\n'
      '   for(i=0;i<pts.length;i++) altMax=Math.max(altMax, pts[i].el.offsetHeight||0);\n'
      '   if(!altMax) altMax=larg+118;\n'
      '  }\n'
      '  var ph=100*altMax/H, pw=100*larg/W;\n'
      '  var mgy=ph/2+0.4;\n'
      '  var ys=[];\n'
      '  for(i=0;i<n;i++){\n'
      '   var soma=0;\n'
      '   for(j=0;j<linhas[i].itens.length;j++) soma+=linhas[i].itens[j].y;\n'
      '   ys.push(soma/linhas[i].itens.length);\n'
      '  }\n'
      '  var serveY=(ys[0]>=mgy) && (ys[n-1]<=100-mgy);\n'
      '  for(i=1;i<n && serveY;i++) if(ys[i]-ys[i-1] < ph) serveY=false;\n'
      '  if(!serveY){\n'
      '   var passo=(n>1)?((100-2*mgy)/(n-1)):0;\n'
      '   for(i=0;i<n;i++){\n'
      '    var yy=(n>1)?(mgy+i*passo):50;\n'
      '    for(j=0;j<linhas[i].itens.length;j++){\n'
      '     linhas[i].itens[j].y=yy;\n'
      '     if(slots[linhas[i].itens[j].ix]) slots[linhas[i].itens[j].ix].y=Math.round(yy*10)/10;\n'
      '    }\n'
      '   }\n'
      '  }\n'
      #  ---------- E DA ESQUERDA PARA A DIREITA ----------
      #  Mesma regra na horizontal, com a foto que ele mandou em 17/08 de duas
      #  vagas empilhadas: se QUALQUER par da linha se toca, a linha inteira e
      #  espalhada por igual — inclusive as que ele arrastou na mao.
      '  var mgx=pw/2+0.5;\n'
      '  for(i=0;i<n;i++){\n'
      '   var L=linhas[i].itens;\n'
      '   L.sort(function(a,b){ return a.x-b.x; });\n'
      '   var serve=(L[0].x>=mgx) && (L[L.length-1].x<=100-mgx);\n'
      '   for(j=1;j<L.length && serve;j++) if(L[j].x-L[j-1].x < pw+0.4) serve=false;\n'
      '   if(!serve){\n'
      '    for(j=0;j<L.length;j++){\n'
      '     L[j].x=(L.length>1)?(mgx+j*((100-2*mgx)/(L.length-1))):50;\n'
      '     if(slots[L[j].ix]) slots[L[j].ix].x=Math.round(L[j].x*10)/10;\n'
      '    }\n'
      '   }\n'
      '  }\n'
      '  for(i=0;i<pts.length;i++){\n'
      '   pts[i].el.style.left=pts[i].x.toFixed(2)+"%";\n'
      '   pts[i].el.style.top =pts[i].y.toFixed(2)+"%";\n'
      '  }\n'
      #  ultima passada: o card mais alto que a media (o que tem o aviso de
      #  "joga de") ainda pode passar da borda. Aqui ele e empurrado para dentro.
      '  for(i=0;i<pts.length;i++){\n'
      '   var e=pts[i].el;\n'
      '   var mh=50*(e.offsetHeight||0)/H, mw=50*(e.offsetWidth||0)/W;\n'
      '   var y2=Math.max(mh+0.3, Math.min(100-mh-0.3, pts[i].y));\n'
      '   var x2=Math.max(mw+0.3, Math.min(100-mw-0.3, pts[i].x));\n'
      '   if(Math.abs(y2-pts[i].y)>0.05) e.style.top =y2.toFixed(2)+"%";\n'
      '   if(Math.abs(x2-pts[i].x)>0.05) e.style.left=x2.toFixed(2)+"%";\n'
      '  }\n'
      ' }\n'
      '\n'
      #  ---------- A ALCA QUE MOVE A VAGA ----------
      #  🔴 17/08 — OS DOIS ARRASTOS BRIGAVAM. O Luis: *"arrastar os que estao no
      #  campo pra outras posicoes esta tudo bagunçado. Tentei arrastar o Aguero
      #  pra ponta, o ponta virou Cristiano Ronaldo e o Aguero nao ficou fora."*
      #  A causa: o MESMO gesto disparava dois comportamentos — o `pointerdown`
      #  comecava a mover a VAGA e o `dragstart` do HTML5 comecava a trocar o
      #  JOGADOR. Os dois mexiam no `MT.slots` na mesma passada.
      #  ⛔ A SOLUCAO E A DO ARQUIVO QUE ELE MANDOU: dois alvos diferentes. O
      #  card arrasta o JOGADOR; a alcinha redonda no canto arrasta a VAGA.
      #  Sem interruptor, sem modo, sem adivinhacao — e o botao "mover
      #  posicoes" deixa de ser obrigatorio para mexer no campo.
      ' function ligaArrastoDaVaga(sl){\n'
      '  var al=sl.querySelector(".elalca"); if(!al) return;\n'
      '  if(al.getAttribute("data-arr")) return;\n'
      '  al.setAttribute("data-arr","1");\n'
      '  al.addEventListener("pointerdown", function(ev){\n'
      '   if(ev.button!==0) return;\n'
      '   ev.preventDefault(); ev.stopPropagation();\n'
      '   var campo=document.querySelector("#mtwrap .mtcampo"); if(!campo) return;\n'
      '   var ix=+sl.getAttribute("data-i");\n'
      '   var st=(MT.slots||[])[ix]; if(!st) return;\n'
      '   var r=campo.getBoundingClientRect(), moveu=0;\n'
      '   sl.classList.add("arr");\n'
      '   function mv(e){\n'
      '    moveu=1; e.preventDefault();\n'
      '    var x=(e.clientX-r.left)/r.width*100, y=(e.clientY-r.top)/r.height*100;\n'
      '    x=Math.max(5,Math.min(95,x)); y=Math.max(4,Math.min(96,y));\n'
      '    sl.style.left=x.toFixed(2)+"%"; sl.style.top=y.toFixed(2)+"%";\n'
      '    st.x=Math.round(x*10)/10; st.y=Math.round(y*10)/10; st.mv=1;\n'
      '   }\n'
      '   function up(){\n'
      '    document.removeEventListener("pointermove",mv);\n'
      '    document.removeEventListener("pointerup",up);\n'
      '    sl.classList.remove("arr");\n'
      '    if(moveu){\n'
      '     religaVaga(ix);\n'
      '     try{ MTdb.save(); }catch(e){}\n'
      '     window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '     try{ mtRender(); }catch(e){}\n'
      '    }\n'
      '   }\n'
      '   document.addEventListener("pointermove",mv);\n'
      '   document.addEventListener("pointerup",up);\n'
      '  });\n'
      ' }\n'
      '\n'
      #  ---------- O AVISO DE BUILD MELHOR ----------
      #  Ordem do Luis, e o argumento e dele, inteiro:
      #    *"se a gente puxar a melhor, ele vai olhar e falar 'nossa, que nota
      #    boa' e vai pensar que esta tudo certo. E nao esta, porque a gente vai
      #    estar considerando uma e no videogame dele vai estar outra. Tem que
      #    considerar a que ele esta utilizando na hora, mas da um aviso de que
      #    ele tem uma melhor pra aquela posicao."*
      #  Entao o numero na tela e sempre o da build DELE. O aviso so conta o que
      #  ele esta deixando na mesa, e a troca so acontece se ele mandar — porque
      #  trocar aqui significa ele ter de trocar no videogame tambem.
      ' function avisoDeBuildMelhor(k, sl){\n'
      '  if(!k || !sl) return "";\n'
      '  if(typeof window.elBuildsDe!=="function") return "";\n'
      '  var idb=String(k).split("|")[0].split("@")[0];\n'
      '  var L=window.elBuildsDe(idb); if(!L || L.length<2) return "";\n'
      '  var fs=[]; try{ fs=MT_FUNCS[sl.pos]||[]; }catch(e){}\n'
      '  if(!fs.length) return "";\n'
      '  var atual=window.elBuildAtiva(idb); if(!atual) return "";\n'
      '  var nAtual=0;\n'
      '  try{ var p=window.elPontuacao(k); nAtual=p?p.n:0; }catch(e){}\n'
      '  var melhor=null, i;\n'
      '  for(i=0;i<L.length;i++){\n'
      '   if(L[i]===atual) continue;\n'
      '   if(fs.indexOf(L[i].func)<0) continue;\n'
      '   var n=0;\n'
      '   try{ n=window.elNotaDaBuild(String(k).split("|")[0]+"|"+L[i].func, L[i], true); }catch(e){}\n'
      '   if(!melhor || n>melhor.n) melhor={n:n, b:L[i], i:i};\n'
      '  }\n'
      '  if(!melhor || melhor.n <= nAtual+0.01) return "";\n'
      '  var d=(melhor.n-nAtual).toFixed(2).replace(".",",");\n'
      '  return \'<div class=elaviso>\\u26a0 voc\\u00ea tem build melhor pra \'+esc(sl.pos)\n'
      '   +\'<br>\\u201c\'+esc(melhor.b.nome)+\'\\u201d daria \'\n'
      '   +melhor.n.toFixed(2).replace(".",",")+\' (+\'+d+\')\'\n'
      '   +\'<button onclick="event.stopPropagation();bldUsa(\\\'\'+idb+\'\\\',\'+melhor.i+\')">\'\n'
      '   +\'usar essa</button></div>\';\n'
      ' }\n'
      '\n'
      ' function refazVaga(sl){\n'
      '  var k=sl.getAttribute("data-key")||"";\n'
      '  var ix=+sl.getAttribute("data-i");\n'
      '  var s=(MT.slots||[])[ix];\n'
      #  a funcao da vaga e recalculada a cada desenho: ela depende de quem esta
      #  nela e da build que ele escolheu, e as duas coisas mudam.
      '  if(s && k){\n'
      '   var fnova=funcaoDaVaga(s, k);\n'
      '   if(fnova && fnova!==s.func){ s.func=fnova; try{ MTdb.save(); }catch(e){} }\n'
      '  }\n'
      '  var assin=k+"|"+(s?s.func:"")+"|"+(s?s.pos:"")+"|"+(window.EL_SELO||0);\n'
      '  if(sl.getAttribute("data-el")!==assin){\n'
      #  a alcinha do arquivo de referencia: duas listras num circulo de 20px no
      #  canto de cima. O GOLEIRO nao tem — a vaga dele nao anda.
      '   var rot=s?(\'<div class=elvagapos>\'+seletorDePosicao(s)\n'
      '     +\'<span class=elvagaseta>\\u25be</span></div>\'):"";\n'
      '   var alca=(s && s.pos!=="GK")\n'
      '    ?\'<button type=button class=elalca title="arraste para mover esta vaga">\'\n'
      '      +\'\\u2725</button>\':"";\n'
      '   if(k){ sl.innerHTML=montaCard(k,"campo",s)+avisoDeBuildMelhor(k,s)+rot+alca; }\n'
      '   else {\n'
      '    var fn=s?String(s.func||""):"";\n'
      '    sl.innerHTML=\'<div class=elvazio onclick="event.stopPropagation();mtAbreSel(\'+ix+\')">\'\n'
      '     +\'<div class=elvpos>\'+esc(s?s.pos:"")+\'</div>\'\n'
      '     +\'<div class=elvmais>+</div>\'\n'
      '     +\'<div class=elvfn>\'+esc(fn)+\'</div></div>\'+rot+alca;\n'
      '   }\n'
      '   sl.setAttribute("data-el",assin);\n'
      '   sl.removeAttribute("data-arr");\n'
      '  }\n'
      '  ligaArrastoDaVaga(sl);\n'
      ' }\n'
      '\n'
      ' /* ---------- 7 · O ESQUELETO DA PAGINA ---------- */\n'
      ' function nomeDoUsuario(){\n'
      '  try{ if(window.EF_USUARIO) return window.EF_USUARIO; }catch(e){}\n'
      '  return null;\n'
      ' }\n'
      #  ---------- O CABECALHO ----------
      #  Do arquivo dele: "ELENCO" miudo em cima, o nome do time grande, e do
      #  outro lado quatro numeros em linha — formacao, quantos em campo,
      #  pontuacao media e tecnico.
      ' function cabecalho(){\n'
      '  var tit=(MT.slots||[]).filter(function(x){return x&&x.key;});\n'
      '  var soma=0;\n'
      '  tit.forEach(function(x){ var p=window.elPontuacao(x.key); if(p) soma+=p.n; });\n'
      '  var med=tit.length?(soma/tit.length):0;\n'
      '  var dono=nomeDoUsuario();\n'
      '  var cr="inherit"; try{ cr=cor(med,0); }catch(e){}\n'
      '  var lida=""; try{ lida=formacaoLida()||""; }catch(e){}\n'
      '  var tec=null; try{ tec=mtTecNome(); }catch(e){}\n'
      '  function st(r,v,est){ return \'<div class=elstat><p>\'+esc(r)+\'</p>\'\n'
      '   +\'<p\'+(est?(\' style="\'+est+\'"\'):"")+\'>\'+v+\'</p></div>\'; }\n'
      '  return \'<div><p class=eleyebrow>Elenco</p>\'\n'
      '   +\'<div class=eltime contenteditable=true spellcheck=false \'\n'
      '    +\'onblur="elGravaNome(this)" onkeydown="if(event.key===\\\'Enter\\\'){event.preventDefault();this.blur();}" \'\n'
      '    +\'title="clique para trocar o nome do seu time">\'+esc(MT.nome||"Meu time")+\'</div>\'\n'
      '   +\'<div class=eldono>\'+(dono?(\'time de <b>\'+esc(dono)+\'</b>\')\n'
      '     :\'<span title="entre na sua conta para o time ficar salvo">time salvo neste navegador</span>\')\n'
      '   +\'</div></div>\'\n'
      '   +\'<div class=elstats>\'\n'
      '    +st("Forma\\u00e7\\u00e3o", esc(lida||MT.form||"\\u2014"))\n'
      '    +st("Em campo", tit.length+"/"+TETO_TIT)\n'
      '    +st("Pontua\\u00e7\\u00e3o m\\u00e9dia",\n'
      '        tit.length?med.toFixed(2).replace(".",","):"\\u2014", "color:"+cr)\n'
      '    +st("T\\u00e9cnico", esc(tec||"\\u2014"))\n'
      '   +\'</div>\';\n'
      ' }\n'
      ' window.elGravaNome=function(el){\n'
      '  var v=String(el.textContent||"").replace(/\\s+/g," ").trim();\n'
      '  MT.nome = v || "Meu time";\n'
      '  el.textContent=MT.nome;\n'
      '  try{ MTdb.save(); }catch(e){}\n'
      ' };\n'
      '\n'
      ' function selFormacao(){\n'
      #  trocar no seletor volta as vagas ao lugar de fabrica daquela formacao —
      #  e o `mv` some, para elas voltarem a ser espalhadas pelo desenho.
      '  var h=\'<select onchange="elTrocaFormacao(this.value)" \'\n'
      '   +\'onclick="event.stopPropagation()" title="trocar a forma\\u00e7\\u00e3o">\';\n'
      '  var ks=[]; try{ ks=Object.keys(MT_FORM); }catch(e){}\n'
      '  for(var i=0;i<ks.length;i++)\n'
      '   h+=\'<option\'+(ks[i]===MT.form?" selected":"")+\'>\'+esc(ks[i])+\'</option>\';\n'
      '  return h+"</select>";\n'
      ' }\n'
      #  *"quando ele faz isso, deixa de ser uma 4-3-3 e vira uma 4-4-2"* — o
      #  numero grande e o que o campo ESTA, nao o que foi escolhido no seletor.
      ' window.elTrocaFormacao=function(v){\n'
      '  var f=null; try{ f=MT_FORM[v]; }catch(e){}\n'
      '  MT.form=v;\n'
      '  var velhos=(MT.slots||[]).map(function(x){ return x?x.key:null; });\n'
      '  MT.slots=[];\n'
      '  try{ mtSlots(); }catch(e){}\n'
      '  var s2=MT.slots||[], i;\n'
      '  for(i=0;i<s2.length;i++){ if(s2[i]){ s2[i].mv=0; s2[i].key=velhos[i]||null; } }\n'
      '  MT.form_lida=null;\n'
      '  window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '  try{ MTdb.save(); }catch(e){}\n'
      '  try{ mtRender(); }catch(e){}\n'
      ' };\n'      #  ---------- A PLACA DA FORMACAO ----------
      #  Do arquivo dele: o numero grande em dourado e as barrinhas ao lado. As
      #  barras nao sao enfeite — cada uma e uma linha do time, e a altura dela
      #  e quanta gente tem naquela linha.
      ' function blocoFormacao(){\n'
      '  var lida="";\n'
      '  try{ lida=formacaoLida(); }catch(e){}\n'
      '  var dif=(lida && lida!==MT.form);\n'
      '  var mostra=String(lida||MT.form||"");\n'
      '  var ns=mostra.split("-").map(function(x){ return parseInt(x,10)||0; });\n'
      '  var dots="";\n'
      '  for(var i=ns.length-1;i>=0;i--)\n'
      '   dots+=\'<i style="height:\'+Math.min(28,6+ns[i]*5)+\'px"></i>\';\n'
      '  return \'<div class=elbadge><div><p class=ellbl>Forma\\u00e7\\u00e3o</p>\'\n'
      '   +\'<p class=elnum>\'+esc(mostra||"\\u2014")+\'</p></div>\'\n'
      '   +\'<div class=eldots>\'+dots+\'</div>\'\n'
      '   +\'<span class=elseta>trocar \\u25be</span>\'\n'
      '   +selFormacao()+\'</div>\'\n'
      '   +(dif?(\'<div class=elnota2>voc\\u00ea moveu as vagas \\u2014 partiu de \'\n'
      '     +esc(MT.form)+\'</div>\'):"");\n'
      ' }\n'
      ' function blocoTecnico(){\n'
      '  var nome=null, bs=[];\n'
      '  try{ nome=mtTecNome(); }catch(e){}\n'
      '  try{ bs=mtTecBs()||[]; }catch(e){}\n'
      '  var ini=String(nome||"?").trim().charAt(0).toUpperCase();\n'
      '  var sel=\'<select class=elsel onchange="mtPoeTec(this.value)">\'\n'
      '   +\'<option value=""\'+((MT.tec===null||MT.tec===undefined)?" selected":"")\n'
      '   +\'>\\u2014 sem t\\u00e9cnico \\u2014</option>\';\n'
      '  try{\n'
      '   for(var i=0;i<_TECOP.length;i++)\n'
      '    sel+=\'<option value="\'+_TECOP[i][0]+\'"\'+((MT.tec===_TECOP[i][0])?" selected":"")\n'
      '     +\'>\'+esc(_TECOP[i][1])+\'</option>\';\n'
      '  }catch(e){}\n'
      '  sel+="</select>";\n'
      '  var efeito="";\n'
      #  ⚠️ o `mtTecBs` devolve a LISTA DE ATRIBUTOS do tecnico (cada um vale
      #  +1), nao pares atributo/valor. Medido na casca: `TECS[i][1].map(tecPT)`.
      #  Ler como par daria `undefined` na tela.
      '  if(bs&&bs.length){\n'
      '   var t=[], j;\n'
      '   for(j=0;j<bs.length;j++){\n'
      '    try{ t.push("+1 em "+((typeof tecPT==="function")?tecPT(bs[j]):bs[j])); }catch(e){}\n'
      '   }\n'
      '   if(t.length) efeito=\'<div class=elnota2>\'+esc(t.join(" \\u00b7 "))\n'
      '    +\'<br>vale para o time inteiro</div>\';\n'
      '  } else {\n'
      '   efeito=\'<div class=elnota2>sem t\\u00e9cnico \\u2014 as pontua\\u00e7\\u00f5es \'\n'
      '    +\'do campo est\\u00e3o sem o b\\u00f4nus dele</div>\';\n'
      '  }\n'
      '  return \'<div class=elcoach><div class=elavatar>\'+esc(nome?ini:"\\u2014")+\'</div>\'\n'
      '   +\'<div class=elcinfo><p class=elrole>T\\u00e9cnico</p>\'\n'
      '   +\'<p class=elcname title="\'+esc(nome||"")+\'">\'\n'
      '   +esc(nome||"\\u2014 sem t\\u00e9cnico \\u2014")+\'</p></div></div>\'\n'
      '   +sel+efeito;\n'
      ' }\n'
      '\n'
      #  as duas áreas, as duas pequenas, as marcas de pênalti, a linha do meio
      #  e o círculo central — do desenho que ele aprovou no base44.
      ' window.EL_RISCOS=\'<div class="risco r-borda"></div>\'\n'
      '  +\'<div class="risco r-meio"></div><div class="risco r-circulo"></div>\'\n'
      '  +\'<div class="risco r-areaG r-cima"></div><div class="risco r-areaP r-cima"></div>\'\n'
      '  +\'<div class="risco r-areaG r-baixo"></div><div class="risco r-areaP r-baixo"></div>\'\n'
      '  +\'<div class="risco r-pena" style="top:11%"></div>\'\n'
      '  +\'<div class="risco r-pena" style="bottom:11%"></div>\';\n'
      ' function esqueleto(){\n'
      '  var w=document.getElementById("mtwrap"); if(!w) return null;\n'
      '  var campo=w.querySelector(".mtcampo"); if(!campo) return null;\n'
      '  var grid=w.querySelector(".mtgrid"); if(!grid) return null;\n'
      '  var caixas=[].slice.call(w.querySelectorAll(".mtbanco"));\n'
      '  var cxBanco=null, cxFora=null;\n'
      '  caixas.forEach(function(x){\n'
      '   if(x.className.indexOf("alvobanco")>=0) cxBanco=x;\n'
      '   if(x.className.indexOf("alvoelenco")>=0) cxFora=x;\n'
      '  });\n'
      '  var wrap=document.createElement("div"); wrap.id="elwrap";\n'
      '  try{\n'
      '   if(!campo.querySelector(".risco")){\n'
      '    campo.insertAdjacentHTML("afterbegin", window.EL_RISCOS);\n'
      '   }\n'
      '  }catch(e){}\n'
      #  ⛔ O DESENHO E O DO ARQUIVO QUE ELE MANDOU, sem invencao minha:
      #      cabecalho de largura total ......... nome do time e os quatro numeros
      #      coluna esquerda, 300px ............. formacao, tecnico e os reservas
      #      coluna direita ..................... o campo
      #      faixa embaixo, largura total ....... o fora do banco
      '  wrap.innerHTML=\'<div id=elfaixa></div>\'\n'
      '   +\'<div id=elgrid>\'\n'
      '   +\'<div id=elreservas class=elpane>\'\n'
      '    +\'<div id=elfmt></div><div id=elban></div>\'\n'
      '   +\'</div>\'\n'
      '   +\'<div id=elesq class=elpane>\'\n'
      '    +\'<div class=elhd>Campo <em>arraste o card para trocar \\u00b7 \'\n'
      '    +\'arraste a al\\u00e7a para mover a vaga</em></div>\'\n'
      '   +\'</div>\'\n'
      '   +\'</div>\'\n'
      '   +\'<div id=elfora class=elpane style="margin-top:20px"></div>\';\n'
      '  grid.parentNode.insertBefore(wrap, grid);\n'
      '  grid.style.display="none";\n'
      '  wrap.querySelector("#elesq").appendChild(campo);\n'
      '  wrap._cxBanco=cxBanco; wrap._cxFora=cxFora;\n'
      '  return wrap;\n'
      ' }\n'
      '\n'
      #  ---------- A BARRA DE VER O FORA DO BANCO ----------
      #  Ordem do Luis: *"a organizacao padrao e o adicionado mais recente. Ai
      #  voce coloca visualizacoes: se ele quer ver os que tem mais pontuacao,
      #  se ele quer so os que sao isso, so os que sao aquilo. E uma barra de
      #  pesquisa pelo nome."*
      #  ⛔ Nada disso mexe em `MT.elenco`: a ordem guardada continua sendo a de
      #  entrada (o mais novo na frente). Isto e so o jeito de OLHAR a lista.
      ' var VER={ord:"recente", setor:"", pos:"", func:"", est:"", q:""};\n'
      ' window.EL_VER=VER;\n'
      ' var SETOR={GK:"goleiro", ZC:"defesa", LE:"defesa", LD:"defesa",\n'
      '            VOL:"meio", MC:"meio", MLE:"meio", MLD:"meio", MO:"meio",\n'
      '            PE:"ataque", PD:"ataque", SA:"ataque", CA:"ataque"};\n'
      ' function listaFora(){\n'
      '  var L=(MT.elenco||[]).slice(), i;\n'
      '  var info=L.map(function(k,ix){\n'
      '   var c=null; try{ c=mtCard(k); }catch(e){}\n'
      '   var p=null; try{ p=window.elPontuacao(k); }catch(e){}\n'
      '   return {k:k, c:c, ix:ix, n:(p?p.n:0), func:(p&&p.func)||(c?c.tipo:""),\n'
      '           pos:c?(c.np||c.pos||""):"", nome:c?String(c.nome||""):"",\n'
      '           est:c?String(c.modelo||""):""};\n'
      '  }).filter(function(x){ return !!x.c; });\n'
      '  var q=VER.q.toLowerCase().trim();\n'
      '  info=info.filter(function(x){\n'
      '   if(q && x.nome.toLowerCase().indexOf(q)<0) return false;\n'
      '   if(VER.setor && SETOR[x.pos]!==VER.setor) return false;\n'
      '   if(VER.pos && x.pos!==VER.pos) return false;\n'
      '   if(VER.func && x.func!==VER.func) return false;\n'
      '   if(VER.est && x.est!==VER.est) return false;\n'
      '   return true;\n'
      '  });\n'
      '  if(VER.ord==="maior") info.sort(function(a,b){ return b.n-a.n; });\n'
      '  else if(VER.ord==="menor") info.sort(function(a,b){ return a.n-b.n; });\n'
      '  else if(VER.ord==="nome") info.sort(function(a,b){\n'
      '   return a.nome.localeCompare(b.nome,"pt"); });\n'
      '  else if(VER.ord==="pos") info.sort(function(a,b){\n'
      '   return String(a.pos).localeCompare(String(b.pos))||(b.n-a.n); });\n'
      '  return info;\n'
      ' }\n'
      ' window.elVer=function(campo, valor){\n'
      '  VER[campo]=valor; desenhaFora();\n'
      ' };\n'
      ' window.elLimpaVer=function(){\n'
      '  VER.setor=""; VER.pos=""; VER.func=""; VER.est=""; VER.q=""; VER.ord="recente";\n'
      '  desenhaFora();\n'
      ' };\n'
      ' function opcoes(lista, sel, vazio){\n'
      '  var h=\'<option value="">\'+esc(vazio)+\'</option>\', i;\n'
      '  for(i=0;i<lista.length;i++)\n'
      '   h+=\'<option value="\'+esc(lista[i])+\'"\'+(lista[i]===sel?" selected":"")\n'
      '    +\'>\'+esc(lista[i])+\'</option>\';\n'
      '  return h;\n'
      ' }\n'
      ' function barraDeVer(mostrando, total){\n'
      '  var poss={}, funs={}, ests={};\n'
      '  (MT.elenco||[]).forEach(function(k){\n'
      '   var c=null; try{ c=mtCard(k); }catch(e){}  if(!c) return;\n'
      '   if(c.np||c.pos) poss[c.np||c.pos]=1;\n'
      '   var p=null; try{ p=window.elPontuacao(k); }catch(e){}\n'
      '   if(p&&p.func) funs[p.func]=1;\n'
      '   if(c.modelo) ests[c.modelo]=1;\n'
      '  });\n'
      '  function ord(o){ return Object.keys(o).sort(function(a,b){\n'
      '   return a.localeCompare(b,"pt"); }); }\n'
      '  var limpou=(VER.setor||VER.pos||VER.func||VER.est||VER.q||VER.ord!=="recente");\n'
      '  return \'<div id=elbarra>\'\n'
      '   +\'<input id=elbusca placeholder="buscar pelo nome\\u2026" value="\'+esc(VER.q)+\'" \'\n'
      '    +\'oninput="elVer(\\\'q\\\',this.value)">\'\n'
      '   +\'<select class=elsel2 onchange="elVer(\\\'ord\\\',this.value)">\'\n'
      '    +\'<option value="recente"\'+(VER.ord==="recente"?" selected":"")+\'>adicionado por \\u00faltimo</option>\'\n'
      '    +\'<option value="maior"\'+(VER.ord==="maior"?" selected":"")+\'>maior pontua\\u00e7\\u00e3o</option>\'\n'
      '    +\'<option value="menor"\'+(VER.ord==="menor"?" selected":"")+\'>menor pontua\\u00e7\\u00e3o</option>\'\n'
      '    +\'<option value="nome"\'+(VER.ord==="nome"?" selected":"")+\'>nome A-Z</option>\'\n'
      '    +\'<option value="pos"\'+(VER.ord==="pos"?" selected":"")+\'>posi\\u00e7\\u00e3o</option>\'\n'
      '   +\'</select>\'\n'
      '   +\'<select class=elsel2 onchange="elVer(\\\'setor\\\',this.value)">\'\n'
      '    +opcoes(["goleiro","defesa","meio","ataque"], VER.setor, "todos os setores")+\'</select>\'\n'
      '   +\'<select class=elsel2 onchange="elVer(\\\'pos\\\',this.value)">\'\n'
      '    +opcoes(ord(poss), VER.pos, "todas as posi\\u00e7\\u00f5es")+\'</select>\'\n'
      '   +\'<select class=elsel2 onchange="elVer(\\\'func\\\',this.value)">\'\n'
      '    +opcoes(ord(funs), VER.func, "todas as fun\\u00e7\\u00f5es")+\'</select>\'\n'
      '   +\'<select class=elsel2 onchange="elVer(\\\'est\\\',this.value)">\'\n'
      '    +opcoes(ord(ests), VER.est, "todos os estilos")+\'</select>\'\n'
      '   +(limpou?\'<button class="elbt ellimpa" onclick="elLimpaVer()">limpar</button>\':"")\n'
      '   +\'<span class=elcont>\'+(mostrando===total?(total+" cards")\n'
      '     :(mostrando+" de "+total))+\'</span>\'\n'
      '   +\'</div>\';\n'
      ' }\n'
      ' function desenhaFora(){\n'
      '  var alvo=document.getElementById("elfora"); if(!alvo) return;\n'
      '  var foco=(document.activeElement && document.activeElement.id==="elbusca");\n'
      '  var pos=foco?document.activeElement.selectionStart:0;\n'
      '  var L=listaFora(), total=(MT.elenco||[]).length;\n'
      '  alvo.innerHTML=\n'
      '   \'<div class=elhd>Fora do banco \'\n'
      '   +\'<em>\'+total+\' cards\'\n'
      '   +\'<button class=elbt style="margin-left:6px" onclick="mtAddElenco()">\'\n'
      '   +\'+ adicionar card</button></em></div>\'\n'
      '   +barraDeVer(L.length, total)\n'
      '   +(L.length?(\'<div class=elgrid>\'\n'
      '     +L.map(function(x){ return montaCard(x.k,"fora"); }).join("")+\'</div>\')\n'
      '    :(\'<div class=elvazia>\'\n'
      '     +(total?"Nenhum card com esse filtro.":"Ningu\\u00e9m fora do banco ainda.")\n'
      '     +\'</div>\'));\n'
      '  if(foco){ var b=document.getElementById("elbusca");\n'
      '   if(b){ b.focus(); try{ b.setSelectionRange(pos,pos); }catch(e){} } }\n'
      '  ligaArrasta();\n'
      ' }\n'
      '\n'
      #  ---------- ARRASTAR ENTRE OS TRES ----------
      #  ORDEM DO LUIS: *"eu preciso que voce implemente a gente arrastar o card
      #  do banco de reservas ou de fora do banco pra dentro do campo... isso ai
      #  ja ate tinha antes, nao sei por que voce tirou."*
      #  🔴 ERRO MEU, e ele esta certo: a casca tem `mtDndInit`, que liga o
      #  arrasto nos elementos que o `mtRender` desenha. Eu passei a redesenhar
      #  os cards por cima e a monta-los em caixas novas — o arrasto ficou preso
      #  nos elementos velhos, que agora estao escondidos. Aqui ele volta,
      #  reusando o `mtSolta` da casca, que ja sabe fazer as nove trocas.
      #  🔴 17/08 — A BAGUNCA DO ARRASTO DENTRO DO CAMPO. O Luis: *"tentei
      #  arrastar o Aguero pra ponta, o ponta virou Cristiano Ronaldo e o Aguero
      #  nao ficou fora."*
      #  A causa: DOIS sistemas de arrasto ligados no MESMO elemento. O
      #  `mtDndInit` da casca liga os listeners dele em todo `.mtsl` no fim de
      #  cada `mtRender`, e eu liguei os meus por cima. No soltar, os dois
      #  rodavam: o da casca mexia no `MT.slots` pelo `mtSolta` e o meu mexia
      #  pelo `solta` — cada um com a sua ideia do que estava sendo arrastado.
      #  O resultado nao era nenhum dos dois.
      #  ⛔ Aqui o da casca e desligado. Um dono so para o arrasto.
      ' (function(){\n'
      '  if(typeof window.mtDndInit==="function") window.mtDndInit=function(){};\n'
      '  if(typeof window.mtDragInit==="function") window.mtDragInit=function(){};\n'
      ' })();\n'
      '\n'
      ' var ARR=null;\n'
      ' function ligaArrasta(){\n'
      '  var w=document.getElementById("mtwrap"); if(!w) return;\n'
      '  [].slice.call(w.querySelectorAll("#elreservas .elcard,#elfora .elcard"))\n'
      '   .forEach(function(el){\n'
      '    if(el.getAttribute("data-dnd")) return;\n'
      '    el.setAttribute("data-dnd","1");\n'
      '    var caixa=el.closest("#elreservas")?"banco":"fora";\n'
      '    el.setAttribute("draggable","true");\n'
      '    el.addEventListener("dragstart", function(e){\n'
      '     var k=el.getAttribute("data-k")||"";\n'
      '     ARR={de:caixa, k:k};\n'
      '     e.dataTransfer.effectAllowed="move";\n'
      '     try{ e.dataTransfer.setData("text/plain",k); }catch(x){}\n'
      '     el.style.opacity=".45";\n'
      '    });\n'
      '    el.addEventListener("dragend", function(){\n'
      '     el.style.opacity="";\n'
      '     [].slice.call(document.querySelectorAll(".pousa"))\n'
      '      .forEach(function(x){ x.classList.remove("pousa"); });\n'
      '    });\n'
      '   });\n'
      '  [].slice.call(w.querySelectorAll("#mtwrap .mtsl")).forEach(function(sl){\n'
      '   if(sl.getAttribute("data-dnd")) return;\n'
      '   sl.setAttribute("data-dnd","1");\n'
      '   sl.setAttribute("draggable","true");\n'
      '   sl.addEventListener("dragstart", function(e){\n'
      '    var ed=false; try{ ed=!!MT_ED; }catch(x){}\n'
      '    if(ed){ e.preventDefault(); return; }\n'
      '    var k=sl.getAttribute("data-key")||"";\n'
      '    if(!k){ e.preventDefault(); return; }\n'
      '    ARR={de:"campo", k:k, i:+sl.getAttribute("data-i")};\n'
      '    e.dataTransfer.effectAllowed="move";\n'
      '    try{ e.dataTransfer.setData("text/plain",k); }catch(x){}\n'
      '    sl.style.opacity=".45";\n'
      '   });\n'
      '   sl.addEventListener("dragend", function(){ sl.style.opacity=""; });\n'
      '   sl.addEventListener("dragover", function(e){\n'
      '    if(!ARR) return; e.preventDefault(); e.dataTransfer.dropEffect="move";\n'
      '    sl.classList.add("pousa"); });\n'
      '   sl.addEventListener("dragleave", function(){ sl.classList.remove("pousa"); });\n'
      '   sl.addEventListener("drop", function(e){\n'
      '    e.preventDefault(); e.stopPropagation(); sl.classList.remove("pousa");\n'
      '    solta("campo", +sl.getAttribute("data-i")); });\n'
      '  });\n'
      '  [["#elreservas","banco"],["#elfora","fora"]].forEach(function(par){\n'
      '   var cx=document.querySelector(par[0]); if(!cx) return;\n'
      '   if(cx.getAttribute("data-dnd")) return;\n'
      '   cx.setAttribute("data-dnd","1");\n'
      '   cx.addEventListener("dragover", function(e){\n'
      '    if(!ARR) return; e.preventDefault(); e.dataTransfer.dropEffect="move";\n'
      '    cx.classList.add("pousa"); });\n'
      '   cx.addEventListener("dragleave", function(){ cx.classList.remove("pousa"); });\n'
      '   cx.addEventListener("drop", function(e){\n'
      '    e.preventDefault(); cx.classList.remove("pousa"); solta(par[1], -1); });\n'
      '  });\n'
      ' }\n'
      ' function solta(destino, ix){\n'
      '  var d=ARR; ARR=null; if(!d || !d.k) return;\n'
      '  var s=MT.slots||[], q;\n'
      '  if(destino==="campo"){\n'
      '   var alvo=s[ix]; if(!alvo) return;\n'
      '   var saiu=alvo.key;\n'
      '   if(d.de==="campo"){\n'
      '    if(d.i===ix) return;\n'
      '    s[d.i].key=saiu; alvo.key=d.k;\n'
      '    s[d.i].func=funcaoDaVaga(s[d.i], saiu);\n'
      '   } else {\n'
      '    if(!podeEntrarNosVinteETres(d.k)) return;\n'
      '    soltaDe(d.k,"campo"); alvo.key=d.k;\n'
      '    if(saiu){ if(d.de==="banco") (MT.banco=MT.banco||[]).push(saiu);\n'
      '              else (MT.elenco=MT.elenco||[]).unshift(saiu); }\n'
      '   }\n'
      '   alvo.func=funcaoDaVaga(alvo, alvo.key);\n'
      '  } else if(destino==="banco"){\n'
      '   if((MT.banco||[]).indexOf(d.k)>=0) return;\n'
      '   if(d.de!=="campo" && !cabeNoBanco()) return;\n'
      '   if(!podeEntrarNosVinteETres(d.k)) return;\n'
      '   if((MT.banco||[]).length>=TETO_BANCO && d.de==="campo"){ cabeNoBanco(); return; }\n'
      '   soltaDe(d.k,"banco"); (MT.banco=MT.banco||[]).push(d.k);\n'
      '  } else {\n'
      '   if((MT.elenco||[]).indexOf(d.k)>=0) return;\n'
      '   soltaDe(d.k,"fora"); (MT.elenco=MT.elenco||[]).unshift(d.k);\n'
      '  }\n'
      '  window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '  try{ MTdb.save(); }catch(e){}\n'
      '  try{ mtRender(); }catch(e){}\n'
      ' }\n'
      '\n'
      #  ---------- O SANEADOR DAS VAGAS ----------
      #  🔴 ACHADO EM 17/08, na tela do Luis: *"nenhum vai pro campo. Voce clica
      #  em titular e ele nao vai."* Aqui reproduzi o estado dele e funcionava —
      #  o defeito estava no TIME SALVO no navegador dele, escrito por uma
      #  versao intermediaria minha: das 11 vagas so 7 apareciam, e nenhuma
      #  mostrava a sigla da posicao. O `MT.slots` tinha vaga sem `pos`, sem
      #  `func` e com coordenada fora de faixa.
      #
      #  A licao: o `MT` fica no navegador do usuario e SOBREVIVE a troca de
      #  versao. Qualquer coisa que eu grave errado uma vez fica gravada nele
      #  para sempre — e a proxima versao, mesmo certa, herda o estrago.
      #  Por isso a tela passa a CONFERIR as vagas antes de desenhar, e a
      #  consertar o que estiver quebrado sem perder o time.
      ' function saneiaSlots(){\n'
      '  var f=null;\n'
      '  try{ f=MT_FORM[MT.form]||MT_FORM["4-3-3"]; }catch(e){ return; }\n'
      '  if(!f) return;\n'
      '  var s=MT.slots||[], mexeu=false, i;\n'
      '  if(s.length!==f.length){\n'
      '   var guarda=s.map(function(x){ return x?x.key:null; });\n'
      '   MT.slots=[]; try{ mtSlots(); }catch(e){ return; }\n'
      '   s=MT.slots||[];\n'
      '   for(i=0;i<s.length;i++) if(s[i]) s[i].key=guarda[i]||null;\n'
      '   mexeu=true;\n'
      '  }\n'
      '  var vistos={};\n'
      '  for(i=0;i<s.length;i++){\n'
      '   if(!s[i]){ s[i]={pos:f[i][0], func:null, key:null, x:f[i][1], y:f[i][2]};\n'
      '              mexeu=true; }\n'
      '   var sl=s[i], fs=null;\n'
      '   try{ fs=MT_FUNCS[sl.pos]; }catch(e){}\n'
      '   if(!sl.pos || !fs || !fs.length){ sl.pos=f[i][0]; sl.mv=0; sl.posFixa=0;\n'
      '    try{ fs=MT_FUNCS[sl.pos]; }catch(e){} mexeu=true; }\n'
      '   if(!fs || !fs.length) continue;\n'
      '   if(!sl.func || fs.indexOf(sl.func)<0){ sl.func=fs[0]; mexeu=true; }\n'
      '   var x=+sl.x, y=+sl.y;\n'
      '   if(!isFinite(x)||!isFinite(y)||x<0||x>100||y<0||y>100){\n'
      '    sl.x=f[i][1]; sl.y=f[i][2]; sl.mv=0; mexeu=true;\n'
      '   }\n'
      #  duas vagas exatamente no mesmo ponto: a segunda volta para o lugar de
      #  fabrica. Foi o que escondeu quatro vagas na tela dele.
      '   var ch=Math.round((+sl.x||0))+"x"+Math.round((+sl.y||0));\n'
      '   if(vistos[ch]){ sl.x=f[i][1]; sl.y=f[i][2]; sl.mv=0; mexeu=true; }\n'
      '   else vistos[ch]=1;\n'
      #  a posicao escolhida na mao e legitima mesmo que nao seja a da formacao
      #  de fabrica — o saneador so a derruba se ela nao existir no MT_FUNCS,
      #  o que ja foi conferido acima.
      '   if(sl.posFixa && sl.pos!==f[i][0]) { /* legitimo, nao mexe */ }\n'
      '  }\n'
      '  if(mexeu){ try{ MTdb.save(); }catch(e){}\n'
      '   window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '   if(window.console) console.info("ELENCO_1608: as vagas do campo "\n'
      '    +"estavam quebradas no time salvo e foram refeitas."); }\n'
      ' }\n'
      ' window.elSaneia=saneiaSlots;\n'
      '\n'
      ' function desenha(){\n'
      '  var w=document.getElementById("mtwrap"); if(!w) return;\n'
      '  saneiaSlots();\n'
      '  var wrap=document.getElementById("elwrap");\n'
      '  if(!wrap || !wrap.isConnected || !w.contains(wrap)) wrap=esqueleto();\n'
      '  if(!wrap) return;\n'
      '  var esq=document.getElementById("elesq");\n'
      '  var campo=w.querySelector(".mtcampo");\n'
      '  if(campo && campo.parentNode!==esq) esq.appendChild(campo);\n'
      #  o mtRender da casca reescreve o campo inteiro — as linhas voltam aqui
      '  try{ if(campo && !campo.querySelector(".risco"))\n'
      '   campo.insertAdjacentHTML("afterbegin", window.EL_RISCOS); }catch(e){}\n'
      '  var fx=document.getElementById("elfaixa");\n'
      '  if(fx) fx.innerHTML=cabecalho();\n'
      #  ⚠️ os dois seletores (formacao e tecnico) vivem nesta caixa. Reescrever
      #  a caixa com um deles aberto mataria o menu no meio da escolha — por
      #  isso ela so e refeita quando o foco esta fora.
      '  var fm=document.getElementById("elfmt");\n'
      '  if(fm && (document.activeElement===null || !fm.contains(document.activeElement)))\n'
      '   fm.innerHTML=blocoFormacao()+blocoTecnico();\n'
      '\n'
      '  var tit=(MT.slots||[]).filter(function(x){return x&&x.key;}).length;\n'
      '  var nb=(MT.banco||[]).length;\n'
      '  document.getElementById("elban").innerHTML=\n'
      '   \'<div class=elhd>Reservas <em>\'+nb+\' de \'+TETO_BANCO+\'</em></div>\'\n'
      '   +(nb?(\'<div class=elgrid>\'\n'
      '     +(MT.banco||[]).map(function(k){ return montaCard(k,"banco"); }).join("")\n'
      '     +\'</div>\')\n'
      '    :\'<div class=elvazia>Arraste cards para c\\u00e1</div>\')\n'
      '   +(nb<TETO_BANCO\n'
      '     ?\'<div style="padding:10px 0 2px"><button class=elbt onclick="mtAddBanco()">\'\n'
      '      +\'+ adicionar reserva</button></div>\':"");\n'
      '  desenhaFora();\n'
      '  [].slice.call(w.querySelectorAll(".mtsl")).forEach(refazVaga);\n'
      '  arrumaCampo();\n'
      '  ligaArrasta();\n'
      '  var cmp=w.querySelector(".mtcampo"), ed=false;\n'
      '  try{ ed=!!MT_ED; }catch(e){}\n'
      '  if(cmp){\n'
      '   cmp.classList.toggle("movendo", ed);\n'
      '   var av=cmp.querySelector(".elmove");\n'
      '   if(ed && !av){ av=document.createElement("div"); av.className="elmove";\n'
      '    av.textContent="\\u2725 arraste as vagas para mover as posi\\u00e7\\u00f5es";\n'
      '    cmp.appendChild(av); }\n'
      '   else if(!ed && av) av.remove();\n'
      '  }\n'
      '  if(tit>TETO_TIT){ /* nunca deveria acontecer; so nao quebra */ }\n'
      ' }\n'
      '\n'
      ' function naAba(){\n'
      '  var w=document.getElementById("mtwrap");\n'
      '  return !!(w && w.style.display!=="none" && (w.innerHTML||"").length>200);\n'
      ' }\n'
      ' function depois(){\n'
      '  try{\n'
      '   document.body.classList.toggle("naelenco", naAba());\n'
      '   if(!naAba()) return;\n'
      '   desenha();\n'
      '  }catch(e){ if(window.console) console.warn("ELENCO_1608:", e); }\n'
      ' }\n'
      ' window.elRedesenha=depois;\n'
      #  o seletor de card (`mtListaSel`) desenha no fim da pagina. Com o
      #  layout novo isso fica fora da vista: o Luis clica em "+ adicionar
      #  card" la em cima e nada parece acontecer. Aqui a tela rola ate ele.
      ' ["mtAddElenco","mtAddBanco","mtAbreSel","mtListaSel"].forEach(function(nm){\n'
      '  var f=window[nm]; if(typeof f!=="function") return;\n'
      '  window[nm]=function(){\n'
      '   var r=f.apply(this,arguments);\n'
      '   setTimeout(function(){ try{\n'
      '    var el=document.getElementById("mtsaida");\n'
      '    if(el && (el.innerHTML||"").length>80)\n'
      '     el.scrollIntoView({behavior:"smooth", block:"center"});\n'
      '   }catch(e){} }, 60);\n'
      '   return r;\n'
      '  };\n'
      ' });\n'
      ' var _mr2=window.mtRender;\n'
      ' window.mtRender=function(){ var v=_mr2.apply(this,arguments); depois(); return v; };\n'
      ' window.addEventListener("resize", function(){ try{ arrumaCampo(); }catch(e){} });\n'
      ' setInterval(function(){ try{ document.body.classList.toggle("naelenco", naAba()); }catch(e){} }, 1200);\n'
      ' setTimeout(depois, 800);\n'
      '})();\n'
      '</script>\n')

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + js + html[k:]
    return html, 'entrou'


# ============================================================================
def patch_build_do_usuario_1608(html):
    """A ABA "FAZER MINHA BUILD" — o card do jeito que o usuario TEM no jogo.

    ORDEM DO LUIS, 16/08, ditada inteira:
      *"o cara vai colocar a cartinha dele aqui e ela vai vir ZERADA, como
      carta base... ele vai la no MEU CARD, escolhe a funcao, faz a otimizacao
      das barras, e salva. Ai vai ter um botaozinho pra ele salvar dentro do
      modal."*
      *"a aba a gente ja pode renomear pra FAZER MINHA BUILD."*
      *"ele da um nome pro que ele construiu. Se nao der nome, fica o padrao:
      falso nove 1."*
      *"so vai deixar ele salvar se ele tiver a funcao selecionada la em cima."*
      *"ele pode salvar varios pra uma carta so — deixa uns cinco."*
      *"poe um outro botaozinho pra ele copiar o que esta no maximo possivel,
      ai ele vai so tirando o que ele nao tem."*
      *"o tecnico, independente do que ele colocar no modal, quando salvar vai
      com o tecnico zerado — porque na aba do elenco o tecnico altera todos de
      uma vez."*
      *"no cardzinho do elenco poe um botao pra ele escolher qual ele quer
      utilizar pro time dele."*
      *"a lista das funcoes nao tem que alterar quando ele mexe. Essas coisas
      sao fixas."*

    ⛔ NENHUMA CONTA NOVA. Tudo sai de `valsDeLvl`, `cadeia`, `notaDe`, `b1nDe`
    e `nota`, que ja existiam e sao a equacao do motor. Este patch aplica,
    guarda e desfaz — nao inventa numero.
    """
    if 'BUILD_DO_USUARIO_1608' in html:
        return html, 'ja estava'

    #  ---- 1 · o nome da aba, trocado no HTML ja montado -------------------
    #  ⚠️ o rotulo mora DENTRO de uma string JS do patch_modal_1608b, escapado
    #  em ⚙. Procurar "MEU CARD" no texto normal nao acha.
    _antes = html
    html = html.replace('\\u2699 MEU CARD', '\\u2699 FAZER MINHA BUILD')
    html = html.replace('⚙ MEU CARD', '⚙ FAZER MINHA BUILD')
    _rot = 0 if html == _antes else 1

    css = (
      '<style>\n'
      '/* BUILD_DO_USUARIO_1608 */\n'
      '#box .bldbar{display:flex;gap:7px;flex-wrap:wrap;align-items:center;\n'
      ' margin:10px 0 4px;padding:10px 12px;border-radius:10px;\n'
      ' background:#22c58b14;border:1px solid #22c58b3d}\n'
      '#box .bldbar .bldtx{flex:1;min-width:150px;font-size:11px;opacity:.75;line-height:1.35}\n'
      '#box .bldbt{font:inherit;font-size:11.5px;font-weight:800;padding:7px 13px;\n'
      ' border-radius:8px;border:1px solid #2b3a46;background:transparent;color:inherit;\n'
      ' cursor:pointer;white-space:nowrap}\n'
      '#box .bldbt:hover{border-color:#22c58b;color:#22c58b}\n'
      '#box .bldbt.ok{background:#22c58b;border-color:#22c58b;color:#08120c}\n'
      '#box .bldbt.ok:hover{filter:brightness(1.08);color:#08120c}\n'
      '#box .bldbt[disabled]{opacity:.35;cursor:not-allowed}\n'
      '#box .bldlista{display:flex;gap:6px;flex-wrap:wrap;width:100%;margin-top:2px}\n'
      '#box .bldch{font-size:10.5px;font-weight:700;padding:4px 9px;border-radius:20px;\n'
      ' border:1px solid #2b3a46;cursor:pointer;display:flex;gap:6px;align-items:center}\n'
      '#box .bldch:hover{border-color:#22c58b}\n'
      '#box .bldch.on{background:#22c58b;border-color:#22c58b;color:#08120c}\n'
      '#box .bldch u{text-decoration:none;opacity:.6;font-size:10px}\n'
      '#box .bldch.on u{opacity:.8}\n'
      '#box .bldch b{font-weight:800}\n'
      '#box .bldch i{font-style:normal;opacity:.55;padding-left:2px}\n'
      '#box .bldch i:hover{opacity:1;color:#e0533d}\n'
      '/* o seletor de build dentro do card do elenco */\n'
      '.elbsel{width:100%;font:inherit;font-size:9.5px;font-weight:700;padding:3px 4px;\n'
      ' border-radius:6px;border:1px solid var(--line,#2b3a46);background:transparent;\n'
      ' color:inherit;cursor:pointer}\n'
      '</style>\n')

    js = (
      '<script>\n'
      '/* ===== BUILD_DO_USUARIO_1608 ===== */\n'
      '(function(){\n'
      ' if(window.BUILD_DO_USUARIO_1608) return; window.BUILD_DO_USUARIO_1608=1;\n'
      ' var TETO_BUILDS=5;\n'
      ' window.EL_SELO=0;\n'
      '\n'
      ' function base(k){ return String(k).split("|")[0].split("@")[0]; }\n'
      ' function chaveAberta(){\n'
      '  try{ if(typeof CUR!=="undefined" && CUR) return CUR; }catch(e){}\n'
      '  try{ if(window._T6_CHAVE_ATUAL) return window._T6_CHAVE_ATUAL; }catch(e){}\n'
      '  return null;\n'
      ' }\n'
      ' function bd(){ if(typeof MT==="undefined") return null;\n'
      '  MT.builds=MT.builds||{}; MT.buildOn=MT.buildOn||{}; return MT; }\n'
      ' function buildsDe(idb){ var m=bd(); if(!m) return []; return m.builds[idb]||[]; }\n'
      ' function buildAtiva(idb){\n'
      '  var L=buildsDe(idb); if(!L.length) return null;\n'
      '  var m=bd(), i=m.buildOn[idb];\n'
      '  if(i===undefined||i===null||!L[i]) i=0;\n'
      '  return L[i];\n'
      ' }\n'
      ' window.elBuildsDe=buildsDe; window.elBuildAtiva=buildAtiva;\n'
      '\n'
      ' /* ---------- 2 · LER E APLICAR UMA BUILD ---------- */\n'
      #  🔴 o `c.imps` esta furado no banco — a verdade do impeto e a STRING
      #  `c.imp`, e quem a le certo e o `impAdicionado` da casca.
      ' function impetoFabricado(c){\n'
      '  try{ if(typeof impAdicionado==="function") return impAdicionado(c)||null; }catch(e){}\n'
      '  var im=(c.imps||[]).filter(function(x){ return !!x.f; });\n'
      '  return im.length?im[0].n:null;\n'
      ' }\n'
      ' function leDaTela(key){\n'
      '  var c=null; try{ c=_card(key); }catch(e){}\n'
      '  if(!c) return null;\n'
      '  var habs=[]; try{ habs=(c._habs!==undefined?c._habs:(c.HAB||[])).slice(); }catch(e){}\n'
      '  var lvl={}; try{ lvl=_lvlDe(c); }catch(e){}\n'
      '  return {func:c.tipo, lvl:lvl, habs:habs, imp:impetoFabricado(c),\n'
      '          grau:(window._GRAU_COND||1)};\n'
      ' }\n'
      '\n'
      ' /* A NOTA DE UMA BUILD.\n'
      '    Mesma receita do `notaCfg` da casca (guarda, mexe, le, devolve), mais\n'
      '    a diferenca das habilidades pela mesma conta do `_trocaHabs`. Nada\n'
      '    aqui e formula nova: `valsDeLvl`, `cadeia`, `notaDe`, `b1nDe` e `nota`\n'
      '    sao os do motor. */\n'
      #  ⚠️ A REFERENCIA DA DIFERENCA DAS HABILIDADES.
      #  O `valsDeLvl` corrige nivel de barra e tecnico, mas NAO habilidade: o
      #  `_ori.v` de onde ele parte JA TRAZ o efeito das habilidades que a carta
      #  tinha quando o `_ori` nasceu. Entao a diferenca tem de ser medida
      #  contra ELAS. Guardo por chave na primeira vez que vejo a carta, antes
      #  de encostar em qualquer campo.
      ' var HREF={};\n'
      ' function habsDoOri(c,key){\n'
      '  if(HREF[key]===undefined){\n'
      '   try{ HREF[key]=(c._habs!==undefined?c._habs:(c.HAB||[])).slice(); }\n'
      '   catch(e){ HREF[key]=[]; }\n'
      '  }\n'
      '  return HREF[key];\n'
      ' }\n'
      #  o ímpeto que o motor escolheu sai; o DE FÁBRICA fica, porque esse vem
      #  na carta e o usuário tem. É o mesmo que `editImp(key,"(nenhum)")` faz
      #  no modal — conferido: os dois deixam `c.imp` na parte "de fabrica:".
      ' function impSoDeFabrica(t){\n'
      '  t=String(t==null?"":t);\n'
      '  var i=t.indexOf("o motor p");\n'
      '  if(i>0) t=t.slice(0,i).replace(/\\s*[\\u00b7+]\\s*$/,"");\n'
      '  t=t.replace(/\\s*[\\u00b7+]\\s*[^\\u00b7]*\\u2692\\s*$/,"");\n'
      '  return t;\n'
      ' }\n'
      ' function pctDoMolde(A){\n'
      '  var n=0,d=0,i,w; A=A||[];\n'
      '  for(i=0;i<A.length;i++){ w=A[i][1]; if(!w) continue;\n'
      '   n+=w*A[i][3]; d+=w*A[i][2]; }\n'
      '  return d?100*n/d:0;\n'
      ' }\n'
      ' function notaDaBuild(key, b, comTecnicoDoTime){\n'
      '  var c=null; try{ c=_card(key); }catch(e){}\n'
      '  if(!c) return 0;\n'
      '  var g={ b1:c.b1, b1n:c.b1n, imp:c.imp,\n'
      '          habs:c._habs, tec:c._tec, tecNome:c._tecNome,\n'
      '          sis:(c.sis||[]).slice(),\n'
      '          arows:c.arows.map(function(r){ return r.slice(); }) };\n'
      '  var v=0;\n'
      '  try{\n'
      #  os quatro insumos, exatamente como o modal os deixa
      '   c._habs=(b.habs||[]).slice();\n'
      '   if(comTecnicoDoTime){\n'
      '    try{ c._tec=mtTecBs()||[]; }catch(e){ c._tec=[]; }\n'
      '    try{ c._tecNome=mtTecNome()||null; }catch(e){ c._tecNome=null; }\n'
      '   } else { c._tec=[]; c._tecNome=null; }\n'
      #  o ímpeto: sai o que O MOTOR pôs, entra o que O USUÁRIO escolheu.
      '   c.imp=impSoDeFabrica(g.imp);\n'
      '   if(b.imp) c.imp = c.imp + " \\u00b7 o motor pos: " + b.imp;\n'
      '   try{ delete c._cp; delete c._n; }catch(e){}\n'
      '   var vals=valsDeLvl(c, b.lvl||{});\n'
      '   c.arows.forEach(function(r){ r[3]=vals[r[0]]; r[4]=r[3]-r[2]; r[5]=r[3]; });\n'
      '   c.sis=vals.slice();\n'
      '   c.b1=notaDe(vals,c.arows);\n'
      '   c.b1n=pctDoMolde(c.arows);\n'
      '   delete c._n;\n'
      '   v=nota(c);\n'
      '  }catch(e){ v=0; }\n'
      '  c.b1=g.b1; c.b1n=g.b1n; c.imp=g.imp; c.arows=g.arows; c.sis=g.sis;\n'
      '  if(g.habs===undefined) delete c._habs; else c._habs=g.habs;\n'
      '  if(g.tec===undefined) delete c._tec; else c._tec=g.tec;\n'
      '  if(g.tecNome===undefined) delete c._tecNome; else c._tecNome=g.tecNome;\n'
      '  try{ delete c._cp; delete c._n; }catch(e){}\n'
      '  return v;\n'
      ' }\n'
      ' window.elNotaDaBuild=notaDaBuild;\n'
      #  ⛔ ESTE E O ENDERECO UNICO DA PONTUACAO. Tela de inicio, modal, card do
      #  elenco, campo, ranking — todos leem daqui. Nao escreva outra.
      ' window.EF_PONTO=function(key, opts){\n'
      '  opts=opts||{};\n'
      '  var b=opts.build;\n'
      '  if(!b){ try{ b=buildAtiva(base(key)); }catch(e){} }\n'
      '  if(!b) b=buildBase(key);\n'
      '  var comTec=(opts.comTecnicoDoTime!==false);\n'
      '  return notaDaBuild(key, b, comTec);\n'
      ' };\n'
      #  e o porque, para conferir qualquer card no Console sem adivinhar:
      #      EF_PORQUE("370537029180759|Falso nove")
      ' window.EF_PORQUE=function(key){\n'
      '  var c=null; try{ c=_card(key); }catch(e){}\n'
      '  if(!c){ console.warn("nao achei o card", key); return null; }\n'
      '  var idb=base(key), b=buildAtiva(idb), qual=b?("build \\u201c"+b.nome+"\\u201d"):"carta base";\n'
      '  if(!b) b=buildBase(key);\n'
      '  var r={ carta:c.nome, funcao:String(key).split("|")[1], vem_de:qual,\n'
      '          pontos_nas_barras:(function(){ var t=0,k; for(k in (b.lvl||{})) t+=(+b.lvl[k]||0); return t; })(),\n'
      '          habilidades_adicionadas:(b.habs||[]).length,\n'
      '          impeto_escolhido:(b.imp||"\\u2014"),\n'
      '          tecnico_do_time:(function(){ try{ return mtTecNome()||"\\u2014"; }catch(e){ return "?"; } })(),\n'
      '          SEM_o_tecnico:+notaDaBuild(key,b,false).toFixed(2),\n'
      '          COM_o_tecnico:+notaDaBuild(key,b,true).toFixed(2),\n'
      '          maximo_do_motor:+(function(){ try{ delete c._n; return nota(c); }catch(e){ return 0; } })().toFixed(2) };\n'
      '  console.table(r); return r;\n'
      ' };\n'
      '\n'
      ' /* A CARTA BASE: nenhum ponto gasto, nenhuma habilidade adicionada,\n'
      '    nenhum tecnico, so o impeto nativo. */\n'
      ' function buildBase(key){\n'
      '  var z={}; try{ MBK.forEach(function(b){ z[b]=0; }); }catch(e){}\n'
      '  var c=null; try{ c=_card(key); }catch(e){}\n'
      '  return {func:c?c.tipo:null, lvl:z, habs:[], imp:null, grau:1, base:1};\n'
      ' }\n'
      ' window.elBuildBase=buildBase;\n'
      '\n'
      ' function aplicaNaTela(key, b){\n'
      '  var c=null; try{ c=_card(key); }catch(e){}  if(!c) return;\n'
      '  try{ _marca(key); }catch(e){}\n'
      '  c._habs=[]; c._tec=[]; c._tecNome=null;\n'
      '  try{ delete c._cp; delete c._n; }catch(e){}\n'
      '  try{ editImp(key, (b.imp||"(nenhum)")); }catch(e){}\n'
      '  try{ c=_card(key)||c; }catch(e){}\n'
      '  var z={}; try{ MBK.forEach(function(x){ z[x]=0; }); }catch(e){}\n'
      '  try{ _grava(c, b.lvl||z); }catch(e){}\n'
      '  if(b.habs && b.habs.length){ try{ _trocaHabs(key, b.habs.slice()); }catch(e){} }\n'
      '  if(!window.BLD_SEM_LACO){ try{ reabrir(key); }catch(e){} }\n'
      '  else { try{ traducaoViva(); render(); }catch(e){} }\n'
      ' }\n'
      '\n'
      ' /* ---------- 3 · O MODAL ABRE NO MAXIMO POSSIVEL ----------\n'
      '    Ordem do Luis: *"quando ele clicar, ele vai abrir o modal que abre pra\n'
      '    todo mundo, que e o que esta no maximo possivel."* E a aba FAZER MINHA\n'
      '    BUILD tem de comecar na CARTA BASE, nao na build do motor — que era o\n'
      '    defeito que ele viu no Messi (112,03 e 62/62 nas duas abas). */\n'
      ' (function(){\n'
      '  var _ab=window.abrir; if(typeof _ab!=="function") return;\n'
      '  window.abrir=function(k){\n'
      '   try{\n'
      '    var s=String(k||"");\n'
      '    if(s && s.split("|")[0]!==String(window._CARTA_ABERTA||"")){\n'
      '     window._CARTA_ABERTA=s.split("|")[0];\n'
      '     window.ENC_MODO="motor";\n'
      '     window._BLD_ZERADA=null; window._BLD_FOTO=null;\n'
      '    }\n'
      '   }catch(e){}\n'
      '   return _ab.apply(this,arguments);\n'
      '  };\n'
      ' })();\n'
      ' (function(){\n'
      '  var _fc=window.fechar; if(typeof _fc!=="function") return;\n'
      '  window.fechar=function(){\n'
      '   try{ if(window.BLD_SUJO && !confirm("Voc\\u00ea mexeu na carta e n\\u00e3o "\n'
      '    +"salvou.\\n\\nFechar assim descarta o que voc\\u00ea montou.")) return; }catch(e){}\n'
      '   window.BLD_SUJO=0; window._CARTA_ABERTA=null; window._BLD_ZERADA=null; window._BLD_FOTO=null;\n'
      '   return _fc.apply(this,arguments);\n'
      '  };\n'
      ' })();\n'
      '\n'
      ' /* ---------- 4 · A MELHOR FUNCAO JA ESCOLHIDA ----------\n'
      '    *"o modal ja vai aparecer por padrao com a melhor funcao escolhida."* */\n'
      ' function melhorFuncao(idb){\n'
      '  var melhor=null;\n'
      '  try{\n'
      '   D.forEach(function(x){\n'
      '    if(!x || x.id==="MOLDE") return;\n'
      '    if(String(x.id).split("@")[0]!==idb) return;\n'
      '    var n=nota(x);\n'
      '    if(!melhor||n>melhor.n) melhor={n:n, tipo:x.tipo, id:x.id};\n'
      '   });\n'
      '  }catch(e){}\n'
      '  return melhor;\n'
      ' }\n'
      ' window.elMelhorFuncao=melhorFuncao;\n'
      ' window.elAbreNaMelhor=function(k){\n'
      '  var m=melhorFuncao(base(k));\n'
      '  try{ abrir(m?(m.id+"|"+m.tipo):k); }catch(e){}\n'
      ' };\n'
      ' window.elAbreCard=function(k){\n'
      '  var idb=base(k), b=buildAtiva(idb);\n'
      '  if(b && b.func){ try{ abrir(String(k).split("|")[0]+"|"+b.func); }catch(e){}\n'
      '                   return; }\n'
      '  window.elAbreNaMelhor(k);\n'
      ' };\n'
      '\n'
      ' /* ---------- 5 · A LISTA DE FUNCOES PARA DE SE MEXER ----------\n'
      '    Ordem do Luis, 16/08: *"a funcao de falso nove deveria estar verde\n'
      '    maior e mais escura, e ficou menor. Cada vez que a gente mexe ela\n'
      '    altera. Ela nao tem que alterar nao, essas coisas aqui sao fixas."*\n'
      '\n'
      '    MEDIDO, e a causa nao e a ordem nem o numero (esses ja estavam\n'
      '    congelados): e o ESTILO. O gerador desenha cada faixa assim —\n'
      '        irm.sort(function(a,b){ return b._n-a._n; });\n'
      '        var p=1-(ix/(irm.length-1)), k=cores(p);\n'
      '    ou seja, a cor, o padding e o tamanho da letra saem da POSICAO NA\n'
      '    LISTA. O `_n` da funcao aberta e recalculado quando o Luis mexe nas\n'
      '    barras e as outras ficam com o valor velho: a ordem vira, o Falso nove\n'
      '    cai para 2o e ganha a roupa do 2o — e o congelador de ordem devolve\n'
      '    ele ao topo ja vestido errado.\n'
      '    Aqui a roupa e guardada por NOME DE FUNCAO na primeira abertura da\n'
      '    carta e reposta em toda renderizacao. ⛔ Nenhum numero e tocado. */\n'
      ' var _roupa={};\n'
      ' function congelaEstiloDaLista(){\n'
      '  var bx=document.getElementById("box"); if(!bx) return;\n'
      '  var k=chaveAberta(); if(!k) return;\n'
      '  var idb=base(k);\n'
      '  var bts=[].slice.call(bx.querySelectorAll(".cbfn"));\n'
      '  if(bts.length<2) return;\n'
      '  function nomeDe(e){ var q=e.querySelector("i");\n'
      '   return q?String(q.textContent||"").trim():""; }\n'
      '  if(!_roupa[idb]){\n'
      '   var m={};\n'
      '   bts.forEach(function(e){\n'
      '    var nm=nomeDe(e); if(!nm) return;\n'
      '    var i=e.querySelector("i"), b=e.querySelector("b");\n'
      '    m[nm]={bg:e.style.background, bd:e.style.borderColor, tx:e.style.color,\n'
      '           pad:e.style.padding,\n'
      '           fi:i?i.style.fontSize:"", fb:b?b.style.fontSize:""};\n'
      '   });\n'
      '   _roupa[idb]=m;\n'
      '   return;\n'
      '  }\n'
      '  var m2=_roupa[idb];\n'
      '  bts.forEach(function(e){\n'
      '   var nm=nomeDe(e), r=m2[nm]; if(!r) return;\n'
      '   var aberta=e.classList.contains("cbfnq");\n'
      '   e.style.background=r.bg;\n'
      '   e.style.borderColor=aberta?"#ffffff":r.bd;\n'
      '   e.style.color=r.tx;\n'
      '   e.style.padding=r.pad;\n'
      '   var i=e.querySelector("i"), b=e.querySelector("b");\n'
      '   if(i&&r.fi) i.style.fontSize=r.fi;\n'
      '   if(b&&r.fb) b.style.fontSize=r.fb;\n'
      '  });\n'
      ' }\n'
      '\n'
      ' /* ---------- 6 · A BARRA DE SALVAR ---------- */\n'
      ' function ehFazerMinha(){\n'
      '  try{ return window.ENC_MODO==="livre"; }catch(e){ return false; }\n'
      ' }\n'
      ' function funcaoSelecionada(){\n'
      '  var bx=document.getElementById("box"); if(!bx) return null;\n'
      '  var b=bx.querySelector(".cbfn.cbfnq"); if(!b) return null;\n'
      '  var i=b.querySelector("i");\n'
      '  return i?String(i.textContent||"").trim():null;\n'
      ' }\n'
      ' function nomePadrao(idb, func){\n'
      '  var L=buildsDe(idb), n=1, i;\n'
      '  for(i=0;i<L.length;i++) if(L[i].func===func) n++;\n'
      '  return func+" "+n;\n'
      ' }\n'
      '\n'
      ' function salvaBuildDireta(k, func, nomeForcado){\n'
      '  if(!k) return;\n'
      '  if(!func){ try{ var cf=_card(k); func=cf&&cf.tipo; }catch(e){} }\n'
      '  if(!func){ alert("Escolha a fun\\u00e7\\u00e3o l\\u00e1 em cima antes de salvar.\\n\\n"\n'
      '   +"A build guarda a fun\\u00e7\\u00e3o junto \\u2014 sem ela n\\u00e3o d\\u00e1 "\n'
      '   +"pra saber em que posi\\u00e7\\u00e3o ele joga."); return; }\n'
      '  var m=bd(); if(!m) return;\n'
      '  var idb=base(k), L=buildsDe(idb);\n'
      '  if(L.length>=TETO_BUILDS){\n'
      '   alert("Voc\\u00ea j\\u00e1 tem "+TETO_BUILDS+" builds guardadas deste card.\\n\\n"\n'
      '    +"Apague uma antes de salvar outra \\u2014 o x fica na etiqueta dela, "\n'
      '    +"aqui embaixo."); return;\n'
      '  }\n'
      '  var b=leDaTela(k); if(!b) return;\n'
      '  b.func=func;\n'
      '  var sug=nomePadrao(idb, func);\n'
      '  if(nomeForcado===undefined && typeof window.t6PedeNomeBuild==="function"){\n'
      '   window.t6PedeNomeBuild(sug,function(v){ if(v!==null) salvaBuildDireta(k,func,v); }); return;\n'
      '  }\n'
      '  var nome=(nomeForcado!==undefined)?nomeForcado:prompt("Nome desta build:", sug);\n'
      '  if(nome===null) return;\n'
      '  nome=String(nome).replace(/\\s+/g," ").trim() || sug;\n'
      '  /*  ⛔ O TECNICO SAI ZERADO. Ordem do Luis: *"o tecnico, independente do\n'
      '      que eu colocar aqui no modal, quando salvar ele vai com o tecnico\n'
      '      zerado, porque na aba do elenco a gente coloca o tecnico e ele\n'
      '      altera todos de uma vez."* */\n'
      '  b.nome=nome; b.tec=null;\n'
      '  b.n=notaDaBuild(String(k).split("|")[0]+"|"+func, b, false);\n'
      '  m.builds[idb]=L.concat([b]);\n'
      '  m.buildOn[idb]=m.builds[idb].length-1;\n'
      '  window.BLD_SUJO=0; window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '  try{ MTdb.save(); }catch(e){}\n'
      '  try{ if(typeof mtRender==="function") mtRender(); }catch(e){}\n'
      '  barra();\n'
      '  var msg="Build \\u201c"+nome+"\\u201d salva: "+b.n.toFixed(2).replace(".",",")\n'
      '   +" em "+func+". Ela j\\u00e1 vale no seu elenco.";\n'
      '  if(typeof window.t6Notifica==="function") window.t6Notifica(msg); else alert(msg);\n'
      ' }\n'
      ' window.bldSalvaDireto=function(k,func){ return salvaBuildDireta(k,func); };\n'
      ' window.bldSalva=function(){\n'
      '  var k=chaveAberta(); if(!k) return;\n'
      '  var func=funcaoSelecionada();\n'
      '  return salvaBuildDireta(k,func);\n'
      ' };\n'
      ' window.bldUsa=function(idb, i){\n'
      '  var m=bd(); if(!m) return;\n'
      '  m.buildOn[idb]=+i; window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '  try{ MTdb.save(); }catch(e){}\n'
      '  var L=buildsDe(idb);\n'
      '  if(L[+i]){ var k=chaveAberta();\n'
      '   if(k && base(k)===idb){\n'
      '    window.ENC_MODO="livre";\n'
      '    aplicaNaTela(String(k).split("|")[0]+"|"+L[+i].func, L[+i]);\n'
      '   } }\n'
      '  try{ if(typeof mtRender==="function") mtRender(); }catch(e){}\n'
      '  barra();\n'
      ' };\n'
      ' window.bldApaga=function(idb, i){\n'
      '  var m=bd(); if(!m) return;\n'
      '  var L=buildsDe(idb); if(!L[i]) return;\n'
      '  if(!confirm("Apagar a build \\u201c"+L[i].nome+"\\u201d?")) return;\n'
      '  L.splice(i,1); m.builds[idb]=L;\n'
      '  if(m.buildOn[idb]>=L.length) m.buildOn[idb]=L.length?L.length-1:0;\n'
      '  window.EL_SELO=(window.EL_SELO||0)+1;\n'
      '  try{ MTdb.save(); }catch(e){}\n'
      '  try{ if(typeof mtRender==="function") mtRender(); }catch(e){}\n'
      '  barra();\n'
      ' };\n'
      ' /* *"poe um outro botaozinho pra ele copiar o que esta no maximo possivel,\n'
      '    ai ele vai so tirando o que ele nao tem."* */\n'
      #  ---------- COPIAR DO MAXIMO POSSIVEL ----------
      #  *"poe um outro botaozinho pra ele copiar o que esta no maximo possivel,
      #  ai ele vai so tirando o que ele nao tem."*
      #  ⚠️ 16/08 — A 1a VERSAO NAO FUNCIONAVA, e o Luis pegou. Eu montava a
      #  build na mao (lvl do `_ori`, habilidades, impeto) e mandava aplicar —
      #  so que o `editImp` reabre a ficha por dentro, e a reabertura jogava
      #  fora as barras que eu tinha acabado de gravar.
      #  Agora usa o `restaurarMotor` da propria casca, que E exatamente isto:
      #  devolver a carta a build que o motor escolheu, com tecnico, impeto e
      #  habilidades juntos. Uma chamada, nada montado na mao.
      ' window.bldCopiaDoMaximo=function(){\n'
      '  var k=chaveAberta(); if(!k) return;\n'
      '  if(typeof restaurarMotor!=="function"){\n'
      '   alert("N\\u00e3o consegui ler a build do m\\u00e1ximo poss\\u00edvel desta carta.");\n'
      '   return;\n'
      '  }\n'
      '  window.BLD_SEM_LACO=1;\n'
      '  try{ _marca(k); }catch(e){}\n'
      '  try{ restaurarMotor(k); }catch(e){}\n'
      '  window.ENC_MODO="livre";\n'
      '  window.BLD_SEM_LACO=0;\n'
      '  try{ reabrir(k); }catch(e){}\n'
      '  window.BLD_SUJO=1;\n'
      '  setTimeout(barra, 60);\n'
      ' };\n'
      '\n'
      #  ---------- TROCAR A FUNCAO NAO MEXE NA FAZER MINHA BUILD ----------
      #  ORDEM DO LUIS, 16/08, e ele repetiu ate eu entender direito:
      #    *"quando voce troca a funcao o MAXIMO POSSIVEL atualiza — ela tem
      #    mesmo. Eu estou dizendo que ela atualiza o FAZER MINHA. Nao e pra
      #    atualizar. Essa aba e manual, tudo que entra aqui e manual."*
      #
      #  A CAUSA: cada funcao e uma LINHA DIFERENTE do banco, e cada linha vem
      #  com a build do motor dentro. Trocar de funcao e carregar outra linha —
      #  e ela chega preenchida. Aqui o que o usuario montou e guardado antes da
      #  troca e reposto na linha nova. So o molde muda; os insumos ficam.
      ' (function(){\n'
      '  var _rab=window.reabrir; if(typeof _rab!=="function") return;\n'
      '  window.reabrir=function(k){\n'
      '   var manter=null;\n'
      '   try{\n'
      '    if(ehFazerMinha() && !window.BLD_SEM_LACO){\n'
      '     var atual=chaveAberta();\n'
      '     if(atual && k){\n'
      '      var a=String(atual).split("|"), b=String(k).split("|");\n'
      '      if(a[0]===b[0] && a[1]!==b[1]) manter=leDaTela(atual);\n'
      '     }\n'
      '    }\n'
      '   }catch(e){}\n'
      '   var r=_rab.apply(this,arguments);\n'
      '   if(manter){\n'
      '    setTimeout(function(){\n'
      '     try{\n'
      '      window.BLD_SEM_LACO=1;\n'
      '      manter.func=String(k).split("|")[1];\n'
      '      aplicaNaTela(k, manter);\n'
      '     }catch(e){}\n'
      '     window.BLD_SEM_LACO=0;\n'
      '    }, 0);\n'
      '   }\n'
      '   return r;\n'
      '  };\n'
      ' })();\n'
      '\n'
      ' function barra(){\n'
      '  var bx=document.getElementById("box"); if(!bx) return;\n'
      '  var velha=bx.querySelector(".bldbar");\n'
      '  if(!ehFazerMinha()){ if(velha) velha.remove(); return; }\n'
      '  var k=chaveAberta(); if(!k){ if(velha) velha.remove(); return; }\n'
      '  var idb=base(k), L=buildsDe(idb), m=bd();\n'
      '  var func=funcaoSelecionada();\n'
      '  var ativa=(m&&m.buildOn[idb]!==undefined)?m.buildOn[idb]:0;\n'
      '  var h=\'<button class="bldbt ok" onclick="bldSalva()"\'\n'
      '   +(func?"":" disabled")+\'>\\u2714 SALVAR MINHA BUILD</button>\'\n'
      '   +\'<button class="bldbt" onclick="bldCopiaDoMaximo()" \'\n'
      '   +\'title="traz tudo do M\\u00c1XIMO POSS\\u00cdVEL pra c\\u00e1; daqui voc\\u00ea \'\n'
      '   +\'vai tirando o que n\\u00e3o tem">\\u29c9 copiar do m\\u00e1ximo poss\\u00edvel</button>\'\n'
      '   +\'<div class=bldtx>\'\n'
      '   +(func?("vai salvar como <b>"+func+"</b> \\u00b7 "+L.length+" de "+TETO_BUILDS+" builds")\n'
      '        :"<b>escolha a fun\\u00e7\\u00e3o l\\u00e1 em cima</b> \\u2014 sem ela n\\u00e3o d\\u00e1 pra salvar")\n'
      '   +\'</div>\';\n'
      '  if(L.length){\n'
      '   h+=\'<div class=bldlista>\';\n'
      '   for(var i=0;i<L.length;i++){\n'
      '    h+=\'<span class="bldch\'+(i===ativa?" on":"")+\'" \'\n'
      '     +\'onclick="bldUsa(\\\'\'+idb+\'\\\',\'+i+\')" \'\n'
      '     +\'title="usar esta build no seu elenco">\'\n'
      '     +\'<b>\'+String(L[i].nome||("build "+(i+1))).replace(/</g,"&lt;")+\'</b>\'\n'
      '     +\'<u>\'+(+L[i].n||0).toFixed(2).replace(".",",")+\'</u>\'\n'
      '     +\'<i onclick="event.stopPropagation();bldApaga(\\\'\'+idb+\'\\\',\'+i+\')" \'\n'
      '     +\'title="apagar esta build">\\u00d7</i></span>\';\n'
      '   }\n'
      '   h+="</div>";\n'
      '  }\n'
      '  if(!velha){\n'
      '   velha=document.createElement("div"); velha.className="bldbar";\n'
      '   var alvo=null, hd=bx.querySelectorAll(".bhd"), j;\n'
      '   for(j=0;j<hd.length;j++) if(/Distribui/i.test(hd[j].textContent)) alvo=hd[j];\n'
      '   if(alvo && alvo.parentNode) alvo.parentNode.insertBefore(velha, alvo);\n'
      '   else bx.appendChild(velha);\n'
      '  }\n'
      '  if(velha.innerHTML!==h) velha.innerHTML=h;\n'
      ' }\n'
      '\n'
      ' /* qualquer mexida na aba FAZER MINHA BUILD marca a carta como suja */\n'
      ' document.addEventListener("click", function(ev){\n'
      '  try{\n'
      '   if(!ehFazerMinha()) return;\n'
      '   var t=ev.target; if(!t||!t.closest) return;\n'
      '   if(t.closest(".bldbar")) return;\n'
      '   if(t.closest(\'[onclick*="editBar"],[onclick*="setBar"],[onclick*="remHab"],\'\n'
      '    +\'.btotbar\')) window.BLD_SUJO=1;\n'
      '  }catch(e){}\n'
      ' }, true);\n'
      ' document.addEventListener("change", function(ev){\n'
      '  try{\n'
      '   if(!ehFazerMinha()) return;\n'
      '   var t=ev.target; if(!t||!t.matches) return;\n'
      '   if(t.matches(\'select[onchange*="addHab"],select[onchange*="trocaTec"],\'\n'
      '    +\'select[onchange*="editImp"]\')) window.BLD_SUJO=1;\n'
      '  }catch(e){}\n'
      ' }, true);\n'
      '\n'
      ' /* ---------- 7 · A PONTUACAO DO CARD NO ELENCO ----------\n'
      '    *"descarta a pontuacao da posicao original. Ele vai aparecer com a\n'
      '    pontuacao que esta na build dele."* Sem build salva, vale a CARTA\n'
      '    BASE — *"ele vai vir zerado, como carta base."* */\n'
      ' var _cache={};\n'
      #  ⚠️ 17/08 — ORDEM DO LUIS: *"a posicao do cara nao condiz com a posicao do
      #  campo. Por mais que a dele seja pra CA, se ele for colocado numa posicao
      #  de MLG ele tem que ser MLG. Tem que buscar, de acordo com os insumos que
      #  estao na dele, como ficaria pra MLG."*
      #  Por isso a funcao entra como PARAMETRO: no campo quem manda e a vaga,
      #  nas listas quem manda e a build. Os insumos sao os mesmos nos dois — so
      #  o molde contra o qual eles sao medidos e que muda.
      ' window.elPontuacao=function(k, funcDaVaga){\n'
      '  var c=null; try{ c=mtCard(k); }catch(e){}\n'
      '  if(!c) return null;\n'
      '  var idb=base(k), b=buildAtiva(idb), nomeB=null;\n'
      '  if(!b){ b=buildBase(k); }\n'
      '  else nomeB=b.nome;\n'
      '  var func=funcDaVaga||b.func||c.tipo;\n'
      '  var chave=idb+"|"+func+"|"+(nomeB||"BASE")+"|"+(window.EL_SELO||0)\n'
      '   +"|"+((typeof MT!=="undefined")?MT.tec:"");\n'
      '  if(_cache[chave]!==undefined) return {n:_cache[chave], func:func, nome:nomeB};\n'
      '  var n=notaDaBuild(String(k).split("|")[0]+"|"+func, b, true);\n'
      '  _cache[chave]=n;\n'
      '  return {n:n, func:func, nome:nomeB};\n'
      ' };\n'
      '\n'
      ' /* o seletor de build dentro do cardzinho do elenco */\n'
      ' window.elBotoesExtra=function(k, de){\n'
      '  var idb=base(k), L=buildsDe(idb);\n'
      '  if(!L.length) return "";\n'
      '  var m=bd(), ativa=(m&&m.buildOn[idb]!==undefined)?m.buildOn[idb]:0;\n'
      '  var h=\'<select class=elbsel onclick="event.stopPropagation()" \'\n'
      '   +\'onchange="event.stopPropagation();bldUsa(\\\'\'+idb+\'\\\',this.value)" \'\n'
      '   +\'title="qual build est\\u00e1 valendo">\';\n'
      '  for(var i=0;i<L.length;i++)\n'
      '   h+=\'<option value="\'+i+\'"\'+(i===ativa?" selected":"")+\'>\'\n'
      '    +String(L[i].nome||("build "+(i+1))).replace(/</g,"&lt;")+\'</option>\';\n'
      '  return h+"</select>";\n'
      ' };\n'
      '\n'
      ' /* ---------- 8 · o laco ---------- */\n'
      ' function passo(){\n'
      '  try{\n'
      '   var bx=document.getElementById("box");\n'
      '   var ov=document.getElementById("ov");\n'
      '   if(!bx || !ov || ov.style.display==="none") return;\n'
      '   congelaEstiloDaLista();\n'
      '   barra();\n'
      '  }catch(e){ if(window.console) console.warn("BUILD_1608:", e); }\n'
      ' }\n'
      ' setInterval(passo, 320);\n'
      ' setTimeout(passo, 900);\n'
      '})();\n'
      '</script>\n')

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + css + js + html[k:]
    return html, ('entrou' if _rot else 'entrou (o rotulo da aba NAO foi trocado)')


# ============================================================================
def patch_seletor_de_card_1608(html):
    """A JANELA DE ESCOLHER CARD — enxuta, e sem a trava errada.

    ORDEM DO LUIS, 16/08:
      *"adicionar ao elenco tem um monte de informacao irrelevante, cara. Aqui
      a gente so precisa do nome da carta, da posicao, da foto dela, da funcao
      dela e do estilo de jogo. Precisa de mais nada."*
      *"estou tentando selecionar uma carta do Messi e esta dando isso ai —
      voce entendeu uma regra errada. Nao pode ter no time titular nem no banco
      de reservas dois cards do mesmo jogador. Agora fora do banco eu posso ter
      quantas eu quiser."*
      *"quando ele selecionar o jogador, ele ja tem que aparecer o primeiro de
      todos aqui no fora do banco."*
    """
    if 'SELETOR_1608' in html:
        return html, 'ja estava'

    js = (
      '<script>\n'
      '/* ===== SELETOR_1608 ===== */\n'
      '(function(){\n'
      ' if(window.SELETOR_1608) return; window.SELETOR_1608=1;\n'
      '\n'
      #  ---------- 1 · A LISTA ENXUTA ----------
      #  A casca monta cada linha com tier, votos, "migrado", nota e percentual.
      #  Nesta janela o Luis nao esta comparando carta — esta PROCURANDO a carta
      #  que ele tem. Numero ali nao ajuda a achar, atrapalha.
      #  ⚠️ Nao reescrevo o `mtListaSel` (ele monta a janela inteira e muda a
      #  cada versao). Depois que ele desenha, a linha e reescrita — assim, se a
      #  casca mudar, o pior que acontece e a linha voltar ao formato antigo.
      ' function esc(t){ return String(t==null?"":t)\n'
      '  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")\n'
      '  .replace(/"/g,"&quot;"); }\n'
      ' function enxuga(){\n'
      '  var bx=document.getElementById("box"); if(!bx) return;\n'
      '  var lista=bx.querySelector("#mtlist"); if(!lista) return;\n'
      '  var linhas=[].slice.call(lista.querySelectorAll(".mtli")), i;\n'
      '  for(i=0;i<linhas.length;i++){\n'
      '   var li=linhas[i];\n'
      '   if(li.getAttribute("data-enx")) continue;\n'
      '   var oc=String(li.getAttribute("onclick")||"");\n'
      '   var m=oc.match(/[\\x27"]([^\\x27"]+\\|[^\\x27"]+)[\\x27"]/);\n'
      '   if(!m){ li.setAttribute("data-enx","1"); continue; }\n'
      '   var c=null; try{ c=_card(m[1]); }catch(e){}\n'
      '   if(!c){ li.setAttribute("data-enx","1"); continue; }\n'
      '   var idb=String(c.id).split("@")[0];\n'
      '   var est=(c.modelo&&c.modelo!==c.tipo)?c.modelo:"";\n'
      '   li.innerHTML=\n'
      '    \'<img src="https://efimg.com/efootballhub22/images/player_cards/\'\n'
      '    +idb+\'_l.png" onerror="this.style.visibility=&quot;hidden&quot;">\'\n'
      '    +\'<div style="flex:1;min-width:0">\'\n'
      '     +\'<b>\'+esc(c.nome)+\'</b>\'\n'
      '     +\'<div class=mini><b style="opacity:.75;letter-spacing:.5px">\'\n'
      '      +esc(c.np||c.pos||"")+\'</b> \\u00b7 \'+esc(c.tipo)+\'</div>\'\n'
      '     +(est?(\'<div class=mini style="opacity:.55">\'+esc(est)+\'</div>\'):"")\n'
      '    +\'</div>\';\n'
      '   li.setAttribute("data-enx","1");\n'
      '  }\n'
      ' }\n'
      '\n'
      #  ---------- 2 · A TRAVA DO REPETIDO ----------
      #  🔴 A regra que eu tinha entendido errado, nas palavras dele:
      #     os 23 (titulares + reservas) .. UM card por jogador
      #     fora do banco ................. QUANTOS ELE QUISER
      #  A casca barra nos tres, porque o `mtPoe` olha `MT.elenco` junto. Aqui a
      #  janela de FORA DO BANCO passa por cima: poe direto, sem consultar o
      #  `mtPoe`. As outras duas (vaga e reserva) continuam com a trava da casca,
      #  que ali esta certa.
      ' (function(){\n'
      '  var _poe=window.mtPoe; if(typeof _poe!=="function") return;\n'
      '  window.mtPoe=function(k){\n'
      '   var paraFora=false;\n'
      '   try{ paraFora = !!(MT_SEL && MT_SEL.elenco && MT_SEL.slot===undefined); }catch(e){}\n'
      '   if(paraFora && k){\n'
      '    MT.elenco=MT.elenco||[];\n'
      #  entra em PRIMEIRO — *"ele tem que aparecer o primeiro de todos"*
      '    if(MT.elenco.indexOf(k)<0) MT.elenco.unshift(k);\n'
      '    try{ MTdb.save(); }catch(e){}\n'
      '    try{ fechar(); }catch(e){}\n'
      '    try{ mtRender(); }catch(e){}\n'
      '    return;\n'
      '   }\n'
      '   return _poe.apply(this,arguments);\n'
      '  };\n'
      ' })();\n'
      '\n'
      #  ---------- 3 · A VAGA ESCALA DE DENTRO DO ELENCO ----------
      #  ORDEM DO LUIS, 17/08: *"clicando na posicao que esta dentro do campo
      #  vazia pra adicionar algum jogador, ele da uma lista de jogador que nem
      #  tem, em vez de dar uma lista dos jogadores que estao na reserva, que
      #  seria muito mais simples."*
      #  Ele esta certo e a diferenca e de conceito: no CAMPO ele esta ESCALANDO
      #  quem ele tem — nao procurando carta no banco de dados. As 2.754 cartas
      #  do catalogo nao tem o que fazer ali.
      #  A lista da vaga passa a ser o ELENCO DELE (reservas + fora do banco),
      #  com um botao para abrir o catalogo inteiro quando ele realmente quiser.
      ' var VER_TUDO=false;\n'
      ' function souVaga(){\n'
      '  try{ return !!(MT_SEL && MT_SEL.slot!==undefined); }catch(e){ return false; }\n'
      ' }\n'
      ' function meuElenco(){\n'
      '  var m={}, s=MT.slots||[], i;\n'
      '  (MT.banco||[]).forEach(function(k){ m[k]=1; });\n'
      '  (MT.elenco||[]).forEach(function(k){ m[k]=1; });\n'
      '  for(i=0;i<s.length;i++) if(s[i]&&s[i].key) m[s[i].key]=1;\n'
      '  return m;\n'
      ' }\n'
      #  ⚠️ 17/08, 2a volta — filtrar as linhas que a casca desenhou NAO bastava:
      #  ela monta a lista so com cards da FUNCAO da vaga, e os cards do elenco
      #  dele quase nunca estao naquela funcao exata. Dava "0 do seu elenco".
      #  Agora a lista da vaga e MONTADA AQUI, com as cartas que ele tem — e a
      #  funcao se resolve sozinha quando o card entra (`funcaoDaVaga`).
      ' function montaListaDoElenco(){\n'
      '  var bx=document.getElementById("box"); if(!bx) return false;\n'
      '  var lista=bx.querySelector("#mtlist"); if(!lista) return false;\n'
      '  var sl=null; try{ sl=MT.slots[MT_SEL.slot]; }catch(e){}\n'
      '  var mm=meuElenco(), vistos={}, itens=[], k;\n'
      '  for(k in mm){\n'
      '   var idb=String(k).split("|")[0].split("@")[0];\n'
      '   if(vistos[idb]) continue; vistos[idb]=1;\n'
      '   var c=null; try{ c=_card(k); }catch(e){}\n'
      '   if(!c) continue;\n'
      '   var pode=true;\n'
      '   try{ pode=(typeof window.elJogaNaPos==="function" && sl)\n'
      '         ? window.elJogaNaPos(c, sl.pos) : true; }catch(e){}\n'
      '   var n=0;\n'
      '   try{ var pp=window.elPontuacao(k, sl?sl.func:null); n=pp?pp.n:0; }catch(e){}\n'
      '   itens.push({k:k, c:c, idb:idb, pode:pode, n:(pode?n:0)});\n'
      '  }\n'
      '  itens.sort(function(a,b){\n'
      '   if(a.pode!==b.pode) return a.pode?-1:1;\n'
      '   return b.n-a.n;\n'
      '  });\n'
      '  var h="", i;\n'
      '  for(i=0;i<itens.length;i++){\n'
      '   var it=itens[i], est=(it.c.modelo&&it.c.modelo!==it.c.tipo)?it.c.modelo:"";\n'
      '   h+=\'<div class=mtli style="\'+(it.pode?"":"opacity:.5")+\'" \'\n'
      '    +\'onclick="mtPoe(\\\'\'+it.k+\'\\\')">\'\n'
      '    +\'<img src="https://efimg.com/efootballhub22/images/player_cards/\'\n'
      '    +it.idb+\'_l.png" onerror="this.style.visibility=&quot;hidden&quot;">\'\n'
      '    +\'<div style="flex:1;min-width:0"><b>\'+esc(it.c.nome)+\'</b>\'\n'
      '    +\'<div class=mini><b style="opacity:.75;letter-spacing:.5px">\'\n'
      '    +esc(it.c.np||it.c.pos||"")+\'</b> \\u00b7 \'+esc(it.c.tipo)+\'</div>\'\n'
      '    +(est?(\'<div class=mini style="opacity:.55">\'+esc(est)+\'</div>\'):"")\n'
      '    +\'</div>\'\n'
      '    +(it.pode\n'
      '      ?(\'<b style="font-size:15px">\'+(+it.n).toFixed(2).replace(".",",")+\'</b>\')\n'
      '      :\'<b style="font-size:10px;color:#e0533d;text-align:right;line-height:1.2">\'\n'
      '       +\'n\\u00e3o joga<br>de \'+esc(sl?sl.pos:"")+\'</b>\')\n'
      '    +\'</div>\';\n'
      '  }\n'
      '  if(!itens.length)\n'
      '   h=\'<div class=mini style="padding:10px 2px">Voc\\u00ea ainda n\\u00e3o tem \'\n'
      '    +\'ningu\\u00e9m no elenco. Use o cat\\u00e1logo inteiro abaixo.</div>\';\n'
      '  if(lista.getAttribute("data-meu")!==String(itens.length)+"|"+(sl?sl.pos:"")){\n'
      '   lista.innerHTML=h;\n'
      '   lista.setAttribute("data-meu",String(itens.length)+"|"+(sl?sl.pos:""));\n'
      '  }\n'
      '  return true;\n'
      ' }\n'
      ' function soDoElenco(){\n'
      '  var bx=document.getElementById("box"); if(!bx) return;\n'
      '  var lista=bx.querySelector("#mtlist"); if(!lista) return;\n'
      '  if(!souVaga()){ var b0=bx.querySelector(".elsofiltro"); if(b0) b0.remove();\n'
      '   lista.removeAttribute("data-meu"); return; }\n'
      '  if(!VER_TUDO){ if(montaListaDoElenco()) { barraDoFiltro(); return; } }\n'
      '  lista.removeAttribute("data-meu");\n'
      #  a chave do card na vaga e SEMPRE id|funcaoDaAba; o que importa e a
      #  CARTA, entao a comparacao e pelo id base, nao pela chave inteira.
      '  barraDoFiltro();\n'
      ' }\n'
      ' function barraDoFiltro(){\n'
      '  var bx=document.getElementById("box"); if(!bx) return;\n'
      '  var lista=bx.querySelector("#mtlist"); if(!lista) return;\n'
      '  var mostrei=[].slice.call(lista.querySelectorAll(".mtli"))\n'
      '   .filter(function(x){ return x.style.display!=="none"; }).length;\n'
      '  var barra=bx.querySelector(".elsofiltro");\n'
      '  if(!barra){\n'
      '   barra=document.createElement("div"); barra.className="elsofiltro";\n'
      '   barra.style.cssText="margin:-2px 0 9px;font-size:11.5px;display:flex;"\n'
      '    +"gap:9px;align-items:center;flex-wrap:wrap";\n'
      '   lista.parentNode.insertBefore(barra, lista);\n'
      '  }\n'
      '  var h = VER_TUDO\n'
      '   ? (\'<b>o cat\\u00e1logo inteiro</b> \\u2014 \'+mostrei+\' cartas\'\n'
      '      +\'<button class=elbt onclick="elSoMeus()">\\u2190 s\\u00f3 o meu elenco</button>\')\n'
      '   : (\'<b>\'+mostrei+\' do seu elenco</b> podem jogar aqui\'\n'
      '      +(mostrei?"":\' \\u2014 nenhum, por enquanto\')\n'
      '      +\' <button class=elbt onclick="elVerTudo()">ver o cat\\u00e1logo inteiro</button>\');\n'
      '  if(barra.innerHTML!==h) barra.innerHTML=h;\n'
      ' }\n'
      ' window.elVerTudo=function(){ VER_TUDO=true; soDoElenco(); };\n'
      ' window.elSoMeus=function(){ VER_TUDO=false; soDoElenco(); };\n'
      #  toda vez que a janela abre de novo, volta a mostrar so o elenco
      ' (function(){\n'
      '  var _ls=window.mtListaSel;\n'
      '  if(typeof _ls==="function"){\n'
      '   window.mtListaSel=function(){ var r=_ls.apply(this,arguments);\n'
      '    setTimeout(function(){ try{ enxuga(); soDoElenco(); }catch(e){} },0);\n'
      '    return r; };\n'
      '  }\n'
      '  var _as=window.mtAbreSel;\n'
      '  if(typeof _as==="function"){\n'
      '   window.mtAbreSel=function(){ VER_TUDO=false; return _as.apply(this,arguments); };\n'
      '  }\n'
      ' })();\n'
      ' setInterval(soDoElenco, 300);\n'
      ' setInterval(enxuga, 260);\n'
      ' document.addEventListener("input", function(){ setTimeout(enxuga,180); }, true);\n'
      '})();\n'
      '</script>\n')

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    html = html[:k] + js + html[k:]
    return html, 'entrou'


# ============================================================================
def patch_nota_do_meu_time_1608(html):
    """UMA REGUA SO PARA O b1n, EM TODA A TELA.

    A regua velha (`b1nDe`) e percentil do b1 BRUTO. Ela nao serve para uma
    carta fora da build do motor: com as barras em zero o b1 do Buffon e
    -711,7 e o `b1nDe` devolve -95,3 — foi assim que UMA habilidade derrubou
    o card de 94,21 para -93,56 no tour do Luis em 17/08.

    A regua desta tela e o PERCENTUAL DE CUMPRIMENTO DO MOLDE, a mesma do
    `achPct` que o `traducaoViva` usa:

        100 * Σ(peso × valor) / Σ(peso × alvo)

    Conferido nos arows do mesmo Buffon: 100*5634/6093 = 92,47.

    ⛔ Troca no HTML PRONTO porque as copias vem de tres lugares: a casca
    (`notaComTec`, `notaCfg`), o proprio gerador e o CONTA-DO-MOTOR.js, que e
    um arquivo da pasta. Editar so o gera_encaixe.py deixava o do arquivo de
    fora — e era justamente ele que vencia.
    ⚠️ O `b1nDe` fica de reserva no fim da expressao, para quando a carta nao
    tiver pesos (ai nao ha molde a cumprir e a conta nao existe).
    """
    import re as _re
    novo = ('c.b1n=(function(A){var n=0,d=0,i,w;A=A||[];'
            'for(i=0;i<A.length;i++){w=A[i][1];if(!w)continue;'
            'n+=w*A[i][3];d+=w*A[i][2];}'
            'return d?100*n/d:b1nDe(c.tipo,c.b1);})(c.arows)')
    alvo = _re.compile(r'c\.b1n\s*=\s*b1nDe\(\s*c\.tipo\s*,\s*c\.b1\s*\)')
    n = len(alvo.findall(html))
    if n:
        html = alvo.sub(lambda m: novo, html)
    return html, n


# ============================================================================
#  CONSERTO DA ABA DO ELENCO — 16/08/2026 (sessao "EF - Meu Time 5", a da TELA)
#
#  Roda POR ULTIMO, depois de todos os renomeios, de proposito.
#  Tres consertos, todos de DESENHO. Nao encosta em conta, em banco nem no
#  motor. Cada um foi medido na tela viva antes de ser escrito.
# ============================================================================
def patch_conserto_elenco_1608(html):
    ok = []

    # ---- 1. A VAGA DE MEIA ATACANTE OFERECIA UMA FUNCAO QUE NAO EXISTE -----
    #  Medido em 16/08 na tela viva: das 27 opcoes que as 13 vagas oferecem,
    #  26 existem entre as 19 funcoes e 1 nao — 'Meia ofensivo infiltrador'.
    #  Vaga configurada nela fica SEM NOTA, calada. Confirmado pela sessao da
    #  transformacao em 16/08 01h15: o molde vigente (dados/molde.json v5) tem
    #  19 funcoes e essa nao esta entre elas; a tabela `funcoes` do banco
    #  tambem nao. O par certo do grupo MEIA ATACANTE, ditado pelo Luis em
    #  16/08 as 00h45, e "Meia ofensivo" + "Atacante infiltrador".
    #
    #  ⛔ SO no MT_FUNCS, que e a OFERTA da vaga. Os alvos e pesos dessa funcao
    #  fantasma continuam assados nas tabelas de calculo da casca e NAO saem
    #  daqui — mexer em tabela de calculo e da outra frente.
    for velho, nvo in (
        ('MO:["Meia ofensivo","Meia ofensivo infiltrador"]',
         'MO:["Meia ofensivo","Atacante infiltrador"]'),
        ("MO:['Meia ofensivo','Meia ofensivo infiltrador']",
         "MO:['Meia ofensivo','Atacante infiltrador']"),
    ):
        if velho in html:
            html = html.replace(velho, nvo, 1)
            ok.append('vaga de meia atacante')
            break

    # ---- 2. O ROTULO CURTO EMBAIXO DA VAGA NO CAMPO ------------------------
    #  Medido: goleiro, lateral, zagueiro e volante mostravam o nome curto
    #  ("defensivo", "de combate", "de contencao") e meia, ponta e centroavante
    #  mostravam o nome INTEIRO espremido numa caixa de 74 pixels
    #  ("Meia armador", "Atacante criador", "Falso nove").
    #  A causa: o rotulo era montado cortando o comeco do nome por uma lista
    #  cravada que ainda tinha as familias VELHAS (Meia central, Meia de lado,
    #  Ponta). Depois do renomeio as familias viraram Meia, Ala e Atacante, e
    #  ai nao cortava nada.
    #  A tela JA TEM a tabela certa e completa — o `ROT`, o mesmo que a barra
    #  da esquerda usa. Agora a vaga le dela, e some a lista cravada.
    velho = ('<div class=mtfn>${sl.func.replace(/^(Goleiro|Zagueiro|Lateral|'
             'Volante|Meia central|Meia de lado|Meia ofensivo|Ponta|'
             'Centroavante|Atacante infiltrador)\\s*/,"")||sl.func}</div>')
    nvo = ('<div class=mtfn>${(typeof ROT!=="undefined"&&ROT[sl.func])'
           '||sl.func}</div>')
    if velho in html:
        html = html.replace(velho, nvo, 1)
        ok.append('rotulo curto da vaga')
    else:
        import re as _re
        m = _re.search(r'<div class=mtfn>\$\{sl\.func\.replace\([^\n]*?</div>',
                       html)
        if m:
            html = html[:m.start()] + nvo + html[m.end():]
            ok.append('rotulo curto da vaga (pelo padrao)')

    # ---- 3. A TRADUCAO DO TIME SALVO ESTAVA APONTANDO PARA ELA MESMA -------
    #  O time fica no navegador (MT_v1) e cada peca e guardada por `id|funcao`.
    #  O CONTA-DO-MOTOR.js traz uma tabela para traduzir a peca salva com nome
    #  velho. Ela esta CERTA no arquivo de origem — mas o `_renomeia()` do
    #  proprio gerador passa um replace de texto no HTML INTEIRO e renomeia
    #  tambem o LADO ESQUERDO da tabela. Resultado medido na tela de 16/08
    #  as 00h35: 4 das 5 linhas traduziam o nome para ELE MESMO, e das 8
    #  funcoes que mudaram de nome em 15/08 a tabela cobria 1.
    #  Peca salva com nome velho aponta para funcao que a tela nao usa mais e
    #  SOME sem erro nenhum.
    #
    #  O conserto: esta funcao roda DEPOIS do ultimo renomeio, e o lado
    #  esquerdo e montado por CONCATENACAO — assim nenhum replace de texto,
    #  nem hoje nem amanha, consegue casar com ele.
    #  ⛔ So no navegador. No banco, no linhas.jsonl e na tabela `funcoes` as
    #  chaves continuam as antigas.
    import re as _re2
    m = _re2.search(r'var DEPARA = \{.*?\.test\(bruto\)\) \{', html, _re2.S)
    if m:
        bloco = (
            "var _DPV = ['Segundo'+' atacante','Ponta'+' finalizadora',"
            "'Ponta'+' criadora','Ponta'+' de lan\u00e7a',"
            "'Meia'+' lateral atacante','Meia'+' lateral cruzador',"
            "'Meia'+' de liga\u00e7\u00e3o armador',"
            "'Meia'+' de liga\u00e7\u00e3o avan\u00e7ado',"
            "'Meia'+' ofensivo armador','Meia'+' central armador',"
            "'Meia'+' central de chegada','Ala'+' atacante'];\n"
            "    var _DPN = ['Atacante infiltrador','Atacante finalizador',"
            "'Atacante criador','Atacante infiltrador',"
            "'Ala finalizador','Ala cruzador',"
            "'Meia armador','Meia de arranque',"
            "'Meia ofensivo','Meia armador',"
            "'Meia de arranque','Ala finalizador'];\n"
            "    var DEPARA = {};\n"
            "    for (var _di = 0; _di < _DPV.length; _di++) "
            "DEPARA[_DPV[_di]] = _DPN[_di];\n"
            "    var bruto = localStorage.getItem('MT_v1');\n"
            "    if (bruto && _DPV.some(function(_x){"
            "return bruto.indexOf('|' + _x) >= 0;})) {")
        html = html[:m.start()] + bloco + html[m.end():]
        ok.append('traducao do time salvo (12 nomes velhos)')

    # ---- 4. O FALSO NOVE VOLTA PARA A VAGA DE SEGUNDO ATACANTE ------------
    #  DECISAO DO LUIS, 16/08: *"Falso nove pode voltar pra segundo atacante."*
    #  A tabela `funcoes` do banco ja dizia `posicoes: ["CA","SA"]`, a funcao
    #  nasceu de CA/SA em 12/08, e o `linhas.jsonl` tem 13 linhas de Falso nove
    #  em carta de SA. A retirada nao tinha decisao por tras — foi efeito
    #  colateral do renomeio de 15/08.
    for velho, nvo in (('SA:["Atacante infiltrador"]',
                        'SA:["Atacante infiltrador","Falso nove"]'),
                       ("SA:['Atacante infiltrador']",
                        "SA:['Atacante infiltrador','Falso nove']")):
        if velho in html:
            html = html.replace(velho, nvo, 1)
            ok.append('Falso nove volta ao segundo atacante')
            break

    # ---- 5. OS CARDS REPETIDOS DO MESMO JOGADOR APARECEM NO ELENCO --------
    #  DECISAO DO LUIS, 16/08: *"nove cards repetidos do mesmo jogador aparecem
    #  no elenco? Aparece."*
    #  Medido em 16/08: ele tem 114 cards e a grade mostrava 105. A lista era
    #  filtrada pelo NOME DO JOGADOR, entao o 2o Neymar sumia.
    #  ⛔ A trava do CAMPO e do BANCO fica: dois cards do mesmo jogador
    #  continuam nao podendo ser escalados juntos. So a GRADE passa a mostrar
    #  todos — e la o repetido tem serventia, que e comparar qual e o melhor.
    velho = ('MT.elenco=(MT.elenco||[]).filter(k=>{const j=_jog(k);'
             'if(vis.has(j))return false;vis.add(j);return true;});')
    nvo = 'MT.elenco=(MT.elenco||[]).filter((k,i,a)=>a.indexOf(k)===i);'
    if velho in html:
        html = html.replace(velho, nvo, 1)
        ok.append('os repetidos do mesmo jogador aparecem no elenco')

    # ---- 6. O ROTULO DA ABA VIRA "ELENCO" --------------------------------
    #  DECISAO DO LUIS, 16/08: *"o rotulo vai virar elenco, sim."*
    #  Cumpre a decisao de 14/08 que separou os nomes: MEU TIME e o DADO
    #  (os 114 cards que ele tem no PS5); ELENCO e a ABA.
    n = 0
    for velho, nvo in (('>\u2605 meu time</button>', '>\u2605 elenco</button>'),
                       ('>\u2605 MEU TIME</b>', '>\u2605 ELENCO</b>'),
                       ('\u2605 MEU TIME</b>', '\u2605 ELENCO</b>')):
        if velho in html:
            html = html.replace(velho, nvo)
            n += 1
    if n:
        ok.append('%d rotulos viram ELENCO' % n)

    return html, (' · '.join(ok) if ok else 'nada casou')


# ============================================================================
#  CONSERTOS DO MODAL — 16/08/2026 (sessao "EF - Meu Time 5", a da TELA)
#
#  Roda depois do patch_conserto_elenco_1608, tambem por ultimo.
#  Tres pedidos do Luis, ditados na madrugada de 16/08. Todos de DESENHO.
#  ⛔ Nao encosta em conta, em banco, no motor, nem na colagem dos bonus.
# ============================================================================
def patch_modal_1608(html):
    ok = []

    # ---- 1. A TARJA "NAO SEI" SAI DO MODAL --------------------------------
    #  ORDEM DO LUIS, 16/08: *"tira isso que eu estou te mostrando aqui, nao e
    #  interessante ter aqui no modal"*.
    #  ⚠️ Isto REVOGA, so no modal, a ordem dele de 15/08 ("quando nao souber,
    #  tem que AVISAR"). O aviso continua existindo fora daqui: o NAO-SEI.txt
    #  da pasta segue sendo escrito, e o dado nao muda.
    #  ⛔ De proposito NAO mexo no patch_bonus_pronto(), que e quem injeta a
    #  tarja — ele e "a colagem dos bonus que vem do motor de bonus", e o
    #  contrato das duas sessoes me proibe de encostar nele. Aqui a tarja e
    #  RETIRADA do HTML ja montado. Para trazer de volta, basta apagar este
    #  bloco: a tarja volta sozinha no ciclo seguinte.
    marca = '/* ===== A TARJA DO NAO SEI - 15/08/2026 ===== */'
    i = html.find(marca)
    if i > 0:
        ini = html.rfind('<script>', 0, i)
        fim = html.find('</script>', i)
        if ini >= 0 and fim > ini:
            html = html[:ini] + html[fim + len('</script>'):]
            ok.append('tarja NAO SEI fora do modal')

    # ---- 2. O BLOCO FISICO EM DUAS LINHAS, O PE TODO EMBAIXO --------------
    #  ORDEM DO LUIS, 16/08: *"na linha de baixo voce coloca so as informacoes
    #  sobre o pe... e em cima voce coloca o restante"*, e depois
    #  *"os itens de pe voce coloca todos juntos na linha de baixo"*.
    #  O pe dominante estava em cima, junto com altura/peso/idade/lesao.
    #  Conferido antes de descer o bonus: o chip "bonus" e o `prBonus(c)` — e
    #  o bonus DO PE RUIM. Por isso ele e item de pe e desce junto.
    #  O chip do pe sai de FORA do `prPar(c)?...:...` de proposito: card sem
    #  dado de pe ruim continua mostrando qual e o pe dominante dele.
    velho = ('<span>${c.age} anos</span><span>${c.foot||\'\u2014\'}</span>'
             '<span>les\u00e3o ${c.inj||\'\u2014\'}</span></div>'
             '<div class=corpopr>${prPar(c)?`')
    nvo = ('<span>${c.age} anos</span>'
           '<span>les\u00e3o ${c.inj||\'\u2014\'}</span></div>'
           '<div class=corpopr><span>p\u00e9 <b>${c.foot||\'\u2014\'}</b></span>'
           '${prPar(c)?`')
    if velho in html:
        html = html.replace(velho, nvo, 1)
        ok.append('fisico em duas linhas (o pe todo embaixo)')

    # ---- 3. OS NOMES DE POSICAO POR EXTENSO -------------------------------
    #  ORDEM DO LUIS, 16/08: *"tira as abreviacoes quando o bloco couber tudo,
    #  o nome inteiro. Lateral esq. e lateral esquerdo, porque o bloco aceita"*.
    #  Varri a tabela POSN inteira: das 13 posicoes, so DUAS estavam abreviadas.
    #  As outras ja estavam por extenso ("Meia lateral esquerda" tem 21 letras,
    #  cinco a mais que "Lateral esquerdo", e cabe) — entao nenhuma outra muda.
    # ---- 4. O "null anos" ------------------------------------------------
    #  Achado ao conferir o item 2 num navegador: card sem idade na base
    #  imprimia literalmente `null anos` na ficha. Medido na tela de 16/08:
    #  813 dos 2.785 cards (29%%) estao sem idade. O chip da lesao ao lado ja
    #  tratava a falta com um travessao; o da idade nao tratava.
    #  ⛔ Isto e so o ROTULO. O buraco de dado em si e da coleta, e esta
    #  registrado no relatorio para a sessao da transformacao.
    for velho, nvo in (("<span>${c.age} anos</span>",
                        "<span>${c.age||'\u2014'} anos</span>"),
                       ("<span>${c.age} anos<" + chr(92) + "/span>",
                        "<span>${c.age||'\u2014'} anos<" + chr(92) + "/span>")):
        if velho in html:
            html = html.replace(velho, nvo)
            ok.append('idade sem dado deixa de sair "null"')
            break

    n = 0
    for velho, nvo in ((':"Lateral esq."', ':"Lateral esquerdo"'),
                       (':"Lateral dir."', ':"Lateral direito"'),
                       (":'Lateral esq.'", ":'Lateral esquerdo'"),
                       (":'Lateral dir.'", ":'Lateral direito'")):
        if velho in html:
            html = html.replace(velho, nvo)
            n += 1
    if n:
        ok.append('%d nomes de posicao por extenso' % n)

    return html, (' · '.join(ok) if ok else 'nada casou')


# ============================================================================
#  MODAL — 2a LEVA, 16/08/2026 (sessao "EF - Meu Time 5", a da TELA)
#
#  Ditado pelo Luis na madrugada. Entra como UM <script> no fim do body, e nao
#  como replace na casca, porque a ficha e REMONTADA a cada abrir/reabrir/
#  encModo — replace pega a primeira montagem e perde as seguintes.
#  Cada peca roda dentro de try/catch: se uma falhar, a ficha continua de pe.
#
#  ⛔ Nao encosta em conta nenhuma. O otimizador chamado pelo botao e o
#     `distBarras` que JA existe na tela (a equacao do motor, fechada em 15/08).
#     Aqui so se decide QUANDO ele roda, e desenha o botao.
#  ⛔ Nada e gravado: ordem do Luis, 16/08 — *"esse aqui e so de visualizacao,
#     nao vai gravar em lugar nenhum"*. O `_grava` da tela so mexe no card em
#     memoria e redesenha; o `_marca`/`_desfaz` ja desfaz ao fechar a ficha.
# ============================================================================

#  As 6 habilidades EXCLUSIVAS DE GOLEIRO. ⚠️ NAO adivinhadas pelo nome:
#  derivadas da Tabela Definitiva do motor (habilidades_por_posicao.json),
#  pegando quem esta bloqueada nas 17 funcoes de linha e liberada nas 2 de
#  goleiro. Repare que "Pegador de penaltis" NAO tem "(GO)" no nome — quem
#  filtrasse por nome erraria essa.
GK_SO = ['Arrem. longo do GO', 'Defesa direta (GO)', 'Grito de garra (GO)',
         'Pegador de pênaltis', 'Repos. baixa do GO', 'Reposição alta do GO']


def patch_modal_1608b(html):
    if 'MODAL_1608B' in html:
        return html, 'ja estava'

    js = ('\n<script>\n/* ===== MODAL - 2a LEVA 16/08/2026 ===== */\n'
          '(function(){\n'
          ' if(window.MODAL_1608B) return; window.MODAL_1608B=1;\n'
          ' var GKSO=' + json.dumps(GK_SO, ensure_ascii=True) + ';\n'

          # ---- 1 e 2 · as colunas de controle e a coluna TOTAL -------------
          #  ORDEM DO LUIS: "essas colunas aqui sao pra controle, coloca uma
          #  tonalidade um pouco mais alta de cinza" (ALVO / VS ALVO / PONTOS)
          #  e "no total voce coloca a tonalidade um pouco mais escura, que e
          #  pra gente saber a soma de tudo".
          #  A tabela tem 13 colunas: 10=Total, 11=Alvo, 12=vs alvo, 13=Pontos.
          #  Uso opacidade nas de controle em vez de trocar a cor: elas recuam
          #  mas o verde/vermelho do sinal continua legivel.
          ' var CSS="#box .at.atgc>*:nth-child(11),#box .at.atgc>*:nth-child(12),'
          '#box .at.atgc>*:nth-child(13),#box .athead.atgc>*:nth-child(11),'
          '#box .athead.atgc>*:nth-child(12),#box .athead.atgc>*:nth-child(13)'
          '{opacity:.5}"\n'
          '  +"#box .at.atgc>*:nth-child(10),#box .athead.atgc>*:nth-child(10)'
          '{background:#8b98a826;border-radius:4px}"\n'
          '  +"#box .at.atgc>*:nth-child(10){font-weight:800}"\n'
          '  +"#box .btotbar{display:flex;flex-direction:column;align-items:flex-start;'
          'gap:1px;cursor:pointer;background:#22c58b;border:none;color:#08120c;'
          'font-weight:800;border-radius:8px;padding:7px 14px;font-size:12px;'
          'line-height:1.2;white-space:nowrap}"\n'
          '  +"#box .btotbar:hover{filter:brightness(1.08)}"\n'
          '  +"#box .btotbar small{font-weight:600;opacity:.85;font-size:10px}"\n'
          # ---- item 11 · a etiqueta da habilidade especial, destacada ------
          '  +"#box .habesp1608{border-color:#22c58b!important;color:#0e6b45!important;'
          'background:#22c58b1f!important;font-weight:700}"\n'
          #  o MAXIMO POSSIVEL e so leitura — o controle aparece apagado e sem clique
          '  +"#box .maxtrava{pointer-events:none!important;opacity:.4!important;'
          'cursor:default!important}"\n'
          #  a linha que explica a ficha sem barras (carta com orcamento 0)
          '  +"#box .semorc{margin:8px 0 2px;padding:9px 12px;border-radius:9px;'
          'background:#f0a5311f;border:1px solid #f0a53155;color:#8a5c12;'
          'font-size:11.5px;font-weight:700}"\n'
          #  o degrau que nao da para confiar: apagado, riscado e sem clique
          '  +"#box .degduv{pointer-events:none!important;opacity:.35!important;'
          'text-decoration:line-through!important;cursor:default!important}";\n'
          ' var st=document.createElement("style"); st.textContent=CSS;\n'
          ' document.head.appendChild(st);\n'

          # ---- a chave da ficha aberta ------------------------------------
          #  ⚠️ o CUR da casca e um `let` no topo de um <script>: NAO vira
          #  window.CUR. Por isso a chave sai do onclick dos botoes das abas.
          ' function chave(){\n'
          '  try{ if(typeof CUR!=="undefined" && CUR) return CUR; }catch(e){}\n'
          '  var bx=document.getElementById("box"); if(!bx) return null;\n'
          '  var bt=bx.querySelector(".encaba[onclick]"); if(!bt) return null;\n'
          '  var m=String(bt.getAttribute("onclick")||"").match(/\x27([^\x27]+\\|[^\x27]+)\x27/);\n'
          '  return m?m[1]:null;\n'
          ' }\n'
          # ---- AS DUAS ABAS (ordem do Luis, 16/08) -------------------------
          #  *"elas sao a mesma coisa... o certo e essas duas virarem so uma,
          #  E TER A IMPLEMENTACAO"* — juntar sem perder nada do que as duas
          #  faziam.
          #
          #  Depois dos pedidos de hoje, COM O QUE EU TENHO e DO MEU JEITO
          #  ficaram com UMA diferenca so: na primeira as barras eram travadas
          #  (`travaBarra` = modo !== 'livre'), na segunda dava para arrastar na
          #  mao. O resto virou igual.
          #
          #  🔑 O TRUQUE, e por que ele e seguro: a aba unica usa POR DENTRO o
          #  modo 'livre'. Assim as travas que ja existem continuam valendo
          #  sozinhas, sem eu ter de mexer nelas:
          #     travaBarra()  = modo !== 'livre'  -> false -> arrasta a barra ✅
          #     travaInsumo() = modo === 'motor'  -> false -> poe insumo    ✅
          #  Nada de trava nova, nada de destravar na marra. O rotulo na tela e
          #  MEU CARD; 'livre' e so o nome interno.
          ' function modoAtual(){ var m=window.ENC_MODO;\n'
          '  return (m==="insumos")?"livre":(m||"motor"); }\n'
          ' function ehInsumos(){ return modoAtual()==="livre"; }\n'
          ' if(window.ENC_MODO==="insumos") window.ENC_MODO="livre";\n'

          #  a barra de abas passa a ter DUAS, no lugar das tres
          ' window._modoBar=function(K){\n'
          '  var M=modoAtual(), q=String.fromCharCode(39),\n'
          '      AB=[["motor","\\u26a1 M\\u00c1XIMO POSS\\u00cdVEL",\n'
          '           "o teto desta carta: a build que o motor escolheu"],\n'
          '          ["livre","\\u2699 MEU CARD",\n'
          '           "monte o card do jeito que ele est\\u00e1 no seu jogo: '
          'habilidades, t\\u00e9cnico, \\u00edmpeto e as barras na m\\u00e3o. '
          'Nada se ajusta sozinho \\u2014 quem otimiza as barras \\u00e9 o bot\\u00e3o."]],\n'
          '      h=\x27<div style="display:flex;gap:6px;margin-bottom:10px">\x27, i, on;\n'
          '  for(i=0;i<AB.length;i++){\n'
          '   on=(AB[i][0]===M);\n'
          '   h+=\x27<button class="encaba\x27+(on?" encabaon":"")+\x27"\x27\n'
          '     +\x27 data-tip="\x27+AB[i][2].replace(/"/g,"&quot;")+\x27"\x27\n'
          '     +\x27 onclick="encModo(\x27+q+AB[i][0]+q+","+q+K+q+\x27)">\x27\n'
          '     +AB[i][1]+"</button>";\n'
          '  }\n'
          '  return h+"</div>";\n'
          ' };\n'

          # ---- 3 · as barrinhas param de se ajustar sozinhas ---------------
          #  ORDEM DO LUIS, 16/08: *"elas tem que ficar sem mexer, porque o cara
          #  esta montando igual ele tem no videogame. Ai vai dar uma nota pra
          #  ele. Se depois ele quiser dar uma melhorada, ai ele clica no botao
          #  e otimiza."*
          #  ⚠️ COMO, e por que assim: o `distBarras` e o `reBarras` moram
          #  DENTRO do fecho do CONTA-DO-MOTOR.js — nao da para desligar de
          #  fora. Entao em vez de desligar, GUARDO os niveis das barras antes
          #  de cada troca de insumo e DEVOLVO depois. O que o Luis montou na
          #  mao fica de pe, e so o botao mexe nas barras.
          #  ⚠️ 16/08 — AQUI TINHA UM TRUQUE MEU QUE FOI REMOVIDO. Ele guardava
          #  os niveis das barras antes de cada troca de insumo e devolvia
          #  depois, para impedir o auto-ajuste. Duas razoes para sair:
          #
          #  1. FICOU DESNECESSARIO. A aba unica roda por dentro no modo
          #     'livre', e o `reBarras` do CONTA-DO-MOTOR.js comeca com
          #     `if(modo() !== 'insumos') return;` — ou seja, ele ja nao dispara
          #     mais sozinho. O `editImp` idem: em 'livre' ele chama `reAplica`,
          #     nao o `distBarras`.
          #  2. ESTAVA QUEBRANDO A NOTA. Para devolver as barras eu chamava o
          #     `_grava`, que recalcula os atributos SO a partir dos niveis —
          #     sem as habilidades. Ele apagava o efeito da habilidade que o
          #     Luis acabara de por ou tirar, e a nota do topo saia sempre um
          #     passo atrasada: pos a 1a habilidade e nao mudou nada; pos a 2a e
          #     apareceu o efeito da 1a. Medido em 16/08.
          #     *"mexeu em qualquer coisa que altera nota, tem que mudar na hora."*


          #  e ao ENTRAR no MEU CARD, as barras comecam zeradas
          #  ⚠️ 16/08, 2o achado: nao basta zerar as BARRAS. Existem DUAS versoes
          #  do `encModo` no HTML — a da casca e a do CONTA-DO-MOTOR.js — e quem
          #  vence depende da ordem em que os blocos entraram. Na tela que o Luis
          #  gerou as 02h25 venceu a DA CASCA, que chama o otimizador em vez de
          #  zerar: as barras iam a zero (por este bloco) mas o tecnico, o impeto
          #  fabricado e as habilidades adicionadas continuavam preenchidos com a
          #  build do motor. Ordem dele: *"nao e pra iniciar com habilidade
          #  adicionada, nem com tecnico, nem com impeto sem ser o nativo"*.
          #  Agora este bloco zera TUDO por conta propria, sem depender de qual
          #  das duas versoes vence.
      #  ---------- A FOTO DO QUE ELE MONTOU ----------
          ' function bldFoto(key){\n'
          '  var c=null; try{ c=_card(key); }catch(e){}\n'
          '  if(!c) return null;\n'
          '  var lvl={}; try{ lvl=_lvlDe(c); }catch(e){}\n'
          '  var add=null;\n'
          '  try{ add=(typeof impAdicionado==="function")?impAdicionado(c):null; }catch(e){}\n'
          '  return { lvl:lvl,\n'
          '           habs:(c._habs!==undefined?c._habs.slice():null),\n'
          '           tec:(c._tec!==undefined?c._tec.slice():null),\n'
          '           tecNome:(c._tecNome!==undefined?c._tecNome:null),\n'
          '           semTec:(c._tec===undefined),\n'
          '           imp:add };\n'
          ' }\n'
          ' function bldPoe(key, f){\n'
          '  if(!f) return;\n'
          '  var c=null; try{ c=_card(key); }catch(e){}\n'
          '  if(!c) return;\n'
          '  try{ _marca(key); }catch(e){}\n'
          '  try{ delete c._cp; delete c._n; }catch(e){}\n'
          '  try{ if(typeof editImp==="function") editImp(key, f.imp||"(nenhum)"); }catch(e){}\n'
          '  try{ c=_card(key)||c; }catch(e){}\n'
          '  if(f.habs===null) delete c._habs; else c._habs=f.habs.slice();\n'
          '  if(f.tec ===null) delete c._tec;  else c._tec =f.tec.slice();\n'
          '  if(f.tecNome===null) delete c._tecNome; else c._tecNome=f.tecNome;\n'
          '  try{ _grava(c, f.lvl||{}); }catch(e){}\n'
          '  if(f.habs && f.habs.length){ try{ _trocaHabs(key, f.habs.slice()); }catch(e){} }\n'
          ' }\n'
          ' window.elBldFoto=bldFoto; window.elBldPoe=bldPoe;\n'
          ' function zeraBarras(key){\n'
          '  var c=null; try{ c=_card(key); }catch(e){}\n'
          '  if(!c) return;\n'
          '  try{ _marca(key); }catch(e){}\n'
          '  var _tb=[], _tn=null;\n'
          '  try{ if(typeof mtTecBs==="function") _tb=mtTecBs()||[]; }catch(e){ _tb=[]; }\n'
          '  try{ if(typeof mtTecNome==="function") _tn=mtTecNome()||null; }catch(e){ _tn=null; }\n'
          '  c._habs=[]; c._tec=_tb.slice(); c._tecNome=_tn;\n'
          '  try{ delete c._cp; delete c._n; }catch(e){}\n'
          '  try{ if(typeof editImp==="function") editImp(key,"(nenhum)"); }catch(e){}\n'
          '  try{ c=_card(key)||c; }catch(e){}\n'
          '  var z={}; try{ MBK.forEach(function(b){ z[b]=0; }); }catch(e){ return; }\n'
          '  try{ c._habs=[]; c._tec=_tb.slice(); c._tecNome=_tn; }catch(e){}\n'
          '  try{ _grava(c,z); }catch(e){}\n'
          ' }\n'
          #  ⚠️ 16/08 — ERRO MEU, PAGO CARO: este bloco so instalava o `encModo`
          #  SE ja existisse um antes (`if(typeof _enc==="function")`). Quando eu
          #  tirei a versao duplicada do patch_edicao_viva, nao sobrou nenhuma —
          #  o `patch_conta_do_motor` nao chega a injetar nesta tela (medido:
          #  `CONTA_DO_MOTOR_1508` e `zeraInsumos` nao existem no HTML gerado).
          #  Resultado: a barra das abas desenhava, mas clicar nela dava
          #  `encModo is not defined` e NADA acontecia.
          #  Agora este bloco E o motor das abas — define sempre, e usa o
          #  anterior so quando ele existe. Um lugar so, e que funciona sozinho.
          ' var _enc = window.encModo;\n'
          ' window.encModo=function(m,key){\n'
          '  if(m==="insumos") m="livre";\n'
          #  saindo do FAZER MINHA BUILD: guarda o que ele montou antes de o
          #  `restaurarMotor` da outra aba reescrever a carta por cima.
          '  try{\n'
          '   if(window.ENC_MODO==="livre" && m!=="livre" && key)\n'
          '    window._BLD_FOTO=bldFoto(key);\n'
          '  }catch(e){}\n'
          '  window.ENC_MODO=m;\n'
          '  if(typeof _enc==="function"){ try{ _enc.call(this,m,key); }catch(e){} }\n'
          '  else if(m==="motor"){ try{ restaurarMotor(key); }catch(e){} }\n'
          '  window.ENC_MODO=m;\n'
          '  if(m==="livre"){\n'
          '   var _ib=String(key||"").split("|")[0].split("@")[0];\n'
          '   if(window._BLD_ZERADA!==_ib){\n'
          '    window._BLD_ZERADA=_ib; window._BLD_FOTO=null;\n'
          '    try{ zeraBarras(key); }catch(e){}\n'
          '   } else if(window._BLD_FOTO){\n'
          '    try{ bldPoe(key, window._BLD_FOTO); }catch(e){}\n'
          '   }\n'
          '  }\n'
          '  try{ reabrir(key); }catch(e){}\n'
          ' };\n'
          ' if(!window.ENC_MODO) window.ENC_MODO="motor";\n'

          # ---- 4 · o botao OTIMIZAR AS BARRAS ------------------------------
          #  ORDEM DO LUIS: *"nesse espaco em branco a gente coloca um botao que
          #  ocupa as duas linhas. Ele vai otimizar somente as barrinhas de
          #  acordo com o que o cara tem nos outros insumos."*
          #  ⛔ Conta nova ZERO: ele chama o `window.otimizarBarras`, que ja
          #  existe e ja e a equacao do motor (fechada em 15/08). E nao grava
          #  em lugar nenhum — so mexe no card em memoria e redesenha.
          ' function poeBotao(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var v=bx.querySelector(".btotbar");\n'
          '  if(!ehInsumos()){ if(v) v.remove(); return; }\n'
          '  if(v) return;\n'
          '  var hd=null, todos=bx.querySelectorAll(".bhd"), i;\n'
          '  for(i=0;i<todos.length;i++) if(/Distribui/i.test(todos[i].textContent)) hd=todos[i];\n'
          '  if(!hd) return;\n'
          '  if(!chave()) return;\n'
          '  var b=document.createElement("button"); b.className="btotbar";\n'
          '  b.title="distribui os pontos das barras buscando a maior nota, '
          'usando o impeto, o tecnico e as habilidades que estao na tela";\n'
          '  b.innerHTML="\\u26a1 OTIMIZAR AS BARRAS'
          '<small>com os insumos que voc\\u00ea p\\u00f4s</small>";\n'
          '  b.onclick=function(){\n'
          '   var kk=chave(); if(!kk) return;\n'
          '   if(typeof window.otimizarBarras!=="function") return;\n'
          #  ⛔ PENDENTE, MESMA CAUSA: este botao otimiza com as habilidades e o
          #  tecnico que o usuario pos (medido: a distribuicao muda e a nota
          #  sobe), mas NAO com o impeto dele — o `impDoMotor` da tela so le o
          #  que vem depois de "o motor pos:", e o `editImp` grava sem esse
          #  prefixo. Quando o impeto tiver fonte unica, e aqui tambem.
          '   try{ _marca(kk); }catch(e){}\n'
          '   try{ window.otimizarBarras(kk); }catch(e){}\n'
          '  };\n'
          '  if(hd.children.length>1) hd.insertBefore(b, hd.children[hd.children.length-1]);\n'
          '  else hd.appendChild(b);\n'
          ' }\n'

          # ---- 5 · a lista de habilidades do MEU CARD ----------------------
          #  ORDEM DO LUIS, 16/08: *"no MEU CARD o cara coloca o que ele quiser,
          #  o que o jogo permite. O jogo permite todas, com excecao das
          #  habilidades de goleiro. O goleiro tem as outras mais as de goleiro;
          #  o jogador de linha tem as outras menos as de goleiro."*
          #  Medido: o seletor NAO usava a lista do motor — usava todas MENOS as
          #  raras, e por isso oferecia habilidade de goleiro a jogador de linha.
          ' function arrumaPool(){\n'
          '  var bx=document.getElementById("box"); if(!bx || !ehInsumos()) return;\n'
          '  var sel=bx.querySelector(\x27select[onchange*="addHab"]\x27); if(!sel) return;\n'
          '  var k=chave(); if(!k) return;\n'
          '  var c=null; try{ c=_card(k); }catch(e){}  if(!c) return;\n'
          '  var ehGK = /^Goleiro/.test(String(c.tipo||""))\n'
          '          || String(c.np||"")==="GK" || String(c.pos||"")==="GK";\n'
          '  var jaTem=[]; try{ jaTem=habsAtual(c)||[]; }catch(e){}\n'
          '  var nat=(c.fab||[]).concat(c.raras||[]);\n'
          '  var todas=[]; try{ todas=Object.keys(HABEF); }catch(e){ return; }\n'
          '  var lista=todas.filter(function(s){\n'
          '   if(jaTem.indexOf(s)>=0 || nat.indexOf(s)>=0) return false;\n'
          '   if(GKSO.indexOf(s)>=0) return ehGK;\n'
          '   return true;\n'
          '  }).sort(function(x,y){ return x.localeCompare(y,"pt"); });\n'
          '  if(sel.options.length-1===lista.length) return;\n'
          '  var h=\x27<option value="">+ adicionar\\u2026</option>\x27, i;\n'
          '  for(i=0;i<lista.length;i++)\n'
          '   h+="<option>"+lista[i].replace(/&/g,"&amp;").replace(/</g,"&lt;")+"</option>";\n'
          '  sel.innerHTML=h; sel.value="";\n'
          ' }\n'

          # ---- 6 · a habilidade especial nao se repete, e ganha destaque ----
          #  ORDEM DO LUIS, 16/08: *"as habilidades especiais estao redundantes,
          #  elas estao nas nativas e em especiais. Da uma destacada nelas —
          #  poe um verdinho nesse botaozinho."*
          #  A causa: a lista de NATIVAS e montada com `c.fab` MAIS `c.raras`, e
          #  as ESPECIAIS sao justamente as `c.raras`. Entao toda especial saia
          #  duas vezes. Aqui a repetida sai da lista das nativas — a especial
          #  continua no lugar dela, e so nele.
          # ---- 6 · a habilidade especial nao se repete, e ganha destaque ----
          #  ORDEM DO LUIS, 16/08: *"as habilidades especiais estao redundantes,
          #  elas estao nas nativas e em especiais. Da uma destacada nelas —
          #  poe um verdinho nesse botaozinho."*
          #  A causa: a lista de NATIVAS e montada com `c.fab` MAIS `c.raras`, e
          #  as ESPECIAIS sao justamente as `c.raras`. Toda especial saia duas
          #  vezes. Aqui a repetida sai da lista das nativas.
          #  ⚠️ O alvo e a etiqueta `.chip.rr` — a especial DO CARD. A secao tem
          #  um segundo bloco de etiquetas, o "as mais valiosas nesta funcao",
          #  que e SUGESTAO e nao pode ser pintado nem tirado de lugar nenhum.
          #  E o nome vem SEM o numero: a etiqueta e "Drible astuto <b>32</b>",
          #  entao comparar o texto inteiro nunca casaria com o <li> da lista.
          ' function nomeDaEtiqueta(el){\n'
          '  var t="", n;\n'
          '  for(n=el.firstChild; n; n=n.nextSibling)\n'
          '   if(n.nodeType===3) t+=n.textContent;\n'
          '  return t.replace(/\\s+/g," ").trim();\n'
          ' }\n'
          ' function especiais(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var chips=bx.querySelectorAll(".chip.rr"), nomes=[], j, nm;\n'
          '  for(j=0;j<chips.length;j++){\n'
          '   chips[j].classList.add("habesp1608");\n'
          '   nm=nomeDaEtiqueta(chips[j]); if(nm) nomes.push(nm);\n'
          '  }\n'
          '  if(!nomes.length) return;\n'
          '  var grupos=bx.querySelectorAll(".hbgrp"), g, cab, lis, x, txt, i;\n'
          '  for(i=0;i<grupos.length;i++){\n'
          '   g=grupos[i]; cab=g.querySelector("b");\n'
          '   if(!cab || !/^Nativas$/i.test(cab.textContent.trim())) continue;\n'
          '   lis=g.querySelectorAll("li");\n'
          '   for(j=lis.length-1;j>=0;j--){\n'
          '    txt=lis[j].textContent.replace(/\\s+/g," ").trim();\n'
          '    for(x=0;x<nomes.length;x++) if(txt===nomes[x]){ lis[j].remove(); break; }\n'
          '   }\n'
          '   if(!g.querySelectorAll("li").length){\n'
          '    var ul=g.querySelector("ul"); if(ul) ul.innerHTML="<li>nenhuma</li>";\n'
          '   }\n'
          '  }\n'
          ' }\n'

          # ---- 7 · o bloco "Boas opcoes" nao aparece no MEU CARD ------------
          #  ORDEM DO LUIS, 16/08: *"tambem nao e pra ter aquelas boas opcoes ali
          #  embaixo, nao — isso na aba com o que eu tenho"*. Sao SUGESTOES do
          #  motor; nesta aba quem monta e ele. Nas outras abas continuam.
          ' function boasOpcoes(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var gs=bx.querySelectorAll(".hbgrp"), i, cab;\n'
          '  for(i=0;i<gs.length;i++){\n'
          '   cab=gs[i].querySelector("b");\n'
          '   if(cab && /^Boas\\s+op/i.test(cab.textContent.trim()))\n'
          '    gs[i].style.display = ehInsumos() ? "none" : "";\n'
          '  }\n'
          ' }\n'
          # ---- 8 · O CAMPINHO ACENDE A POSICAO DA FUNCAO ABERTA -------------
          #  ORDEM DO LUIS, 16/08: *"cliquei em Falso nove e ele nao marcou no
          #  campo as posicoes"*.
          #  Medido: o campinho decide o que acender pelo `funcDaPos`, que casa
          #  ESTILO + posicao. Para o Falso nove ele so responde quando o estilo
          #  e "Atacante Piv\u00f4" — mas existem linhas de Falso nove com estilo
          #  Artilheiro, Homem de area, Piv\u00f4 e Puxa marcacao. Nessas, nenhuma
          #  posicao acendia.
          #  ⛔ A regra em si e do motor e nao se toca. Aqui e so DESENHO: o
          #  botao da funcao aberta JA mostra as posicoes certas na etiqueta
          #  (o `sigsDoCard`, que olha o que ESTE card exerce). Se o campinho
          #  nao acendeu nada, ele passa a acender exatamente o que o botao diz.
          #  Assim os dois nunca se contradizem na tela.
          #  ⚠️ 16/08, 2a volta — ORDEM DO LUIS, com as palavras dele:
          #    *"quando ele clica numa posicao, acende outra posicao nao.
          #      So acende mais de uma posicao quando ele clica na FUNCAO,
          #      que pode ser feita por mais de uma posicao."*
          #  Ou seja, a regra e simetrica:
          #    clicou na FUNCAO  -> acende TODAS as posicoes onde ela e exercida
          #    clicou na POSICAO -> acende SO ELA (as funcoes aparecem na lista)
          #  A primeira versao deste bloco acendia tudo o que a etiqueta do botao
          #  dizia, sem olhar no que o Luis tinha clicado — e por isso clicar em
          #  PTD acendia o PTE junto.
          #  Aqui eu anoto QUAL foi o ultimo clique (na fase de captura, antes do
          #  onclick da propria tela rodar) e uso isso para decidir.
          ' document.addEventListener("click", function(ev){\n'
          '  try{\n'
          #  ⚠️ o reset mora DENTRO do proprio ouvinte, de proposito. A 1a versao
          #  zerava no `abrir` — mas clicar numa posicao tambem passa pelo
          #  `abrir` por dentro, e o reset apagava a memoria antes de eu usar.
          '   var t=ev.target;\n'
          '   if(!t||!t.closest){ window._ULT_CLIQUE=null; return; }\n'
          '   var dg=t.closest(\x27[onclick*="setCondCard"]\x27);\n'
          #  ⚠️ o degrau sai do TEXTO do botao ("+2"), nao de expressao regular no
          #  onclick. A 1a versao usava regex e ela saiu com barra dupla no HTML
          #  (`\\s` em vez de `\s`) — nunca casava, o degrau ficava sempre 1 e as
          #  notas nao mudavam. Sem regex, sem esse risco.
          '   if(dg){ var mm=String(dg.textContent||"").replace(/[^0-9]/g,"");\n'
          '           if(mm) window._GRAU_COND=+mm;\n'
          '           window._ULT_CLIQUE="grau"; return; }\n'
          '   if(t.closest(".cbfn")){ window._ULT_CLIQUE="func";\n'
          '                           window._ULT_POS=null; return; }\n'
          '   var ps=t.closest(".cbcampo .cbp");\n'
          '   if(ps){ window._ULT_CLIQUE="pos";\n'
          '           window._ULT_POS=String(ps.textContent||"").trim(); return; }\n'
          '   window._ULT_CLIQUE=null; window._ULT_POS=null;\n'
          '  }catch(e){}\n'
          ' }, true);\n'
          ' function acendeCampo(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var campo=bx.querySelector(".cbcampo"); if(!campo) return;\n'
          '  var cels=campo.querySelectorAll(".cbp"), i, t;\n'
          #  clicou numa POSICAO: acende SO ela, doa a quem doer
          '  if(window._ULT_CLIQUE==="pos" && window._ULT_POS){\n'
          '   for(i=0;i<cels.length;i++){\n'
          '    t=String(cels[i].textContent||"").trim();\n'
          '    if(t===window._ULT_POS){\n'
          '     cels[i].classList.remove("cboff"); cels[i].classList.remove("cbsec");\n'
          '     cels[i].classList.add("cbnat");\n'
          '    } else if(cels[i].classList.contains("cbnat")){\n'
          '     cels[i].classList.remove("cbnat"); cels[i].classList.add("cbsec");\n'
          '    }\n'
          '   }\n'
          '   return;\n'
          '  }\n'
          '  if(campo.querySelector(".cbnat")) return;\n'
          '  var bt=bx.querySelector(".cbfn.cbfnq"); if(!bt) return;\n'
          '  var u=bt.querySelector("u"); if(!u) return;\n'
          '  var sigs=String(u.textContent||"").split("/")\n'
          '   .map(function(s){return s.trim();}).filter(function(s){return !!s;});\n'
          '  if(!sigs.length) return;\n'
          '  var cels=campo.querySelectorAll(".cbp"), i, t;\n'
          '  for(i=0;i<cels.length;i++){\n'
          '   t=String(cels[i].textContent||"").trim();\n'
          '   if(sigs.indexOf(t)>=0){\n'
          '    cels[i].classList.remove("cboff"); cels[i].classList.remove("cbsec");\n'
          '    cels[i].classList.add("cbnat");\n'
          '   }\n'
          '  }\n'
          ' }\n'
          # ---- 9 · O "OTIMIZAR - A BUILD DO MOTOR" SAI DO MEU CARD ----------
          #  ORDEM DO LUIS, 16/08: *"por que voltou esse botao de otimizar a do
          #  motor? Onde tem o MEU, isso nao tem que colocar."*
          #  Ele e o otimizador COMPLETO: troca habilidade, tecnico e impeto
          #  pela build que o motor escolheu — o oposto do que a aba faz, que e
          #  o Luis montar o card do jeito que ele tem no jogo. No MAXIMO ele
          #  continua, que la e o lugar dele.
          #  ⚠️ Casar por `otimizar(` sozinho pegaria o `otimizarBarras(` junto;
          #  por isso o casamento inclui a aspa: `otimizar('`.
          ' function botaoDoMotor(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var bts=bx.querySelectorAll("[onclick]"), i, oc;\n'
          '  for(i=0;i<bts.length;i++){\n'
          '   oc=String(bts[i].getAttribute("onclick")||"");\n'
          #  ⚠️ o onclick dele e `restaurarMotor(...)`, nao `otimizar(...)` —
          #  medido no HTML gerado. Casar pelo nome errado nao pegava nada.
          '   if(oc.indexOf("restaurarMotor(")<0) continue;\n'
          '   bts[i].style.display = ehInsumos() ? "none" : "";\n'
          '  }\n'
          ' }\n'
          # ---- 10 · O TETO DA PUNICAO — a tela punia SEM LIMITE ------------
          #  ORDEM DO LUIS, 16/08, pela sessao da transformacao: *"o otimizador
          #  do modal tem que botar as coisas do jeito que a gente faz no motor.
          #  Tem que seguir exatamente a mesma coisa."*
          #
          #  Medido nos dois codigos, lado a lado:
          #    regua.py (o motor) .. TETO_PUN = 9  — "a punicao para no 9o ponto"
          #                          lim = min(-d, TETO_PUN)
          #    casca (a tela) ...... for(k=1; k<=d; k++)   ← SEM TETO
          #  Os degraus PARA CIMA sao identicos nos dois (o `P.DEG` da casca e o
          #  `DEG` do regua.py). So a punicao para baixo estava sem limite.
          #
          #  O que isso causava: sem teto, um buraco de 30 pontos continua
          #  rendendo ate o trigesimo — entao o otimizador da tela despeja ponto
          #  em atributo perdido, exatamente o que a decisao de 04/08 quis
          #  impedir. Era por isso que "otimizar" PIORAVA a nota: as duas
          #  distribuicoes eram otimas, cada uma para a sua regua, e a da tela
          #  nao era a do motor.
          #
          #  ⛔ Nao invento regra: o teto 9 e do `regua.py`, do motor.
          ' (function(){\n'
          '  if(typeof _fal!=="function") return;\n'
          '  var TETO=9;\n'
          '  var novo=function(d,p){ var inc=0.25*p/12, t=0, k,\n'
          '   lim=Math.min(d,TETO);\n'
          '   for(k=1;k<=lim;k++) t+=(1+(k-1)*inc)*p;\n'
          '   return t; };\n'
          '  try{ _fal=novo; }catch(e){}\n'
          '  try{ window._fal=novo; }catch(e){}\n'
          '  window.PUNICAO_COM_TETO=TETO;\n'
          ' })();\n'
          # ---- 11 · O ⚡ MAXIMO POSSIVEL NAO E EDITAVEL ---------------------
          #  ORDEM DO LUIS, 16/08: *"a aba maximo possivel nao e editavel, eu ja
          #  falei isso. Nao e editavel."*
          #  ⚠️ ISTO E CONSERTO DE ESTRAGO MEU. As travas que ja existiam
          #  (`travaBarra`, `travaInsumo`) bloqueiam a ACAO, mas quem escondia os
          #  CONTROLES dependia das tres abas antigas. Quando eu juntei as duas,
          #  os botoes e seletores voltaram a aparecer no MAXIMO — apertar nao
          #  fazia nada, mas apareciam, e nao e isso que ele decidiu.
          #  Aqui os controles ficam apagados e sem clique quando a aba e a do
          #  MAXIMO. Nao mexo em trava nenhuma: so no desenho.
          # ---- 12 · TROCAR INSUMO NAO MEXE NAS BARRAS ----------------------
          #  ORDEM DO LUIS, 16/08: *"quando a gente muda o impeto, olha o que
          #  acontece? Ele otimiza. Nao e pra otimizar. So e pra otimizar quando
          #  o cara clicar em OTIMIZAR AS BARRAS."*
          #
          #  Medido: o degrau do impeto condicional chama o `setCondCard`, e ele
          #  nao "reotimiza" — ele TROCA A BUILD INTEIRA pela que o motor guardou
          #  para aquele degrau (`c.CD[degrau]`), e a build traz as barras junto.
          #  Por isso saltava de `0/62 sobram 62` para `62/62 tudo gasto`.
          #
          #  O conserto: guardo os niveis das barras antes, deixo a funcao fazer
          #  o que ela faz, e devolvo os niveis depois.
          #  ⚠️ E AQUI ESTA A LICAO QUE ME CUSTOU CARO HOJE: devolver com
          #  `_grava` sozinho NAO BASTA — ele remonta os atributos so a partir
          #  dos niveis, sem as habilidades, e a nota sai um passo atrasada.
          #  Por isso vem o `_renota` logo atras, que recalcula com tudo.
          ' function nivelDe(c){\n'
          '  var o={}; try{ var l=_lvlDe(c); for(var k in l) o[k]=l[k]; }catch(e){}\n'
          '  return o;\n'
          ' }\n'
          ' function semMexerNasBarras(nome){\n'
          '  var f=window[nome]; if(typeof f!=="function") return;\n'
          '  window[nome]=function(){\n'
          '   var a0=arguments[0],\n'
          '       k=(typeof a0==="string"&&a0.indexOf("|")>0)?a0:chave();\n'
          '   var antes=null, c=null;\n'
          '   if(ehInsumos()&&k){ try{ c=_card(k); if(c) antes=nivelDe(c); }catch(e){} }\n'
          '   var r=f.apply(this,arguments);\n'
          '   if(antes&&k){\n'
          '    try{ var cc=_card(k)||c;\n'
          '     if(cc){ _grava(cc,antes);\n'
          '             if(typeof _renota==="function") _renota(cc); }\n'
          '    }catch(e){}\n'
          '    try{ reabrir(k); }catch(e){}\n'
          '   }\n'
          '   return r;\n'
          '  };\n'
          ' }\n'
          #  ⚠️ o `setCondCard` NAO entra nesta lista. Ele nao "reotimiza": troca
          #  a linha inteira do motor, que e o certo. Segurar as barras ali
          #  deixava o card num estado meio-trocado e a nota saia em -36,99.
          #  O que o MEU CARD precisa — trocar so o impeto — depende do nivel do
          #  condicional por degrau, que nao existe nos dados. Pedido no
          #  `PARA-A-SESSAO-DA-TRANSFORMACAO-1608-H`.
          ' ["editImp","trocaTec","_trocaHabs","addHab","remHab"]\n'
          '  .forEach(semMexerNasBarras);\n'
          # ---- 13 · A LISTA DAS FUNCOES PARA DE PULAR ----------------------
          #  ORDEM DO LUIS, 16/08: *"ele esta invertendo — e Falso nove, depois
          #  Falso nove vai pro final, Centroavante fixo vai pra frente, sempre
          #  isso. Arruma."*
          #  Medido: a lista e reordenada por nota a cada render
          #  (`irm.sort(function(a,b){return b._n-a._n;})`), e o `_n` e apagado
          #  quando o card muda. So que ao trocar o degrau do condicional
          #  SO A FUNCAO ABERTA troca de linha — as outras continuam no degrau 1.
          #  A lista passava a comparar uma funcao no degrau 2 com as outras no
          #  degrau 1, e pulava.
          #  O conserto: a ordem e congelada na PRIMEIRA vez que a carta abre —
          #  que e sempre no degrau 1, o mesmo do ranking — e mantida enquanto a
          #  ficha estiver aberta. ⛔ Nenhuma nota e alterada: so a ordem dos
          #  botoes no DOM.
          # ---- 14 · AS NOTAS DA LISTA VEM DO BANCO, POR DEGRAU --------------
          #  ORDEM DO LUIS, 16/08: *"qualquer coisa que ele mexer no modal nao
          #  muda aqueles numeros, exceto o impeto +1/+2/+3. Se mexer no
          #  +1/+2/+3, ai passa a mostrar o daquele degrau."* E, logo depois:
          #  *"do MAXIMO, do OTIMIZADO — nao do que ele esta fazendo na tela
          #  agora, do que a gente tem no banco de dados otimizado."*
          #
          #  Medido: cada funcao da carta tem `CD["2"]` e `CD["3"]` com o `b1n`
          #  otimizado daquele degrau. E a distancia entre a nota e o b1n e
          #  CONSTANTE (sao os bonus, que o degrau nao muda). No Messi:
          #     nota 112,0 - b1n 109,22 = 2,78
          #     degrau 2:  109,41 + 2,78 = 112,2   <- o que a tela dele mostrou
          #  Entao a nota de qualquer degrau sai do banco, sem a tela recalcular.
          #
          #  A base (degrau 1) e congelada quando a carta abre. Depois disso
          #  NADA no editor mexe nesses numeros — so o botao do degrau.
          ' var _ordemFunc={}, _baseFunc={};\n'
          ' if(!window._GRAU_COND) window._GRAU_COND=1;\n'
          ' function baseDaCarta(){\n'
          '  var k=chave(); if(!k) return null;\n'
          '  return String(k).split("|")[0].split("@")[0];\n'
          ' }\n'
          ' function irmaosDa(base){\n'
          '  try{ return D.filter(function(x){ return x && x.id!=="MOLDE"\n'
          '   && String(x.id).split("@")[0]===base; }); }catch(e){ return []; }\n'
          ' }\n'
          ' function congelaBase(base){\n'
          '  if(_baseFunc[base]) return;\n'
          '  var m={}, irm=irmaosDa(base), i, x;\n'
          '  for(i=0;i<irm.length;i++){ x=irm[i];\n'
          '   try{ m[x.tipo]={ nota:nota(x), b1n:(x.b1n!==undefined?x.b1n:null),\n'
          '                    CD:x.CD||null }; }catch(e){}\n'
          '  }\n'
          '  _baseFunc[base]=m;\n'
          ' }\n'
          ' function notaNoDegrau(base, funcao, grau){\n'
          '  var m=_baseFunc[base]; if(!m||!m[funcao]) return null;\n'
          '  var b=m[funcao];\n'
          '  if(grau<=1 || !b.CD || !b.CD[String(grau)]) return b.nota;\n'
          '  if(b.b1n===null) return b.nota;\n'
          '  var d=b.CD[String(grau)];\n'
          '  if(d.b1n===undefined || d.b1n===null) return b.nota;\n'
          '  return d.b1n + (b.nota - b.b1n);\n'
          ' }\n'
          ' function pintaNotas(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var base=baseDaCarta(); if(!base) return;\n'
          '  congelaBase(base);\n'
          '  var bts=bx.querySelectorAll(".cbfn"), i, nm, b, v;\n'
          '  for(i=0;i<bts.length;i++){\n'
          '   nm=bts[i].querySelector("i"); b=bts[i].querySelector("b");\n'
          '   if(!nm||!b) continue;\n'
          '   v=notaNoDegrau(base, String(nm.textContent||"").trim(), window._GRAU_COND);\n'
          '   if(v===null||isNaN(v)) continue;\n'
          '   b.textContent=v.toFixed(1).replace(".",",");\n'
          '  }\n'
          ' }\n'
          ' function ordemEstavel(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var lista=bx.querySelector(".cbfnl"); if(!lista) return;\n'
          '  var bts=[].slice.call(lista.querySelectorAll(".cbfn"));\n'
          '  if(bts.length<2) return;\n'
          '  var k=chave(); if(!k) return;\n'
          '  var base=String(k).split("|")[0].split("@")[0];\n'
          '  function nomeDe(e){ var q=e.querySelector("i");\n'
          '   return q?String(q.textContent||"").trim():""; }\n'
          '  var agora=bts.map(nomeDe);\n'
          '  if(!_ordemFunc[base]){ _ordemFunc[base]=agora; return; }\n'
          '  var alvo=_ordemFunc[base], i, mudou=false;\n'
          '  if(alvo.length!==agora.length) return;\n'
          '  for(i=0;i<agora.length;i++) if(agora[i]!==alvo[i]){ mudou=true; break; }\n'
          '  if(!mudou) return;\n'
          '  for(i=0;i<alvo.length;i++){\n'
          '   var achou=null, j;\n'
          '   for(j=0;j<bts.length;j++) if(nomeDe(bts[j])===alvo[i]){ achou=bts[j]; break; }\n'
          '   if(achou) lista.appendChild(achou);\n'
          '  }\n'
          ' }\n'
          ' function travaMaximo(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var trava=!ehInsumos();\n'
          #  ⚠️ 16/08, 2a volta: os botoes +1/+2/+3 do impeto condicional chamam
          #  `setCondCard`, NAO `toggleCondCard` — por isso continuaram clicaveis
          #  no MAXIMO na primeira versao. E o estrago era grande: cada clique
          #  troca a build INTEIRA (funcao aberta, tecnico, habilidades e barras),
          #  porque ele aplica a build que o motor guardou para aquele degrau.
          '  var sel=\x27[onclick*="editBar"],[onclick*="setBar"],[onclick*="remHab"],\x27\n'
          '   +\x27select[onchange*="addHab"],select[onchange*="trocaTec"],\x27\n'
          #  ⚠️ 16/08 — os botoes do condicional FICARAM DE FORA da trava, e de
          #  proposito. O Luis explicou o modelo: o motor roda uma linha para
          #  cada funcao x degrau, e ja estao prontas no banco. No MAXIMO, clicar
          #  no +2 nao edita nada — NAVEGA para a linha do degrau 2. Travar ali
          #  seria tirar a unica forma de ver a carta nos tres degraus.
          '   +\x27select[onchange*="editImp"]\x27;\n'
          '  var a=bx.querySelectorAll(sel), i;\n'
          '  for(i=0;i<a.length;i++){\n'
          '   if(trava) a[i].classList.add("maxtrava");\n'
          '   else a[i].classList.remove("maxtrava");\n'
          '  }\n'
          ' }\n'
          #  ⚠️ 16/08 — ESTE ERA O DEFEITO. A 1a versao zerava o degrau em TODA
          #  chamada de `abrir`. So que o `setCondCard` termina chamando
          #  `reabrir(key)`, e o `reabrir` chama `abrir` — entao a propria
          #  troca de degrau se apagava: o clique punha 2, o `abrir` punha 1 de
          #  volta, e o `pintaNotas` sempre lia 1. Medido: o ouvinte PEGAVA o
          #  "2" e o `window._GRAU_COND` voltava a 1 no mesmo instante.
          #  Agora so zera quando a CARTA muda de verdade.
          ' (function(){ var _ab=window.abrir;\n'
          '  if(typeof _ab!=="function") return;\n'
          #  ⚠️ compara a CHAVE INTEIRA (carta|funcao), nao so a carta: trocar de
          #  funcao na lista reabre a carta na build de fabrica dela, entao o
          #  degrau tem mesmo que voltar a 1. Trocar de degrau reabre a MESMA
          #  chave — e so nesse caso o degrau sobrevive.
          '  window.abrir=function(k){\n'
          '   try{ var s=String(k||"");\n'
          '    if(s && s!==window._CHAVE_ABERTA){ window._CHAVE_ABERTA=s;\n'
          '                                       window._GRAU_COND=1; }\n'
          '   }catch(e){}\n'
          '   return _ab.apply(this,arguments); };\n'
          ' })();\n'
          #  fechar a ficha esquece a chave, para reabrir a mesma carta comecar
          #  no degrau 1 de novo (o `fechar` ja desfaz a build pelo `_desfaz`).
          ' (function(){ var _fc=window.fechar;\n'
          '  if(typeof _fc!=="function") return;\n'
          '  window.fechar=function(){ window._CHAVE_ABERTA=null;\n'
          '   window._GRAU_COND=1; return _fc.apply(this,arguments); };\n'
          ' })();\n'
          # ---- 21 · O DEGRAU QUE NAO DA PARA CONFIAR -----------------------
          #  A sessao da transformacao mediu e mandou a funcao (16/08). O
          #  mecanismo, nas palavras deles:
          #
          #    "Quando dois impetos tocam o MESMO atributo, o `nm` guarda a
          #     SOMA. Esse atributo deixa de parecer nivel 1 e o motor nao o
          #     enxerga. No degrau 2 os visiveis vao de 1 para 2 — certo. O
          #     ESCONDIDO fica em 4 e devia ir para 5."
          #
          #    Jude Bellingham  Motor do Time +1 + Instinto Artilheiro +3
          #      os dois tocam Aceleracao -> nm = 1+3 = 4 -> o motor ve 3 de 4
          #    Harry Kane       Chute +1 + Forca +3
          #      DOIS atributos em comum -> o motor ve 2 de 4, erra em dobro
          #
          #  Ou seja: nessas cartas o `CD` do banco foi calculado sobre menos
          #  atributos do que a carta tem, e o numero do degrau esta errado.
          #
          #  ⛔ A funcao abaixo e DELES, copiada sem uma virgula de mudanca.
          #  Eu escrevi uma alternativa e medi as duas nas 176 cartas com CD:
          #  concordam em 12, a deles pega 6 a mais, a minha nao pega nenhuma
          #  que a deles nao pegue. Na duvida fica a mais conservadora — e a
          #  regra e deles, entao quem mantem e quem mediu.
          #
          #  Medido nesta tela: 18 das 176 cartas com CD (10,2%).
          #  ⚠️ 16/08, 12h30 — 2a VERSAO. A 1a perguntava "o `nmn` sabe nomear os
          #  impetos?" e desligava 18. Mas o motor NAO le o `nmn` — ele le so
          #  QUAIS ATRIBUTOS VALEM 1. Perguntar outra coisa gerava 8 falsos
          #  positivos, e um deles era justamente o Messi Falso nove
          #  `89138556575063`, o card das fotos do Luis:
          #     nm: Controle=1 Posse=1 Contato fisico=1 Equilibrio=1  (= Fisica)
          #         Passe rasteiro=4 Passe alto=4 Finalizacao=4 Forca chute=4
          #     o conjunto de nivel 1 casa a Fisica inteira -> nada escondido
          #  Os 112,0 / 112,2 / 112,2 dele estao CERTOS.
          #
          #  A pergunta certa: o conjunto de atributos em nivel 1 forma um impeto
          #  INTEIRO do catalogo? Se nao forma, faltou atributo — ele foi somado
          #  com outro impeto e o motor nao o enxerga.
          #
          #  Medido por mim nas 176 cartas com CD, contra a versao antiga:
          #     pela antiga .... 18   ·   pela nova .... 10
          #     casos que so a NOVA pega ................. 0  (nao perde nenhum real)
          ' function condicionalDuvidoso(c){\n'
          '  try{\n'
          '   var a=[], i;\n'
          '   (c.nm||[]).forEach(function(p){ if(p && +p[1]===1) a.push(+p[0]); });\n'
          '   if(!a.length) return false;\n'
          '   var ch=a.sort(function(x,y){return x-y;}).join(",");\n'
          '   for(i=0;i<CAT.length;i++){\n'
          '    var pr=CAT[i][2].map(function(x){ return +x[0]; })\n'
          '                    .sort(function(x,y){ return x-y; }).join(",");\n'
          '    if(pr===ch) return false;\n'
          '   }\n'
          '   return true;\n'
          '  }catch(e){ return false; }\n'
          ' }\n'
          #  exposta de proposito: e a regra DELES, e assim qualquer sessao (ou
          #  o console do Luis) confere a lista sem ter de reescrever a funcao.
          ' window.condicionalDuvidoso=condicionalDuvidoso;\n'
          #  o botao sai desligado, com o motivo no title. NAO some: o Luis
          #  precisa ver que existe e por que nao da para clicar.
          ' function travaDegrauDuvidoso(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var c=null; try{ c=_card(chave()); }catch(e){}\n'
          '  if(!c) return;\n'
          '  var duv = !!(c.CD && (c.CD["2"]||c.CD["3"])) && condicionalDuvidoso(c);\n'
          '  var a=bx.querySelectorAll(\x27[onclick*="setCondCard"]\x27), i;\n'
          '  for(i=0;i<a.length;i++){\n'
          '   if(duv){ a[i].classList.add("degduv");\n'
          '    a[i].setAttribute("title","nesta carta dois ímpetos somam no mesmo '
          'atributo, e o motor calculou o degrau sem enxergar um deles. O número '
          'sairia errado — por isso o botão está desligado.");\n'
          '   } else { a[i].classList.remove("degduv"); }\n'
          '  }\n'
          '  if(duv) window._GRAU_COND=1;\n'
          ' }\n'
          # ---- 18 · o dado em INGLES no bloco FISICO ------------------------
          #  ACHADO 16/08, medido nas 12.203 linhas da tela:
          #
          #    pe    : Direito 8.882 · Esquerdo 2.760 · Left 160 · Right 401
          #    lesao : Baixa 1.853 · Media 4.135 · Alta 1.697 · 0/1/2 em 561 · sem 3.957
          #
          #  561 linhas com "Left/Right" e 561 linhas com 0/1/2 — o MESMO lote.
          #  Um pedaco da base entrou sem traducao. Era o que o Luis viu no Messi
          #  Falso nove: "lesao 1" e "pe Left".
          #
          #  O pe eu traduzo (Left=Esquerdo, Right=Direito, nao tem duvida).
          #  A LESAO EU NAO TRADUZO: nao sei se 0 e Baixa ou se e Alta, e chutar
          #  aqui seria mentir na cara do Luis. Fica "—", como todo dado que
          #  falta na tela, e o numero cru vai no title para nao se perder.
          ' function arrumaFisico(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var pr=bx.querySelector(".corpopr"), sp, i, t;\n'
          '  if(pr){ sp=pr.querySelectorAll("b");\n'
          '   for(i=0;i<sp.length;i++){ t=String(sp[i].textContent||"").trim();\n'
          '    if(t==="Left")  sp[i].textContent="Esquerdo";\n'
          '    if(t==="Right") sp[i].textContent="Direito";\n'
          '   } }\n'
          '  var tp=bx.querySelector(".corpotop"); if(!tp) return;\n'
          '  sp=tp.querySelectorAll("span");\n'
          '  for(i=0;i<sp.length;i++){ t=String(sp[i].textContent||"").trim();\n'
          '   if(/^lesão\\s+\\d+$/.test(t)){\n'
          '    sp[i].setAttribute("title","o dado veio em ingles, como numero ("\n'
          '     +t.replace(/[^0-9]/g,"")+"). Baixa/Media/Alta ainda nao foi medido.");\n'
          '    sp[i].textContent="lesão —";\n'
          '   } }\n'
          ' }\n'
          # ---- 19 · a carta SEM ORCAMENTO abria muda -----------------------
          #  ACHADO 16/08: 827 das 2.785 cartas (30%) tem `orc` = 0. A casca faz
          #  `function painelBuild(c){ if(!c.orc) return ""; }` — e some com TUDO:
          #  a barra de abas, as barrinhas, os insumos. O Luis abria o Mbappe e
          #  encontrava a ficha pela metade, sem nada explicando por que.
          #  A lista de funcoes e o campinho continuam (moram no cabecalho).
          #
          #  ⚠️ Eu perguntei se `orc`=0 e a verdade ou dado faltando, e a sessao
          #  da transformacao MEDIU (16/08). E a verdade — o teto prova:
          #     as 827 com orc=0 .... sobra media de OVR  -0,02
          #     as 1.958 com orc>0 .. sobra media de OVR +12,61
          #     29% ja passaram do teto · 76% estao a menos de 1 ponto dele
          #     OVR medio: 93,8 nas de orcamento zero x 83,7 nas outras
          #  Sao as cartas boas, que ja vem no teto. Por isso o texto diz
          #  "ja esta no teto" e nao "nao tem pontos" — ordem deles, e explica
          #  o porque em vez de so constatar.
          ' function avisaSemOrcamento(){\n'
          '  var bx=document.getElementById("box"); if(!bx) return;\n'
          '  var velho=bx.querySelector(".semorc"); if(velho) velho.remove();\n'
          '  if(bx.querySelector(".bpan")) return;\n'
          #  ⚠️ `cardAberto` NAO e global — mora dentro do IIFE do CONTA-DO-MOTOR.
          #  Medido: global mesmo so tem `_card`. A chave sai do `chave()` daqui.
          '  var c=null; try{ c=_card(chave()); }catch(e){}\n'
          '  if(!c || c.id==="MOLDE" || c.orc) return;\n'
          #  ⚠️ 2a volta: entrar como irmao do `.fhdcampo` jogava o aviso DENTRO
          #  da linha flex do cabecalho — virava uma coluna estreita e espremia
          #  a lista de funcoes, cortando as notas. Sobe um nivel e entra depois
          #  do cabecalho inteiro, na largura toda.
          '  var anc=bx.querySelector(".fhdcampo") || bx.querySelector(".cbwrap");\n'
          '  if(anc && anc.parentNode && anc.parentNode.parentNode) anc=anc.parentNode;\n'
          '  if(!anc || !anc.parentNode) return;\n'
          '  var d=document.createElement("div");\n'
          '  d.className="semorc";\n'
          '  d.textContent="esta carta já está no teto — não há progressão '
          "para distribuir\";\n"
          '  anc.parentNode.insertBefore(d, anc.nextSibling);\n'
          ' }\n'
          # ---- 20 · o impeto +5 que nao existe -----------------------------
          #  A sessao da transformacao mandou em 16/08: "nao existe impeto nivel
          #  5; o 5 e 2+3, dois impetos do mesmo nome empilhados". O `pimpNativos`
          #  daqui clona toda entrada +3 em +4 e +5 e casa com o clone ANTES de
          #  tentar o par — por isso o George Best saia "Conducao Tecnica +5"
          #  enquanto o motor dele diz "Conducao Tecnica +2 · Conducao Tecnica +3".
          #
          #  Medi as 2.785 cartas com o catalogo LIMPO (sem clone), procurando
          #  1, 2 ou 3 impetos de verdade que somem igual:
          #     24 cartas usam hoje um +4/+5 fabricado
          #     TODAS as 24 tem explicacao so com entradas reais do catalogo
          #     mas so 4 tem explicacao UNICA — as de soma 5 (2+3)
          #     as 20 de soma 4 aceitam 1+3 OU 2+2, e eu nao sei qual e
          #
          #  ⛔ Entao troco SO as 4 de explicacao unica. As 20 ambiguas ficam
          #  como estao e foram para a sessao da transformacao. Escolher uma das
          #  duas seria adivinhar.
          ' (function(){ var _pn=window.pimpNativos;\n'
          '  if(typeof _pn!=="function" || typeof CAT==="undefined") return;\n'
          '  function sg(e){ var o={},k; for(k=0;k<e.length;k++)\n'
          '   o[e[k][0]]=(o[e[k][0]]||0)+e[k][1]; return o; }\n'
          '  function ig(a,b){ var x=Object.keys(a), y=Object.keys(b), k;\n'
          '   if(x.length!==y.length) return false;\n'
          '   for(k=0;k<x.length;k++) if(b[x[k]]!==a[x[k]]) return false;\n'
          '   return true; }\n'
          '  var PN=null, PS=null;\n'
          '  window.pimpNativos=function(c){\n'
          '   var r=_pn(c); if(!r) return r;\n'
          '   var temFake=false, i, j;\n'
          '   for(i=0;i<r.length;i++) if(/\\+[45]$/.test(r[i].nome)) temFake=true;\n'
          '   if(!temFake) return r;\n'
          '   try{\n'
          '    if(!PN){ PN=[]; PS=[];\n'
          '     for(i=0;i<CAT.length;i++){ PN.push(CAT[i]); PS.push(sg(CAT[i][2])); } }\n'
          '    var nm=(c&&c.nm)||[], d={};\n'
          '    for(i=0;i<nm.length;i++) d[nm[i][0]]=(d[nm[i][0]]||0)+nm[i][1];\n'
          '    var achou=[];\n'
          '    for(i=0;i<PN.length;i++) for(j=i;j<PN.length;j++){\n'
          '     var t={}, x;\n'
          '     for(x in PS[i]) t[x]=PS[i][x];\n'
          '     for(x in PS[j]) t[x]=(t[x]||0)+PS[j][x];\n'
          '     if(ig(t,d)) achou.push([i,j]);\n'
          '    }\n'
          '    if(achou.length===1){ var a=achou[0];\n'
          '     return [{nome:PN[a[0]][0], efeito:PN[a[0]][2]},\n'
          '             {nome:PN[a[1]][0], efeito:PN[a[1]][2]}]; }\n'
          '   }catch(e){}\n'
          '   return r;\n'
          '  };\n'
          ' })();\n'
          #  ⚠️ o `pintaNotas` roda TRES vezes, e nao e desleixo: a ficha termina de
          #  desenhar DEPOIS do `reabrir`, e a primeira pintura era sobrescrita.
          #  Medido: a conta ja estava certa (degrau 2 dava 112,2 no Falso nove e
          #  99,2 no Centroavante fixo, batendo com a tela do Luis) — o que
          #  faltava era pintar de novo quando o desenho terminasse.
          ' function tudo(){ try{ poeBotao(); }catch(e){}\n'
          '                  try{ ordemEstavel(); }catch(e){}\n'
          '                  try{ pintaNotas(); }catch(e){}\n'
          '                  setTimeout(function(){ try{ pintaNotas(); }catch(e){} }, 80);\n'
          '                  setTimeout(function(){ try{ pintaNotas(); }catch(e){} }, 320);\n'
          '                  try{ travaMaximo(); }catch(e){}\n'
          '                  try{ botaoDoMotor(); }catch(e){}\n'
          '                  try{ acendeCampo(); }catch(e){}\n'
          '                  try{ boasOpcoes(); }catch(e){}\n'
          '                  try{ arrumaPool(); }catch(e){}\n'
          '                  try{ arrumaFisico(); }catch(e){}\n'
          '                  try{ travaDegrauDuvidoso(); }catch(e){}\n'
          '                  try{ avisaSemOrcamento(); }catch(e){}\n'
          '                  try{ especiais(); }catch(e){} }\n'
          ' ["abrir","reabrir","encModo"].forEach(function(n){\n'
          '  var o=window[n]; if(typeof o!=="function") return;\n'
          '  window[n]=function(){ var r=o.apply(this,arguments);\n'
          '   setTimeout(tudo,0); return r; };\n'
          ' });\n'
          ' setTimeout(tudo,400);\n'
          '})();\n</script>\n')

    k = html.rfind('</body>')
    if k < 0:
        k = len(html)
    return html[:k] + js + html[k:], 'entrou'


if __name__ == '__main__':
    # CONTINUO: regera sozinho a cada CICLO segundos, do lado do motor.
    # Fecha quando aparecer o PARAR.txt, igual aos outros processos da esteira.
    CICLO = int(os.environ.get('ENCAIXE_CICLO', '0') or 0)
    if CICLO <= 0:
        main()
    else:
        import time
        print('MODO CONTINUO: regerando a cada %d s. Fecha com o PARAR.txt.' % CICLO)
        print()
        while not os.path.exists('PARAR.txt'):
            try:
                main()
            except Exception as ex:
                print('tropecei: %s — tento de novo no proximo ciclo' % ex, flush=True)
            print('-' * 60, flush=True)
            time.sleep(CICLO)
        print('fechado.')
