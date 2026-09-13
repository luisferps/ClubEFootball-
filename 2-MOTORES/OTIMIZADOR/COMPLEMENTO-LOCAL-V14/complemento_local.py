"""Fila local e envio independente do complemento V14."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
import urllib.error
import msvcrt

BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))


def salvar(p, dados):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def ler(p):
    return json.loads(p.read_text(encoding='utf-8'))


def rpc(nome, corpo=None):
    from complemento_contexto_v14 import ler_config
    url, key = ler_config(BASE.parent, BASE)
    headers = {'apikey':key,'Content-Type':'application/json'}
    if key.startswith('eyJ'): headers['Authorization'] = 'Bearer '+key
    req = urllib.request.Request(url+'/rest/v1/rpc/'+nome,
        json.dumps(corpo or {}).encode(), headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError('Banco recusou: '+e.read().decode('utf-8',errors='replace')) from None


def baixar():
    if (BASE/'FILA-BAIXADA.json').exists(): return
    if not (BASE/'contexto.json').exists():
        salvar(BASE/'contexto.json', rpc('complemento_contexto_v14'))
        salvar(BASE/'regua.json', rpc('otimizador_regua_v2'))
    elif not (BASE/'regua.json').exists():
        salvar(BASE/'regua.json', rpc('otimizador_regua_v2'))
    paginas = sorted((BASE/'FILA').glob('*.json'))
    cursor = ler(paginas[-1])[-1]['linha']['linha_id'] if paginas else 0
    numero = len(paginas)
    total = sum(len(ler(p)) for p in paginas)
    while True:
        rows = rpc('complemento_exportar_v14', {'p_depois_id':cursor,'p_limite':100})
        if not rows: break
        numero += 1
        salvar(BASE/'FILA'/f'pagina-{numero:06}.json', rows)
        cursor = rows[-1]['linha']['linha_id']; total += len(rows)
        print(f'FILA BAIXADA: {total} linhas', flush=True)
    salvar(BASE/'FILA-BAIXADA.json', {'linhas':total,'paginas':numero})


def calcular():
    baixar()
    from complemento_recomposicao_v14 import preparar,recompor
    from complemento_contexto_v14 import por_funcao
    runner = preparar(ler(BASE/'regua.json'))
    ctx = ler(BASE/'contexto.json')
    total = 0
    for p in sorted((BASE/'FILA').glob('*.json')):
        destino = BASE/'RESULTADOS'/p.name
        rows = ler(p); total += len(rows)
        if destino.exists(): continue
        resultados = []
        for row in rows:
            linha = row['linha']; c = runner.carrega_carta_snapshot_producao_v3(row['carta'])
            try:
                r = recompor(runner,row['carta'],linha,row['anterior'],
                    nativas=list(c.get('fab') or [])+list(c.get('raras') or []),
                    aceita_adicionais=bool(c.get('orc')),
                    **por_funcao(ctx,linha['funcao_id']))
            except Exception as e:
                salvar(BASE/'FALHAS'/f"linha-{linha['linha_id']}.json",{'linha_id':linha['linha_id'],'erro':str(e)})
                raise RuntimeError(f"Linha {linha['linha_id']}: {e}") from e
            if r is not None: resultados.append(r)
        salvar(destino,resultados)
        print(f'CALCULO LOCAL: {total} linhas; {len(resultados)} atualizacoes nesta pagina.',flush=True)
    salvar(BASE/'CALCULO-CONCLUIDO.json',{'linhas':total})
    print('Calculo concluido. O enviador pode continuar aberto.',flush=True)


def enviar():
    while True:
        pendentes = [p for p in sorted((BASE/'RESULTADOS').glob('*.json'))
                     if not (BASE/'RECIBOS'/p.name).exists()]
        for p in pendentes:
            rows = ler(p)
            resposta = rpc('complemento_importar_lote_v14',
                {'p_contexto':ler(BASE/'contexto.json')['fingerprint'],'p_resultados':rows}) if rows else []
            if len(resposta)!=len(rows): raise RuntimeError('Banco devolveu quantidade inesperada de recibos')
            erros = [r for r in resposta if r.get('ok') is not True]
            if erros:
                salvar(BASE/'FALHAS'/p.name, resposta)
                raise RuntimeError('Envio incompleto; confirmadas serao reconhecidas na retomada: '+json.dumps(erros,ensure_ascii=False))
            salvar(BASE/'RECIBOS'/p.name,resposta)
            print(f'ENVIO: {p.name}: {len(rows)} confirmadas; recibo salvo.',flush=True)
        if (BASE/'CALCULO-CONCLUIDO.json').exists() and not any(
            not (BASE/'RECIBOS'/p.name).exists() for p in (BASE/'RESULTADOS').glob('*.json')):
            print('ENVIO CONCLUIDO: todas as paginas locais confirmadas.',flush=True)
            return
        print('Aguardando proxima pagina local. Ctrl+C para parar.',flush=True)
        time.sleep(5)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('acao',choices=['calcular','enviar'])
    args=parser.parse_args()
    BASE.mkdir(parents=True,exist_ok=True)
    with (BASE/(args.acao+'.lock')).open('a+b') as lock:
        lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
        try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError: raise RuntimeError('Este botao ja esta rodando nesta pasta')
        try: globals()[args.acao]()
        finally: lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


if __name__=='__main__':
    try: main()
    except KeyboardInterrupt:
        print('Pausado. Fila, JSONs e recibos preservados.'); sys.exit(0)
    except Exception as e:
        print('ERRO: '+str(e)); sys.exit(1)
