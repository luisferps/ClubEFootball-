# -*- coding: utf-8 -*-
"""Compara os 19 moldes v5 sem usar rótulo como identidade.

O código legado aparece apenas na ponte explícita `funcoes.codigo_compatibilidade`.
Depois da ponte, toda chave de comparação é `funcao_id + indice_otimizador`.
"""

from __future__ import print_function

import argparse
import hashlib
import json
import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)
from auditar_entradas_v1 import le_config, rpc


def _canonico(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def fingerprint(x):
    return hashlib.sha256(_canonico(x).encode('utf-8')).hexdigest()


def normaliza_antigo(regua_antiga, regua_nova):
    ponte = {str(f['codigo_compatibilidade']): int(f['funcao_id'])
             for f in (regua_nova.get('funcoes') or [])}
    out, faltas = {}, []
    for codigo, attrs in (regua_antiga.get('molde') or {}).items():
        fid = ponte.get(str(codigo))
        if fid is None:
            faltas.append({'codigo_compatibilidade': codigo,
                           'motivo': 'sem funcao_id comprovado'})
            continue
        for idx, par in (attrs or {}).items():
            out[(fid, int(idx))] = (float(par[0]), int(par[1]))
    return out, faltas


def normaliza_novo(regua_nova):
    out, duplicadas = {}, []
    for r in (regua_nova.get('molde') or []):
        k = (int(r['funcao_id']), int(r['indice_otimizador']))
        if k in out:
            duplicadas.append(k)
        out[k] = (float(r['alvo']), int(r['peso']))
    return out, duplicadas


def compara(regua_antiga, regua_nova):
    antigo, faltas = normaliza_antigo(regua_antiga, regua_nova)
    novo, duplicadas = normaliza_novo(regua_nova)
    ids = sorted({x[0] for x in set(antigo) | set(novo)})
    moldes, divergencias = [], []
    for fid in ids:
        a = {k[1]: v for k, v in antigo.items() if k[0] == fid}
        n = {k[1]: v for k, v in novo.items() if k[0] == fid}
        dif = []
        for idx in sorted(set(a) | set(n)):
            if a.get(idx) != n.get(idx):
                dif.append({'funcao_id': fid, 'indice_otimizador': idx,
                            'antigo': a.get(idx), 'novo': n.get(idx)})
        divergencias.extend(dif)
        moldes.append({'funcao_id': fid, 'linhas_antigas': len(a),
                       'linhas_novas': len(n), 'fingerprint_antigo': fingerprint(a),
                       'fingerprint_novo': fingerprint(n), 'divergencias': len(dif)})
    aprovado = (not faltas and not duplicadas and not divergencias and len(ids) == 19
                and len(antigo) == 494 and len(novo) == 494)
    return {'somente_leitura': True, 'identidade': 'funcao_id+indice_otimizador',
            'versao_antiga': regua_antiga.get('versao_molde'),
            'versao_nova': regua_nova.get('versao_molde'),
            'funcoes': len(ids), 'linhas_antigas': len(antigo),
            'linhas_novas': len(novo), 'faltas_na_ponte': faltas,
            'chaves_duplicadas': duplicadas, 'moldes': moldes,
            'divergencias': divergencias, 'aprovado': aprovado}


def prova_renomeacao(regua_antiga, regua_nova):
    alterada = json.loads(json.dumps(regua_nova))
    for f in alterada.get('funcoes') or []:
        f['rotulo_apresentacao'] = 'RENOMEADO:' + str(f.get('rotulo_apresentacao'))
    antes = compara(regua_antiga, regua_nova)
    depois = compara(regua_antiga, alterada)
    return (antes['aprovado'] == depois['aprovado'] and
            antes['moldes'] == depois['moldes'] and
            antes['divergencias'] == depois['divergencias'])


def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument('--config', default='config.txt')
    p.add_argument('--saida'); args = p.parse_args(argv)
    cfg = le_config(args.config); url = cfg.get('SUPABASE_URL', ''); key = cfg.get('SUPABASE_KEY', '')
    if not url or not key:
        raise SystemExit('faltam SUPABASE_URL/SUPABASE_KEY; sem fallback')
    antigo = rpc(url, key, 'regua_pacote', {}) or {}
    novo = rpc(url, key, 'otimizador_regua_v2', {}) or {}
    rel = compara(antigo, novo); rel['prova_renomeacao'] = prova_renomeacao(antigo, novo)
    if not rel['prova_renomeacao']:
        rel['aprovado'] = False
    texto = json.dumps(rel, ensure_ascii=False, indent=2, sort_keys=True)
    if args.saida:
        with open(args.saida, 'w', encoding='utf-8') as f: f.write(texto + '\n')
    print(texto); return 0 if rel['aprovado'] else 2


if __name__ == '__main__':
    sys.exit(main())
