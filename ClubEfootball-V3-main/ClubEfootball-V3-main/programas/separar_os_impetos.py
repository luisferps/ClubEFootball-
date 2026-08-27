# -*- coding: utf-8 -*-
"""
SEPARAR OS IMPETOS — 16/08/2026 (v2, refeito sobre o id do jogo)

O QUE ESTE PROGRAMA RESOLVE, nas palavras do Luis:

    "Todos os impetos tem o nome deles e a quantidade de pontos de atributo que
     eles dao a mais. O nome do impeto nao e 'Precisao mais quatro' — ele e
     Precisao, e o +4 e o quanto ele aumenta nos atributos que vem junto."

E a segunda ordem dele, no mesmo dia:

    "Era pra colocar chave unica em tudo."

============================================================================
 A CHAVE E O `id` DO JOGO. NAO E O NOME.
============================================================================
O `efscout_boosters.json` estava na pasta desde 14/08 e ninguem tinha aberto.
Ele traz os 402 impetos do jogo, com id proprio:

    {"id": 1, "name": "Shooting +1", "conditional": false,
     "booster_version": 1, "variable": false, "color": 0,
     "stat_modifiers": [[1,1],[6,1],[12,1],[14,1]]}

⛔ E SO O `id` SERVE DE CHAVE. Medido: a combinacao (nome, nivel, slot)
   REPETE em 62 casos, e nos 62 os atributos sao identicos:

       ('Shooting', 3, fixo)   id 23  version 1  variable nao  color 0
                               id 104 version 2  variable sim  color 1

   Sao impetos diferentes, de versoes diferentes do jogo. Qualquer chave
   montada a partir do nome funde os dois. Nem o conjunto de atributos
   distingue. So o id.

============================================================================
 O QUE MAIS ESTAVA NESSA FONTE E DERRUBA SUPOSICAO NOSSA
============================================================================
  `conditional` .... 232 condicionais · 170 fixos. O SLOT ESTA NO DADO.
                     Nao precisa mais inferir por "nivel 1 = condicional"
                     (roda_lote_v6.py linha 521) — aquilo era palpite.

  os niveis ........ FIXO        1:30 · 2:29 · 3:61 · 4:31 · 5:17 · 6:2
                     CONDICIONAL 1:3  · 2:3  · 3:220 · 4:3  · 5:3
                     O condicional NAO vive em nivel 1: 220 dos 232 sao +3.

  +4, +5, +6 ....... existem de verdade. A tela fabricava os +4 e +5
                     clonando as entradas +3. Nao precisa mais.

  ⚠️ tres entradas quebradas NA PROPRIA FONTE — nao invento o que falta:
       id 136  Bearer of Fate +1     ZERO atributos
       id 250  Ball Control +6       1 atributo
       id 265  Physical Contact +6   1 atributo

============================================================================
 O QUE ESTE PROGRAMA NAO FAZ
============================================================================
⛔ Nao adivinha. Cada card so recebe impeto quando a conta FECHA contra o
   `nm` dele, atributo por atributo. O que nao fechar vira `nao_sei` com o
   motivo escrito, nunca um chute.
⛔ Nao escreve no banco. Nao mexe em card nenhum. So le e grava arquivo.
"""
import json, os, re, sys, collections

# 16/08 — encoding='utf-8' EXPLICITO em todo open() de texto.
# Sem ele o Windows usa cp1252 e qualquer acento derruba o programa inteiro.
def le(caminho):
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)

def P(*a): print(*a, flush=True)

ATTRS_PT = ["Consciencia ofensiva", "Controle de bola", "Drible", "Posse de bola",
            "Passe rasteiro", "Passe alto", "Finalizacao", "Cabeceio",
            "Cobranca de falta", "Curva", "Velocidade", "Aceleracao",
            "Forca do chute", "Salto", "Contato fisico", "Equilibrio",
            "Resistencia", "Consciencia defensiva", "Roubo de bola",
            "Cobertura defensiva", "Agressividade", "Consciencia (GL)",
            "Defesa com as maos (GL)", "Rebatida (GL)", "Reflexos (GL)",
            "Alcance (GL)"]
ATTRS_EN = ["offensiveAwareness", "ballControl", "dribbling", "tightPossession",
            "lowPass", "loftedPass", "finishing", "heading", "setPieceTaking", "curl",
            "speed", "acceleration", "kickingPower", "jump", "physicalContact",
            "balance", "stamina", "defensiveAwareness", "ballWinning", "trackingBack",
            "aggression", "gkAwareness", "gkCatching", "gkClearing", "gkReflexes",
            "gkReach"]

# ============================================================================
#  OS DEGRAUS DO IMPETO CONDICIONAL
#  Lidos no videogame em 31/07/2026 e escritos no roda_lote_v6.py desde 05/08.
#  O degrau e QUANTOS JOGADORES DA CONDICAO estao em campo — nao e escolha, e
#  NAO e a mesma coisa que o nivel do catalogo.
# ============================================================================
DEGRAUS = {'1': {'jogadores': '1 a 7',  'obs': 'o ranking usa SEMPRE este'},
           '2': {'jogadores': '8 a 10'},
           '3': {'jogadores': '11 a 23'}}


def parte(nome):
    """'Shooting +3' -> ('Shooting', 3). Sem sufixo -> nivel None."""
    m = re.search(r'\s*\+(\d+)\s*$', nome or '')
    if not m:
        return (nome or '').strip(), None
    return nome[:m.start()].strip(), int(m.group(1))


def main():
    for f in ('efscout_boosters.json', 'dados/base_unica.json'):
        if not os.path.exists(f):
            P('⛔ nao achei %s na pasta.' % f)
            return 2

    P('=' * 70)
    P('  SEPARAR OS IMPETOS  —  a chave e o id do jogo')
    P('=' * 70)

    # ================================================================ 1
    P('')
    P('[1/5] o catalogo do jogo (efscout_boosters.json)')
    BST = le('efscout_boosters.json')
    ids = [b['id'] for b in BST]
    if len(set(ids)) != len(ids):
        P('   ⛔ o id NAO e unico nesta fonte. PARANDO — a chave nao serve.')
        return 1
    P('   boosters ........... %d · id unico, de %d a %d' % (len(BST), min(ids), max(ids)))

    cat = {}
    quebrados = []
    for b in BST:
        nome, nivel = parte(b.get('name'))
        sm = b.get('stat_modifiers') or []
        atrs = sorted(p[0] for p in sm)
        niveis = sorted({p[1] for p in sm})
        # ⚠️ entrada quebrada NA FONTE. Entra no catalogo marcada, para ninguem
        #    "consertar" inventando os atributos que faltam.
        ruim = None
        if len(atrs) not in (4, 26):
            ruim = ('a fonte traz %d atributos (o normal e 4, ou 26 no Total Package)'
                    % len(atrs))
        elif nivel is not None and niveis != [nivel]:
            ruim = ('o nivel do nome (%s) nao bate com o dos atributos (%s)'
                    % (nivel, niveis))
        if ruim:
            quebrados.append((b['id'], b.get('name'), ruim))
        cat[b['id']] = {
            'id': b['id'], 'nome_en': nome, 'nivel': nivel,
            'slot': 'condicional' if b.get('conditional') else 'fixo',
            'atributos': atrs,
            'versao_do_jogo': b.get('booster_version'),
            'variable': bool(b.get('variable')),
            'color': b.get('color'),
            'defeito_na_fonte': ruim,
        }
    fix = sum(1 for v in cat.values() if v['slot'] == 'fixo')
    P('   fixos %d · condicionais %d' % (fix, len(cat) - fix))
    P('   niveis ............. %s'
      % dict(sorted(collections.Counter(v['nivel'] for v in cat.values()).items())))
    if quebrados:
        P('   ⚠️  %d entradas quebradas NA FONTE (marcadas, nao consertadas):'
          % len(quebrados))
        for i, n, r in quebrados:
            P('        id %-4s %-24s %s' % (i, n, r))

    # ================================================================ 2
    #  O NOME EM PORTUGUES sai do CAT_dom.json casando pelo CONJUNTO DE
    #  ATRIBUTOS — nunca pela palavra. "Technique" vira "Tecnica" porque toca
    #  exatamente os mesmos 4 atributos, nao porque parece.
    P('')
    P('[2/5] o nome em portugues, pelo conjunto de atributos')
    pt_por_conjunto = {}
    if os.path.exists('CAT_dom.json'):
        for txt, _slot, pares in le('CAT_dom.json'):
            n, _ = parte(txt)
            pt_por_conjunto[frozenset(p[0] for p in pares)] = n
    #  ⛔ 16/08 — MEDIDO NO JOGO, PELO LUIS: o jogo NAO traduz estes nomes.
    #     Ele abriu o Joaquin Piquerez no PS5 e a ficha, EM PORTUGUES, diz
    #     "Total Package +3" — em ingles, do mesmo jeito.
    #
    #     Por isso "sem nome em portugues" tem de ser DOIS estados, nao um:
    #        nao_se_aplica = o jogo nao traduz. Nao ha o que coletar.
    #        nao_sei       = pode ter traducao e a gente nao tem.
    #
    #     Antes era um `false` so, e isso fez a sessao da tela gastar tempo
    #     tentando tapar um buraco que nao existe. O aviso foi dela.
    NAO_TRADUZ = {
        'Total Package': ('medido no jogo em 16/08/2026 (Joaquin Piquerez, PS5): '
                          'a ficha em portugues escreve "Total Package +3"'),
    }
    #  Nomes proprios de carta lendaria — MESMA familia do Total Package, e
    #  quase certamente tambem nao traduzem. Mas "quase certamente" nao e
    #  medido, e o Luis nao tem nenhuma dessas cartas para conferir.
    #  Ficam em nao_sei, com o motivo escrito. Um card cada.
    PROVAVEL_NAO_TRADUZ = {'Bearer of Fate', 'Son of God', 'King of Football',
                           'Le Petit Prince', 'The Undisputed', 'Magical',
                           'Natural-born', 'Natural Born', 'Striking'}

    achou = 0
    sem_pt = collections.Counter()
    for v in cat.values():
        pt = pt_por_conjunto.get(frozenset(v['atributos']))
        v['nome'] = pt or v['nome_en']
        if pt:
            v['nome_em_portugues'] = 'valor'
            achou += 1
        elif v['nome_en'] in NAO_TRADUZ:
            v['nome_em_portugues'] = 'nao_se_aplica'
            v['por_que'] = NAO_TRADUZ[v['nome_en']]
        else:
            v['nome_em_portugues'] = 'nao_sei'
            if v['nome_en'] in PROVAVEL_NAO_TRADUZ:
                v['por_que'] = ('nome proprio de carta lendaria — provavelmente o jogo '
                                'nao traduz, como o Total Package, mas NAO foi medido: '
                                'o Luis nao tem esta carta')
            sem_pt[v['nome_en']] += 1
    _na = sum(1 for v in cat.values() if v['nome_em_portugues'] == 'nao_se_aplica')
    P('   com nome em portugues ......... %d de %d' % (achou, len(cat)))
    P('   o jogo NAO traduz (medido) .... %d entradas' % _na)
    P('   em nao_sei .................... %d nomes distintos' % len(sem_pt))
    for n, q in sem_pt.most_common():
        P('        %-24s %3d entradas' % (n, q))

    # ================================================================ 3
    P('')
    P('[3/5] a base unica')
    base = le('dados/base_unica.json')
    cards = base.get('cards') or []
    P('   cards .............. %d' % len(cards))

    por_nome = collections.defaultdict(list)
    for v in cat.values():
        por_nome[(v['nome_en'], v['nivel'])].append(v)
        if v['tem_nome_em_portugues']:
            por_nome[(v['nome'], v['nivel'])].append(v)
    por_conjunto = collections.defaultdict(list)
    for v in cat.values():
        if v['nivel'] is not None and v['atributos']:
            por_conjunto[(frozenset(v['atributos']), v['nivel'])].append(v)

    NAO_E_NOME = {'não decomposto', 'nao decomposto', ''}

    def fecha(escolhidos, nm):
        """os impetos escolhidos reproduzem o `nm` do card?

        ⛔ A REGRA E SOMA, e nao ha duvida sobre isso. Duas provas:

        1. A EQUACAO 1, medida no eFootball em 04/08/2026 — 265 medicoes,
           2 cartas, 2 tecnicos, 10 proficiencias, 5 taticas, ZERO ERRO:

               1. x = base do atributo
               2. x = x + niveis da barra          -> MIN(99, x)
               3. x = x + TRUNCA(x * (m-1))        -> MIN(99, MAX(40, x))
               4. se for atributo do tecnico: x += 1        (passa de 99)
               5. PARA CADA IMPETO ATIVO que pegue o atributo: x += valor

           O passo 5 diz "para cada impeto: x += valor". Cada um soma o seu.

        2. O motor faz exatamente isso, motor.py linha 234:

               add = [self.nm[i] + (ex[i] if ex else 0) + ... ]
                      ^ o NATIVO      ^ o FABRICADO

           e linha 232, quando os DOIS slots sao fabricados:

               [va[i] + vb[i] for i in range(26)]

        Palavras do Luis, 16/08: "ele vai adicionar, tanto faz, e o mesmo ou
        se e outro".

        ⚠️ Quando o `nm` do card NAO bate com a soma mas bateria com o MAIOR,
           NAO e outra regra — e o dado da fonte estando errado naquele card.
           A funcao devolve isso separado, para virar defeito na lista em vez
           de virar regra nova.
        """
        soma = collections.Counter()
        mx = {}
        for i in escolhidos:
            for a in cat[i]['atributos']:
                soma[a] += cat[i]['nivel']
                mx[a] = max(mx.get(a, 0), cat[i]['nivel'])
        r = []
        if dict(soma) == nm:
            r.append('soma')
        elif mx == nm and mx != dict(soma):
            r.append('SO PELO MAIOR — o nm da fonte esta errado neste card')
        return r, dict(soma), mx

    def assinatura(t):
        """o que faz DIFERENCA na conta: os atributos e o nivel. So isso.

        ⛔ O `id` NAO entra: dois ids gemeos (versoes diferentes do jogo) tem
           os mesmos atributos e o mesmo nivel, e dao exatamente a mesma conta.
        ⛔ O `slot` NAO entra: o mesmo impeto existe como fixo E como
           condicional, com os mesmos atributos e nivel. Quem decide o slot e o
           campo `impeto_condicional` da base — nao a conta. Se ele nao disser,
           o slot fica `nao_sei` e o resto do impeto continua sabido. Jogar o
           card inteiro fora por causa de um campo seria perder 1.863 cards de
           informacao boa por uma duvida pequena.
        """
        return tuple(sorted((tuple(cat[i]['atributos']), cat[i]['nivel'])
                            for i in t))

    # ================================================================ 4
    P('')
    P('[4/5] separando card por card')
    saida = {}
    cont = collections.Counter()
    pend = []
    regra = collections.Counter()
    defeitos = []

    for c in cards:
        cid = str(c.get('id'))
        nm = {p[0]: p[1] for p in (c.get('nm') or []) if p}
        nomes = c.get('impeto_nomes') or []
        # o slot que a BASE ja sabe, por posicao na lista de nomes
        slot_da_base = c.get('impeto_condicional') or []

        if not c.get('impeto_tem'):
            # ZERADO x NAO_SE_APLICA: quem nao tem vaga NAO PODE ter impeto.
            # Quem tem vaga livre PODE ter e nao tem. Sao coisas diferentes.
            sit = c.get('impeto_situacao') or ''
            est = 'nao_se_aplica' if 'sem vaga' in sit else 'zerado'
            saida[cid] = {'estado': est, 'impetos': [], 'situacao': sit}
            cont[est] += 1
            continue

        boas = []
        motivo = None

        # ---- (a) a fonte NOMEOU: acha o id pelo nome + nivel
        nomeou = bool(nomes) and all(parte(n)[0] not in NAO_E_NOME
                                     and parte(n)[1] is not None for n in nomes)
        if nomeou:
            cands = [por_nome.get(parte(n)) for n in nomes]
            if all(cands):
                def combina(i, atual):
                    if i == len(cands):
                        r, _, _ = fecha(atual, nm)
                        if r:
                            boas.append((tuple(atual), r))
                        return
                    vistos = set()
                    for v in cands[i]:
                        if v['id'] in vistos:
                            continue
                        vistos.add(v['id'])
                        combina(i + 1, atual + [v['id']])
                combina(0, [])
                if not boas:
                    motivo = ('a fonte nomeou %s mas nenhum id do catalogo reproduz '
                              'o nm do card' % nomes)
            else:
                motivo = ('nome fora do catalogo do jogo: %s'
                          % [n for n, cd in zip(nomes, cands) if not cd])

        # ---- (b) a fonte NAO nomeou: tenta pelo conjunto de atributos
        elif nm:
            atrs = frozenset(nm)
            niveis = sorted(set(nm.values()))
            if len(niveis) == 1:
                for v in por_conjunto.get((atrs, niveis[0]), []):
                    boas.append(((v['id'],), ['soma', 'maior']))
            if not boas:
                # dois impetos empilhados — e por isso que o conjunto sozinho
                # nao casa: o atributo que os dois tocam saiu da conta simples.
                vs = [v for v in cat.values()
                      if v['nivel'] is not None and v['atributos']
                      and set(v['atributos']) <= atrs]
                for i, a in enumerate(vs):
                    for bb in vs[i:]:
                        if set(a['atributos']) | set(bb['atributos']) != atrs:
                            continue
                        r, _, _ = fecha([a['id'], bb['id']], nm)
                        if r:
                            boas.append((tuple(sorted([a['id'], bb['id']])), r))
            if not boas:
                motivo = ('a fonte nao decompos e nenhum impeto do catalogo '
                          'reproduz o nm')
        else:
            motivo = 'o card diz que tem impeto mas nao tem nm'

        # ---- decide, agrupando os gemeos (mesma conta, id diferente)
        escolha = None
        if boas and motivo is None:
            porass = {}
            for t, r in boas:
                porass.setdefault(assinatura(t), []).append((t, r))
            if len(porass) == 1:
                op = list(porass.values())[0]
                escolha = (op[0][0], op[0][1],
                           [o[0] for o in op] if len(op) > 1 else None)
            else:
                motivo = ('existem %d decomposicoes DIFERENTES possiveis — '
                          'nao da para escolher sem chutar' % len(porass))

        if escolha is None:
            saida[cid] = {'estado': 'nao_sei', 'impetos': [], 'por_que': motivo,
                          'o_que_a_fonte_disse': nomes, 'nm': sorted(nm.items())}
            cont['nao_sei'] += 1
            pend.append((cid, c.get('nome'), motivo, nomes))
            continue

        escolhidos, regras, gemeos = escolha
        #  se a base sabe o slot, prefere o id do catalogo que esta NAQUELE
        #  slot — mesmo atributos, mesmo nivel, so a identidade fica certa.
        aj = []
        for k, i in enumerate(escolhidos):
            if k < len(slot_da_base) and slot_da_base[k] is not None:
                quero = 'condicional' if slot_da_base[k] else 'fixo'
                if cat[i]['slot'] != quero:
                    troca = [w['id'] for w in cat.values()
                             if w['slot'] == quero and w['nivel'] == cat[i]['nivel']
                             and w['atributos'] == cat[i]['atributos']]
                    if troca:
                        i = troca[0]
            aj.append(i)
        escolhidos = tuple(aj)
        _, soma, mx = fecha(list(escolhidos), nm)
        if any('SO PELO MAIOR' in x for x in regras):
            regra['cards com o nm ERRADO na fonte'] += 1
            defeitos.append((cid, c.get('nome'),
                             [(a, nm.get(a), soma[a]) for a in sorted(soma)
                              if nm.get(a) != soma[a]],
                             [(cat[i]['nome'], cat[i]['nivel']) for i in escolhidos]))

        itens = []
        for k, i in enumerate(escolhidos):
            v = cat[i]
            #  O SLOT: quem manda e a base (`impeto_condicional`), porque o
            #  mesmo impeto existe nos dois slots com os mesmos atributos e
            #  nivel — a conta nao distingue. Se a base nao disser, fica
            #  `nao_sei`: o resto do impeto continua sabido.
            if k < len(slot_da_base) and slot_da_base[k] is not None:
                slot = 'condicional' if slot_da_base[k] else 'fixo'
                de_onde = 'impeto_condicional da base unica'
            else:
                slot = 'nao_sei'
                de_onde = 'a base nao disse, e a conta nao distingue os dois slots'
            itens.append({'id': v['id'], 'nome': v['nome'], 'nome_en': v['nome_en'],
                          'nivel': v['nivel'],
                          'slot': slot, 'slot_de_onde_veio': de_onde,
                          'slot_no_catalogo_deste_id': v['slot'],
                          'atributos': v['atributos'],
                          'atributos_pt': [ATTRS_PT[a] for a in v['atributos']],
                          'versao_do_jogo': v['versao_do_jogo'],
                          'defeito_na_fonte': v['defeito_na_fonte']})
        d = {'estado': 'valor', 'impetos': itens,
             'conferido': 'reproduz o nm do card pelo ' + ' e pelo '.join(regras)}
        if gemeos:
            # ⚠️ a CONTA e a mesma; a IDENTIDADE e que fica em duvida. Guardo
            #    todos os ids possiveis em vez de escolher um.
            d['id_em_duvida'] = ('ha mais de um id com estes mesmos atributos e nivel '
                                 '(versoes diferentes do jogo). A conta nao muda.')
            d['ids_possiveis'] = [list(t) for t in gemeos]
            cont['   ...desses, com o id em duvida (gemeos)'] += 1
        saida[cid] = d
        cont['valor'] += 1
        if any(x['slot'] == 'condicional' for x in itens):
            cont['   ...desses, com condicional'] += 1
        if any(x['slot'] == 'nao_sei' for x in itens):
            cont['   ...desses, com o SLOT em nao_sei'] += 1

    for k, v in cont.most_common():
        P('   %-42s %5d' % (k, v))
    if defeitos:
        P('')
        P('   🔴 O `nm` DA FONTE ESTA ERRADO EM %d CARDS' % len(defeitos))
        P('      A Equacao 1 (passo 5) e o motor.py (linha 234) SOMAM cada impeto.')
        P('      Nestes o dado guardou o MAIOR em vez da soma — e o motor rodou')
        P('      esses cards com o atributo mais baixo do que o jogo da.')
        P('')
        for cid, nome, dif, its in defeitos:
            P('      %-22s %s' % ((nome or '?')[:22],
                                  ' + '.join('%s +%d' % t for t in its)))
            for a, tem, devia in dif:
                P('         atributo %-3d a fonte diz %s · a soma da %s   (%+d)'
                  % (a, tem, devia, devia - (tem or 0)))

    # ================================================================ 5
    P('')
    P('[5/5] gravando')
    cs = {
        '_leia': ('O catalogo dos impetos do jogo. A CHAVE E O `id` — nao o nome. '
                  'Medido: (nome, nivel, slot) repete em 62 casos, com os mesmos '
                  'atributos, porque sao versoes diferentes do jogo.'),
        '_fonte': 'efscout_boosters.json',
        '_o_nome_em_portugues': ('veio do CAT_dom.json casando pelo CONJUNTO DE '
                                 'ATRIBUTOS, nunca pela palavra.'),
        'degraus_do_condicional': DEGRAUS,
        '_degraus_medidos_em': '31/07/2026, lidos no videogame',
        '_atencao': ('o DEGRAU do condicional e quantos jogadores da condicao estao em '
                     'campo. NAO e o mesmo que o NIVEL do catalogo — o mesmo impeto '
                     'condicional existe em cinco niveis aqui.'),
        'atributos_pt': ATTRS_PT, 'atributos_en': ATTRS_EN,
        'impetos': [cat[i] for i in sorted(cat)],
    }
    with open('IMPETOS.json', 'w', encoding='utf-8') as f:
        json.dump(cs, f, ensure_ascii=False, indent=1)
    P('   IMPETOS.json ................. %d impetos, com id do jogo' % len(cat))

    with open('dados/impetos_por_card.json', 'w', encoding='utf-8') as f:
        json.dump({'_leia': ('O impeto de cada card: id do jogo, nome, nivel, slot e '
                             'quais atributos ele toca. '
                             'estado: valor · zerado · nao_se_aplica · nao_sei'),
                   '_a_chave': 'impetos[].id — o id do efscout_boosters.json',
                   'cards': saida}, f, ensure_ascii=False, indent=1)
    P('   dados/impetos_por_card.json .. %d cards' % len(saida))

    L = ['O QUE NAO DEU PARA SEPARAR — %d cards' % len(pend), '']
    for cid, nome, mot, nomes in pend:
        L.append('%-18s %-26s %s' % (cid, (nome or '?')[:26], mot))
        if nomes:
            L.append('%-18s   a fonte disse: %s' % ('', nomes))
    with open('IMPETOS-QUE-FALTAM.txt', 'w', encoding='utf-8') as f:
        f.write('\r\n'.join(L) + '\r\n')
    P('   IMPETOS-QUE-FALTAM.txt ....... %d pendencias' % len(pend))

    P('')
    P('=' * 70)
    if pend:
        P('  ⚠️  %d cards em NAO SEI — a lista esta no IMPETOS-QUE-FALTAM.txt.'
          % len(pend))
        P('      Nenhum deles foi chutado.')
    else:
        P('  ✅ TODOS os cards com impeto foram separados e conferidos.')
    P('=' * 70)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        P('')
        P('⛔ parou com erro. Nada ficou gravado pela metade: os arquivos so')
        P('   sao escritos no fim, depois de tudo conferido.')
        sys.exit(1)
