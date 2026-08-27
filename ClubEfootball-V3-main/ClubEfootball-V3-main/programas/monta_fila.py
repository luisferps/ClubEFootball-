# -*- coding: utf-8 -*-
"""
FILA DA v6 — TODOS os cards do cards.json, em TODAS as posicoes que cada um pode ocupar.

ORDEM
  1o) os cards das CAMPANHAS QUE ESTAO NO AR — a lista sai de lancamento_agora.json,
      tirada da pagina inicial do efHub (efhub.com/pt-BR). Esses furam a fila.
  2o) o resto pela regra normal: S+ primeiro, depois S, A, B, C, D — e dentro de
      cada tier por OVR decrescente.

  POSICAO NATIVA   -> as DUAS funcoes da familia (a nativa e a migrada)
  POSICAO COMPRADA -> UMA funcao, decidida por (posicao + estilo)
  O card e tratado UMA VEZ, por id base. As variantes @POS entram so como lista
  de posicoes que ele pode jogar — nao geram linha repetida.

NINGUEM FICA DE FORA por falta de pontos de progressao. Card levelCap 1
(Featured / Show Time) entra com orc = 0: as barras ficam em zero, mas o motor
ainda escolhe impeto, tecnico e habilidades — e a nota sai. Era esse o 'if orc'
que descartava esses cards em silencio.

⛔ A TRAVA DE POOL VAZIO CAIU EM 08/08 (ordem do Luis). Nao repor — ver o
  comentario dentro do laco. Card sem `falta` proprio RODA NORMAL: o pool vem da
  regra do jogo, nao do `falta`.
   pool = card['falta'] ∪ dados/falta_por_card.json[id]
   Nota com pool zero nao e "deprimida", e INUTILIZAVEL: Musiala mediu 57,7 com
   pool 5 e -135,5 com pool 0. Medido em 08/08 nos 2.568 cards da base: 59 cards
   (154 linhas) tem os DOIS lados da uniao vazios ao mesmo tempo — card['falta']
   vazio E ausentes do falta_por_card.json. E buraco de coleta, nao conjunto vazio
   legitimo: 1.216 cards tambem estao ausentes do falta_por_card e ficam com pool
   cheio pelo lado do card, e 2.509 cards tem fab de 10 e TEM pool.
   Esses 59 vao para fila_ADIADA_pool_vazio.json e rodam quando a regra do `falta`
   fechar — mesmo tratamento dos cards novos que vem da coleta.

Se sobrar algo fora, vai para fila_EXCLUIDOS.csv com o motivo escrito.
"""
import sys, json, csv, os, collections

# ⛔ 18/08 — ELE MORA EM ClubEfootball\programas\ AGORA.
#    Regra do Luis, repetida em 17 e 18/08: "os arquivos uteis vao na pasta do
#    ClubEfootball. A pasta raiz nao vai existir mais."
#    O padrao das pastas: o arquivo MORA em programas\, mas TRABALHA na pasta
#    que tem o config.txt — e la que estao dados\, saida_v6\ e o resto.
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
    print('nao achei o config.txt subindo a partir de %s' % AQUI)
    raise SystemExit(1)
os.chdir(CASA)
for _d in (AQUI, CASA):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from funcao_nativa import funcao_nativa, familia, normaliza, SA_FAMILIA

def pausa(msg='Enter para fechar...'):
    """Nao trava quando o .bat chama sem teclado."""
    try:
        if sys.stdin and sys.stdin.isatty():
            input(msg)
    except Exception:
        pass


D = 'dados/'
TIER_ORD = {'S+': 0, 'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
LANC = 'lancamento_agora.json'   # os cards das campanhas que estao no ar AGORA
CAMPANHA = {}                    # id do card -> nome da box de onde ele veio
ADIADA_POOL = 'fila_ADIADA_pool_vazio.json'


def em_lancamento():
    """Os ids das campanhas da pagina inicial do efHub. Esses furam a fila.

    Aproveita e guarda de QUAL BOX cada card veio (CAMPANHA) — ordem do Luis,
    08/08: "salvar de qual box ele veio, se a gente quiser remontar ela depois a
    gente consegue". So da para os cards que estao na home agora; card antigo nao
    tem como saber, e fica sem.
    """
    if not os.path.exists(LANC):
        return set()
    d = json.load(open(LANC, encoding='utf-8'))
    if isinstance(d, dict):
        for k, v in (d.get('campanha_do_card') or {}).items():
            CAMPANHA[str(k)] = v
        if not CAMPANHA:
            for nome, ids in (d.get('por_campanha') or {}).items():
                for i in ids: CAMPANHA[str(i)] = nome
        return set(str(x) for x in (d.get('ids') or []))
    return set(str(x) for x in d)


def main():
    C = json.load(open(D + 'cards.json', encoding='utf-8'))
    LANCA = em_lancamento()
    FALTA = json.load(open(D + 'falta_por_card.json', encoding='utf-8'))
    LC = json.load(open(D + 'levelcap.json', encoding='utf-8')) if os.path.exists(D + 'levelcap.json') else {}

    base = {}
    for c in C:
        base.setdefault(str(c['id']).split('@')[0], []).append(c)

    fila, fora, adiada, sem_pool = [], [], [], []
    for b, regs in base.items():
        c = max(regs, key=lambda x: x.get('orc') or 0)
        orc = c.get('orc') or 0
        if not orc and b in LC:
            orc = 2 * int(LC[b]) - 2
        est = c.get('modelo')
        nat = c.get('np') or c.get('pos')

        # SA/SS nao tem familia propria: o ESTILO decide para qual casa ele vai
        nat_pt = normaliza(nat, None)[0]
        if nat_pt == 'SA':
            nat_pt = SA_FAMILIA.get(normaliza(nat, est)[1]) or nat_pt

        funcs = {}
        for f in familia(nat_pt):
            funcs[f] = 'nativa'
        posicoes = set()
        for r in regs:
            for k in ('pos', 'np'):
                if r.get(k): posicoes.add(str(r[k]).strip())
            for x in str(r.get('sec') or '').split('/'):
                if x.strip(): posicoes.add(x.strip())
        # ====================================================================
        #  ⛔ 18/08 — POSICAO COMPRADA RODA AS DUAS FUNCOES DA FAMILIA
        # ====================================================================
        #  ORDEM DO LUIS, aprovada em 18/08:
        #    "A vantagem e que pra cada carta a gente teria todos os possiveis,
        #     otimizados. E ai no modal da carta a gente poderia separar por
        #     funcoes ativas e funcoes basicas."
        #
        #  O QUE ERA: a posicao comprada gerava UMA funcao so, a que o estilo do
        #  card escolhe. A outra funcao da mesma familia nunca rodava.
        #
        #  POR QUE ISSO ERA ERRADO, medido em 18/08 nas 12.368 linhas:
        #     posicao comprada em que o estilo ATIVA ..... 2.218 rodam 1 funcao
        #     posicao comprada em que o estilo NAO ativa . 5.492 rodam 1 funcao
        #  Quando o estilo nao ativa, as duas funcoes valem O MESMO em estilo — e
        #  o sistema escolhia uma sem criterio nenhum. Escolha arbitraria.
        #
        #  ⛔ A POSICAO NATIVA JA FAZIA ISSO (`for f in familia(nat_pt)` acima).
        #     A comprada e que era o unico lugar cortado.
        #
        #  ⛔ ATIVA x BASICA NAO E DESCARTE, E ROTULO. As duas rodam; a tela e que
        #     separa no modal. Sem o rotulo, 527 cartas apareceriam em dez funcoes
        #     cada sem ninguem saber quais valem.
        for p in posicoes:
            if normaliza(p, None)[0] == nat_pt:
                continue
            f = funcao_nativa(p, est)
            # ⛔ SA NAO TEM FAMILIA PROPRIA — o ESTILO decide para qual casa ele
            #    vai. Achado ao testar em 18/08: chamar familia('SA') direto
            #    devolve a UNIAO das duas casas (Segundo atacante, Meia ofensivo
            #    armador, Centroavante fixo, Centroavante movel, Falso nove) e a
            #    carta ganhava CINCO funcoes por uma posicao comprada so.
            #    A posicao NATIVA ja resolvia isso antes de chamar familia(); a
            #    comprada tem que fazer igual.
            p_fam = normaliza(p, None)[0]
            if p_fam == 'SA':
                p_fam = SA_FAMILIA.get(normaliza(p, est)[1]) or p_fam
            fam = familia(p_fam)
            if not fam:
                fora.append((b, c.get('nome'), c.get('tier'), c.get('ovr'), p,
                             'posicao sem familia: %r' % (p,)))
                continue
            if not f:
                fora.append((b, c.get('nome'), c.get('tier'), c.get('ovr'), p,
                             'estilo/posicao sem regra: %r + %r' % (p, est)))
            for g in fam:
                funcs.setdefault(g, ('comprada:' + p) if g == f else ('basica:' + p))

        if not funcs:
            fora.append((b, c.get('nome'), c.get('tier'), c.get('ovr'), nat,
                         'posicao nativa desconhecida'))
            continue
        # ⛔ A TRAVA DE POOL VAZIO CAIU — 08/08, ordem do Luis. NAO REPOR.
        # Ela existia porque o `falta` vinha da comunidade e podia ser zero. O pool
        # NAO vem mais do `falta`: vem da regra do jogo — as 44 comuns menos as que o
        # card ja tem (roda_lote_v6.py, POOL='regra'). Card novo, sem `falta` nenhum,
        # tem pool cheio do mesmo jeito. E carta que nao evolui tem pool vazio DE
        # PROPOSITO (nao adiciona habilidade). A trava perdeu o objeto.
        #
        # Custo de ter reposto por engano, medido em 08/08 quando ela voltou de carona
        # numa copia velha: 209 linhas / 73 cards segurados, entre eles 14 DOS 21
        # CARDS NOVOS da home do efHub — incluindo gente da campanha Vozinha.
        #
        # No lugar dela, um AVISO (sugestao da sessao do motor): nao segura a linha,
        # so nao deixa passar calado.
        sem_pool.append(b) if not (set(c.get('falta') or []) | set(FALTA.get(b) or [])) else None

        # ⛔ 18/08 — A BASICA NAO ENTRA SE O POOL ESTIVER VAZIO.
        #    Ordem do Luis, 18/08: mandar estas linhas direto para o motor sem
        #    passar pela coleta "e um caso EXCEPCIONAL". Excecao boa nao vira
        #    regra e nao carrega lixo junto.
        #
        #    Medido em 18/08 nas 12.368 linhas ja rodadas:
        #       linha de carta com pool VAZIO  ... b1 mediana -177,4
        #       linha de carta com pool cheio ... b1 mediana  -14,9
        #    e 312 linhas rodaram com n_pool = 0. Nota de pool zero nao e
        #    "deprimida", e INUTILIZAVEL — e nota errada e pior que nota nenhuma.
        #
        #    ⛔ ISTO NAO E A TRAVA DE 08/08 VOLTANDO. Aquela segurava a carta
        #       INTEIRA; esta segura SO A BASICA NOVA. A linha ATIVA continua
        #       entrando exatamente como antes — nada que rodava parou de rodar.
        _pool_vazio = not (set(c.get('falta') or []) | set(FALTA.get(b) or []))
        for f, o in funcs.items():
            _basica = o.startswith('basica:')
            _r = {'card_id': b, 'nome': c.get('nome'), 'funcao': f,
                  'origem': o, 'tier': c.get('tier'), 'ovr': c.get('ovr') or 0,
                  'orc': orc, 'progressao': bool(orc), 'estilo': est,
                  # ⛔ `estilo_ativa` e o que a tela usa para separar ATIVA de
                  #    BASICA no modal. E medido: o estilo do card ativa aqui?
                  'estilo_ativa': not _basica,
                  'lancamento': b in LANCA, 'box': CAMPANHA.get(b)}
            if _basica and _pool_vazio:
                _r['por_que_adiada'] = 'basica nova de carta com pool vazio'
                adiada.append(_r)
            else:
                fila.append(_r)

    # 1o os cards em lancamento (campanhas no ar). Depois a regra normal: S+, S, A, B, C, D.
    # ⛔ CORRECAO 08/08: DENTRO do grupo de lancamento o tier NAO ordena.
    # Card novo entra com tier '?' (o efHub so da tier depois de votacao), e
    # TIER_ORD.get('?', 9) jogava justamente os cards NOVOS para o FIM da fila de
    # lancamento — o contrario da ordem do Luis. Medido em 08/08: dos 121 em
    # lancamento 33 ja tinham rodado e dos 21 NOVOS, zero.
    # Dentro do lancamento a ordem e so OVR decrescente.
    # ⛔ 18/08 — AS BASICAS VAO ATRAS. Ordem do Luis: "a gente manda as que a
    #    gente identificou na frente e elas atras". A basica e aditivo: ninguem
    #    esta esperando por ela, e sao 8.393 linhas. Ela nao pode atrasar carta
    #    de lancamento nem carta consertada.
    #    ⛔ Lancamento continua furando tudo, inclusive isto.
    #    ⛔ A BASICA E A PRIMEIRA CHAVE, ATE NA FRENTE DO LANCAMENTO. Testado em
    #    18/08: com o lancamento em primeiro, a basica de uma carta em campanha
    #    caia na posicao 5 da fila e passava na frente de 12 mil linhas ATIVAS.
    #    Carta de lancamento continua furando a fila — mas nas funcoes em que o
    #    estilo dela ATIVA. As basicas dela sao aditivo como as outras.
    #    ⛔ E DENTRO DAS BASICAS A ORDEM E O OVERALL, SO ELE. Ordem do Luis,
    #    18/08: "depois coloca pra rodar as outras, as seis mil e tantas linhas,
    #    POR ORDEM DE OVERALL". O tier nao entra aqui: entre as basicas nao ha
    #    carta esperada nem carta de campanha — sao todas aditivo, e o unico
    #    criterio que ele quer e a carta mais forte primeiro.
    fila.sort(key=lambda r: (0 if r.get('estilo_ativa', True) else 1,
                             0 if (not r.get('estilo_ativa', True) or r['lancamento']) else 1,
                             (TIER_ORD.get(r['tier'], 9)
                              if (r.get('estilo_ativa', True) and not r['lancamento']) else 0),
                             -r['ovr'], r['card_id'], r['funcao']))
    for i, r in enumerate(fila, 1):
        r['n'] = i

    json.dump(fila, open('fila_v6.json', 'w', encoding='utf-8'), ensure_ascii=False)
    adiada.sort(key=lambda r: -(r['ovr'] or 0))
    for i, r in enumerate(adiada, 1): r['n'] = i
    json.dump(adiada, open(ADIADA_POOL, 'w', encoding='utf-8'), ensure_ascii=False)
    with open('fila_EXCLUIDOS.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['id', 'nome', 'tier', 'ovr', 'detalhe', 'motivo'])
        w.writerows(fora)

    seg = len(fila) * 21
    print('=' * 64)
    print('  FILA v6 — um card, todas as funcoes que ele pode ocupar')
    print('=' * 64)
    n_lanc = sum(1 for r in fila if r['lancamento'])
    print('cards base .............', len(base))
    print('EM LANCAMENTO (furam a fila)', n_lanc, 'linhas')
    print('com a box de origem gravada', sum(1 for r in fila if r.get('box')), 'linhas',
          '·', len({r['box'] for r in fila if r.get('box')}), 'campanhas')
    print('LINHAS NA FILA .........', len(fila))
    print('excluidas com motivo ...', len(fora), '-> fila_EXCLUIDOS.csv')
    print('ADIADAS por pool vazio .', len(adiada), 'linhas -> ' + ADIADA_POOL)
    if adiada:
        print('       so BASICA nova. A linha ATIVA de todas elas entrou normal.')
        print('       elas entram quando o `falta` fechar — nao se perdem.')
    if sem_pool:
        print('AVISO: sem `falta` proprio ...', len(set(sem_pool)), 'cards — RODAM NORMAL.')
        print('       o pool deles vem da regra do jogo, nao do falta. So nao passa calado.')
    print()
    o = collections.Counter(r['origem'].split(':')[0] for r in fila)
    print('   por posicao nativa .', o.get('nativa', 0))
    print('   por posicao comprada', o.get('comprada', 0))
    print()
    for t, n in sorted(collections.Counter(r['tier'] for r in fila).items(),
                       key=lambda x: TIER_ORD.get(x[0], 9)):
        print('   tier %-3s %6d linhas' % (t, n))
    print()
    print('custo a 21 s/linha: %.0f h  (%.1f dias)' % (seg / 3600, seg / 86400))
    print('gerado: fila_v6.json')


if __name__ == '__main__':
    main()
