# -*- coding: utf-8 -*-
"""
RODADA DIARIA - o sistema se alimenta sozinho, 1x por dia, meia-noite.

DECISAO DO LUIS - 14/08/2026
    "voce deixa a estrutura pronta e eu aviso quando vamos ligar ele pra rodar
     automaticamente. a minha ideia e concluir todos os cards que temos no banco
     hoje com suas respectivas linhas SEM NENHUM ERRO pra depois comecar a
     coletar e otimizar as novidades automaticamente"

Por isso este arquivo nasce com a ULTIMA ETAPA DESLIGADA.

    ETAPAS 1 a 6   coletar, unificar, conferir, subir, achar card novo, enfileirar
                   -> LIGADAS. Nenhuma delas roda o motor. Nenhuma delas apaga nada.

    ⚠️ A COLETA NAO E SO DE CARD. (Luis, 14/08/2026)
       A etapa 1 regrava o CATALOGO DE IMPETOS inteiro (efscout_boosters.json).
       Por isso impeto NOVO entra sozinho: no dia em que o efScout catalogar,
       a rodada pega, e o card que estava "orfao" se resolve sem ninguem pedir.

    ⚠️ FONTE EM BRANCO NAO E RESPOSTA — E VALE PARA TUDO. (Luis, 14/08/2026)
       "Nao e so o impeto nao, e TUDO. As habilidades tambem podem ser
        alteradas, tudo que a gente precisar de insumo, tecnicos, tudo."
       Insumo que nenhuma fonte respondeu NAO vira "esse card nao tem" — vira
       "hoje eu nao sei", e a etapa 5d pergunta de novo amanha, todo dia, ate
       alguma fonte responder ou o Luis conferir no jogo (CONFERIDO.json).

    ETAPA 7        RODAR O MOTOR nos cards novos
                   -> DESLIGADA. So liga quando existir, nesta pasta, um arquivo
                      chamado  LIGAR-MOTOR-AUTOMATICO.txt
                      Sem esse arquivo o motor NAO e chamado. Os cards novos ficam
                      esperando na FRENTE da fila, prontos pra quando voce mandar.

    ETAPA 8        regerar o Encaixe e espelhar
                   -> LIGADA.

    ETAPA 9        gerar o PAINEL.html de acompanhamento
                   -> LIGADA.

REGRA DESTE ARQUIVO
    Se uma etapa falhar, ele AVISA e SEGUE nas outras. Nunca aborta tudo por causa
    de uma. No fim escreve o relatorio em  ULTIMA-RODADA.txt  e acrescenta uma
    linha no historico  RODADA-DIARIA-LOG.txt.

    Nao apaga nada. Nao mexe no molde. Nao mexe no banco alem do upsert da
    cards_base, que ja era o que o SUBIR-BASE fazia.
"""
import os, sys, io, json, time, subprocess, datetime, shutil, threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
AQUI = os.path.dirname(os.path.abspath(__file__))


def acha_a_pasta_do_sistema(inicio):
    """⛔ 17/08 — Este programa mora em ClubEfootball\\programas\\, mas TRABALHA
    na pasta do sistema (a que tem o config.txt, o dados\\ e os programas do
    motor). Sobe as pastas ate achar e muda o diretorio para la.

    Ordem do Luis, 17/08: "eu ja pedi pra colocar todos os arquivos que a gente
    vai utilizar pra fazer isso funcionar numa pasta so". O arquivo vai para a
    pasta oficial; o lugar onde ele trabalha continua o mesmo.

    Mesmo padrao do do_banco.py, do sobe_a_tela.py e do o_vigia.py."""
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
AQUI = CASA        # o resto do programa usa AQUI como "a pasta do sistema"

CHAVE_MOTOR = 'LIGAR-MOTOR-AUTOMATICO.txt'
LOG         = 'RODADA-DIARIA-LOG.txt'
ULTIMA      = 'ULTIMA-RODADA.txt'
TRAVA       = 'RODADA-DIARIA-RODANDO.txt'

linhas  = []
oks     = 0
falhas  = 0
pulados = 0


def diz(t=''):
    print(t, flush=True)
    linhas.append(t)


def agora():
    return datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')


# ============================================================================
#  O LOG DE CADA PASSO — 18/08/2026
# ============================================================================
#  ORDEM DO LUIS, 18/08: "nao esquecer de guardar log de cada um desses
#  processos, pro caso de dar erro a gente saber onde consertar."
#
#  ⛔ O QUE FALTAVA: o ULTIMA-RODADA.txt so guardava o CABECALHO de cada passo
#     e o [OK]/[XX]. O que cada programa IMPRIMIU ia para a tela e sumia quando
#     a janela fechava. Quando o passo 5h falhou em 17/08 23:34, a razao
#     ("campo visto_na_casca sem regra") so existiu na tela — se o Luis nao
#     tivesse colado aqui, ninguem saberia por que a fila nao foi refeita.
#
#  AGORA cada passo escreve o proprio arquivo em:
#       logs\rodada\AAAA-MM-DD_HHhMM\NN-nome-do-passo.txt
#
#  ⛔ CONTINUA APARECENDO NA TELA AO VIVO. Nao adianta guardar tudo e o Luis
#     ficar olhando janela parada por 12 horas de motor. Cada linha vai para os
#     dois lugares no mesmo instante.
#  ⛔ O TEMPO E CONTADO MESMO QUE O PROGRAMA NAO IMPRIMA NADA. Quem espera e a
#     rodada, num relogio proprio — programa travado sem imprimir tambem morre
#     no prazo.
PASTA_LOG = os.path.join('logs', 'rodada',
                         datetime.datetime.now().strftime('%Y-%m-%d_%Hh%M'))
_n_passo = [0]


def _limpa_logs_velhos(quantos_ficam=30):
    """Guarda as ultimas 30 rodadas. Log que ninguem apaga vira disco cheio."""
    try:
        raiz = os.path.join('logs', 'rodada')
        if not os.path.isdir(raiz):
            return
        pastas = sorted(d for d in os.listdir(raiz)
                        if os.path.isdir(os.path.join(raiz, d)))
        for d in pastas[:-quantos_ficam]:
            shutil.rmtree(os.path.join(raiz, d), ignore_errors=True)
    except Exception:
        pass


def _nome_de_arquivo(titulo):
    t = ''.join(ch if (ch.isalnum() or ch in ' .-_') else '' for ch in titulo)
    return t.strip().replace(' ', '-')[:60] or 'passo'


def roda(titulo, script, minutos=90, obrigatorio_existir=True):
    """Roda um script python desta pasta. Nunca deixa a rodada morrer.

    Tudo que o programa imprime vai para a TELA e para o LOG do passo, ao
    mesmo tempo. Se ele falhar, as ultimas linhas do que ele disse entram no
    relatorio da rodada — que e onde alguem vai procurar amanha."""
    global oks, falhas, pulados
    diz()
    diz('-' * 68)
    diz('  ' + titulo)
    diz('-' * 68)
    _arq = script[0] if isinstance(script, list) else script
    if not os.path.exists(_arq):
        diz('  [--] %s  (PULADO - o arquivo %s nao esta nesta pasta)' % (titulo, _arq))
        pulados += 1
        return False

    _n_passo[0] += 1
    try:
        os.makedirs(PASTA_LOG, exist_ok=True)
    except Exception:
        pass
    arq_log = os.path.join(PASTA_LOG, '%02d-%s.txt'
                           % (_n_passo[0], _nome_de_arquivo(titulo)))

    t0 = time.time()
    ultimas = []          # as ultimas linhas, para o relatorio quando falha
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable] + (script if isinstance(script, list) else [script]),
            cwd=AQUI, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=1, universal_newlines=True, encoding='utf-8',
            errors='replace',
            env=dict(os.environ, PYTHONUTF8='1', PYTHONUNBUFFERED='1',
                     PYTHONDONTWRITEBYTECODE='1'))

        def bombeia():
            try:
                with open(arq_log, 'w', encoding='utf-8', errors='replace') as f:
                    f.write('%s\n%s\n%s\n\n' % ('=' * 68, titulo, agora()))
                    for linha in proc.stdout:
                        try:
                            print(linha, end='', flush=True)
                        except Exception:
                            pass
                        # ⛔ 18/08 — FLUSH. Sem ele o Windows segura a saida no
                        #    buffer e o log parece PARADO enquanto o programa
                        #    trabalha. Medido hoje: o log do motor congelou as
                        #    06:41 e o linhas.jsonl continuou crescendo ate as
                        #    15:26 — 8h30 de trabalho invisivel. Eu mesmo li o
                        #    log e disse ao Luis que tinha travado. Nao tinha.
                        f.write(linha); f.flush()
                        ultimas.append(linha.rstrip('\n'))
                        if len(ultimas) > 25:
                            del ultimas[0]
            except Exception:
                pass

        t = threading.Thread(target=bombeia, daemon=True)
        t.start()
        proc.wait(timeout=minutos * 60)
        t.join(timeout=20)
        seg = int(time.time() - t0)
        if proc.returncode == 0:
            diz('  [OK] %s  (%d min %d s)' % (titulo, seg // 60, seg % 60))
            diz('       log: %s' % arq_log)
            oks += 1
            return True
        diz('  [XX] FALHOU: %s  (codigo %s)' % (titulo, proc.returncode))
        diz('       log: %s' % arq_log)
        # ⛔ AS ULTIMAS LINHAS ENTRAM NO RELATORIO. Sem isto, "FALHOU codigo 1"
        #    e tudo o que sobra amanha — e codigo 1 nao conserta nada.
        if ultimas:
            diz('       o que ele disse antes de parar:')
            for ln in ultimas[-8:]:
                diz('         | ' + ln[:150])
        diz('       Aviso e SIGO em frente. Nada do que ja foi feito se perde.')
        falhas += 1
        return False
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        diz('  [XX] ESTOUROU O TEMPO (%d min): %s' % (minutos, titulo))
        diz('       log: %s' % arq_log)
        if ultimas:
            diz('       ultima coisa que ele disse:')
            for ln in ultimas[-5:]:
                diz('         | ' + ln[:150])
        falhas += 1
        return False
    except Exception as e:
        diz('  [XX] ERRO: %s -> %s' % (titulo, e))
        falhas += 1
        return False


# ⛔ 18/08 — A EXCECAO DO DIA. Ela nao mexe em interruptor nenhum: so declara,
#    com data, o que a rodada de HOJE faz diferente. A rodada PERGUNTA aqui.
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import excecao_de_hoje as EXCECAO
except Exception:
    class EXCECAO(object):
        @staticmethod
        def vale(_d):
            return False


def quantas_linhas_faltam():
    """Quantas linhas da fila_v6 ainda NAO tem resultado no linhas.jsonl.

    ⛔ 18/08 — O BURACO QUE ISTO TAPA. A etapa 7 so ligava quando entrava CARD
       NOVO ou quando linha VOLTOU para a fila. Fila cheia de linha que nunca
       rodou nao contava para nada: o motor dizia "nada a rodar" e ia embora.
       Descoberto quando as posicoes compradas passaram a rodar as DUAS funcoes
       da familia: 8.393 linhas novas entraram na fila e nenhuma delas e "card
       novo" nem "linha devolvida". Sem esta conta, elas ficariam paradas para
       sempre e a rodada nao daria um pio.

    Le a mesma fonte que o motor considera verdade (saida_v6/linhas.jsonl).
    So conta; nao mexe em nada.
    """
    try:
        fila = json.load(open('fila_v6.json', encoding='utf-8'))
    except Exception:
        return 0
    feitos = set()
    try:
        with open('saida_v6/linhas.jsonl', encoding='utf-8') as f:
            for L in f:
                L = L.strip()
                if not L:
                    continue
                try:
                    r = json.loads(L)
                except Exception:
                    continue
                feitos.add('%s|%s' % (r.get('card_id') or r.get('card'), r.get('funcao')))
    except Exception:
        return len(fila)
    return sum(1 for r in fila
               if '%s|%s' % (r.get('card_id'), r.get('funcao')) not in feitos)


def ids_do_cards():
    """Os ids base que o sistema ja conhece."""
    try:
        c = json.load(open('dados/cards.json', encoding='utf-8'))
        return {str(x['id']).split('@')[0] for x in c}
    except Exception:
        return set()


# ======================================================================
#  A TRAVA - duas rodadas ao mesmo tempo estragariam a fila
# ======================================================================
if os.path.exists(TRAVA):
    try:
        idade = (time.time() - os.path.getmtime(TRAVA)) / 3600.0
    except Exception:
        idade = 0
    if idade < 12:
        print('Ja tem uma rodada diaria em andamento (ha %.1f h). Nao vou abrir outra.' % idade)
        raise SystemExit(0)
    print('Achei uma trava velha de %.1f h. Vou considerar abandonada e seguir.' % idade)
open(TRAVA, 'w', encoding='utf-8').write(agora())

try:
    inicio = time.time()
    diz('=' * 68)
    diz('  RODADA DIARIA - %s' % agora())
    diz('=' * 68)

    antes = ids_do_cards()
    diz('  O sistema conhece %d cards agora.' % len(antes))

    # ---------------- 1 a 4: as coletas -------------------------------
    # ---------------- 0: O VIGIA - a coleta do efHub -------------------
    # ⛔ 17/08 — O VIGIA NAO ESTAVA NESTA RODADA, e e ele quem acha BOX NOVA.
    #    Sem ele, carta lancada hoje so entrava quando o Luis clicasse.
    #
    #    Ele abre o Chrome sozinho (perfil proprio em dados\chrome_do_vigia,
    #    nao mexe no navegador do dia a dia), le as box, puxa as fichas e
    #    fecha. Nao espera tecla nenhuma — ja nasceu para rodar sem ninguem.
    #
    #    ⚠️ A tarefa agendada precisa rodar COM O USUARIO CONECTADO. Chrome
    #       sem sessao de usuario nao sobe no Windows.
    #
    #    Teto de 400 fichas por rodada, de proposito: o efHub devolve HTTP 429
    #    quando se pede demais (medido em 17/08: 159 de 400 recusadas). Melhor
    #    pegar 241 por dia todo dia do que ser bloqueado.
    # ⛔ 18/08 — O INTERRUPTOR DE UMA VEZ SO.
    #    Ordem do Luis: "o vigia a gente acabou de rodar, nao tem necessidade.
    #    Vamos fazer essa rodada de hoje, EXCEPCIONALMENTE, sem o vigia."
    #
    #    Com o arquivo PULAR-O-VIGIA.txt na pasta, a coleta do efHub e pulada
    #    e o arquivo E APAGADO no mesmo instante. Ou seja: vale UMA rodada, e
    #    a proxima ja volta ao normal sozinha.
    #    ⛔ E APAGADO ANTES de rodar qualquer coisa, de proposito. Se ele fosse
    #       apagado no fim, uma rodada interrompida no meio deixaria o vigia
    #       desligado para sempre sem ninguem perceber — e a coleta pararia em
    #       silencio, que e o pior defeito que este sistema pode ter.
    #
    #    Os passos 0b e 0c continuam rodando: eles ENTRAM com o que o vigia ja
    #    colheu antes. Pular a coleta nao pode significar jogar fora a colheita.
    _pular = 'PULAR-O-VIGIA.txt'
    _pulou_o_vigia = os.path.exists(_pular)
    if _pulou_o_vigia:
        try:
            os.remove(_pular)
        except Exception:
            pass
        diz()
        diz('-' * 68)
        diz('  0a. O VIGIA — PULADO A PEDIDO (PULAR-O-VIGIA.txt)')
        diz('-' * 68)
        diz('  O arquivo ja foi apagado: vale so esta rodada.')
        diz('  As fichas que o vigia ja tinha colhido ENTRAM normalmente abaixo.')

    # ⛔⛔ 18/08 — A FILA SE REFAZ ANTES DO VIGIA, e isto e o conserto de um
    #     defeito que anulou duas rodadas inteiras.
    #
    #     Ordem do Luis, 18/08: "a gente passou um tempao falando 'vamos pegar
    #     de novo os dados dessa carta, dessa e dessa'. Contamos tudo. Ai voce
    #     vem falar que nao valeu de nada porque em vez de solicitar dessas
    #     cartas a gente solicitou de outras."
    #
    #     O QUE ACONTECIA: a fila de coleta so era refeita no fim da rodada
    #     (passo 5h). O vigia, que roda no COMECO, usava sempre a fila da
    #     vespera. E como o 5h falhou nas rodadas de 17/08 (campo sem regra),
    #     o vigia de 23:29 trabalhou com a fila de 16/08 as 09:00 — dois dias
    #     velha. Pediu 400 cartas de uma lista que nao era mais a verdade.
    #
    #     Agora ela se refaz AQUI, com a base que esta no disco, antes de
    #     qualquer coleta. So le arquivo, e barato. E continua sendo refeita no
    #     fim (5h), com o que a rodada trouxe — sao dois momentos diferentes e
    #     os dois importam: este manda no que PERGUNTAR hoje; o do fim manda no
    #     que perguntar amanha.
    # ==================================================================
    #  -1. A EXCECAO DE ONTEM MORRE AQUI
    # ==================================================================
    #  ORDEM DO LUIS, 18/08: "como e que a gente faz pro sistema ser uma
    #  excecao e na proxima rodada voltar ao normal, SEM A GENTE ESQUECER?"
    #
    #  ⛔ NAO SE RESOLVE LEMBRANDO. Quem desliga um interruptor "so hoje" nao
    #     esta la amanha para religar. Foi assim que o VOLTAR-PARA-A-FILA ficou
    #     desligado por dias sem ninguem notar.
    #     Entao a excecao carrega a propria validade: o EXCECAO-DE-HOJE.json
    #     guarda a DATA, os interruptores que mexeu e o conteudo que cada um
    #     tinha. Na primeira rodada de outro dia, isto repoe tudo, guarda o
    #     recibo com a data em que desfez, e avisa em letra grande.
    roda('-1. Conferir a excecao (e desfazer se venceu)',
         [os.path.join('ClubEfootball', 'programas', 'excecao_de_hoje.py'), 'conferir'],
         60, obrigatorio_existir=False)

    roda('0. Refazer a fila ANTES de sair perguntando',
         os.path.join('ClubEfootball', 'programas', 'fila_de_coleta.py'),
         10 * 60, obrigatorio_existir=False)

    _vigia = os.path.join('ClubEfootball', 'programas', 'o_vigia.py')
    if os.path.exists(_vigia):
        if not _pulou_o_vigia:
            # ⛔ 18/08 — 4 HORAS, nao 90 minutos. O vigia deixou de ter teto
            #    por carta e passou a puxar ate a fila acabar (freio proprio de
            #    2 h). O prazo aqui tem que ser MAIOR que o freio dele, senao a
            #    rodada mata o vigia no meio e a coleta nunca fecha.
            roda('0a. O VIGIA — box nova e fichas do efHub', _vigia, 4 * 60 * 60)
        roda('0b. Entrar com as fichas do efHub',
             os.path.join('ClubEfootball', 'programas', 'entrar_com_o_efhub.py'), 20 * 60)
        roda('0c. Separar a data que estava no NOME da box',
             os.path.join('ClubEfootball', 'programas', 'separar_a_data_do_box.py'), 10 * 60)

    roda('1. Coleta do efScout (impetos, campanhas, base binaria)', 'coletar_efscout.py', 60)
    roda('2. Impeto de fabrica por card (so relatorio)',            'impeto_do_efscout.py', 30)
    roda('3. Vagas de impeto (efootballdb)',                        'coletar_vaga_efootballdb.py', 90)
    roda('4. Box e data de lancamento (efootballdb)',               'coletar_box.py', 90)

    # ---------------- 5: backup, unificar, conferir, subir ------------
    roda('5a. Backup da base atual',                                'backup_base.py', 30)
    roda('5b. Unificar a base (dados/base_unica.json)',             'unificar_base.py', 45)
    roda('5c. Conferir a completude',                               'completude_base.py', 30)
    roda('5c2. O PLACAR das fontes (o que cresceu hoje)',            'conferir_fontes.py', 15)
    roda('5c3. O QUE FALTA DE VERDADE (cruza com o que os cards citam)',
         'o_que_falta_de_verdade.py', 15)
    roda('5d. Reperguntar TUDO que ficou sem resposta',              'repergunta_tudo.py', 15)
    roda('5d2. E o detalhe do impeto orfao',                         'repergunta_impeto.py', 15)
    # 15/08 — O SISTEMA CONFERINDO A SI MESMO.
    # Ordem do Luis: "voce acha que eu vou olhar card por card? E o seu metodo
    # que esta errado". Estes dois acham sozinhos, sem ninguem abrir o jogo:
    #   contradicoes.py        o dado que NAO PODE ser verdade
    #   quem_veio_pela_metade  o card entregue incompleto e o relogio de 24h
    roda('5d3. O dado que nao pode ser verdade',                     'contradicoes.py', 20)
    roda('5d4. Quem veio pela metade (o relogio de 24h)',            'quem_veio_pela_metade.py', 20)
    roda('5e. Subir para o Supabase (cards_base)',                  'subir_base.py', 60)

    # ⛔ 16/08/2026 — O 5f NAO E OPCIONAL, E O CICLO SO FECHA COM ELE.
    #    Em 16/08 15h28 o banco virou a fonte unica: 15 campos (o estilo de
    #    jogo da IA, a idade, o pe ruim, o maximo, o estado de cada campo)
    #    passaram a vir DELE, e o unificar_base.py deixou de monta-los.
    #
    #    Sem esta linha a rodada da meia-noite faria isto:
    #       5b unificar -> a pasta fica SEM os 15 campos
    #       5e subir ---> o banco nao perde nada (campo vazio nao sobe)
    #       ... e a pasta passa a noite inteira sem eles
    #
    #    E ai o motor de bonus, que desde 16/08 le o estilo de jogo da IA da
    #    base, calcularia bonus ZERO para 2.479 cartas — sem erro nenhum na
    #    tela, so o numero errado.
    # ⛔ 17/08 — AQUI DESCEM TODOS OS INSUMOS, nao so as cartas.
    #    O do_banco.py chama o baixar_base.py por dentro (as 6.469 cartas) e
    #    ainda traz molde, tecnicos, habilidades, bloqueios e o catalogo de
    #    impetos. Sao os seis insumos que os motores leem.
    #    Ordem do Luis, 17/08: "os motores leem eles de dentro do banco de
    #    dados, processa, e o resultado salva de novo pro banco".
    #    Se o do_banco nao estiver na pasta, cai no baixar_base de sempre.
    # ⛔ 18/08 — A ORDEM TEM QUE SER ESTA, e nao e detalhe:
    #    5e2 monta o catalogo de impeto A PARTIR DAS CARTAS que acabaram de
    #    subir, e grava no banco. 5f desce o catalogo do banco para o
    #    CAT_dom.json, que e o arquivo que o motor le. Invertido, o motor roda
    #    com o catalogo de ontem e impeto novo do jogo nao existe para ele.
    #    Ordem do Luis, 18/08: "nao adianta a gente arrumar no banco de dados e,
    #    quando ele for procurar la, estar pre-definido, e ai achar que nao existe."
    roda('5e2. Montar o catalogo de impeto (nome unico, nivel como numero)',
         os.path.join('ClubEfootball', 'programas', 'monta_catalogo_impeto.py'),
         10 * 60, obrigatorio_existir=False)

    if os.path.exists(os.path.join('ClubEfootball', 'programas', 'do_banco.py')):
        roda('5f. Os insumos descem do banco (cartas, molde, tecnicos, habilidades, impeto)',
             os.path.join('ClubEfootball', 'programas', 'do_banco.py'), 15 * 60)
    else:
        roda('5f. Baixar do Supabase (o banco manda de volta)',     'baixar_base.py', 60)

    # ⛔ 18/08 — A MARCA DE CADA CAMPO SE REFAZ TODA RODADA.
    #    Ordem do Luis: "isso nao e um conserto pontual, tem que deixar o
    #    sistema funcionar assim, senao daqui a pouco tem o mesmo problema."
    #    Sem isto a marca envelhece calada: em 18/08 ela dizia "nao sei" no
    #    estilo de jogo da IA das 6.469 cartas, e 2.479 ja tinham o dado. Toda
    #    conta de pendencia que sair dela mente enquanto ela for velha.
    roda('5g. Refazer a marca de cada campo (os quatro estados)',
         os.path.join('ClubEfootball', 'programas', 'estados.py'),
         15 * 60, obrigatorio_existir=False)
    roda('5h. Refazer a fila de coleta a partir da marca nova',
         os.path.join('ClubEfootball', 'programas', 'fila_de_coleta.py'),
         10 * 60, obrigatorio_existir=False)

    # ==================================================================
    #  5i a 5k — O ELO QUE FALTAVA: dado novo vira nota nova
    # ==================================================================
    #  ORDEM DO LUIS, 18/08, com estas palavras:
    #    "Era pra quando a rodada do dia acontecesse, ele ja mandasse os dados
    #     das cartas que foram coletadas cem por cento pros motores. E as que
    #     nao foram coletadas cem por cento, mandava pra fila de pendencias.
    #     E nao esta acontecendo isso."
    #
    #  ⛔ ELE ESTA CERTO, e o motivo e este: a etapa 7 so roda em CARD NOVO.
    #     Carta que ja existia e cujo dado melhorou hoje NUNCA voltava para a
    #     fila. Medido em 17/08 23:33: entraram 192 fichas novas e o motor
    #     disse "nao tem card novo hoje, nao ha o que rodar".
    #     Os tres programas abaixo ja existiam e nenhum estava na rodada.
    #
    #  5i  A VOLTA AUTOMATICA .... SO LE. Compara o que a carta tem hoje com o
    #      que a linha usou, e escreve PRECISA-REFAZER.txt. Ele proprio PARA e
    #      avisa quando a resposta e "refaz quase tudo" — numero grande demais
    #      nao e trabalho, e sintoma.
    #  5j  SEPARAR BARRINHA x BONUS ... SO LE. Divide a lista em duas: quem
    #      mudou algo que o motor de barrinhas le, e quem so mexeu no bonus.
    #      Sem isto, rodar barrinha por causa de pe ruim e desperdicio puro.
    #  5k  REFAZER DE VERDADE ..... o unico que MEXE: tira a linha dos tres
    #      lugares que o motor considera "ja feito" e poe na FRENTE da fila.
    #      Faz backup de tudo antes. So roda com o motor parado — e aqui esta,
    #      porque a etapa 7 vem depois.
    roda('5i. A volta automatica (quem ficou com dado velho)',
         os.path.join('ClubEfootball', 'programas', 'a_volta_automatica.py'),
         20 * 60, obrigatorio_existir=False)
    roda('5j. Separar quem refaz a barrinha de quem so refaz o bonus',
         os.path.join('ClubEfootball', 'programas', 'separar_barrinha_de_bonus.py'),
         15 * 60, obrigatorio_existir=False)

    # ⛔ 18/08 — O ARQUIVO DO MEIO. Ordem do Luis:
    #    "a rodada traz os resultados num arquivo; voce desmembra ele e joga
    #     nas filas — as incompletas voltam amanha, as completas vao pros
    #     motores, e ai o motor ja sabe que tem que rodar."
    #    O 5L le a marca de cada campo, separa as duas pilhas e escreve:
    #       RESULTADO-DA-RODADA.json ... o arquivo do meio
    #       fila_PENDENCIAS.json ....... volta na coleta de amanha
    #       fila_PRIORIDADE.json ....... acrescenta o que esta COMPLETO e mudou
    #    ⛔ Vem DEPOIS do 5j (que faz a lista de quem mudou) e ANTES do 5k.
    roda('5L. Fechar a rodada: separar completas de incompletas',
         os.path.join('ClubEfootball', 'programas', 'fecha_a_rodada.py'),
         15 * 60, obrigatorio_existir=False)

    # ⛔ O 5k SO ANDA COM O INTERRUPTOR, e de proposito. Ele DESCARTA linha
    #    pronta para o motor refazer. Enquanto o VOLTAR-PARA-A-FILA.txt nao
    #    estiver na pasta, os passos 5i e 5j so mostram a lista — ninguem
    #    perde linha nenhuma. Mesmo desenho do LIGAR-MOTOR-AUTOMATICO.txt.
    # ⛔ o motor da etapa 7 precisa SABER que voltou linha, senao ele diz
    #    "nao tem card novo" e vai embora com a fila cheia.
    _voltaram = 0
    if os.path.exists('VOLTAR-PARA-A-FILA.txt'):
        _antes_fila = 0
        try:
            _antes_fila = len(json.load(open('fila_PRIORIDADE.json', encoding='utf-8')))
        except Exception:
            pass
        # ⛔ A LISTA E O PARA-REFAZER-AGORA.txt, nao o PRECISA-REFAZER.txt.
        #    O primeiro ja veio filtrado pelo 5L: so linhas de carta que tem
        #    TUDO que os motores leem. Linha de carta furada rodaria com dado
        #    faltando e gravaria nota errada, que e pior que nao ter nota.
        # ⛔ 18/08 — ELE ALIMENTA O MOTOR EM VEZ DE ARRANCAR A LINHA.
        #    O refazer_de_verdade tirava a linha do linhas.jsonl, dos lotes e do
        #    feitos.txt — e para isso o motor tinha que estar PARADO. Era a
        #    UNICA razao pela qual coletar e rodar nao podiam andar juntos.
        #    Agora a linha vai para o fila_EXTRA.json com a marca `refazer`, e o
        #    motor a recalcula pela entrada quente, sem parar nada.
        _voltaram = 0
        try:
            _chaves = [L.strip() for L in open('PARA-REFAZER-AGORA.txt',
                                               encoding='utf-8')
                       if L.strip() and not L.startswith('#') and '|' in L]
            _fila = {}
            for _r in (json.load(open('fila_v6.json', encoding='utf-8')) or []):
                _fila['%s|%s' % (_r.get('card_id'), _r.get('funcao'))] = _r
            _extra = []
            try:
                _extra = json.load(open('fila_EXTRA.json', encoding='utf-8')) or []
            except Exception:
                _extra = []
            _ja = {'%s|%s' % (r.get('card_id'), r.get('funcao')) for r in _extra}
            for _k in _chaves:
                if _k in _ja:
                    continue
                _r = dict(_fila.get(_k) or {})
                if not _r:
                    _c, _f = _k.split('|', 1)
                    _r = {'card_id': _c, 'funcao': _f}
                _r['refazer'] = True
                _r['por_que_refazer'] = 'o dado da carta melhorou nesta rodada'
                _extra.append(_r)
                _voltaram += 1
            if _voltaram:
                _tmp = 'fila_EXTRA.json.parcial'
                json.dump(_extra, open(_tmp, 'w', encoding='utf-8'),
                          ensure_ascii=False)
                os.replace(_tmp, 'fila_EXTRA.json')
        except Exception as _e:
            diz('  nao consegui alimentar o fila_EXTRA: %s' % str(_e)[:110])
        if _voltaram:
            diz('  -> %d linhas foram para o fila_EXTRA.json com a marca `refazer`.'
                % _voltaram)
            diz('     O motor pega pela entrada quente, sem ninguem parar nada.')
        else:
            diz('  -> nada a refazer nesta rodada.')
    else:
        _voltaram = 0
        diz()
        diz('-' * 68)
        diz('  5k. Devolver as linhas para a fila — DESLIGADO')
        diz('-' * 68)
        diz('  A lista de quem precisa refazer esta em PRECISA-REFAZER.txt.')
        diz('  Para o sistema devolver sozinho, crie o arquivo')
        diz('  VOLTAR-PARA-A-FILA.txt nesta pasta. Ate la, so a lista sai.')

    # ---------------- 6: card novo entra e vai pra FRENTE da fila -----
    roda('6a. Entrar os cards novos no cards.json',                 'inserir_novos.py', 20)
    depois = ids_do_cards()
    novos = sorted(depois - antes)
    diz()
    diz('-' * 68)
    diz('  6b. CARDS NOVOS NESTA RODADA')
    diz('-' * 68)
    if novos:
        diz('  Entraram %d cards que o sistema nao tinha:' % len(novos))
        for i in novos[:40]:
            diz('     %s' % i)
        if len(novos) > 40:
            diz('     ... e mais %d.' % (len(novos) - 40))
        json.dump(novos, open('cards_novos_de_hoje.json', 'w', encoding='utf-8'),
                  ensure_ascii=False)
        roda('6c. Enfileirar os novos',                             'alimenta_fila.py', 20)
        roda('6d. Por os novos na FRENTE da fila',                  'por_os_novos_na_frente.py', 20)
    else:
        diz('  Nenhum card novo hoje. Nada a enfileirar.')
        if os.path.exists('cards_novos_de_hoje.json'):
            os.remove('cards_novos_de_hoje.json')

    # ---------------- 7: O MOTOR - a etapa que nasce DESLIGADA --------
    diz()
    diz('-' * 68)
    diz('  7. O MOTOR')
    diz('-' * 68)
    # ⛔ 18/08 — A EXCECAO DO DIA MANDA AQUI, e so no dia dela.
    #    Ordem do Luis: "hoje, excepcionalmente, ela nao chama os motores. Voce
    #    deixa a lista preparada e a gente junta com as outras e chama eles."
    #    Isto NAO mexe no LIGAR-MOTOR-AUTOMATICO.txt: o interruptor continua
    #    onde estava, e amanha a rodada volta a chamar o motor sozinha, sem
    #    ninguem religar nada.
    if EXCECAO.vale('nao_chamar_o_motor'):
        diz('  NAO CHAMEI O MOTOR — excecao declarada para hoje.')
        diz()
        _f = quantas_linhas_faltam()
        diz('  A fila esta pronta e esperando: %s linhas sem resultado.'
            % '{:,}'.format(_f))
        diz('     1o  o que esta no fila_PRIORIDADE (o que a rodada identificou hoje)')
        diz('     2o  o resto, na ordem da fila')
        diz()
        diz('  Para rodar: ClubEfootball\\SO-O-MOTOR.bat')
        diz('  Amanha a rodada volta a chamar o motor sozinha.')
        pulados += 1
    elif not os.path.exists(CHAVE_MOTOR):
        diz('  DESLIGADO - e assim que voce mandou deixar (14/08/2026).')
        if novos:
            diz('  O motor NAO foi chamado. Os %d cards que entraram hoje estao na'
                % len(novos))
            diz('  FRENTE da fila, esperando voce mandar rodar.')
        else:
            diz('  O motor NAO foi chamado - e nao entrou card novo hoje mesmo.')
        diz()
        diz('  PARA LIGAR, quando voce decidir: crie nesta pasta um arquivo')
        diz('  chamado  %s  (pode ser vazio).' % CHAVE_MOTOR)
        diz('  PARA DESLIGAR de novo: apague esse arquivo.')
        pulados += 1
    elif not novos and not _voltaram and not quantas_linhas_faltam():
        diz('  LIGADO, mas nao tem card novo, nem linha devolvida, nem linha')
        diz('  parada na fila. Nada a rodar — e isso e resposta, nao falha.')
        pulados += 1
    else:
        if _voltaram and not novos:
            diz('  LIGADO. Nao entrou card novo, mas %d linhas voltaram para a fila'
                % _voltaram)
            diz('  porque o dado delas melhorou hoje. Vou rodar essas.')
        elif _voltaram:
            diz('  LIGADO. %d cards novos e %d linhas devolvidas por dado novo.'
                % (len(novos), _voltaram))
        else:
            diz('  LIGADO. Vou rodar o motor SO nos cards novos que entraram hoje.')
        _faltam = quantas_linhas_faltam()
        if _faltam:
            diz('  Na fila, sem resultado ainda: %s linhas.' % '{:,}'.format(_faltam))
        diz('  Custo esperado: ~21 s por linha.')
        # ⛔ 18/08 — O TEMPO NAO PODE SER 20 MINUTOS. Ordem do Luis:
        #    "assim que terminasse a rodada, ja chama os motores; os motores
        #     fariam a parte deles e subiriam pro banco."
        #    Medido nas 12.368 linhas ja rodadas: mediana 3,5 s por linha, mas
        #    a media e 51,7 s e a pior levou 53 MINUTOS sozinha. Com teto de 20
        #    minutos a rodada matava o motor no meio de uma carta grande, todo
        #    dia, e ninguem via porque ele "seguia em frente".
        #    12 horas: ele para quando acabar o trabalho, nao quando o relogio
        #    mandar. E o grava_direto ja salvou linha a linha, entao mesmo que
        #    o tempo estoure nada do que foi feito se perde.
        # ================================================================
        #  ⛔ 18/08 — A RODADA NAO ESPERA MAIS O MOTOR
        # ================================================================
        #  ORDEM DO LUIS, e o desenho e dele:
        #    "Voce nao tem que esperar coletar tudo pra rodar o motor nao. Voce
        #     tem que coletar, colocar o motor pra rodar, VOLTAR, coletar mais
        #     ENQUANTO ele esta rodando, e alimentar ele de novo."
        #
        #  O QUE ACONTECIA: o motor rodava DENTRO da rodada, e a rodada ficava
        #  parada esperando. Medido em 18/08: o motor entrou as 05:09, entrou na
        #  parte pesada da fila a 0,4 linha por minuto, e as 15:26 ainda estava
        #  la. Nove horas de coleta parada — e o espelho do Drive, que e a etapa
        #  8, nem chegou a rodar.
        #
        #  AGORA: a rodada ABRE o motor numa janela propria e SEGUE. O motor tem
        #  entrada quente (fila_EXTRA.json) e nunca fecha sozinho: a coleta de
        #  amanha joga trabalho novo la e ele pega, sem ninguem reiniciar nada.
        #
        #  ⛔ E SE ELE JA ESTIVER DE PE, NAO ABRE OUTRO. O motor carimba a hora
        #     no MOTOR-VIVO.txt a cada linha. Carimbo de menos de 15 minutos =
        #     esta trabalhando, so alimenta e sai.
        _VIVO = 'MOTOR-VIVO.txt'
        _de_pe = False
        if os.path.exists(_VIVO):
            try:
                _idade = (time.time() - os.path.getmtime(_VIVO)) / 60.0
                _de_pe = _idade < 15
                diz('  o MOTOR-VIVO.txt tem %.0f min de idade' % _idade)
            except Exception:
                pass
        if _de_pe:
            diz('  O MOTOR JA ESTA DE PE. Nao abri outro.')
            diz('  O que esta na fila ele pega sozinho pela entrada quente.')
            try:
                diz('  ' + open(_VIVO, encoding='utf-8').read().strip().replace('\n', ' · '))
            except Exception:
                pass
        else:
            diz('  Abrindo o motor numa JANELA PROPRIA — a rodada NAO espera.')
            try:
                if os.path.exists('PARAR.txt'):
                    os.remove('PARAR.txt')
                    diz('  (apaguei o PARAR.txt que estava na pasta)')
                _cria = 0
                if os.name == 'nt':
                    _cria = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0x00000010)
                subprocess.Popen([sys.executable, 'roda_lote_v6.py'],
                                 creationflags=_cria)
                diz('  ✅ motor aberto. Ele fica de pe esperando trabalho novo.')
                diz('     para fechar: crie um PARAR.txt nesta pasta.')
            except Exception as _e:
                diz('  ⛔ nao consegui abrir o motor: %s' % str(_e)[:120])
                diz('     abra na mao: ClubEfootball\\SO-O-MOTOR.bat')
        oks += 1
        # ⛔ 17/08 — A ETAPA 7c FOI RETIRADA, e por dois motivos medidos:
        #
        #  1. Ela chamava o `enviar.py`, que MORRE com
        #     FileNotFoundError: 'saida/'. Como etapa da rodada diaria, isso
        #     daria uma FALHA todo santo dia, e falha que aparece todo dia
        #     vira falha que ninguem le.
        #
        #  2. Ela nao tem mais objeto. Desde 14/08 o motor grava DIRETO na
        #     tabela `builds` (grava_direto.py, ligado pelo GRAVA-DIRETO.txt),
        #     e desde 17/08 ele grava LINHA A LINHA, no instante em que cada
        #     uma fica pronta. Quando o 7b termina, as builds ja estao no
        #     banco — nao ha o que enviar depois.
        #
        #  Se o GRAVA-DIRETO.txt for apagado um dia, o proprio motor avisa na
        #  tela dele: "grava direto: DESLIGADO". Ai sim volta a fazer falta.
        diz('  as builds ja subiram durante a rodada (grava direto, linha a linha).')

    # ---------------- 7e: O MOTOR DE BONUS ----------------------------
    # ⛔ 17/08 — ELE NAO ESTAVA NESTA RODADA, e faltava mesmo.
    #
    #  Sao DOIS motores, e eles leem coisas diferentes (regra de 17/08):
    #     otimizacao  ->  base · orcamento · impeto · vaga · habilidades
    #     bonus       ->  altura · estilo da IA · corpo · modelo · pe · pe ruim
    #
    #  Sem esta etapa, carta nova entrava com a nota do motor mas SEM bonus —
    #  e o encaixe da etapa 8 mostraria o numero incompleto, sem avisar.
    #
    #  Roda SEMPRE, nao so quando entra card novo: o bonus muda quando a base
    #  muda (corpo, pe ruim, estilo da IA), e a base muda todo dia na etapa 5.
    #  Ele grava sozinho na tabela `bonus` no fim.
    diz()
    diz('-' * 68)
    diz('  7e. O MOTOR DE BONUS')
    diz('-' * 68)
    roda('7e. Motor de bonus (corpo, pe ruim, estilo, estilo da IA)',
         'motor_bonus.py', 20 * 60)

    # ---------------- 8: o Encaixe ------------------------------------
    # ⛔ 18/08 — AQUI TEVE UM INTERRUPTOR E ELE FOI RETIRADO NO MESMO DIA.
    #    Eu criei um NAO-GERAR-O-ENCAIXE.txt para "proteger o design" enquanto
    #    o Luis mexia na tela. Medindo depois, ele era uma armadilha:
    #
    #      o motor grava em ....... builds
    #      o encaixe LE de ........ tela_encaixe
    #      quem enche a tela_encaixe e ESTA etapa (gera_encaixe.py: _tela.sobe(D))
    #
    #    Com ela desligada, tudo o que o motor fizesse no dia ficaria no banco
    #    e NUNCA apareceria na tela — sem erro, sem aviso. Interruptor que
    #    causa perda silenciosa nao fica na pasta esperando alguem usar.
    #
    #    E nao havia o que proteger: medido, o gera_encaixe NUNCA escreve na
    #    casca (encaixe\encaixe_B_v171_datas_tela.html) nem no CONTA-DO-MOTOR.js
    #    que ja exista. Ele so LE os dois. Quem mexe no design mexe na casca, e
    #    esta etapa APLICA a mudanca — nao desfaz.
    # ⛔ 19/08 — O GERADOR MORA NO ClubEfootball\programas.
    #    "Nao existe mais essa pasta pro futebol. A pasta agora e
    #    ClubEfootball. E tudo la." (Luis, 19/08). O caminho da raiz so
    #    fica como rede: se um dia alguem apagar o atalho, a rodada segue.
    _ger = os.path.join('ClubEfootball', 'programas', 'gera_encaixe.py')
    if not os.path.exists(_ger):
        _ger = 'gera_encaixe.py'
    roda('8. Regerar o Encaixe e espelhar',                         _ger, 30)

    # ---------------- o fim -------------------------------------------
    seg = int(time.time() - inicio)
    diz()
    diz('=' * 68)
    diz('  FIM DA RODADA - %s  (levou %d h %d min)' % (agora(), seg // 3600, (seg % 3600) // 60))
    diz('=' * 68)
    diz('  etapas OK ......... %d' % oks)
    diz('  etapas com falha .. %d' % falhas)
    diz('  etapas puladas .... %d' % pulados)
    diz('  cards novos ....... %d' % len(novos))
    diz()
    if falhas:
        diz('  Uma etapa falhar NAO invalida as outras. O que subiu, subiu.')
        diz('  A rodada de amanha retoma sozinha - as coletas continuam de onde')
        diz('  pararam e o upsert nao duplica nada.')
    diz()
    diz('  O que ainda falta em cada card ... RELATORIO-COMPLETUDE.txt')
    diz('  O LOG DE CADA PASSO .............. %s\\' % PASTA_LOG)
    diz('     (um arquivo por passo, com tudo que o programa imprimiu)')
    diz('  Conflito entre as fontes ......... RELATORIO-BASE-UNICA.txt')
    diz('  Backup desta rodada .............. pasta backups_base\\')
    diz('  O PAINEL de acompanhamento ....... PAINEL.html (duplo clique)')
    diz('  O placar das fontes .............. FONTES-O-PLACAR.txt')
    diz('  O buraco de verdade .............. O-QUE-FALTA-DE-VERDADE.txt')
    diz('  Insumo que ainda falta ........... INSUMOS-PERGUNTAR-DE-NOVO.txt')
    diz('  Impeto orfao, em detalhe ......... IMPETO-PERGUNTAR-DE-NOVO.txt')

    texto = '\n'.join(linhas) + '\n'
    open(ULTIMA, 'w', encoding='utf-8').write(texto)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('\n\n' + '#' * 68 + '\n')
        f.write(texto)

    # ---------------- 9: o painel -------------------------------------
    # Por ULTIMO, de proposito: o painel le o ULTIMA-RODADA.txt que acabou de
    # ser escrito. Se rodasse antes, mostraria sempre a rodada de ontem.
    os.environ['PAINEL_DENTRO_DA_RODADA'] = '1'
    roda('9. Gerar o painel (PAINEL.html)', 'gera_painel.py', 15)

finally:
    # ⛔ o log da rodada inteira tambem fica na pasta do dia, do lado dos passos
    try:
        os.makedirs(PASTA_LOG, exist_ok=True)
        with open(os.path.join(PASTA_LOG, '00-A-RODADA-INTEIRA.txt'),
                  'w', encoding='utf-8', errors='replace') as _f:
            _f.write('\n'.join(linhas) + '\n')
    except Exception:
        pass
    _limpa_logs_velhos()
    try:
        os.remove(TRAVA)
    except Exception:
        pass
