# -*- coding: utf-8 -*-
"""Fila isolada de 100 cartas. Reusa roda_lote_v6; nunca chama gravar_build."""
from __future__ import annotations
import hashlib,json,multiprocessing as mp,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
PASTA=Path(__file__).resolve().parent
ESTADO_DIR=PASTA/"teste-100"; ESTADO=ESTADO_DIR/"estado-lote.json"; LOG=ESTADO_DIR/"execucao.log"
sys.path.insert(0,str(PASTA)); import fonte_unica
_RUNNER=None
def agora(): return datetime.now(timezone.utc).isoformat()
def registra(texto):
    ESTADO_DIR.mkdir(parents=True,exist_ok=True); linha=f"[{agora()}] {texto}"; print(linha,flush=True)
    with LOG.open("a",encoding="utf-8") as f: f.write(linha+"\n")
def salva_estado(d):
    ESTADO_DIR.mkdir(parents=True,exist_ok=True); t=ESTADO.with_suffix(".tmp")
    t.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8"); t.replace(ESTADO)
def le_estado(): return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else None
def rpc(nome,corpo=None): return fonte_unica._rpc(nome,corpo or {},timeout=180,tentativas=2)
def formula_fingerprint():
    h=hashlib.sha256()
    for nome in ("equacao.py","motor.py","regua.py"): h.update(nome.encode()); h.update((PASTA/nome).read_bytes())
    return h.hexdigest()
def contrato_fingerprint():
    pacote=rpc("otimizador_regua_v1",{})
    return hashlib.sha256(json.dumps(pacote,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def preparar():
    estado=le_estado()
    if not estado:
        estado={"contrato":"otimizador_teste_100_v3","lote_id":str(uuid.uuid4()),
          "semente":"teste-100-"+uuid.uuid4().hex,"criado_local_em":agora()}
    ff=formula_fingerprint(); fc=contrato_fingerprint()
    resposta=rpc("otimizador_criar_amostra_teste_v2",{"p_lote_id":estado["lote_id"],
      "p_semente":estado["semente"],"p_formula_fingerprint":ff,"p_contrato_fingerprint":fc,
      "p_motor_versao":"v6-teste-isolado"})
    if int(resposta.get("cards") or 0)!=100: raise SystemExit("PARE: banco nao selou 100 cartas unicas")
    estado.update({"fingerprint":resposta.get("fingerprint"),"cards":100,"linhas":resposta.get("linhas"),
      "formula_fingerprint":ff,"contrato_fingerprint":fc})
    salva_estado(estado); registra(f"amostra selada: 100 cards, {estado['linhas']} linhas, lote {estado['lote_id']}")
    return estado
def status():
    e=le_estado(); return {"ok":False,"erro":"amostra ainda nao criada"} if not e else rpc("otimizador_status_teste_v1",{"p_lote_id":e["lote_id"]})
def controlar(acao,confirmado=False):
    e=le_estado()
    if not e: raise SystemExit("PARE: amostra ainda nao criada")
    return rpc("otimizador_controlar_lote_teste_v2",{"p_lote_id":e["lote_id"],"p_acao":acao,
      "p_confirmado":bool(confirmado)})
def _inicia_worker(ids):
    global _RUNNER
    import roda_lote_v6 as runner
    runner._W.clear(); runner._carrega_no_processo(ids); _RUNNER=runner
def _calcula(item):
    return _RUNNER.trabalha({"n":item["linha_id"],"card_id":item["card_id"],"funcao_id":item["funcao_id"],
      "funcao_codigo_compat":item.get("funcao_codigo_compat"),"origem":"teste_100_isolado"})
def _fecha_controle_pendente():
    depois=status().get("estado_lote")
    if depois=="pausando": controlar("confirmar_pausa")
    elif depois=="encerrando": controlar("confirmar_encerramento",True)
def executar_lote_selado():
    """Executa somente o lote já selado no estado local; não cria amostra."""
    e=le_estado()
    if not e or not e.get("lote_id"):
        raise SystemExit("PARE: lote selado local ausente")
    lote=e["lote_id"]; inicial=status()
    if inicial.get("lote_id")!=lote or inicial.get("modo")!="teste_nao_publicado":
        raise SystemExit("PARE: contrato devolveu lote ou modo inesperado")
    if inicial.get("estado_lote")!="rodando":
        registra("worker nao iniciado: lote nao esta rodando"); return inicial
    fila=rpc("otimizador_fila_teste_v1",{"p_lote_id":lote}) or []
    pend=[x for x in fila if x.get("estado")=="pendente"]
    if not pend:
        registra("nenhuma linha pendente; reexecucao idempotente"); return inicial
    _inicia_worker(sorted({str(x["card_id"]) for x in pend})); ff=formula_fingerprint()
    registra(f"motor v6 iniciado: {len(pend)} linha(s) autorizada(s)")
    for item in pend:
        atual=status(); estado=atual.get("estado_lote")
        if estado!="rodando":
            registra("pausa respeitada antes de nova linha")
            if estado in ("pausando","encerrando") and not atual.get("corrente"):
                _fecha_controle_pendente()
            break
        iniciou=rpc("otimizador_iniciar_linha_teste_v1",{"p_linha_id":item["linha_id"],"p_lote_id":lote})
        if not iniciou:
            registra(f"linha {item['linha_id']} já não estava pendente; nenhuma duplicação executada")
            continue
        saida=_calcula(item)
        if not saida or saida.get("ERRO"):
            motivo=(saida or {}).get("ERRO") or "motor nao devolveu resultado"
            rpc("otimizador_bloquear_linha_teste_v1",{"p_linha_id":item["linha_id"],"p_lote_id":lote,"p_motivo":motivo})
            registra(f"BLOQUEADA linha {item['linha_id']}: {motivo}"); _fecha_controle_pendente(); continue
        saida.update({"formula_fingerprint":ff,"motor_versao":"v6-teste-isolado",
          "contrato_fingerprint":e["contrato_fingerprint"],"lote_fingerprint":e["fingerprint"],
          "card_id":item["card_id"],"funcao_id":item["funcao_id"],"posicao_id":item["posicao_id"],
          "carta_versao":item["carta_versao"],"carta_fingerprint":item["carta_fingerprint"]})
        rpc("otimizador_concluir_linha_teste_v1",{"p_linha_id":item["linha_id"],"p_lote_id":lote,"p_resultado":saida})
        registra(f"CONCLUIDA linha {item['linha_id']}")
    final=status()
    if final.get("estado_lote") in ("pausando","encerrando") and not final.get("corrente"):
        _fecha_controle_pendente(); final=status()
    salva_estado({**e,"ultimo_status":final,"finalizado_local_em":agora()})
    return final
def executar(limite=None):
    e=preparar(); lote=e["lote_id"]; controlar("retomar")
    fila=rpc("otimizador_fila_teste_v1",{"p_lote_id":lote}) or []
    pend=[x for x in fila if x.get("estado")=="pendente"]
    if limite is not None: pend=pend[:limite]
    if not pend: registra("nenhuma linha pendente; reexecucao idempotente"); return
    _inicia_worker(sorted({str(x["card_id"]) for x in pend})); ff=formula_fingerprint()
    registra(f"motor v6 iniciado: {len(pend)} linha(s) autorizada(s)")
    for item in pend:
        if status().get("estado_lote")!="rodando": registra("pausa respeitada antes de nova linha"); break
        rpc("otimizador_iniciar_linha_teste_v1",{"p_linha_id":item["linha_id"],"p_lote_id":lote})
        saida=_calcula(item)
        if not saida or saida.get("ERRO"):
            motivo=(saida or {}).get("ERRO") or "motor nao devolveu resultado"
            rpc("otimizador_bloquear_linha_teste_v1",{"p_linha_id":item["linha_id"],"p_lote_id":lote,"p_motivo":motivo})
            registra(f"BLOQUEADA linha {item['linha_id']}: {motivo}"); continue
        saida.update({"formula_fingerprint":ff,"motor_versao":"v6-teste-isolado",
          "contrato_fingerprint":e["contrato_fingerprint"],"lote_fingerprint":e["fingerprint"],
          "card_id":item["card_id"],"funcao_id":item["funcao_id"],"posicao_id":item["posicao_id"],
          "carta_versao":item["carta_versao"],"carta_fingerprint":item["carta_fingerprint"]})
        rpc("otimizador_concluir_linha_teste_v1",{"p_linha_id":item["linha_id"],"p_lote_id":lote,"p_resultado":saida})
        registra(f"CONCLUIDA linha {item['linha_id']}")
        _fecha_controle_pendente()
    if limite is not None: controlar("pausar")
    final=status(); salva_estado({**e,"ultimo_status":final,"finalizado_local_em":agora()})
    print(json.dumps(final,ensure_ascii=False,indent=2))
def main():
    a=(sys.argv[1] if len(sys.argv)>1 else "status").lower()
    if a=="preparar": print(json.dumps(preparar(),ensure_ascii=False,indent=2))
    elif a=="status": print(json.dumps(status(),ensure_ascii=False,indent=2))
    elif a in ("executar","retomar"): executar()
    elif a=="executar-selado": print(json.dumps(executar_lote_selado(),ensure_ascii=False,indent=2))
    elif a=="provar-uma": executar(1)
    elif a in ("iniciar","pausar"): print(json.dumps(controlar(a),ensure_ascii=False,indent=2))
    elif a=="parar": print(json.dumps(controlar("parar",True),ensure_ascii=False,indent=2))
    else: raise SystemExit("use: preparar | executar | retomar | provar-uma | iniciar | pausar | parar | status")
if __name__=="__main__": mp.freeze_support(); main()
