# -*- coding: utf-8 -*-
"""
SUBIR OS IMPETOS PARA O BANCO — 16/08/2026

Le o que o SEPARAR-OS-IMPETOS.bat gravou na pasta e poe no banco:

    IMPETOS.json .................. -> impeto  +  impeto_atributo
    dados/impetos_por_card.json ... -> card_impeto

⛔ NAO calcula nada. Nao decide nada. Se o numero estiver errado na pasta,
   sobe errado — o lugar de consertar e o separar_os_impetos.py, nao aqui.

⚠️ AS DUAS ARMADILHAS QUE JA CUSTARAM DIA DE TRABALHO NESTE SISTEMA, e que
   estao resolvidas aqui:

   1. COLUNAS UNIFORMES POR LOTE. O PostgREST exige que todas as linhas de
      um mesmo POST tenham EXATAMENTE as mesmas chaves, senao devolve
      400 "All object keys must match". A saida facil seria completar as
      linhas com null nas colunas que faltam — e isso SOBRESCREVERIA com
      vazio o que ja esta no banco. Aqui as linhas sao agrupadas pela
      assinatura de colunas e cada grupo sobe no seu proprio lote.

   2. CONTAR O QUE O SERVIDOR GRAVOU, nao o que eu mandei. Com
      return=representation o banco devolve as linhas que entraram; o
      programa conta ESSAS. Ja aconteceu de dizer "494 subidas" com o
      banco em zero.
"""
import json, os, sys, urllib.request, urllib.error, collections

def P(*a): print(*a, flush=True)

# 16/08 — encoding='utf-8' EXPLICITO em todo open() de texto.
def le_json(caminho):
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)

# ---- a chave -------------------------------------------------------------
def config():
    cfg = {}
    for ln in open('config.txt', encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if '=' in ln and not ln.startswith('#'):
            k, v = ln.split('=', 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg

C = config()
URL = (C.get('SUPABASE_URL') or '').rstrip('/')
KEY = C.get('SUPABASE_KEY') or C.get('SUPABASE_SERVICE_KEY') or ''
if not URL or not KEY:
    P('NAO ACHEI SUPABASE_URL / SUPABASE_KEY no config.txt. Nada foi feito.')
    sys.exit(1)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}


def conta(tabela):
    """Quantas linhas a tabela tem — PERGUNTANDO, nao baixando e contando.
    O Supabase devolve no maximo 1.000 linhas por leitura; contar baixando
    para em 1.000 e mente."""
    r = urllib.request.Request(URL + '/rest/v1/' + tabela + '?select=*',
                               headers=dict(H, Prefer='count=exact'), method='HEAD')
    try:
        with urllib.request.urlopen(r, timeout=90) as f:
            cr = f.headers.get('Content-Range') or ''
            return int(cr.split('/')[-1]) if '/' in cr else -1
    except urllib.error.HTTPError:
        return -1


def sobe(tabela, linhas, conflito, lote_tam=200):
    """Sobe agrupando por assinatura de colunas. Devolve (mandei, gravou)."""
    if not linhas:
        return 0, 0
    grupos = collections.OrderedDict()
    for L in linhas:
        grupos.setdefault(tuple(sorted(L.keys())), []).append(L)
    if len(grupos) > 1:
        P('      (%d conjuntos de colunas diferentes — cada um vai no seu lote)'
          % len(grupos))
    mandei = gravou = 0
    for _assin, grupo in grupos.items():
        for i in range(0, len(grupo), lote_tam):
            lote = grupo[i:i + lote_tam]
            u = URL + '/rest/v1/' + tabela + '?on_conflict=' + conflito
            d = json.dumps(lote, ensure_ascii=False).encode('utf-8')
            r = urllib.request.Request(u, data=d, headers=dict(
                H, Prefer='resolution=merge-duplicates,return=representation'),
                method='POST')
            try:
                with urllib.request.urlopen(r, timeout=300) as f:
                    corpo = f.read().decode('utf-8', 'replace')
                    try:
                        volta = json.loads(corpo)
                        g = len(volta) if isinstance(volta, list) else 0
                    except Exception:
                        g = 0
                    mandei += len(lote); gravou += g
                    if g != len(lote):
                        P('      ⚠️ mandei %d, o banco devolveu %d' % (len(lote), g))
                        if corpo[:200]:
                            P('         resposta: %s' % corpo[:200])
            except urllib.error.HTTPError as e:
                corpo = e.read().decode('utf-8', 'replace')
                P('      ⛔ ERRO %s ao subir para %s' % (e.code, tabela))
                P('         %s' % corpo[:500])   # a mensagem do servidor, inteira
                raise
            P('      %d/%d' % (mandei, len(linhas)))
    return mandei, gravou


def main():
    for f in ('IMPETOS.json', 'dados/impetos_por_card.json'):
        if not os.path.exists(f):
            P('⛔ nao achei %s — rode o SEPARAR-OS-IMPETOS.bat primeiro.' % f)
            return 2

    P('=' * 70)
    P('  SUBIR OS IMPETOS PARA O BANCO')
    P('=' * 70)

    cat = le_json('IMPETOS.json')
    imp = cat.get('impetos') or []
    pt = cat.get('atributos_pt') or []

    # ---------------------------------------------------------------- 1
    P('')
    P('[1/3] o catalogo -> impeto')
    linhas = [{
        'id': v['id'],
        'nome': v.get('nome') or v.get('nome_en'),
        'nome_en': v.get('nome_en'),
        'nivel': v.get('nivel'),
        'slot': v.get('slot'),
        'versao_do_jogo': v.get('versao_do_jogo'),
        'variavel': bool(v.get('variable')),
        'color': v.get('color'),
        'defeito_na_fonte': v.get('defeito_na_fonte'),
    } for v in imp]
    m, g = sobe('impeto', linhas, 'id')
    P('   %d mandadas · %d gravadas pelo banco' % (m, g))

    # ---------------------------------------------------------------- 2
    P('')
    P('[2/3] o que cada impeto aumenta -> impeto_atributo')
    linhas = []
    for v in imp:
        for a in (v.get('atributos') or []):
            linhas.append({'impeto_id': v['id'], 'atributo': a,
                           'atributo_nome': pt[a] if a < len(pt) else None,
                           'quanto': v.get('nivel')})
    m, g = sobe('impeto_atributo', linhas, 'impeto_id,atributo')
    P('   %d mandadas · %d gravadas pelo banco' % (m, g))

    # ---------------------------------------------------------------- 3
    P('')
    P('[3/3] o impeto de cada card -> card_impeto')
    cards = (le_json('dados/impetos_por_card.json').get('cards') or {})
    linhas = []
    for cid, d in cards.items():
        est = d.get('estado')
        its = d.get('impetos') or []
        if not its:
            # ⛔ Card SEM impeto tambem entra. "Nao tem linha" e ambiguo:
            #    nao diz se e zerado, se nao se aplica ou se ninguem olhou.
            #    Uma linha com o estado escrito diz.
            linhas.append({'card_id': cid, 'ordem': 0, 'impeto_id': None,
                           'slot': None, 'slot_de_onde': None,
                           'estado': est,
                           'por_que': d.get('por_que') or d.get('situacao'),
                           'ids_possiveis': None,
                           'conferido': None})
            continue
        poss = d.get('ids_possiveis')
        for k, it in enumerate(its):
            linhas.append({
                'card_id': cid, 'ordem': k, 'impeto_id': it.get('id'),
                'slot': it.get('slot'),
                'slot_de_onde': it.get('slot_de_onde_veio'),
                'estado': est,
                'por_que': d.get('id_em_duvida'),
                # so o que couber neste impeto, nao a lista inteira do card
                'ids_possiveis': (sorted({t[k] for t in poss if k < len(t)})
                                  if poss else None),
                'conferido': d.get('conferido'),
            })
    m, g = sobe('card_impeto', linhas, 'card_id,ordem')
    P('   %d mandadas · %d gravadas pelo banco' % (m, g))

    # ---------------------------------------------------------------- conferencia
    P('')
    P('=' * 70)
    P('  A CONFERENCIA — perguntando ao banco, nao ao programa')
    P('=' * 70)
    ok = True
    for t, esperado in (('impeto', len(imp)),
                        ('impeto_atributo', sum(len(v.get('atributos') or [])
                                                for v in imp)),
                        ('card_impeto', len(linhas))):
        n = conta(t)
        bate = (n == esperado)
        ok = ok and bate
        P('   %-18s banco %6s · esperado %6s  %s'
          % (t, n, esperado, '✅' if bate else '⛔'))
    P('')
    P('   %s' % ('✅ O BANCO TEM O IMPETO SEPARADO.' if ok
                 else '⛔ ALGUMA TABELA NAO FECHOU. Nao siga — o numero de cima diz qual.'))
    P('=' * 70)
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        P('')
        P('⛔ parou com erro. O que ja subiu esta no banco e sobe de novo sem')
        P('   duplicar (as tabelas tem chave). Pode rodar outra vez.')
        sys.exit(1)
