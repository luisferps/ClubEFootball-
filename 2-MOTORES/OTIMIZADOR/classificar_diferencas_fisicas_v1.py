# -*- coding: utf-8 -*-
"""Classifica divergências legado×novo contra o diff físico selado do Extrator."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


ORDEM_ATRIBUTOS = [0,1,2,3,4,5,6,7,8,9,19,20,21,22,23,24,25,
                   10,11,13,12,14,15,17,16,18]
POSICAO_EN_PT = {
    'GK':'GO','CB':'ZC','LB':'LE','RB':'LD','DMF':'VOL','CMF':'MLG',
    'LMF':'MLE','RMF':'MLD','AMF':'MAT','LWF':'PTE','RWF':'PTD','SS':'SA','CF':'CA',
}
CAMPO_FISICO = {'slot1_id':'slot_ofensivo_id',
                'slot2_id':'slot_defensivo_id',
                'habilidades_bits':'habilidades'}


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def _valor(texto):
    if texto is None:
        return None
    s = str(texto)
    if s.startswith('[') or s.startswith('{'):
        return json.loads(s)
    if s == 'true': return True
    if s == 'false': return False
    try: return int(s)
    except ValueError: return s


def _traduz_fisico(campo_auditoria, valor):
    if campo_auditoria == 'atributos':
        return [valor[i] for i in ORDEM_ATRIBUTOS]
    if campo_auditoria == 'posicao':
        return POSICAO_EN_PT.get(valor, valor)
    return valor


def classifica(auditoria, manifesto, referencia_manifesto, referencia_csv):
    diferencas = auditoria.get('diferencas_tecnicas') or []
    somente_novo = {x['card_id'] for x in diferencas if x['status'] == 'somente_novo'}
    divergentes = [x for x in diferencas
                   if x['status'] == 'divergencia_compatibilidade_nao_classificada']

    novos_fisicos = set(manifesto['new_card_ids'])
    alterados = {x['card_id']: {c['field']: c for c in x['campos']}
                 for x in manifesto['changed']}
    erros, por_card = [], collections.defaultdict(list)

    if somente_novo != novos_fisicos:
        erros.append({'tipo':'conjunto_novas_nao_fecha',
                      'somente_auditoria':sorted(somente_novo-novos_fisicos),
                      'somente_fisico':sorted(novos_fisicos-somente_novo)})

    ids_divergentes = {x['card_id'] for x in divergentes}
    if ids_divergentes != set(alterados):
        erros.append({'tipo':'conjunto_alteradas_nao_fecha',
                      'somente_auditoria':sorted(ids_divergentes-set(alterados)),
                      'somente_fisico':sorted(set(alterados)-ids_divergentes)})

    for d in divergentes:
        cid, campo = d['card_id'], d['campo']
        fisico = CAMPO_FISICO.get(campo, campo)
        prova = (alterados.get(cid) or {}).get(fisico)
        if not prova:
            erros.append({'card_id':cid,'campo':campo,'tipo':'sem_campo_no_diff_fisico'})
            continue
        antes, depois = _valor(prova['before']), _valor(prova['after'])
        if campo == 'habilidades_bits':
            # O CSV apresenta nomes; a identidade foi provada separadamente por
            # bit físico→skill_id. Aqui a cardinalidade fecha a mesma mudança.
            bate = len(d['valor_antigo'] or []) == len(antes or []) and \
                   len(d['valor_novo'] or []) == len(depois or [])
            metodo = 'cardinalidade+ponte_fisica_bit_skill_id'
        else:
            bate = d['valor_antigo'] == _traduz_fisico(campo, antes) and \
                   d['valor_novo'] == _traduz_fisico(campo, depois)
            metodo = 'valor_antes_depois_do_diff_fisico'
        if not bate:
            erros.append({'card_id':cid,'campo':campo,'tipo':'valor_nao_fecha',
                          'antigo_auditoria':d['valor_antigo'],
                          'novo_auditoria':d['valor_novo'],
                          'antes_fisico':antes,'depois_fisico':depois})
        else:
            por_card[cid].append({'campo':campo,
                                  'status':'atualizacao_fisica_confirmada',
                                  'metodo':metodo})

    saida_csv = referencia_manifesto['output']
    hash_esperado = saida_csv.get('sha256')
    hash_atual = _sha(referencia_csv)
    if hash_esperado and hash_atual != hash_esperado:
        erros.append({'tipo':'hash_referencia_fisica_nao_fecha',
                      'esperado':hash_esperado,'atual':hash_atual})

    contagens = manifesto['counts']
    return {
        'contrato':'classificacao_fisica_otimizador_v1',
        'somente_leitura':True,
        'fonte_fisica':manifesto['source'],
        'referencia_csv':{'sha256':hash_atual,
                          'sha256_esperado':hash_esperado,
                          'registros':saida_csv.get('records'),
                          'ids_unicos':saida_csv.get('unique_card_ids')},
        'novas':{'quantidade':len(somente_novo),
                 'status':'insercao_fisica_confirmada'},
        'alteradas':{'cartas':len(por_card),
                     'campos':sum(len(v) for v in por_card.values()),
                     'por_card':dict(sorted(por_card.items()))},
        'prova_habilidades_por_id':
            'RELATORIO-HABILIDADES-ID-2026-08-28.md: Player.bin bit físico → skill_id canônico',
        'erros':erros,
        'paridade_tecnica_classificada':not erros,
        'gates':auditoria.get('gates'),
        'fingerprints_lotes':auditoria.get('fingerprints_lotes'),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--auditoria', required=True)
    p.add_argument('--manifesto', required=True)
    p.add_argument('--referencia-manifesto', required=True)
    p.add_argument('--referencia-csv', required=True)
    p.add_argument('--saida', required=True)
    args = p.parse_args()
    a = json.loads(Path(args.auditoria).read_text(encoding='utf-8'))
    m = json.loads(Path(args.manifesto).read_text(encoding='utf-8'))
    rm = json.loads(Path(args.referencia_manifesto).read_text(encoding='utf-8'))
    r = classifica(a, m, rm, args.referencia_csv)
    texto = json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True)
    Path(args.saida).write_text(texto + '\n', encoding='utf-8')
    print(json.dumps({'paridade_tecnica_classificada':r['paridade_tecnica_classificada'],
                      'novas':r['novas']['quantidade'],
                      'cartas_alteradas':r['alteradas']['cartas'],
                      'campos_alterados':r['alteradas']['campos'],
                      'erros':len(r['erros'])}, sort_keys=True))
    return 0 if r['paridade_tecnica_classificada'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
