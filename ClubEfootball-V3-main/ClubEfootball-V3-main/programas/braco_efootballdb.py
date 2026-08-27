# -*- coding: utf-8 -*-
"""
O BRACO QUE BUSCA SOZINHO — passo 5, segunda metade. 16/08/2026

O QUE ELE E:
  O primeiro pedaco do motor de atualizacao. Le a fila de coleta, visita SO as
  cartas que estao em "nao sei", e grava o que veio — com a data e de quem veio.

POR QUE SO O efootballdb:
  Medido, nao suposto. Esta escrito no COLETAR-EFHUB-PELO-CONSOLE.md (10/08) e
  repetido dentro do coletar_so_os_furados.py (14/08):

     efHub ....... 403 fora do Chrome logado. So pelo Console (F12).
     efScout ..... nao atende por carta. Entrega o banco inteiro num .bin.
     efootbase ... so com o navegador aberto, colando o script.
     efootballdb . RESPONDE DIRETO. E uma visita traz box, data e vaga.

  Entao ele e o unico braco que anda sem ninguem olhando. Os outros tres viram
  gerador de script para o Console — outro programa, outra hora.

⛔ NAO INVENTA FONTE NOVA. Usa a mesma rota e o mesmo cabecalho que o
   coletar_so_os_furados.py ja usava e que ja funcionava.

⛔ NUNCA APAGA DADO BOM. So escreve onde estava vazio.
⛔ Para a qualquer momento (Ctrl+C ou fechar): grava a cada 25 e CONTINUA de
   onde parou na proxima vez.
"""
import json, os, sys, io, time, shutil, urllib.request, urllib.error
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def P(*a):
    print(*a, flush=True)


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
    P('⛔ nao achei o config.txt subindo a partir de %s' % AQUI)
    sys.exit(1)
os.chdir(CASA)

# quantas cartas nesta rodada — vazio = todas
LIMITE = None
for i, a in enumerate(sys.argv):
    if a.lower().startswith('--limite') and i + 1 < len(sys.argv):
        try:
            LIMITE = int(sys.argv[i + 1])
        except Exception:
            LIMITE = None
    elif a.isdigit():
        LIMITE = int(a)

FILA = os.path.join('dados', 'fila_de_coleta.json')
BOX = 'box_por_card.json'
VAGA = 'vaga_por_card.json'
RECIBOS = os.path.join('dados', 'recibos_de_coleta.jsonl')
DIVERG = os.path.join('dados', 'divergencias.json')
JA = os.path.join('dados', 'ja_perguntei.json')

# ⛔ mesma rota e mesmo cabecalho do coletar_so_os_furados.py. Nao invento fonte.
ROTA = 'https://api.efootballdb.com/api/2022/players/%s'
CAB = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'),
       'Accept': 'application/json', 'Referer': 'https://www.efootballdb.com/'}
PAUSA = 0.15

# as mesmas 26 flags do coletar_vaga_efootballdb.py, para classificar a vaga
FLAGS = ['low_pass', 'attacking_prowess', 'body_control', 'place_kicking', 'jump',
         'catching', 'aggression', 'physical_contact', 'speed', 'swerve', 'clearing',
         'reflexes', 'stamina', 'explosive_power', 'coverage', 'lofted_pass',
         'tackling', 'dribbling', 'finishing', 'kicking_power', 'goalkeeping',
         'defensive_awareness', 'defensive_engagement', 'tight_possession',
         'ball_control', 'header']


def tipo(b):
    if not isinstance(b, dict):
        return None
    if sum(b.get(f) or 0 for f in FLAGS) == 0:
        if b.get('booster_type') == 4 or b.get('pes_id') == 136:
            return 'VAGA'
        return 'ZERADO?'
    return 'NATIVO'


def pega(pid, tentativas=3):
    ultimo = None
    for k in range(tentativas):
        try:
            req = urllib.request.Request(ROTA % pid, headers=CAB)
            with urllib.request.urlopen(req, timeout=25) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            d = j.get('data', j) if isinstance(j, dict) else j
            if isinstance(d, list):
                d = d[0] if d else None
            return (d if isinstance(d, dict) else None), None
        except urllib.error.HTTPError as e:
            ultimo = 'HTTP %s' % e.code
            if e.code == 404:
                return None, 'HTTP 404'        # nao existe la: nao adianta insistir
            time.sleep(0.8 * (k + 1))
        except Exception as e:
            ultimo = str(e)[:60]
            time.sleep(0.8 * (k + 1))
    return None, (ultimo or 'sem resposta')


def ler(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    try:
        return json.load(open(caminho, encoding='utf-8'))
    except Exception:
        return padrao


# ============================================================================
P('=' * 78)
P('  O BRACO QUE BUSCA SOZINHO  ·  ' + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
P('=' * 78)
P('')
P('  Fonte: efootballdb — a unica que responde fora do navegador.')
P('  Uma visita por carta traz BOX, DATA DE LANCAMENTO e VAGA de uma vez.')
P('')
P('  ⛔ nunca apaga dado bom · grava a cada 25 · continua de onde parou')
P('  ⛔ pode fechar a janela a hora que quiser')
P('')

if not os.path.exists(FILA):
    P('⛔ nao achei o %s.' % FILA)
    P('   Rode antes o FILA-DE-COLETA.bat. Nada foi feito.')
    sys.exit(1)

F = json.load(open(FILA, encoding='utf-8'))
porc = F.get('por_campo') or {}
quando_a_fila = (F.get('gerado_em') or '')[:16]
P('  fila lida ................. gerada em %s' % quando_a_fila)

# --------------------------------------------- quem o efootballdb responde
MEUS = [c for c, v in porc.items()
        if (v.get('quem_perguntar') or [None])[0] == 'efootballdb']
if not MEUS:
    P('')
    P('  ⛔ a fila nao tem nenhum campo cujo primeiro da vez seja o efootballdb.')
    P('     Ou ja acabou, ou a fila esta velha. Rode o FILA-DE-COLETA.bat.')
    sys.exit(1)

P('  campos que ele responde ... %s' % ', '.join(sorted(MEUS)))

# ============================================================================
#  A CHAVE COMPOSTA — carta@posicao
# ============================================================================
#  ⛔ 16/08 09h20: o braco levou 404 em 92 de cada 100 cartas. Nao era a fonte:
#     73% dos ids da fila sao COMPOSTOS — `57309@ZC`, `105661027358435@GK`.
#     E a carta MAIS a posicao comprada. O efootballdb nao conhece `@ZC`.
#
#     Medido: 5.017 linhas na fila, mas so 2.402 CARTAS de verdade. A mesma
#     carta aparecia ate 19 vezes, uma por posicao — e cada uma ia virar uma
#     visita.
#
#  box, data e vaga sao da CARTA, nao da posicao. Entao: pergunta uma vez pelo
#  id de verdade, e a resposta vale para todas as linhas daquela carta.
por_carta = {}          # id REAL -> campos
apelidos = {}           # id REAL -> as linhas da fila que ele atende
for campo in MEUS:
    for cid in (porc[campo].get('cartas_a_perguntar') or []):
        cid = str(cid)
        real = cid.split('@')[0]
        por_carta.setdefault(real, set()).add(campo)
        apelidos.setdefault(real, set()).add(cid)

compostos = sum(1 for v in apelidos.values() for a in v if '@' in a)
ordem = sorted(por_carta, key=lambda c: -len(por_carta[c]))
P('  linhas na fila ............ %d' % sum(len(v) for v in apelidos.values()))
P('     delas com @posicao ..... %d  (carta + posicao comprada)' % compostos)
P('  CARTAS de verdade ......... %d   <<< e isto que se visita' % len(ordem))
for campo in sorted(MEUS, key=lambda c: -len(porc[c].get('cartas_a_perguntar') or [])):
    P('     %-10s %6d cartas em "nao sei"' % (campo, len(porc[campo].get('cartas_a_perguntar') or [])))

if LIMITE:
    ordem = ordem[:LIMITE]
    P('')
    P('  ⚠️  LIMITE desta rodada ..... %d cartas (voce pediu)' % LIMITE)

P('')
P('  tempo estimado ............ ~%d minuto(s)' % max(1, int(len(ordem) * 0.45 / 60) + 1))
P('     (era %d visitas antes de juntar a carta com as posicoes dela)' % sum(len(v) for v in apelidos.values()))
P('')
P('-' * 78)

# ============================================================================
#  A BASE ESTA MAIS VELHA QUE A COLETA?
# ============================================================================
#  ⛔ 16/08 09h45: a fila le o dados/base_unica.json. O que este braco traz vai
#     para box_por_card.json e vaga_por_card.json. Se ninguem rodar o
#     UNIFICAR-BASE entre uma coisa e outra, a fila pede DE NOVO o que ja foi
#     coletado — e o braco chega la, ve que ja tem, e nao tem o que fazer.
#     Foi assim que uma rodada inteira deu zero em tudo. Melhor avisar do que
#     deixar o Luis descobrir por um placar de zeros.
_bu = os.path.join('dados', 'base_unica.json')
if os.path.exists(_bu):
    _t_base = os.path.getmtime(_bu)
    _mais_novos = [c for c in (BOX, VAGA) if os.path.exists(c) and os.path.getmtime(c) > _t_base]
    if _mais_novos:
        P('  ⚠️  A BASE ESTA MAIS VELHA QUE A COLETA.')
        P('      base_unica.json ..... %s' % datetime.fromtimestamp(_t_base).strftime('%d/%m %H:%M'))
        for c in _mais_novos:
            P('      %-20s %s   <<< mais novo' % (c, datetime.fromtimestamp(os.path.getmtime(c)).strftime('%d/%m %H:%M')))
        P('')
        P('      A fila foi montada da base velha, entao ela vai pedir coisa que')
        P('      voce JA TEM. Nao estraga nada — so gasta tempo a toa.')
        P('')
        P('      O certo e: UNIFICAR-BASE.bat -> FILA-DE-COLETA.bat -> este aqui.')
        P('')

# ------------------------------------------------------------------ backup
B = ler(BOX, {})
V = ler(VAGA, {})
carimbo = datetime.now().strftime('%Y%m%d-%H%M%S')
for cam, dado in ((BOX, B), (VAGA, V)):
    if os.path.exists(cam):
        shutil.copy2(cam, cam + '.ANTES-DO-BRACO-' + carimbo)
P('  backup feito .............. %s.ANTES-DO-BRACO-%s (e o da vaga)' % (BOX, carimbo))
P('')

# ------------------------------------------------------------------ buscar
novos = {'box': 0, 'dt': 0, 'vaga': 0}
vazios = {'box': 0, 'dt': 0, 'vaga': 0}
# ⛔ 16/08 09h45: tres caminhos do codigo NAO tinham contador — quando a fonte
#    trazia o dado e a gente JA TINHA, e quando a contraprova pegava divergencia.
#    O placar dava zero em tudo e parecia programa morto. Todo desfecho tem de
#    cair em algum numero, senao a tela mente por omissao.
ja_tinha = {'box': 0, 'dt': 0, 'vaga': 0}
divergiu = 0
erros = 0
nao_existe = 0
visitadas = 0
recibos = []
divergencias = []

# ============================================================================
#  O QUE JA FOI PERGUNTADO — o conserto do laco infinito
# ============================================================================
#  ⛔ 16/08 09h15: o braco visitou 350 cartas, o efootballdb respondeu "nao
#     tenho" em todas, e NADA registrou isso. Na proxima fila as mesmas 350
#     voltavam para o comeco da fila. Para sempre.
#
#     "Nao tem" e RESPOSTA, nao buraco. Quem respondeu tem de ficar gravado,
#     senao a fila pergunta a mesma coisa a mesma fonte todo dia.
#
#  Este arquivo e o recibo em forma de indice: carta -> campo -> quem
#  respondeu, quando, e o que disse. A fila_de_coleta le dele.
JAP = {}
if os.path.exists(JA):
    try:
        JAP = (json.load(open(JA, encoding='utf-8')) or {}).get('perguntas') or {}
    except Exception:
        JAP = {}

# ---- LIMPEZA DO ENGANO DAS 09h08 ------------------------------------------
# ⛔ A rodada das 09h08 perguntou pelos ids COMPOSTOS (`57309@ZC`) e levou 404.
#    Ela gravou "nao existe nesta fonte" para 92 de cada 100 — e aquilo tiraria
#    essas cartas da fila PARA SEMPRE, por um erro meu, nao por resposta da
#    fonte. Quem levou 404 com id composto nunca foi perguntado de verdade.
#    Entao esse registro sai. Registro errado e pior que registro nenhum.
_sujo = 0
for _chave in list(JAP):
    if '@' not in _chave:
        continue
    for _campo in list(JAP[_chave]):
        if (JAP[_chave][_campo] or {}).get('resposta') == 'nao existe nesta fonte':
            del JAP[_chave][_campo]
            _sujo += 1
    if not JAP[_chave]:
        del JAP[_chave]
if _sujo:
    P('  ⚠️  apaguei %d registros de "nao existe" que vieram de id composto —' % _sujo)
    P('      aquelas cartas nunca foram perguntadas de verdade.')
    P('')
t0 = time.time()


def marca(pid, campo, resposta):
    # a resposta vale para a carta E para todas as linhas dela na fila
    # (`57309`, `57309@ZC`, `57309@VOL`...) — box, data e vaga sao da CARTA.
    r = {'fonte': 'efootballdb',
         'quando': datetime.now().isoformat(timespec='seconds'),
         'resposta': resposta}
    for chave in (apelidos.get(pid) or {pid}):
        JAP.setdefault(chave, {})[campo] = r


def grava():
    json.dump(B, open(BOX, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(V, open(VAGA, 'w', encoding='utf-8'), ensure_ascii=False)
    if recibos:
        with open(RECIBOS, 'a', encoding='utf-8') as f:
            for r in recibos:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        del recibos[:]
    json.dump({'o_que_e': ('o recibo em forma de indice: para cada carta e cada campo, '
                           'quem ja foi perguntado, quando, e o que respondeu. A fila de '
                           'coleta le daqui para nao perguntar duas vezes a mesma coisa a '
                           'mesma fonte. "nao tem" e resposta, nao buraco.'),
               'gerado_por': 'braco_efootballdb.py',
               'atualizado_em': datetime.now().isoformat(timespec='seconds'),
               'perguntas': JAP},
              open(JA, 'w', encoding='utf-8'), ensure_ascii=False)
    if divergencias:
        antigas = ler(DIVERG, {'o_que_e': '', 'itens': []})
        antigas['o_que_e'] = ('onde duas fontes disseram coisas diferentes sobre o mesmo '
                              'campo da mesma carta. NADA foi sobrescrito: os dois lados '
                              'estao aqui esperando uma TERCEIRA fonte desempatar. '
                              'Ordem do Luis, 16/08.')
        antigas.setdefault('itens', []).extend(divergencias)
        json.dump(antigas, open(DIVERG, 'w', encoding='utf-8'), ensure_ascii=False)
        del divergencias[:]


try:
    for k, pid in enumerate(ordem, 1):
        x, erro = pega(pid)
        visitadas += 1
        agora = datetime.now().isoformat(timespec='seconds')

        if erro == 'HTTP 404':
            nao_existe += 1
            for _c in por_carta[pid]:
                marca(pid, _c, 'nao existe nesta fonte')
            recibos.append({'card': pid, 'fonte': 'efootballdb', 'quando': agora,
                            'resposta': 'nao existe la', 'campos': sorted(por_carta[pid])})
        elif x is None:
            erros += 1
            recibos.append({'card': pid, 'fonte': 'efootballdb', 'quando': agora,
                            'resposta': 'erro: %s' % (erro or '?'),
                            'campos': sorted(por_carta[pid])})
        else:
            vd = x.get('variation_details') or {}
            if not isinstance(vd, dict):
                vd = {}
            atual = B.get(pid) or {}
            veio = {}

            # ================================================================
            #  A CONTRAPROVA — ordem do Luis, 16/08 03h30
            # ================================================================
            #  "se caso um banco de dados tenha divergencia com o outro e pra
            #   poder tirar contraprova"
            #
            #  Quando a fonte responde uma coisa DIFERENTE do que ja esta
            #  guardado, este programa NAO decide quem esta certo e NAO
            #  sobrescreve. Ele guarda os dois lados em dados/divergencias.json
            #  para uma terceira fonte desempatar.
            #
            #  ⛔ Escolher em silencio e o pior dos dois mundos: some o
            #     desacordo e ninguem nunca descobre que havia um.
            def confere(campo, novo, velho, de_onde_velho):
                if novo in (None, '') or velho in (None, ''):
                    return
                if str(novo).strip() == str(velho).strip():
                    return
                divergencias.append({
                    'card': pid, 'campo': campo,
                    'ja_estava': velho, 'de_onde': de_onde_velho,
                    'agora_disse': novo, 'quem_disse': 'efootballdb',
                    'quando': agora,
                    'o_que_fazer': 'terceira fonte desempata. NAO foi sobrescrito.'})

            confere('box', vd.get('name'), atual.get('box'), 'box_por_card.json')
            #  ⛔ 19/08 — O `release_date` DO efootballdb NAO E DATA DE LANCAMENTO.
            #  Medido no proprio divergencias.json desta pasta, 3.333 cartas:
            #      o que ja estava ..  2022:141 · 2023:444 · 2024:520 · 2025:1120 · 2026:1060
            #      o que ele disse ..  2026-07-09 nas 3.333, SEM UMA EXCECAO
            #  Uma fonte que responde a mesma data para tres mil cartas de anos
            #  diferentes nao esta dizendo quando a carta saiu: esta dizendo
            #  quando ELA capturou a carta. Ordem do Luis, 19/08: *"uma e a data
            #  da coleta do card, a outra e a data que a Konami fez o lancamento"*.
            #  A conferencia continua — o desacordo fica registrado —, mas com o
            #  nome certo, para ninguem ler isso como divergencia de lancamento.
            confere('coletado_no_efootballdb', vd.get('release_date'),
                    atual.get('dt'), 'box_por_card.json')

            # ⛔ so escrevo onde estava VAZIO. Dado bom nunca e apagado.
            if not vd.get('name'):
                vazios['box'] += 1
                marca(pid, 'box', 'nao tem')
            elif not atual.get('box'):
                novos['box'] += 1
                veio['box'] = vd.get('name')
                marca(pid, 'box', 'trouxe')
            else:
                ja_tinha['box'] += 1
                marca(pid, 'box', 'trouxe')

            #  ⛔ 19/08 — E POR ISSO ELE NAO ESCREVE MAIS O `dt`.
            #  Antes ele preenchia onde estava vazio — e onde estava vazio era
            #  justamente a carta que ninguem sabia a data. Resultado: a carta
            #  sem data recebia 2026-07-09 e passava a MENTIR com cara de
            #  certeza, enquanto a carta que ja tinha data era poupada pela
            #  regra do "nao sobrescreve". O pior dos dois mundos: so errava
            #  onde nao havia como conferir.
            #  Sem data continua sem data. Vazio e honesto; carimbo errado nao.
            if not vd.get('release_date'):
                vazios['dt'] += 1
                marca(pid, 'dt', 'nao tem')
            elif not atual.get('dt'):
                vazios['dt'] += 1
                marca(pid, 'dt', 'nao tem')
            else:
                ja_tinha['dt'] += 1
                marca(pid, 'dt', 'trouxe')

            B[pid] = {'box': atual.get('box') or vd.get('name'),
                      #  a data so vem do que ja estava — ver o bloco acima
                      'dt': atual.get('dt'),
                      'nm': atual.get('nm') or x.get('player_name')}

            v = [tipo(x.get('booster')), tipo(x.get('booster2')), tipo(x.get('booster3'))]
            antes = (V.get(pid) or {}).get('v')
            tinha_antes = bool(antes and any(t is not None for t in antes))
            if any(t is not None for t in v):
                if not tinha_antes:
                    novos['vaga'] += 1
                    veio['vaga'] = v
                    V[pid] = {'v': v, 'nm': x.get('player_name')}
                    marca(pid, 'vaga', 'trouxe')
                else:
                    _antes_n = len(divergencias)
                    confere('vaga', json.dumps(v, ensure_ascii=False),
                            json.dumps(antes, ensure_ascii=False), 'vaga_por_card.json')
                    # ⛔ tinha antes: NAO sobrescreve. Se divergiu, ja foi anotado.
                    if len(divergencias) > _antes_n:
                        divergiu += 1
                    else:
                        ja_tinha['vaga'] += 1
                        marca(pid, 'vaga', 'trouxe')
            else:
                vazios['vaga'] += 1
                marca(pid, 'vaga', 'nao tem')

            recibos.append({'card': pid, 'fonte': 'efootballdb', 'quando': agora,
                            'resposta': 'respondeu', 'trouxe': veio,
                            'campos': sorted(por_carta[pid])})

        if k % 25 == 0 or k == len(ordem):
            grava()
            pass_seg = time.time() - t0
            resta = (pass_seg / k) * (len(ordem) - k)
            # ⛔ mostrar TODOS os desfechos. A versao anterior so mostrava o que
            #    entrou, e por isso 350 cartas respondidas com "nao tenho"
            #    pareciam programa travado.
            P('   %6d/%-5d  NOVO box %-4d dt %-4d vaga %-4d  ·  ja tinha %-5d  ·  '
              'NAO TEM %-5d  ·  nao existe %-4d  ·  divergiu %-3d  ·  erro %-3d  ·  ~%d min'
              % (k, len(ordem), novos['box'], novos['dt'], novos['vaga'],
                 ja_tinha['box'] + ja_tinha['dt'] + ja_tinha['vaga'],
                 vazios['box'] + vazios['dt'] + vazios['vaga'],
                 nao_existe, divergiu, erros, int(resta / 60) + 1))
        time.sleep(PAUSA)

except KeyboardInterrupt:
    grava()
    P('')
    P('  ⚠️  VOCE MANDOU PARAR. O que veio ate agora esta gravado.')
    P('     Rode de novo quando quiser: ele pula o que ja tem.')

grava()

# ------------------------------------------------------------------ resultado
P('')
P('=' * 78)
P('  O QUE VEIO')
P('')
P('  cartas visitadas .......... %d' % visitadas)
P('  box novos ................. %d' % novos['box'])
P('  datas novas ............... %d' % novos['dt'])
P('  vagas novas ............... %d' % novos['vaga'])
P('')
P('  ja tinha aqui ............. box %d · data %d · vaga %d' %
  (ja_tinha['box'], ja_tinha['dt'], ja_tinha['vaga']))
P('     (a fonte trouxe e o arquivo local ja tinha igual — nada a fazer)')
P('  divergiu .................. %d' % divergiu)
P('  respondeu e NAO TEM ....... box %d · data %d · vaga %d' %
  (vazios['box'], vazios['dt'], vazios['vaga']))
P('     ⛔ isto NAO e falta. E resposta. Vira "nao se aplica", nao "nao sei".')
P('  nao existe no efootballdb . %d' % nao_existe)
P('  erros de rede ............. %d' % erros)
P('')
P('  ja perguntei .............. dados/ja_perguntei.json  (%d cartas)' % len(JAP))
P('     ⛔ e daqui que a fila aprende a NAO perguntar duas vezes a mesma')
P('        coisa para a mesma fonte. "nao tem" e resposta, nao buraco.')
P('')
P('  recibos gravados em ....... dados/recibos_de_coleta.jsonl')
P('     cada linha: qual carta, a quem perguntei, quando, e o que veio.')

# ------------------------------------------------------- A CONTRAPROVA
_d = ler(DIVERG, {'itens': []})
_itens = _d.get('itens') or []
P('')
P('  DIVERGENCIAS — as duas fontes disseram coisas diferentes')
P('')
if not _itens:
    P('     nenhuma. Onde as duas falaram, falaram igual.')
else:
    _porc = {}
    for it in _itens:
        _porc[it['campo']] = _porc.get(it['campo'], 0) + 1
    for campo, n in sorted(_porc.items(), key=lambda x: -x[1]):
        P('     %-10s %5d cartas' % (campo, n))
    P('')
    P('     ⛔ NADA foi sobrescrito. Os dois lados estao guardados em')
    P('        dados/divergencias.json, esperando uma TERCEIRA fonte.')
    P('     Exemplo:')
    for it in _itens[-2:]:
        P('        carta %s · %s' % (it['card'], it['campo']))
        P('           ja estava .. %s   (%s)' % (str(it['ja_estava'])[:40], it['de_onde']))
        P('           agora disse  %s   (%s)' % (str(it['agora_disse'])[:40], it['quem_disse']))

# ------------------------------------------------------------ CONFERENCIA
P('')
P('  CONFERENCIA — lendo os arquivos de volta do disco')
B2 = ler(BOX, {})
V2 = ler(VAGA, {})
com_box = sum(1 for v in B2.values() if isinstance(v, dict) and v.get('box'))
com_dt = sum(1 for v in B2.values() if isinstance(v, dict) and v.get('dt'))
com_vaga = sum(1 for v in V2.values()
               if isinstance(v, dict) and any(t is not None for t in (v.get('v') or [])))
P('     box_por_card.json ...... %d cartas · com box %d · com data %d' % (len(B2), com_box, com_dt))
P('     vaga_por_card.json ..... %d cartas · com vaga %d' % (len(V2), com_vaga))
if len(B2) < len(B) or len(V2) < len(V):
    P('')
    P('  ⛔ o arquivo ficou menor do que a memoria. PAREI para voce olhar.')
    P('     Os backups estao ao lado, com ANTES-DO-BRACO-%s no nome.' % carimbo)
    sys.exit(1)
P('     ✅ nada encolheu')

P('')
P('  O QUE FAZER AGORA:')
P('     1. UNIFICAR-BASE.bat    - poe o que veio na base unica')
P('     2. FILA-DE-COLETA.bat   - refaz a fila com o que ainda falta')
P('')
if visitadas < len(por_carta):
    P('  ⚠️  ainda faltam %d cartas nesta fonte. Rode este mesmo programa de novo.'
      % (len(por_carta) - visitadas))
P('  PRONTO.')
