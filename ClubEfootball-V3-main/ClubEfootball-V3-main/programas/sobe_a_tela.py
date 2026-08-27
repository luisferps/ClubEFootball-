# -*- coding: utf-8 -*-
r"""
SOBE AS LINHAS DA TELA — o encaixe deixa de carregar os dados dentro dele.

ORDEM DO LUIS, 17/08/2026:
    "A unica diferenca e essa. Esse jogar os dados e levar eles junto com o
     arquivo do encaixe — a gente vai pegar esses mesmos dados do banco de
     dados, online. So isso. O restante dele nao toca, e pra ficar do jeito
     que esta: o design, os trem tudo."

O QUE SAO "AS LINHAS DA TELA"
    A lista pronta que o encaixe mostra: uma linha por carta x funcao, com os
    53 campos que aparecem. Sao 12.370 linhas, e sao elas que fazem o arquivo
    do encaixe ter 39,1 MB (a casca sozinha tem 3,0 MB).

POR QUE ESTE ARQUIVO EXISTE, EM VEZ DE EU REESCREVER A MONTAGEM
    Quem monta essas linhas e o gera_encaixe.py, e ele ja monta certo — com as
    travas dele, inclusive a que PARA tudo se sobrar ponto de barra. Reescrever
    essa montagem em outro lugar criaria a segunda verdade que este sistema
    inteiro esta tentando acabar. Entao aqui nao se monta nada: recebe pronto
    e manda.

DUAS ETAPAS, DE PROPOSITO
    ETAPA 1 (esta):  as linhas SOBEM para o banco. O arquivo do encaixe continua
                     exatamente como esta, com as linhas dentro. Nada muda para
                     o Luis. Serve para conferir que chegaram certas.
    ETAPA 2 (depois): o arquivo passa a buscar as linhas no banco e sai sem elas.

LIGA COM: o arquivo SOBE-A-TELA.txt na pasta do sistema. Sem ele, nada acontece
    e o gera_encaixe segue igual. Mesmo padrao do GRAVA-DIRETO.txt.

⛔ SO SOBE O QUE MUDOU. O gera_encaixe roda a cada 300 segundos; mandar 36 MB
   a cada cinco minutos seria inviavel. Guarda a impressao digital de cada
   linha e manda so as diferentes. A primeira rodada sobe tudo; as seguintes
   sobem dezenas.

A CHAVE sai do config.txt na hora de rodar. Nunca e impressa nem gravada aqui.
"""
import json, os, sys, time, hashlib, urllib.request, urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))


def _acha_a_casa(inicio):
    p = inicio
    for _ in range(4):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None


CASA = _acha_a_casa(AQUI) or AQUI
TABELA = 'tela_encaixe'
LOTE = 100                 # ~290 KB por requisicao, medido
TIMEOUT = 120
LIGADO = os.path.exists(os.path.join(CASA, 'SOBE-A-TELA.txt'))

# ⛔ ETAPA 2 — enquanto este arquivo NAO existir, o encaixe continua saindo com
#    as linhas dentro. E o interruptor que separa "sobe" de "sobe e tira".
SEM_DADOS = os.path.exists(os.path.join(CASA, 'TELA-SEM-DADOS.txt'))

IMPRESSOES = os.path.join(CASA, 'dados', 'sobe_a_tela_impressoes.json')
PENDENTE = os.path.join(CASA, 'sobe_a_tela_PENDENTE.jsonl')

_conta = {'iguais': 0, 'mandadas': 0, 'falharam': 0, 'lotes': 0}
_cfg = {}


def _config():
    if _cfg:
        return _cfg
    p = os.path.join(CASA, 'config.txt')
    if not os.path.exists(p):
        return {}
    for linha in open(p, encoding='utf-8'):
        linha = linha.strip()
        if linha and not linha.startswith('#') and '=' in linha:
            k, v = linha.split('=', 1)
            _cfg[k.strip()] = v.strip()
    return _cfg


# ⛔ 18/08 (noite) — A FORCA DA LINHA VAI JUNTO.
#    Ordem do Luis: "isso ai voce tem que fazer alguma coisa no banco de dados
#    que ja identifica com os dados atuais qual e o maior, e pronto."
#    Sem isso a tela so sabe quem e o maior de uma funcao DEPOIS de baixar as
#    17 mil linhas — e ate la cada usuario ve uma porcentagem diferente.
#    `forca` e o Bloco 1 normalizado (b1n), o termo que manda na nota; os bonus
#    somam de -2 a +4 em cima dele. Pedindo as 2.000 linhas de maior forca
#    ANTES de tudo, o topo de cada funcao ja nasce certo na primeira pintura.
VERSAO_DO_ENVIO = 'v2-forca'   # muda a impressao digital: forca um reenvio unico


def _digital(obj):
    """A impressao digital da linha. Chaves ordenadas para o mesmo conteudo dar
    sempre o mesmo numero, independente da ordem em que o dicionario foi montado."""
    return hashlib.md5(
        (VERSAO_DO_ENVIO + json.dumps(obj, ensure_ascii=False, sort_keys=True)).encode('utf-8')
    ).hexdigest()


def _le_impressoes():
    try:
        with open(IMPRESSOES, encoding='utf-8') as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _grava_impressoes(d):
    try:
        os.makedirs(os.path.dirname(IMPRESSOES), exist_ok=True)
        # ⛔ newline='' — no Windows o modo texto troca \n por \r\n. Aqui nao
        #    muda nada funcional, mas ja derrubou uma trava de md5 hoje (o
        #    dados/molde.json). Fica explicito.
        with open(IMPRESSOES, 'w', encoding='utf-8', newline='') as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass


def _manda(linhas):
    cfg = _config()
    URL = cfg.get('SUPABASE_URL', '').rstrip('/')
    KEY = cfg.get('SUPABASE_KEY', '')
    if not URL or not KEY:
        return False, 'config.txt sem URL ou chave'
    req = urllib.request.Request(
        '%s/rest/v1/%s?on_conflict=card_id,funcao' % (URL, TABELA),
        data=json.dumps(linhas, ensure_ascii=False).encode('utf-8'),
        headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json',
                 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            r.read()
        return True, None
    except urllib.error.HTTPError as e:
        det = ''
        try:
            det = e.read().decode('utf-8', 'ignore')[:250]
        except Exception:
            pass
        return False, 'HTTP %s: %s' % (e.code, det)
    except Exception as e:
        return False, 'REDE: %s' % str(e)[:200]


def _guarda(linhas, motivo):
    """Linha que nao subiu NAO se perde."""
    try:
        with open(PENDENTE, 'a', encoding='utf-8') as f:
            for l in linhas:
                f.write(json.dumps({'motivo': motivo, 'linha': l},
                                   ensure_ascii=False) + '\n')
    except Exception:
        pass


def sobe(D, diz=print):
    """Recebe as linhas da tela PRONTAS e manda para o banco. Nao monta nada.

    Devolve (mandadas, falharam). Nunca levanta excecao: se o banco estiver
    fora, o encaixe tem que ser gerado do mesmo jeito."""
    if not LIGADO:
        return 0, 0
    if not D:
        diz('   [tela] nao veio linha nenhuma — nao mexi no banco.')
        return 0, 0

    velhas = _le_impressoes()
    novas = {}
    manda = []
    for r in D:
        try:
            cid = str(r.get('id') or '')
            fun = r.get('tipo') or ''
            if not cid or not fun:
                continue
            chave = cid + '|' + fun
            dig = _digital(r)
            novas[chave] = dig
            if velhas.get(chave) == dig:
                _conta['iguais'] += 1
                continue
            try:
                _f = float(r.get('b1n'))
            except Exception:
                _f = None
            manda.append({'card_id': cid, 'funcao': fun, 'linha': r, 'forca': _f,
                          'gerado_em': time.strftime('%Y-%m-%dT%H:%M:%S')})
        except Exception:
            continue

    diz('   [tela] %d linhas · %d iguais (nao sobem) · %d para mandar'
        % (len(D), _conta['iguais'], len(manda)))
    if not manda:
        _grava_impressoes(novas)
        return 0, 0

    subiram = set()
    for i in range(0, len(manda), LOTE):
        lote = manda[i:i + LOTE]
        ok, erro = _manda(lote)
        _conta['lotes'] += 1
        if ok:
            _conta['mandadas'] += len(lote)
            for x in lote:
                subiram.add(x['card_id'] + '|' + x['funcao'])
        else:
            _conta['falharam'] += len(lote)
            _guarda(lote, erro)
            diz('   [tela] ⛔ lote nao subiu (%s)' % erro)
            if 'does not exist' in (erro or '') or 'schema cache' in (erro or ''):
                diz('   [tela]    -> falta rodar o sql/28-as-linhas-da-tela.sql')
                break
        if (i // LOTE) % 10 == 9:
            diz('   [tela] %d de %d...' % (min(i + LOTE, len(manda)), len(manda)))

    # ⛔ A IMPRESSAO DIGITAL SO ENTRA DEPOIS DO BANCO ACEITAR.
    #    Se gravasse antes, um lote que falhou nunca mais seria tentado — o
    #    mesmo defeito do cursor de envio que escondeu 1.679 builds em 16/08.
    final = dict(velhas)
    for chave, dig in novas.items():
        if chave in subiram or velhas.get(chave) == dig:
            final[chave] = dig
    _grava_impressoes(final)

    return _conta['mandadas'], _conta['falharam']


def resumo():
    if not LIGADO:
        return ('tela no banco: DESLIGADO '
                '(crie o SOBE-A-TELA.txt na pasta para ligar)')
    t = ('tela no banco: %d linhas mandadas · %d iguais · %d falharam · %d lotes'
         % (_conta['mandadas'], _conta['iguais'], _conta['falharam'], _conta['lotes']))
    if _conta['falharam']:
        t += '\n   as que falharam estao em %s' % os.path.basename(PENDENTE)
    if SEM_DADOS:
        t += '\n   ETAPA 2 LIGADA: o arquivo do encaixe sai SEM as linhas dentro.'
    else:
        t += '\n   etapa 1: o arquivo do encaixe continua com as linhas dentro.'
    return t
