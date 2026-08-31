# -*- coding: utf-8 -*-
"""Auditoria somente leitura: legado de compatibilidade versus contrato V3.

A referência antiga é usada apenas para explicar compatibilidade. A identidade e o
fingerprint do contrato novo usam exclusivamente IDs/códigos físicos. Nomes de
apresentação nunca entram numa aprovação de cálculo.
"""

from __future__ import print_function

import argparse
import copy
import hashlib
import json
import sys
import urllib.error
import urllib.request


FONTE_ANTIGA = 'public.cartas_do_motor -> clube.carta_jogo e catalogos legados'
FONTE_NOVA = 'public.otimizador_cartas_v3 -> clube_novo normalizado por IDs'

CAMPOS_COMPATIBILIDADE = (
    'overall', 'posicao', 'atributos', 'altura', 'peso', 'idade', 'pe',
    'pe_ruim_uso', 'pe_ruim_precisao', 'resistencia_lesao', 'forma', 'corpo',
    'level_cap', 'orcamento', 'cap_estimado', 'habilidades_bits', 'aptidoes',
    'slot1_id', 'slot2_id', 'vaga_s1', 'vaga_s2', 'box', 'tipo'
)


def _json_canonico(valor):
    return json.dumps(valor, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'))


def fingerprint(valor):
    return hashlib.sha256(_json_canonico(valor).encode('utf-8')).hexdigest()


def _ordenados(linhas, chaves):
    def chave(x):
        return tuple(x.get(k) for k in chaves)
    return sorted((linhas or []), key=chave)


def assinatura_calculo(carta):
    """Retrato do que pode afetar vínculo/regra; exclui todo rótulo/nome."""
    return {
        'card_id': str(carta.get('card_id')),
        'atributos': _ordenados([
            {'indice_otimizador': x.get('indice_otimizador'),
             'codigo': x.get('codigo'), 'bit': x.get('bit'),
             'valor': x.get('valor')}
            for x in (carta.get('atributos') or [])
        ], ('indice_otimizador',)),
        'corpo': _ordenados([
            {'pos': x.get('pos'), 'codigo': x.get('codigo'),
             'valor': x.get('valor')}
            for x in (carta.get('corpo') or [])
        ], ('pos',)),
        'posicao_principal_id': carta.get('posicao_principal_id'),
        'posicoes': _ordenados([
            {'posicao_id': x.get('posicao_id'),
             'nivel_aptidao': x.get('nivel_aptidao')}
            for x in (carta.get('posicoes') or [])
        ], ('posicao_id',)),
        'habilidades': _ordenados([
            {'skill_id': h.get('skill_id'), 'ordem': h.get('ordem'),
             'bit_na_carta': h.get('bit_na_carta'), 'tipo': h.get('tipo'),
             'fabricavel': h.get('fabricavel'), 'vetada': h.get('vetada')}
            for h in (carta.get('habilidades') or [])
        ], ('skill_id',)),
        'estilos_ia': _ordenados([
            {'bit_estilo_ia': x.get('bit_estilo_ia')}
            for x in (carta.get('estilos_ia') or [])
        ], ('bit_estilo_ia',)),
        'pes': _ordenados([
            {'campo': x.get('campo'), 'valor': x.get('valor'), 'codigo': x.get('codigo')}
            for x in (carta.get('pes') or [])
        ], ('campo',)),
        'playstyles': _ordenados([
            {'slot_fisico': x.get('slot_fisico'),
             'playstyle_id': x.get('playstyle_id')}
            for x in (carta.get('playstyles') or [])
        ], ('slot_fisico',)),
        'dimensoes': carta.get('dimensoes') or {},
        'escalares': carta.get('escalares') or {},
        'impetos': _ordenados([
            {'slot': x.get('slot'), 'codigo_impeto': x.get('codigo_impeto'),
             'vaga': x.get('vaga'), 'condicional': x.get('condicional')}
            for x in (carta.get('impetos') or [])
        ], ('slot',)),
    }


def indexa(linhas):
    return {str(x.get('card_id')): x for x in (linhas or [])
            if isinstance(x, dict) and x.get('card_id')}


def _compat(carta):
    x = dict(carta.get('compatibilidade_legado') or {})
    x['card_id'] = carta.get('card_id')
    return x


def _valida_cardinalidades(carta):
    esperadas = {'atributos': 26, 'corpo': 12, 'posicoes': 12,
                 'posicao_principal': 1, 'pes': 3, 'playstyles': 2}
    atuais = carta.get('cardinalidades') or {}
    return {k: {'esperado': v, 'atual': atuais.get(k)}
            for k, v in esperadas.items() if atuais.get(k) != v}


def compara(antigas, novas):
    """Relatório determinístico; divergência sempre registra origem e valores."""
    a_por_id, n_por_id = indexa(antigas), indexa(novas)
    ids = sorted(set(a_por_id) | set(n_por_id))
    diferencas, cards = [], []

    for card_id in ids:
        antigo, novo = a_por_id.get(card_id), n_por_id.get(card_id)
        if antigo is None:
            diferencas.append({
                'card_id': card_id, 'campo': '$card', 'status': 'somente_novo',
                'origem_antiga': FONTE_ANTIGA, 'valor_antigo': None,
                'origem_nova': FONTE_NOVA, 'valor_novo': novo})
            continue
        if novo is None:
            diferencas.append({
                'card_id': card_id, 'campo': '$card', 'status': 'ausente_no_novo',
                'origem_antiga': FONTE_ANTIGA, 'valor_antigo': antigo,
                'origem_nova': FONTE_NOVA, 'valor_novo': None})
            continue

        gate = novo.get('gate') or {}
        if not gate.get('pode_rodar', False):
            diferencas.append({
                'card_id': card_id, 'campo': '$gate', 'status': 'bloqueado_gate_novo',
                'origem_antiga': FONTE_ANTIGA,
                'valor_antigo': {'roda_motor': antigo.get('roda_motor')},
                'origem_nova': FONTE_NOVA, 'valor_novo': gate})

        ruins = _valida_cardinalidades(novo)
        if ruins:
            diferencas.append({
                'card_id': card_id, 'campo': '$cardinalidades',
                'status': 'cardinalidade_nova_invalida',
                'origem_antiga': FONTE_ANTIGA, 'valor_antigo': None,
                'origem_nova': FONTE_NOVA, 'valor_novo': ruins})

        compat = _compat(novo)
        por_campo = []
        for campo in CAMPOS_COMPATIBILIDADE:
            va, vn = antigo.get(campo), compat.get(campo)
            if va != vn:
                d = {
                    'card_id': card_id, 'campo': campo,
                    'status': 'divergencia_compatibilidade_nao_classificada',
                    'origem_antiga': FONTE_ANTIGA, 'valor_antigo': va,
                    'origem_nova': FONTE_NOVA, 'valor_novo': vn,
                    'fingerprint_antigo': fingerprint(va),
                    'fingerprint_novo': fingerprint(vn)}
                diferencas.append(d); por_campo.append(campo)

        assinatura = assinatura_calculo(novo)
        cards.append({
            'card_id': card_id, 'gate_novo': gate,
            'cardinalidades_novas': novo.get('cardinalidades') or {},
            'fingerprint_calculo_por_ids': fingerprint(assinatura),
            'fingerprints_colecoes': {
                k: fingerprint(assinatura[k]) for k in
                ('atributos','corpo','posicoes','habilidades','estilos_ia','pes','playstyles','impetos')
            },
            'campos_compatibilidade_divergentes': por_campo})

    falhas = [d for d in diferencas if d['status'] in (
        'ausente_no_novo', 'divergencia_compatibilidade_nao_classificada',
        'cardinalidade_nova_invalida')]
    return {
        'contrato_auditado': 'otimizador_entradas_v3', 'somente_leitura': True,
        'origem_antiga': FONTE_ANTIGA, 'origem_nova': FONTE_NOVA,
        'regra_identidade': 'IDs/codigos fisicos; rotulos excluidos da assinatura',
        'quantidades': {'pedidos': len(ids), 'antigos': len(a_por_id),
                        'novos': len(n_por_id), 'diferencas': len(diferencas),
                        'falhas_de_paridade': len(falhas)},
        'fingerprints_lotes': {
            'antigo_compatibilidade': fingerprint(antigas or []),
            'novo_por_ids': fingerprint([assinatura_calculo(x) for x in (novas or [])])},
        'cards': cards, 'diferencas': diferencas,
        'aprovado_para_troca': not falhas and bool(n_por_id)}


def prova_renomeacao(carta):
    """Muda somente apresentação e prova que a assinatura de cálculo é invariável."""
    alterada = copy.deepcopy(carta)
    ap = alterada.setdefault('apresentacao', {})
    for k in list(ap):
        if isinstance(ap[k], str):
            ap[k] = 'RENOMEADO:' + ap[k]
    for colecao in ('atributos','corpo','habilidades','posicoes','estilos_ia','pes','playstyles','impetos'):
        for item in alterada.get(colecao) or []:
            for k in list(item):
                if ('nome' in k or 'rotulo' in k) and isinstance(item[k], str):
                    item[k] = 'RENOMEADO:' + item[k]
    return fingerprint(assinatura_calculo(carta)) == fingerprint(assinatura_calculo(alterada))


def le_config(caminho):
    cfg = {}
    with open(caminho, encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith('#') and '=' in linha:
                k, v = linha.split('=', 1); cfg[k.strip()] = v.strip()
    return cfg


def rpc(url, chave, nome, corpo, timeout=180):
    req = urllib.request.Request(
        url.rstrip('/') + '/rest/v1/rpc/' + nome,
        data=json.dumps(corpo).encode('utf-8'), method='POST',
        headers={'apikey': chave, 'Authorization': 'Bearer ' + chave,
                 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            texto = r.read().decode('utf-8')
            return json.loads(texto) if texto.strip() else None
    except urllib.error.HTTPError as e:
        raise RuntimeError('RPC %s falhou com HTTP %s; sem fallback' % (nome, e.code))


def cartas_novas_v3(url, chave, ids):
    """Lê apenas a ficha V3 e recusa versão inesperada, sem queda para V1/V2."""
    cartas = rpc(url, chave, 'otimizador_cartas_v3', {'p_ids': ids}) or []
    for carta in cartas:
        if carta.get('contrato') != 'otimizador_entradas_v3':
            raise RuntimeError('contrato novo inesperado; esperado otimizador_entradas_v3')
    return cartas


def compara_em_lotes(url, chave, ids, tamanho=200):
    """Compara a população sem guardar cartas idênticas no relatório."""
    ids = sorted(set(str(x).split('@')[0] for x in ids))
    h_antigo, h_novo = hashlib.sha256(), hashlib.sha256()
    diferencas, amostras_bloqueadas = [], []
    motivos, totais = {}, {'pedidos': len(ids), 'antigos': 0, 'novos': 0,
                            'aptos': 0, 'bloqueados': 0, 'falhas_de_paridade': 0}
    renomeacao = True

    for inicio in range(0, len(ids), tamanho):
        pedaco = ids[inicio:inicio + tamanho]
        antigas = rpc(url, chave, 'cartas_do_motor', {'p_ids': pedaco}) or []
        novas = cartas_novas_v3(url, chave, pedaco)
        parcial = compara(antigas, novas)
        totais['antigos'] += parcial['quantidades']['antigos']
        totais['novos'] += parcial['quantidades']['novos']
        totais['falhas_de_paridade'] += parcial['quantidades']['falhas_de_paridade']

        antigos_por_id = indexa(antigas)
        novos_por_id = indexa(novas)
        for card_id in pedaco:
            if card_id in antigos_por_id:
                h_antigo.update(_json_canonico(
                    [card_id, fingerprint(antigos_por_id[card_id])]).encode('utf-8'))
            novo = novos_por_id.get(card_id)
            if novo is not None:
                h_novo.update(_json_canonico(
                    [card_id, fingerprint(assinatura_calculo(novo))]).encode('utf-8'))
                gate = novo.get('gate') or {}
                if gate.get('pode_rodar'):
                    totais['aptos'] += 1
                else:
                    totais['bloqueados'] += 1
                    for motivo in gate.get('motivos') or ['gate_sem_motivo']:
                        motivos[motivo] = motivos.get(motivo, 0) + 1
                    if len(amostras_bloqueadas) < 20:
                        amostras_bloqueadas.append(
                            {'card_id': card_id, 'motivos': gate.get('motivos') or []})
                renomeacao = renomeacao and prova_renomeacao(novo)

        for d in parcial['diferencas']:
            if d.get('status') == 'bloqueado_gate_novo':
                continue
            if d.get('status') == 'somente_novo':
                novo = d.get('valor_novo') or {}
                diferencas.append({
                    'card_id': d['card_id'], 'campo': '$card',
                    'status': 'somente_novo',
                    'origem_antiga': d['origem_antiga'],
                    'origem_nova': d['origem_nova'],
                    'fingerprint_novo_por_ids': fingerprint(assinatura_calculo(novo)),
                    'gate_novo': novo.get('gate') or {}})
            else:
                diferencas.append(d)
        print('auditados %d/%d' % (min(inicio + tamanho, len(ids)), len(ids)),
              file=sys.stderr)

    return {
        'contrato_auditado': 'otimizador_entradas_v3', 'somente_leitura': True,
        'origem_antiga': FONTE_ANTIGA, 'origem_nova': FONTE_NOVA,
        'regra_identidade': 'IDs/codigos fisicos; rotulos excluidos da assinatura',
        'quantidades': totais,
        'gates': {'motivos': motivos, 'amostras_bloqueadas': amostras_bloqueadas},
        'fingerprints_lotes': {'antigo_compatibilidade': h_antigo.hexdigest(),
                               'novo_por_ids': h_novo.hexdigest()},
        'diferencas_tecnicas': diferencas,
        'prova_renomeacao': renomeacao,
        'aprovado_para_troca': totais['falhas_de_paridade'] == 0 and
                               totais['novos'] == len(ids) and renomeacao,
        'tamanho_lote': tamanho,
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    grupo = p.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--ids', nargs='+')
    grupo.add_argument('--todos-da-fila', action='store_true')
    grupo.add_argument('--todos', action='store_true')
    p.add_argument('--lote', type=int, default=200)
    p.add_argument('--config', default='config.txt')
    p.add_argument('--saida')
    args = p.parse_args(argv)
    cfg = le_config(args.config)
    url, chave = cfg.get('SUPABASE_URL', ''), cfg.get('SUPABASE_KEY', '')
    if not url or not chave:
        raise SystemExit('faltam SUPABASE_URL/SUPABASE_KEY; sem fallback')
    if args.todos:
        ids = rpc(url, chave, 'otimizador_ids_cartas_auditoria_v1', {}) or []
        rel = compara_em_lotes(url, chave, ids, max(1, args.lote))
        rel['universo'] = 'todas as cartas de clube_novo.carta_jogo'
    elif args.todos_da_fila:
        raise SystemExit(
            '--todos-da-fila foi desativado: a porta histórica de fila foi '
            'revogada. Use --ids ou --todos; sem fallback para clube.fila.')
    else:
        ids = [str(x).split('@')[0] for x in args.ids]
        antigas = rpc(url, chave, 'cartas_do_motor', {'p_ids': ids}) or []
        novas = cartas_novas_v3(url, chave, ids)
        rel = compara(antigas, novas)
        rel['prova_renomeacao'] = all(prova_renomeacao(x) for x in novas)
        if not rel['prova_renomeacao']:
            rel['aprovado_para_troca'] = False
    texto = json.dumps(rel, ensure_ascii=False, indent=2, sort_keys=True)
    if args.saida:
        with open(args.saida, 'w', encoding='utf-8') as f:
            f.write(texto + '\n')
    print(texto)
    return 0 if rel['aprovado_para_troca'] else 2


if __name__ == '__main__':
    sys.exit(main())
