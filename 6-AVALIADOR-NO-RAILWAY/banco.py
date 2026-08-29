# -*- coding: utf-8 -*-
"""
BANCO — a unica porta do servico para o Supabase.

Le a regua por UMA chamada: public.otimizador_regua_v1(), que so o service_role pode
executar. Nenhuma tabela de segredo fica exposta: quem nao tem a chave secreta
(que mora so nas variaveis do Railway) nao le nada.

⛔ A chave nunca e impressa, nunca vai para log, nunca volta numa resposta.
"""
import os, json, urllib.request, urllib.error

class BancoIndisponivel(Exception):
    pass

URL    = (os.environ.get('SUPABASE_URL') or '').rstrip('/')
SECRET =  os.environ.get('SUPABASE_SECRET') or os.environ.get('SUPABASE_SERVICE_KEY') or ''


def _post(caminho, corpo=None, timeout=30):
    if not URL or not SECRET:
        raise BancoIndisponivel('faltam as variaveis SUPABASE_URL e SUPABASE_SECRET')
    dados = json.dumps(corpo or {}).encode('utf-8')
    req = urllib.request.Request(URL + caminho, data=dados, method='POST', headers={
        'apikey': SECRET, 'Authorization': 'Bearer ' + SECRET,
        'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise BancoIndisponivel('o banco respondeu %s' % e.code)
    except Exception as e:
        raise BancoIndisponivel('nao consegui falar com o banco: %s' % type(e).__name__)


def pacote_da_regua():
    return _post('/rest/v1/rpc/otimizador_regua_v1')


def carta_para_simular(card_id):
    """O que a ficha precisa da carta — e SO isso. Sem alvo, sem peso, sem molde."""
    j = _post('/rest/v1/rpc/otimizador_carta_v1', {'p_card_id': str(card_id)})
    if not j:
        return None
    atributos = sorted(j.get('atributos') or [], key=lambda x: int(x['indice_otimizador']))
    habilidades = j.get('habilidades') or []
    impetos = j.get('impetos') or []
    gate = j.get('gate') or {}
    return {
        'card_id': str(j.get('card_id')),
        'atributos': [x.get('valor') for x in atributos],
        'orcamento': (j.get('escalares') or {}).get('orcamento'),
        'habilidades_fixas': [int(x['skill_id']) for x in habilidades],
        'vagas_livres': sum(1 for x in impetos if x.get('vaga')),
        'gate': gate,
        'pronto_motor_otimizacao': bool(gate.get('pode_rodar')),
    }


def pool_da_funcao(card_id, funcao_id):
    """As habilidades que a carta pode receber NAQUELA funcao.

    ⛔ 25/08 — POR QUE ESTA FUNCAO EXISTE.
    A validacao do servico usava `habilidades_possiveis` da carta_para_simular,
    que sai de clube.carta_habilidade (relacao='espaco') — uma lista POR CARTA.
    Com ela, o /avaliar RECUSAVA as builds que o proprio motor tinha feito: das
    4 builds gravadas que tentamos reproduzir, as 4 voltaram HTTP 400 "esta
    carta nao aceita", citando habilidades que o motor pos.

    O pool do motor e POR FUNCAO. Prova: numa carta so (89130772077328) ele
    varia de 22 a 30 conforme a funcao — 8 tamanhos distintos em 10 funcoes.
    E a medida que fecha o caso: das 6.000 habilidades usadas em builds nao
    marcadas para recalcular, 6.000 de 6.000 estao no pool da propria build.
    ZERO fora. O motor nunca escolheu errado; a validacao e que conferia contra
    a lista errada.

    O que volta daqui e o pool que a rodada REALMENTE usou (gravado em
    clube.build.falta_pool), nao uma formula deduzida. Se a build daquela funcao
    ainda nao existir, volta None e quem chamou cai na lista da carta.
    """
    r = _post('/rest/v1/rpc/otimizador_pool_habilidades_v1',
              {'p_card_id': str(card_id), 'p_funcao_id': int(funcao_id)})
    if not r or not (r.get('gate') or {}).get('pode_rodar'):
        return None
    return [int(x) for x in (r.get('skill_ids') or [])]
