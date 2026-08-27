# -*- coding: utf-8 -*-
r"""
SUBIR AS LINHAS AGORA — pega o encaixe da pasta e manda as linhas dele pro banco.

ORDEM DO LUIS, 17/08/2026:
    "Eu nao entendo por que essa complicacao toda. A gente so nao tem um HTML
     pronto aqui? Se so me da o HTML que vai pra internet, a gente acessa aqui
     no navegador pra poder ver."

    Ele estava certo. Eu tinha ido mexer no gera_encaixe.py — que e o
    encanamento para MANTER as linhas atualizadas — antes de entregar a coisa
    simples: o arquivo funcionando. Este programa e a parte simples.

O QUE ELE FAZ
    Le o encaixe\encaixe_v6_NOVO.html que ja esta na pasta, tira as linhas de
    dentro dele e manda todas para a tabela `tela_encaixe`. So isso.

    Depois disso o ENCAIXE-DO-BANCO.html tem o que mostrar.

⛔ NAO GERA NADA. Nao roda motor, nao recalcula, nao toca no encaixe.
⛔ NAO APAGA NADA. Tudo e upsert por carta+funcao. Rodar duas vezes nao duplica.
⛔ SO SOBE O QUE MUDOU (guarda a impressao digital de cada linha). A primeira
   vez sobe tudo; as seguintes sobem dezenas.

QUANDO RODAR
    Toda vez que o encaixe for gerado de novo e voce quiser que a versao da
    internet acompanhe. Se quiser que isso aconteca sozinho, o gera_encaixe.py
    ja sabe fazer — basta o SOBE-A-TELA.txt estar na pasta.
"""
import json, os, sys, io, time

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
sys.path.insert(0, AQUI)

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
except Exception:
    pass


def P(*a):
    print(*a, flush=True)


def pausa(msg='Enter para fechar...'):
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


ENCAIXE = os.path.join('encaixe', 'encaixe_v6_NOVO.html')

P('=' * 74)
P('  SUBIR AS LINHAS DO ENCAIXE PARA O BANCO')
P('=' * 74)

# ----------------------------------------------- 1. tirar as linhas do encaixe
P('')
P('[1/2] lendo o encaixe da pasta')
if not os.path.exists(ENCAIXE):
    P('   ⛔ nao achei o %s' % ENCAIXE)
    P('      Rode o COMECAR-TUDO.bat uma vez para ele ser gerado.')
    pausa(); sys.exit(1)

# ⛔ Mesma leitura do gera_encaixe.py (funcao le_D). Nao inventei outra: se o
#    formato mudar, os dois quebram junto em vez de um seguir com dado velho.
s = open(ENCAIXE, encoding='utf-8', errors='replace').read()
i = s.find('const D=')
if i < 0:
    i = s.find('const D =')
if i < 0:
    P('   ⛔ nao achei as linhas dentro do encaixe.')
    pausa(); sys.exit(1)
j = s.find('\n', i)
try:
    D = json.loads(s[s.find('[', i):j].rstrip().rstrip(';'))
except Exception as e:
    P('   ⛔ nao consegui ler as linhas: %s' % e)
    pausa(); sys.exit(1)

if not D:
    P('   ⛔ o encaixe esta SEM linhas dentro.')
    P('      Se voce ja trocou pelo ENCAIXE-DO-BANCO.html, o original')
    P('      continua sendo gerado pelo COMECAR-TUDO — e dele que sai daqui.')
    pausa(); sys.exit(1)

P('   %s linhas · o arquivo tem %.1f MB'
  % ('{:,}'.format(len(D)).replace(',', '.'), len(s.encode('utf-8')) / 1048576))
P('   %s cartas distintas · %d funcoes'
  % ('{:,}'.format(len({r.get('id') for r in D})).replace(',', '.'),
     len({r.get('tipo') for r in D})))

# ------------------------------------------------------------ 2. mandar
P('')
P('[2/2] mandando para a tabela tela_encaixe')
try:
    import sobe_a_tela as st
except Exception as e:
    P('   ⛔ nao achei o sobe_a_tela.py nesta pasta: %s' % e)
    pausa(); sys.exit(1)

# ⛔ Este programa e AVULSO: o Luis clicou nele de proposito, entao ele sobe
#    mesmo sem o SOBE-A-TELA.txt (que e o interruptor do gera_encaixe).
st.LIGADO = True

t0 = time.time()
mandadas, falharam = st.sobe(D, diz=P)
gasto = time.time() - t0

P('')
P('=' * 74)
P('  ' + st.resumo().replace('\n', '\n  '))
P('')
P('  tempo: %d min %d s' % (gasto // 60, gasto % 60))
if falharam:
    P('')
    P('  ⛔ %d linhas nao subiram. Rode este programa de novo — ele tenta so' % falharam)
    P('     as que faltaram, nao recomeca do zero.')
else:
    P('')
    P('  ✅ Pronto. Agora abra o ENCAIXE-DO-BANCO.html.')
P('=' * 74)
pausa()
sys.exit(1 if falharam else 0)
