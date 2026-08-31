# -*- coding: utf-8 -*-
"""Fila isolada de 50 cards do arquivo anterior. Nunca publica nem chama gravar_build."""
from __future__ import annotations
import hashlib,json,multiprocessing as mp,sys,uuid
from datetime import datetime,timezone
from pathlib import Path

PASTA=Path(__file__).resolve().parent
ESTADO_DIR=PASTA/"teste-legado-50"
ESTADO=ESTADO_DIR/"estado-lote.json"
LOG=ESTADO_DIR/"execucao.log"
QTD_CARDS=50
SEMENTE="comparacao-legado-50-2026-08-30"
CONTRATO_LOTE="otimizador_teste_lote_v14"
MOTOR_VERSAO="v7-teste-legado-50"
sys.path.insert(0,str(PASTA)); import fonte_unica
_RUNNER=None

def agora(): return datetime.now(timezone.utc).isoformat()

def registra(texto):
    ESTADO_DIR.mkdir(parents=True,exist_ok=True)
    linha=f"[{agora()}] {texto}"
    print(linha,flush=True)
    with LOG.open("a",encoding="utf-8") as f: f.write(linha+"\n")

def salva_estado(d):
    ESTADO_DIR.mkdir(parents=True,exist_ok=True)
    t=ESTADO.with_suffix(".tmp")
    t.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
    t.replace(ESTADO)

def le_estado():
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else None

def rpc(nome,corpo=None):
    return fonte_unica._rpc(nome,corpo or {},timeout=180,tentativas=2)

def formula_fingerprint():
    h=hashlib.sha256()
    for nome in ("equacao.py","motor.py","regua.py"):
        h.update(nome.encode()); h.update((PASTA/nome).read_bytes())
    return h.hexdigest()

def contrato_fingerprint():
    pacote=rpc("otimizador_regua_v2",{})
    return hashlib.sha256(json.dumps(
        pacote,ensure_ascii=False,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()

def _confere_status(resposta,lote_id,fingerprint=None):
    if resposta.get("contrato")!=CONTRATO_LOTE:
        raise SystemExit("PARE: versao inesperada do contrato da fila")
    if resposta.get("lote_id")!=lote_id:
        raise SystemExit("PARE: banco devolveu outro lote")
    if fingerprint and resposta.get("fingerprint")!=fingerprint:
        raise SystemExit("PARE: fingerprint do lote divergiu")
    if int(resposta.get("cards") or 0)!=QTD_CARDS:
        raise SystemExit("PARE: banco nao selou 50 cards unicos")
    if int(resposta.get("linhas") or 0)<QTD_CARDS:
        raise SystemExit("PARE: fila nao preservou todas as linhas dos cards")
    if resposta.get("modo")!="teste_nao_publicado" or resposta.get("pode_publicar") is not False:
        raise SystemExit("PARE: lote nao esta isolado de publicacao")
    return resposta

def preparar():
    estado=le_estado()
    if estado:
        resposta=rpc("otimizador_status_teste_v2",{"p_lote_id":estado["lote_id"]}) or {}
        _confere_status(resposta,estado["lote_id"],estado.get("fingerprint"))
        return estado

    estado={
      "contrato":"otimizador_comparacao_legado_50_v1",
      "lote_id":str(uuid.uuid4()),"semente":SEMENTE,"criado_local_em":agora()
    }
    ff=formula_fingerprint(); fc=contrato_fingerprint()
    resposta=rpc("otimizador_criar_fila_comparacao_legado_50_v1",{
      "p_lote_id":estado["lote_id"],"p_semente":estado["semente"],
      "p_formula_fingerprint":ff,"p_contrato_fingerprint":fc,
      "p_motor_versao":MOTOR_VERSAO}) or {}
    _confere_status(resposta,estado["lote_id"])
    estado.update({
      "fingerprint":resposta.get("fingerprint"),"cards":QTD_CARDS,
      "linhas":resposta.get("linhas"),"formula_fingerprint":ff,
      "contrato_fingerprint":fc,"motor_versao":MOTOR_VERSAO,
      "ultimo_status":resposta
    })
    salva_estado(estado)
    registra(f"fila selada: 50 cards do arquivo anterior, {estado['linhas']} linhas, lote {estado['lote_id']}")
    return estado

def status():
    e=le_estado()
    if not e: return {"ok":False,"erro":"fila de comparacao ainda nao criada"}
    resposta=rpc("otimizador_status_teste_v2",{"p_lote_id":e["lote_id"]}) or {}
    return _confere_status(resposta,e["lote_id"],e.get("fingerprint"))

def controlar(acao,confirmado=False):
    e=le_estado()
    if not e: raise SystemExit("PARE: fila de comparacao ainda nao criada")
    return rpc("otimizador_controlar_lote_teste_v2",{
      "p_lote_id":e["lote_id"],"p_acao":acao,"p_confirmado":bool(confirmado)})

def _inicia_worker(ids):
    global _RUNNER
    import roda_lote_v6 as runner
    runner._W.clear(); runner._carrega_no_processo(ids); _RUNNER=runner

def _calcula(item):
    return _RUNNER.trabalha({
      "n":item["linha_id"],"card_id":item["card_id"],"funcao_id":item["funcao_id"],
      "impeto_condicional_codigo":item.get("impeto_condicional_codigo"),
      "impeto_condicional_nivel":item.get("impeto_condicional_nivel"),
      "origem":"comparacao_legado_50_isolado"})

def _fecha_controle_pendente():
    depois=status().get("estado_lote")
    if depois=="pausando": controlar("confirmar_pausa")
    elif depois=="encerrando": controlar("confirmar_encerramento",True)

def _confere_codigo_selado(e):
    if formula_fingerprint()!=e.get("formula_fingerprint"):
        raise SystemExit("PARE: formula mudou depois que a fila foi selada")
    if contrato_fingerprint()!=e.get("contrato_fingerprint"):
        raise SystemExit("PARE: contrato de entradas mudou depois que a fila foi selada")
    if e.get("motor_versao")!=MOTOR_VERSAO:
        raise SystemExit("PARE: versao local do worker diverge da fila")

def executar_lote_selado():
    """Executa somente o lote já selado; nunca cria outra amostra."""
    e=le_estado()
    if not e or not e.get("lote_id"):
        raise SystemExit("PARE: lote selado local ausente")
    _confere_codigo_selado(e)
    lote=e["lote_id"]; inicial=status()
    if inicial.get("estado_lote")!="rodando":
        registra("worker nao iniciado: lote nao esta rodando"); return inicial
    fila=rpc("otimizador_fila_teste_v2",{"p_lote_id":lote}) or []
    pend=[x for x in fila if x.get("estado")=="pendente"]
    if not pend:
        registra("nenhuma linha pendente; reexecucao idempotente"); return inicial
    _inicia_worker(sorted({str(x["card_id"]) for x in pend}))
    registra(f"motor iniciado: {len(pend)} linha(s) autorizada(s)")
    for item in pend:
        atual=status(); estado=atual.get("estado_lote")
        if estado!="rodando":
            registra("pausa respeitada antes de nova linha")
            if estado in ("pausando","encerrando") and not atual.get("corrente"):
                _fecha_controle_pendente()
            break
        iniciou=rpc("otimizador_iniciar_linha_teste_v1",{
          "p_linha_id":item["linha_id"],"p_lote_id":lote})
        if not iniciou:
            registra(f"linha {item['linha_id']} ja nao estava pendente; nenhuma duplicacao")
            continue
        saida=_calcula(item)
        if not saida or saida.get("ERRO"):
            motivo=(saida or {}).get("ERRO") or "motor nao devolveu resultado"
            rpc("otimizador_bloquear_linha_teste_v1",{
              "p_linha_id":item["linha_id"],"p_lote_id":lote,"p_motivo":motivo})
            registra(f"BLOQUEADA linha {item['linha_id']}: {motivo}")
            _fecha_controle_pendente(); continue
        saida.update({
          "formula_fingerprint":e["formula_fingerprint"],"motor_versao":MOTOR_VERSAO,
          "contrato_fingerprint":e["contrato_fingerprint"],
          "lote_fingerprint":e["fingerprint"],"card_id":item["card_id"],
          "funcao_id":item["funcao_id"],"posicao_id":item["posicao_id"],
          "impeto_condicional_codigo":item.get("impeto_condicional_codigo"),
          "impeto_condicional_nivel":item.get("impeto_condicional_nivel"),
          "carta_versao":item["carta_versao"],
          "carta_fingerprint":item["carta_fingerprint"]})
        rpc("otimizador_concluir_linha_teste_v2",{
          "p_linha_id":item["linha_id"],"p_lote_id":lote,"p_resultado":saida})
        registra(f"CONCLUIDA linha {item['linha_id']}")
    final=status()
    if final.get("estado_lote") in ("pausando","encerrando") and not final.get("corrente"):
        _fecha_controle_pendente(); final=status()
    salva_estado({**e,"ultimo_status":final,"finalizado_local_em":agora()})
    return final

def executar(limite=None):
    e=preparar(); _confere_codigo_selado(e)
    atual=status(); acao="iniciar" if atual.get("estado_lote")=="parado" else "retomar"
    controlar(acao)
    if limite is None: return executar_lote_selado()
    fila=rpc("otimizador_fila_teste_v2",{"p_lote_id":e["lote_id"]}) or []
    pend=[x for x in fila if x.get("estado")=="pendente"][:limite]
    if not pend: return status()
    _inicia_worker(sorted({str(x["card_id"]) for x in pend}))
    # A prova curta usa o mesmo caminho selado, mas só autoriza o recorte pedido.
    for item in pend:
        rpc("otimizador_iniciar_linha_teste_v1",{
          "p_linha_id":item["linha_id"],"p_lote_id":e["lote_id"]})
        saida=_calcula(item)
        if not saida or saida.get("ERRO"):
            motivo=(saida or {}).get("ERRO") or "motor nao devolveu resultado"
            rpc("otimizador_bloquear_linha_teste_v1",{
              "p_linha_id":item["linha_id"],"p_lote_id":e["lote_id"],"p_motivo":motivo})
            continue
        saida.update({
          "formula_fingerprint":e["formula_fingerprint"],"motor_versao":MOTOR_VERSAO,
          "contrato_fingerprint":e["contrato_fingerprint"],
          "lote_fingerprint":e["fingerprint"],"card_id":item["card_id"],
          "funcao_id":item["funcao_id"],"posicao_id":item["posicao_id"],
          "impeto_condicional_codigo":item.get("impeto_condicional_codigo"),
          "impeto_condicional_nivel":item.get("impeto_condicional_nivel"),
          "carta_versao":item["carta_versao"],"carta_fingerprint":item["carta_fingerprint"]})
        rpc("otimizador_concluir_linha_teste_v2",{
          "p_linha_id":item["linha_id"],"p_lote_id":e["lote_id"],"p_resultado":saida})
    controlar("pausar")
    final=status(); salva_estado({**e,"ultimo_status":final,"finalizado_local_em":agora()})
    return final

def main():
    a=(sys.argv[1] if len(sys.argv)>1 else "status").lower()
    if a=="preparar": print(json.dumps(preparar(),ensure_ascii=False,indent=2))
    elif a=="status": print(json.dumps(status(),ensure_ascii=False,indent=2))
    elif a in ("executar","retomar"): print(json.dumps(executar(),ensure_ascii=False,indent=2))
    elif a=="executar-selado": print(json.dumps(executar_lote_selado(),ensure_ascii=False,indent=2))
    elif a=="provar-uma": print(json.dumps(executar(1),ensure_ascii=False,indent=2))
    elif a in ("iniciar","pausar"): print(json.dumps(controlar(a),ensure_ascii=False,indent=2))
    elif a=="parar": print(json.dumps(controlar("parar",True),ensure_ascii=False,indent=2))
    else: raise SystemExit("use: preparar | executar | retomar | provar-uma | iniciar | pausar | parar | status")

if __name__=="__main__": mp.freeze_support(); main()
