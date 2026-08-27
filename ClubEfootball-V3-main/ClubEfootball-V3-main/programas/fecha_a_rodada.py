# -*- coding: utf-8 -*-
r"""
FECHA A RODADA — o resultado do dia vira duas listas, e as duas perguntas
ficam SEPARADAS.

ORDEM DO LUIS, 18/08/2026:

    "A rodada diaria traz os resultados num arquivo. Voce desmembra ele e joga
     nas filas: as incompletas voltam na rodada do dia seguinte, e as completas
     vao pra fila dos motores."

E a correcao que ele fez logo em seguida, que e o coracao deste programa:

    "Se a pergunta for 'a ficha tem tudo que os dois motores leem', sabe o que
     vai acontecer? Ela vai pros motores, sobe pro sistema — e se ela tinha
     alguma coisa que os motores NAO leem, a gente nunca mais vai conseguir
     identificar isso. Ela vai continuar incompleta pra sempre."

⛔⛔ POR ISSO SAO DUAS PERGUNTAS, E ELAS NAO SE MISTURAM:

    1. PODE RODAR O MOTOR?    tem tudo que os dois motores leem
    2. A FICHA ESTA COMPLETA? tem tudo, ponto — inclusive o que motor nao le

    Uma carta pode responder SIM na 1 e NAO na 2. Nesse caso ela faz as duas
    coisas: vai para o motor E CONTINUA na fila de pendencias, sendo cobrada
    todo dia ate a ficha fechar. Uma nunca cancela a outra.

    Se fosse uma pergunta so, a carta que roda sairia da cobranca e o box, a
    data, a idade e a lesao dela nunca mais seriam perguntados a ninguem.

⛔ A FILA DE PRIORIDADE NAO E TOCADA AQUI. Ordem do Luis, 18/08:
    "a fila da prioridade tem que ser so aquelas que eu entro no meio e falo
     'coloca essas aqui na frente'."
   Conferido no roda_lote_v6.py: a fila_PRIORIDADE.json nao ACRESCENTA linha
   nenhuma — ela so REORDENA o que ja esta na fila normal. Entao escrever nela
   nao faria a linha rodar; so furaria a fila do Luis.

   O que faz a linha voltar a rodar e sair do "ja feito", e quem faz isso e o
   refazer_de_verdade.py. Este programa so entrega a ele a lista certa:
   PARA-REFAZER-AGORA.txt, ja com as cartas incompletas removidas.

⛔ SO `nao_sei` E BURACO. `zerado` e `nao_se_aplica` sao RESPOSTA.
⛔ NAO APAGA LINHA NENHUMA, nao mexe no banco, nao mexe no feitos.txt.
⛔ GUARDA HISTORICO. Cada rodada deixa a sua copia em logs\rodada\<data>\ —
   sem isso, descoberto um erro daqui a uma semana, nao ha como saber a partir
   de quando e quais cartas foram afetadas.
"""
import json, os, sys, io, time, shutil, collections

AQUI = os.path.dirname(os.path.abspath(__file__))


def acha_a_casa(inicio):
    p = inicio
    for _ in range(4):
        if os.path.exists(os.path.join(p, 'config.txt')):
            return p
        pai = os.path.dirname(p)
        if pai == p:
            break
        p = pai
    return None


CASA = acha_a_casa(AQUI)
if not CASA:
    print('PAREI: nao achei o config.txt nem aqui nem nas pastas de cima.')
    sys.exit(1)
os.chdir(CASA)

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass

SO_OLHAR = any(a.lower().startswith('confer') for a in sys.argv[1:])

BASE       = os.path.join('dados', 'base_unica.json')
RESULTADO  = 'RESULTADO-DA-RODADA.json'
PENDENCIAS = 'fila_PENDENCIAS.json'
REFAZER    = 'PRECISA-REFAZER.txt'
PARA_AGORA = 'PARA-REFAZER-AGORA.txt'

# ⛔ TIRADOS DOS PROPRIOS MOTORES, nao de lista escrita a mao.
#    motor.py ........ base · orc · fab · raras · falta · nm · sl
#    motor_bonus.py .. com · corpo · modelo · pe · pe_ruim
LE_O_MOTOR       = ['base', 'orc', 'fab', 'raras', 'falta', 'nm', 'sl']
LE_O_MOTOR_BONUS = ['com', 'corpo', 'modelo', 'pe', 'pe_ruim']
PRECISA_PRO_MOTOR = LE_O_MOTOR + LE_O_MOTOR_BONUS

AGORA = time.strftime('%Y-%m-%dT%H:%M:%S')
DIA = time.strftime('%Y-%m-%d_%Hh%M')


def P(*a):
    print(*a, flush=True)


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


P('=' * 78)
P('  FECHA A RODADA — as duas perguntas, separadas')
P('=' * 78)
P('')
P('  1. PODE RODAR O MOTOR?    tem tudo que os dois motores leem')
P('  2. A FICHA ESTA COMPLETA? tem tudo, inclusive o que motor nenhum le')
P('')
P('  Uma carta pode ir pro motor E continuar sendo cobrada. Uma nao cancela')
P('  a outra — foi ordem do Luis, e e o que impede a ficha de ficar furada')
P('  para sempre so porque a nota ja saiu.')
if SO_OLHAR:
    P('')
    P('  ⚠️ MODO CONFERIR: nada vai ser gravado.')

# ----------------------------------------------------------------- 1. a base
P('')
P('[1/4] lendo a base e a marca de cada campo')
if not os.path.exists(BASE):
    P('   ⛔ nao achei o %s' % BASE)
    pausa(); sys.exit(1)
B = json.load(open(BASE, encoding='utf-8'))
cards = B.get('cards') or []
P('   %s registros' % '{:,}'.format(len(cards)).replace(',', '.'))

# -------------------------------------------------------- 2. as duas contas
P('')
P('[2/4] respondendo as duas perguntas, uma de cada vez')

pode_rodar, nao_pode = [], []
ficha_ok, ficha_furada = [], []
falta_motor = collections.Counter()
falta_ficha = collections.Counter()
sem_marca = 0

for c in cards:
    cid = str(c.get('id') or '')
    if not cid:
        continue
    e = c.get('estado_de_cada_campo')
    if not isinstance(e, dict) or not e:
        # ⛔ carta sem marca NAO vira completa por omissao. Entra nas duas
        #    pendencias — no maximo se pergunta de novo, que e o lado barato.
        sem_marca += 1
        nao_pode.append(cid)
        ficha_furada.append({'card': cid, 'nome': c.get('nome'),
                             'ovr': c.get('ovr'), 'falta': ['(sem marca)']})
        continue

    # pergunta 1 — so o que os motores leem
    b_motor = [k for k in PRECISA_PRO_MOTOR if e.get(k) == 'nao_sei']
    if b_motor:
        nao_pode.append(cid)
        for k in b_motor:
            falta_motor[k] += 1
    else:
        pode_rodar.append(cid)

    # pergunta 2 — TUDO. Aqui entra box, data, idade, lesao, tier, votos...
    b_ficha = sorted(k for k, v in e.items() if v == 'nao_sei')
    if b_ficha:
        ficha_furada.append({'card': cid, 'nome': c.get('nome'),
                             'ovr': c.get('ovr'), 'falta': b_ficha})
        for k in b_ficha:
            falta_ficha[k] += 1
    else:
        ficha_ok.append(cid)

n = lambda x: '{:,}'.format(x).replace(',', '.')
P('')
P('   1. PODE RODAR O MOTOR')
P('      sim ... %s' % n(len(pode_rodar)))
P('      nao ... %s' % n(len(nao_pode)))
for k, q in falta_motor.most_common():
    dono = 'motor' if k in LE_O_MOTOR else 'bonus'
    P('         falta %-10s %6d   (%s)' % (k, q, dono))
P('')
P('   2. A FICHA ESTA COMPLETA')
P('      sim ... %s' % n(len(ficha_ok)))
P('      nao ... %s' % n(len(ficha_furada)))
for k, q in falta_ficha.most_common(14):
    marca = '  <- o motor le' if k in PRECISA_PRO_MOTOR else ''
    P('         falta %-24s %6d%s' % (k, q, marca))

# ⛔ ESTE E O NUMERO QUE O LUIS PEDIU PARA NAO SUMIR: quem ja pode rodar mas
#    continua com a ficha furada. Sem esta linha, sao exatamente estas cartas
#    que sairiam da cobranca sem ninguem ver.
prontos = set(pode_rodar)
furadas = {x['card'] for x in ficha_furada}
roda_e_furada = prontos & furadas
P('')
P('   ⚠️ RODAM MAS CONTINUAM FURADAS: %s cartas' % n(len(roda_e_furada)))
P('      elas vao para o motor E continuam na fila de pendencias.')

# ------------------------------------------- 3. quem mudou e ja pode rodar
P('')
P('[3/4] cruzando com quem mudou hoje')
mudou = []
if os.path.exists(REFAZER):
    for ln in open(REFAZER, encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if '|' in ln and not ln.startswith('#'):
            mudou.append(ln)
    P('   %s tem %s linhas' % (REFAZER, n(len(mudou))))
else:
    P('   sem %s — o a_volta_automatica nao rodou ou nao achou nada.' % REFAZER)

vai_rodar = [x for x in mudou if x.split('|', 1)[0] in prontos]
espera = [x for x in mudou if x.split('|', 1)[0] not in prontos]
P('   de carta que PODE RODAR .......... %s' % n(len(vai_rodar)))
P('   de carta que ainda nao pode ...... %s  (esperam a coleta)' % n(len(espera)))

# ------------------------------------------------------------- 4. gravar
P('')
P('[4/4] gravando')

resultado = {
    'o_que_e': 'o resultado da rodada, com as DUAS perguntas separadas',
    'ordem_do_luis': (
        '18/08: "se a pergunta for so o que os motores leem, a carta vai pro '
        'motor e a gente nunca mais identifica o que faltava nela". Por isso '
        'sao duas contas: pode_rodar e ficha_completa, e uma nao cancela a outra.'),
    'quando': AGORA,
    'le_o_motor': LE_O_MOTOR,
    'le_o_motor_bonus': LE_O_MOTOR_BONUS,
    'quantas': {
        'pode_rodar': len(pode_rodar),
        'nao_pode_rodar': len(nao_pode),
        'ficha_completa': len(ficha_ok),
        'ficha_furada': len(ficha_furada),
        'roda_mas_continua_furada': len(roda_e_furada),
        'linhas_para_refazer_agora': len(vai_rodar),
        'linhas_esperando_coleta': len(espera),
    },
    'falta_para_o_motor': dict(falta_motor),
    'falta_na_ficha': dict(falta_ficha),
    'pode_rodar': pode_rodar,
    'ficha_furada': ficha_furada,
    'roda_mas_continua_furada': sorted(roda_e_furada),
    'linhas_para_refazer_agora': vai_rodar,
    'linhas_esperando_coleta': espera,
}

if SO_OLHAR:
    P('   (modo conferir — nada gravado)')
else:
    with open(RESULTADO, 'w', encoding='utf-8', newline='') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)
    P('   %s' % RESULTADO)

    with open(PENDENCIAS, 'w', encoding='utf-8', newline='') as f:
        json.dump({'o_que_e': ('as cartas com a ficha furada. Voltam na coleta '
                               'de amanha, campo a campo, mesmo as que ja rodam.'),
                   'quando': AGORA, 'quantas': len(ficha_furada),
                   'cartas': ficha_furada}, f, ensure_ascii=False, indent=1)
    P('   %s  (%s cartas)' % (PENDENCIAS, n(len(ficha_furada))))

    # ⛔ A LISTA PARA O refazer_de_verdade.py. So carta que PODE RODAR.
    #    Linha de carta furada rodaria com dado faltando e gravaria nota errada
    #    — que e pior do que nao ter nota.
    with open(PARA_AGORA, 'w', encoding='utf-8', newline='') as f:
        f.write('# gerado pelo fecha_a_rodada.py em %s\n' % AGORA)
        f.write('# so linhas de carta que tem TUDO que os motores leem\n')
        for x in vai_rodar:
            f.write(x + '\n')
    P('   %s  (%s linhas)' % (PARA_AGORA, n(len(vai_rodar))))

    # ⛔ HISTORICO. Ordem do Luis: "se a gente descobre um erro la na frente e
    #    ele afetou um monte de cartas, sem log como e que a gente vai saber a
    #    partir de quando e quais foram afetadas?"
    try:
        pasta = os.path.join('logs', 'rodada', DIA)
        os.makedirs(pasta, exist_ok=True)
        shutil.copy2(RESULTADO, os.path.join(pasta, '90-RESULTADO-DA-RODADA.json'))
        shutil.copy2(PENDENCIAS, os.path.join(pasta, '91-fila_PENDENCIAS.json'))
        if os.path.exists(PARA_AGORA):
            shutil.copy2(PARA_AGORA, os.path.join(pasta, '92-PARA-REFAZER-AGORA.txt'))
        P('   historico em %s\\' % pasta)
    except Exception as e:
        P('   (nao consegui guardar o historico: %s)' % str(e)[:100])

P('')
P('=' * 78)
P('  O DIA, EM DUAS LINHAS')
P('=' * 78)
P('  MOTOR ... %s podem rodar · %s ainda nao' % (n(len(pode_rodar)), n(len(nao_pode))))
P('  FICHA ... %s completas   · %s furadas' % (n(len(ficha_ok)), n(len(ficha_furada))))
P('')
P('  %s cartas rodam E continuam sendo cobradas. E de proposito.' % n(len(roda_e_furada)))
P('=' * 78)
pausa()
sys.exit(0)
