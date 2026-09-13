"""Adapta o snapshot selado; nao consulta o banco durante o calculo."""
from complemento_habilidades_v14 import VERSAO


def carregar_atual(raiz):
    """Uma leitura no preparo; o calculo de cada linha permanece local."""
    import json
    import urllib.request
    from pathlib import Path
    url, key = ler_config(raiz)
    headers = {'apikey':key,'Content-Type':'application/json'}
    if key.startswith('eyJ'): headers['Authorization']='Bearer '+key
    req = urllib.request.Request(url+'/rest/v1/rpc/complemento_contexto_v14',b'{}',headers)
    with urllib.request.urlopen(req,timeout=120) as resposta:
        contexto = json.load(resposta)
    por_funcao(contexto,1)
    return contexto


def por_funcao(snapshot, funcao_id):
    if snapshot.get('versao') != VERSAO:
        raise ValueError('Versao do complemento desconhecida')
    fp = snapshot.get('fingerprint', '')
    if len(fp) != 64 or any(c not in '0123456789abcdef' for c in fp):
        raise ValueError('Snapshot de complemento sem selo')
    fid = int(funcao_id)
    pesos = {r['codigo_atributo']: r['peso'] for r in snapshot['pesos']
             if int(r['funcao_id']) == fid}
    if len(pesos) != 26:
        raise ValueError('Molde do complemento incompleto')
    catalogo = {int(h['skill_id']): h for h in snapshot['catalogo']}
    if len(catalogo) != len(snapshot['catalogo']):
        raise ValueError('Catalogo duplicado')
    return dict(catalogo=catalogo, ranking=snapshot['ranking'],
                bloqueios={int(r['skill_id']) for r in snapshot['bloqueios']
                           if int(r['funcao_id']) == fid},
                pesos_por_codigo=pesos)


def ler_config(raiz, pasta_complemento=None):
    """Mesma busca do enviador oficial, com configuracao local opcional."""
    from pathlib import Path
    raiz = Path(raiz)
    candidatas = ([Path(pasta_complemento)/'config.txt'] if pasta_complemento else [])
    candidatas += [raiz/'OPERACAO-LOCAL-JSON'/'config.txt',
                   raiz.parent/'config.txt', raiz/'config.txt']
    for caminho in candidatas:
        if not caminho.is_file():
            continue
        cfg = {}
        for linha in caminho.read_text(encoding='utf-8-sig').splitlines():
            if '=' in linha and not linha.lstrip().startswith('#'):
                k,v=linha.split('=',1); cfg[k.strip()]=v.strip()
        url=cfg.get('SUPABASE_URL','').strip().strip('[]').rstrip('/')
        key=cfg.get('SUPABASE_KEY','').strip()
        if not url or not key:
            continue
        if url != 'https://trqqpsnafpbudtvvicch.supabase.co':
            raise RuntimeError('Projeto diferente do clube_novo autorizado')
        return url,key
    raise RuntimeError('Configuracao valida nao encontrada. Caminhos consultados: '+
                       '; '.join(str(p) for p in candidatas))
