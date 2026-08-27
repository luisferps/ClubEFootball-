# -*- coding: utf-8 -*-
"""
GRAVA DIRETO NA TABELA — o motor escreve na `builds`, sem arquivo no meio.

ORDEM DO LUIS, 14/08/2026:
    "Essa tabela alimentar o motor, e o motor gerar OUTRA TABELA com as
     otimizacoes."

ORDEM DO LUIS, 17/08/2026 — a que mudou este arquivo:
    "Tem que fazer e salvar na hora."
    e, antes: "a gente vai esquecer o arquivo e ele nao vai subir."

COMO ERA (ate 17/08)
    O motor acumulava 50 linhas na MEMORIA antes de mandar. Se a janela fosse
    fechada no X, ou faltasse luz, ate 49 linhas prontas nunca chegavam ao
    banco — ficavam so no linhas.jsonl, que e exatamente o arquivo que a gente
    esquece.

COMO FICA
    LOTE = 1. Cada linha vai para o banco no instante em que fica pronta.
    Nao existe mais nada "em transito" na memoria.

⛔ O ARQUIVO NAO SOME. Ele continua sendo escrito, por dois motivos:
   1. o carrega_feitos() do motor le dele para saber o que ja rodou;
   2. e a copia de seguranca se a internet cair.

DE BRINDE, o lote de 1 conserta um defeito conhecido:
   Em 15/08 a tabela `funcoes` nao tinha o Falso nove. O banco recusava o lote
   INTEIRO de 50 por causa de UMA linha — 2.100 linhas presas, de 6 funcoes.
   Com lote de 1, uma linha ruim prende ela mesma e mais ninguem.

A INTERNET CAIDA NAO SEGURA O MOTOR
   Mandar linha a linha com timeout de 90 s significaria 90 s de espera POR
   LINHA se a rede caisse. Por isso existe o DISJUNTOR: 3 falhas de rede
   seguidas e o modulo para de tentar por 60 s e joga direto no pendente, sem
   esperar. Ele religa sozinho e o pendente sobe no proximo start do motor.

LIGA COM: o arquivo GRAVA-DIRETO.txt na pasta. Sem ele, nada muda.

A CHAVE sai do config.txt na hora de rodar. Nunca e gravada nem impressa aqui.
"""

# ===========================================================================
#  ⛔ 19/08 — ESTE PROGRAMA MORA NO ClubEfootball\programas.
#     "Nao existe mais essa pasta pro futebol. A pasta agora e ClubEfootball.
#      E tudo la." (Luis, 19/08)
#
#  ⛔ ESTE BLOCO VEM ANTES DOS IMPORTS, E POR MEDIDA. Quando ele ficava
#     DEPOIS, o `from equacao import ...` la de cima ja tinha rodado e pegava
#     o arquivo errado — o programa nem chegava a saber onde estava a casa.
#
#     Ele faz duas coisas, e as duas importam:
#       1. acha a pasta que tem o config.txt e trabalha LA (os dados nao se
#          mudaram: dados\, saida_v6\, encaixe\ continuam na casa);
#       2. poe `programas\` na frente do caminho de busca, para os modulos
#          vizinhos serem achados aqui e nao na raiz.
# ===========================================================================
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
if _CASA:
    if _os.path.abspath(_os.getcwd()) != _os.path.abspath(_CASA):
        _os.chdir(_CASA)
    if _CASA not in _sys.path:
        _sys.path.append(_CASA)          # a casa vem DEPOIS
if _MEU_LUGAR in _sys.path:
    _sys.path.remove(_MEU_LUGAR)
_sys.path.insert(0, _MEU_LUGAR)          # `programas` vem PRIMEIRO
# --------------------------------------------------------------------------
import json, os, time, atexit, urllib.request, urllib.error

# ⛔ 19/08 — a pasta dos DADOS e a CASA (a do config.txt), nao a

#    pasta deste arquivo. Ele mudou de lugar; os dados nao.

AQUI = _CASA or os.path.dirname(os.path.abspath(__file__))
LIGADO = os.path.exists(os.path.join(AQUI, 'GRAVA-DIRETO.txt'))
TABELA = 'builds'

# ⛔ 17/08 — LOTE = 1, ordem do Luis: "tem que fazer e salvar na hora".
#    NAO AUMENTAR. Qualquer numero maior que 1 volta a deixar linha pronta
#    parada na memoria, e foi isso que fez as 1.679 builds sumirem.
LOTE = 1

TIMEOUT = 20            # por linha. Curto de proposito: quem espera e o disjuntor.
TIMEOUT_LOTE = 90       # o reenvio em massa do pendente pode esperar mais
FALHAS_PARA_ABRIR = 3   # 3 falhas seguidas e o disjuntor abre
SEGUNDOS_ABERTO = 60    # ...e fica aberto este tanto antes de tentar de novo

PENDENTE = os.path.join(AQUI, 'grava_direto_PENDENTE.jsonl')

_fila = []
_cfg = {}
_conta = {'ok': 0, 'falha': 0, 'lotes': 0, 'disjuntor': 0}
_disj = {'seguidas': 0, 'aberto_ate': 0.0}


def _config():
    if _cfg:
        return _cfg
    p = os.path.join(AQUI, 'config.txt')
    if not os.path.exists(p):
        return {}
    for linha in open(p, encoding='utf-8'):
        linha = linha.strip()
        if linha and not linha.startswith('#') and '=' in linha:
            k, v = linha.split('=', 1)
            _cfg[k.strip()] = v.strip()
    return _cfg


def _texto_impeto(v):
    if not v:
        return None
    if isinstance(v, list):
        itens = [str(x) for x in v if x]
        return ' - '.join(itens) if itens else None
    return str(v)


def _linha(x, motor_versao, versao):
    return {
        'motor_versao': motor_versao,
        'card_id': str(x['card_id']), 'funcao': x['funcao'], 'b1': x.get('b1'),
        'barras': x.get('barras'), 'vals': x.get('vals'),
        'impeto': _texto_impeto(x.get('impeto')),
        'tecnico': x.get('tecnico'),
        # ⛔ 14/08: o ID do tecnico vai junto. Sao 5 "Jose Mourinho" diferentes;
        # so o nome nao diz qual entrou na build.
        'tecnico_id': x.get('tecnico_id'),
        'habilidades': x.get('habilidades'), 'cadeia': x.get('cadeia'),
        'vals_carta': x.get('vals_carta'), 'vals_tela': x.get('vals_tela'),
        'buff': x.get('buff'), 'cond': x.get('cond'),
        'origem': x.get('origem'), 'estilo': x.get('estilo'),
        'segundos': x.get('segundos'), 'rodado_em': x.get('quando'),
        'versao': versao, 'insumos': x.get('insumos'),
    }


def _manda(linhas, timeout=None):
    cfg = _config()
    URL = cfg.get('SUPABASE_URL', '').rstrip('/')
    KEY = cfg.get('SUPABASE_KEY', '')
    if not URL or not KEY:
        return False, 'config.txt sem URL ou chave'
    corpo = json.dumps(linhas, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        '%s/rest/v1/%s?on_conflict=card_id,funcao' % (URL, TABELA), data=corpo,
        headers={'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
                 'Content-Type': 'application/json',
                 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=(timeout or TIMEOUT)) as r:
            r.read()
        return True, None
    except urllib.error.HTTPError as e:
        # ⚠️ HTTP e o banco RESPONDENDO e recusando — nao e rede caida.
        #    Nao conta para o disjuntor: tentar de novo nao vai adiantar, e
        #    abrir o disjuntor por causa disso pararia de subir o que esta bom.
        return False, 'HTTP %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:200])
    except Exception as e:
        return False, 'REDE: %s' % str(e)[:200]


def _guarda(linhas, motivo):
    """Linha que nao subiu NAO se perde: vai para o pendente, com o motivo."""
    try:
        with open(PENDENTE, 'a', encoding='utf-8') as f:
            for l in linhas:
                f.write(json.dumps({'motivo': motivo, 'linha': l},
                                   ensure_ascii=False) + '\n')
    except Exception:
        pass


def junta(x, motor_versao, versao):
    """Chamado pelo motor a cada linha pronta. Com LOTE=1 ela sobe AGORA."""
    if not LIGADO:
        return
    _fila.append(_linha(x, motor_versao, versao))
    if len(_fila) >= LOTE:
        descarrega()


def descarrega():
    """Manda o que estiver acumulado. Com LOTE=1 e sempre uma linha so."""
    if not LIGADO or not _fila:
        return
    lote = list(_fila)
    del _fila[:]

    # ---- DISJUNTOR: rede caida nao segura o motor
    agora = time.time()
    if agora < _disj['aberto_ate']:
        _conta['falha'] += len(lote)
        _conta['disjuntor'] += len(lote)
        _guarda(lote, 'REDE: disjuntor aberto (sobe no proximo start do motor)')
        return

    ok, erro = _manda(lote)
    _conta['lotes'] += 1
    if ok:
        _conta['ok'] += len(lote)
        _disj['seguidas'] = 0
        return

    _conta['falha'] += len(lote)
    _guarda(lote, erro)
    if erro and erro.startswith('REDE'):
        _disj['seguidas'] += 1
        if _disj['seguidas'] >= FALHAS_PARA_ABRIR:
            _disj['aberto_ate'] = time.time() + SEGUNDOS_ABERTO
            _disj['seguidas'] = 0
            print('   [grava_direto] rede fora. Vou parar de tentar por %ds e '
                  'guardar no pendente — o motor NAO para.' % SEGUNDOS_ABERTO,
                  flush=True)
            return
    else:
        _disj['seguidas'] = 0
    print('   [grava_direto] linha nao subiu (%s). Guardada em %s'
          % (erro, os.path.basename(PENDENTE)), flush=True)


def resumo():
    if not LIGADO:
        return 'grava direto: DESLIGADO (crie o GRAVA-DIRETO.txt para ligar)'
    txt = ('grava direto: %d linhas na tabela %s · %d falharam · lote de %d'
           % (_conta['ok'], TABELA, _conta['falha'], LOTE))
    if _conta['disjuntor']:
        txt += ' · %d guardadas com a rede fora' % _conta['disjuntor']
    if _conta['falha']:
        txt += '\n   as que falharam estao em %s e sobem sozinhas no proximo start' \
               % os.path.basename(PENDENTE)
    return txt

# ===========================================================================
# REENVIO AUTOMATICO DO PENDENTE — 15/08/2026
#
# ORDEM DO LUIS (regra n1): "quem vai fazer e voce. Toda vez eu tenho que pedir
# pra voce fazer os trem". Entao o pendente nao espera clique de ninguem: toda
# vez que o motor sobe, ele tenta mandar de novo o que ficou para tras.
#
# O CASO QUE FEZ ISTO EXISTIR: a tabela `funcoes` nao tinha o Falso nove (a 19a,
# criada em 12/08). O banco recusava o lote INTEIRO de 50 por causa de UMA linha
# de Falso nove — 2.100 linhas presas, de 6 funcoes diferentes. Resolvido no
# banco em 15/08; sem este reenvio, as 2.100 ficariam paradas para sempre.
#
# 17/08: com LOTE=1 na rodada, esse tipo de contagio nao acontece mais. Aqui no
# reenvio em massa o lote continua 50, de proposito — sao linhas ja paradas, e
# em massa vale a velocidade. Se um lote de 50 falhar, os 50 voltam ao pendente.
# ===========================================================================
def reenvia_pendentes(silencioso=True):
    """Tenta subir de novo o que esta no PENDENTE. O que subir sai do arquivo."""
    if not os.path.exists(PENDENTE):
        return 0, 0
    itens = []
    try:
        for l in open(PENDENTE, encoding='utf-8'):
            if l.strip():
                try: itens.append(json.loads(l))
                except Exception: pass
    except Exception:
        return 0, 0
    linhas = [x.get('linha') for x in itens if x.get('linha')]
    if not linhas:
        return 0, 0
    if not silencioso:
        print('[grava_direto] tentando reenviar %d linhas paradas...' % len(linhas), flush=True)
    subiu, ficou = 0, []
    for i in range(0, len(linhas), 50):
        lote = linhas[i:i + 50]
        ok, erro = _manda(lote, timeout=TIMEOUT_LOTE)
        if ok:
            subiu += len(lote)
        else:
            for l in lote:
                ficou.append({'motivo': erro, 'linha': l})
    try:
        if ficou:
            with open(PENDENTE, 'w', encoding='utf-8') as f:
                for x in ficou:
                    f.write(json.dumps(x, ensure_ascii=False) + '\n')
        else:
            os.remove(PENDENTE)
    except Exception:
        pass
    if subiu:
        print('[grava_direto] reenviadas %d linhas que estavam paradas%s'
              % (subiu, (' — %d ainda presas' % len(ficou)) if ficou else ' (o pendente zerou)'),
              flush=True)
    return subiu, len(ficou)


# ===========================================================================
# CINTO E SUSPENSORIO — 17/08
# Com LOTE=1 a fila esta sempre vazia, entao isto nunca deveria ter o que fazer.
# Fica registrado assim mesmo: se alguem um dia mexer no LOTE, o que estiver na
# memoria vai para o pendente em vez de sumir. Custa nada e cobre o erro humano.
# ===========================================================================
def _no_fim():
    try:
        if _fila:
            _guarda([dict(x) for x in _fila], 'saida do motor com fila na memoria')
            del _fila[:]
    except Exception:
        pass


# ---- roda uma vez, quando o motor sobe
if LIGADO:
    atexit.register(_no_fim)
    try:
        reenvia_pendentes()
    except Exception:
        pass
