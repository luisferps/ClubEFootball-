"""Teste determinístico da aplicação local, sem banco, lote ou escrita."""
from __future__ import annotations

import importlib.util
import io
import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
SERVIDOR = RAIZ / "2-MOTORES" / "BONIFICADOR" / "interface" / "servidor.py"
LANCADOR = RAIZ / "2-MOTORES" / "BONIFICADOR" / "windows-app" / "ClubEfootballBonificadorLauncher.cs"
ESPEC = importlib.util.spec_from_file_location("bonificador_interface", SERVIDOR)
MODULO = importlib.util.module_from_spec(ESPEC)
assert ESPEC and ESPEC.loader
ESPEC.loader.exec_module(MODULO)


class GatewayFalso:
    def rpc(self, nome, corpo=None):
        if nome == "bonificador_regua_v2":
            return {
                "contrato": "bonificador-regua-v2", "pode_rodar": True, "falta_o_que": [],
                "funcao_molde": {"goleiro_ofensivo": {"id": 19, "rotulo": "Goleiro ofensivo", "pode_rodar": True}},
                "parametro": {
                    "bonus_corpo_max": 1.5, "pe_ruim_teto": 1, "pe_ruim_frequencia_0": 0,
                    "pe_ruim_frequencia_1": .5, "pe_ruim_frequencia_2": .75, "pe_ruim_frequencia_3": 1,
                    "pe_ruim_precisao_0": 0, "pe_ruim_precisao_1": .5, "pe_ruim_precisao_2": .75,
                    "pe_ruim_precisao_3": 1, "estilo_ativo": 1, "estilo_ativo_secundario": .5,
                    "estilo_ia_ponto": 1, "estilo_ia_teto": 4,
                },
                "corpo_ordem": {"0": {"nosso": "altura"}},
                "molde_corpo": {"19": {"altura": {"cortes": [180, 185, 190, 195], "peso": 1, "direcao": "+"}}},
                "posicao_slot": {"0": "ofensivo"}, "casa": {"291": {"0": 19}}, "liga": {"336": [0]},
                "cardinalidades": {"molde": 1}, "proveniencia": {"modelo": "clube_novo"},
            }
        if nome == "bonificador_carta_v2" and corpo == {"p_card_id": "casillas-teste"}:
            return {
                "card_id": "casillas-teste", "nome": "Iker Casillas", "pode_rodar": True, "falta_o_que": [],
                "corpo": [185], "pe_ruim_uso": 2, "pe_ruim_precisao": 2,
                "posicao_id": 0, "posicao_codigo": "GO", "posicao_raw": "Goleiro",
                "slot1_id_jogo": 291, "slot1_nome": "Goleiro adiantado",
                "slot2_id_jogo": 336, "slot2_nome": "Goleiro ofensivo", "estilos_ia": [1, 2],
                "corpo_cardinalidade": 1, "pe_relacao_cardinalidade": 1,
                "posicao_relacao_cardinalidade": 1, "playstyle_relacao_cardinalidade": 2,
                "estilos_ia_cardinalidade": 2,
            }
        if nome == "bonificador_contexto_fila_v5":
            assert corpo == {"p_limit": 5000, "p_offset": 0}
            return [{
                "build_linha_card_id": 77, "card_id": "casillas-teste", "carta_nome": "Iker Casillas", "carta_tipo": "Épica", "carta_overall": 99, "funcao_id": 19,
                "funcao_codigo": "GO", "funcao_nome": "Goleiro ofensivo", "posicao_id": 0, "posicao_codigo": "GO", "posicao_nome": "Goleiro",
                "carta_versao": "v-teste", "carta_fingerprint": "a" * 64,
                "contrato_versao": "bonificador-regua-v2", "contrato_fingerprint": "b" * 64,
                "formula_fingerprint": "c" * 64,
            }]
        if nome == "bonificador_resultados_v1":
            assert corpo == {"p_limit": 5000, "p_offset": 0}
            return [{
                "build_linha_card_id": 77, "card_id": "casillas-teste", "carta_nome": "Iker Casillas", "carta_tipo": "Épica", "carta_overall": 99,
                "funcao_id": 19, "funcao_codigo": "GO", "funcao_nome": "Goleiro ofensivo", "posicao_id": 0, "posicao_codigo": "GO", "posicao_nome": "Goleiro",
                "estado": "confirmado", "b_corpo": 0.75, "b_pe_ruim": 0.5, "b_estilo": 1.5, "b_ia": 0.25, "b_total": 3.0, "faltou": [],
            }]
        raise AssertionError(f"RPC inesperada: {nome} {corpo}")


class GatewayFilaSemRegua:
    """Prova que a fila não depende da régua para ser exibida."""
    def rpc(self, nome, corpo=None):
        if nome != "bonificador_contexto_fila_v5":
            raise AssertionError(f"a fila não deveria consultar {nome}")
        return [{
            "build_linha_card_id": 88, "card_id": "fila-isolada", "carta_nome": "Carta isolada", "carta_tipo": "Teste", "carta_overall": 1, "funcao_id": 19,
            "funcao_codigo": "GO", "funcao_nome": "Goleiro ofensivo", "posicao_id": 0, "posicao_codigo": "GO", "posicao_nome": "Goleiro",
            "carta_versao": "v-fila", "carta_fingerprint": "d" * 64,
        }]


def obter(url, dados=None):
    pedido = urllib.request.Request(url, data=dados, method="POST" if dados is not None else "GET")
    with urllib.request.urlopen(pedido, timeout=5) as resposta:
        return resposta.status, json.loads(resposta.read().decode("utf-8"))


class ProcessoFalso:
    def __init__(self):
        self.stdout = io.StringIO(
            "PIPELINE VIVO\nFILA_RESULTADO: {\"linha_id\":77,\"estado\":\"apta\",\"b_corpo\":1.0,\"b_pe_ruim\":0.5,\"b_estilo\":1.5,\"b_ia\":0.25,\"b_total\":3.25,\"faltou\":[]}\nFILA_CALCULADA: linha=77 estado=apta\nAGUARDANDO NOVAS LINHAS: nenhuma linha apta\n"
        )
        self._ativo = True
        self._fim = threading.Event()

    def poll(self):
        return None if self._ativo else 0

    def wait(self):
        limite = time.time() + 2
        while time.time() < limite:
            if getattr(self, "arquivo_parada", None) and self.arquivo_parada.exists():
                self._ativo = False
                self._fim.set()
                break
            time.sleep(.01)
        return 0

    def send_signal(self, _sinal):
        self._ativo = False
        self._fim.set()


def esperar(predicado):
    limite = time.time() + 2
    while time.time() < limite:
        if predicado():
            return
        time.sleep(.01)
    raise AssertionError("estado assíncrono não chegou a tempo")


def main():
    servico = MODULO.ServicoBonificador(GatewayFalso())
    resultado = servico.simular("casillas-teste", 19)
    assert resultado["ok"], resultado
    assert resultado["bonus"]["estilo"] == 1.5, resultado["bonus"]
    assert resultado["bonus"]["total"] is not None
    assert resultado["carta"]["playstyles"][0]["id"] == 291
    assert resultado["carta"]["playstyles"][1]["id"] == 336
    assert "clube_novo" in json.dumps(servico.auditoria(), ensure_ascii=False)
    fila_isolada = MODULO.ServicoBonificador(GatewayFilaSemRegua()).fila_pendente()
    assert fila_isolada["total"] == 1
    assert fila_isolada["itens"][0]["carta_nome"] == "Carta isolada"

    processos = []
    def criar_processo(*_args, **kwargs):
        processo = ProcessoFalso()
        processo.arquivo_parada = Path(kwargs["env"]["CLUBEF_BONIFICADOR_STOP_FILE"])
        processos.append(processo)
        return processo
    pipeline = MODULO.PipelineBonificador(criar_processo)
    httpd = MODULO.criar_servidor(servico, 0, pipeline)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        status, saude = obter(base + "/api/saude")
        assert status == 200 and saude["ok"]
        assert saude["aplicativo"] == "bonificador_clubefootball"
        status, fila = obter(base + "/api/fila/status")
        assert status == 200 and fila["fila"]["total"] == 1
        assert fila["fila"]["itens"][0]["funcao_nome"] == "Goleiro ofensivo"
        status, resultados = obter(base + "/api/resultados")
        assert status == 200 and resultados["resultados"]["itens"][0]["carta_nome"] == "Iker Casillas"
        status, simulado = obter(base + "/api/simular?card_id=casillas-teste&funcao_id=19")
        assert status == 200 and simulado["bonus"]["estilo"] == 1.5
        status, iniciado = obter(base + "/api/pipeline/iniciar", b"{}")
        assert status == 200 and iniciado["pipeline"]["ativo"] is True
        esperar(lambda: bool(pipeline.estado().get("resultados")))
        status, fila_com_resultado = obter(base + "/api/fila/status")
        item = fila_com_resultado["fila"]["itens"][0]
        assert item["estado"] == "apta" and item["b_total"] == 3.25
        status, estado = obter(base + "/api/pipeline/estado")
        assert status == 200 and estado["pipeline"]["ativo"] is True
        assert processos and processos[0].poll() is None
        status, parada = obter(base + "/api/pipeline/parar", b"{}")
        assert status == 200 and parada["pipeline"]["estado"] in {"parando", "parado"}
        esperar(lambda: pipeline.estado()["ativo"] is False)
        try:
            obter(base + "/api/simular", b"{}")
            raise AssertionError("POST deveria ser bloqueado")
        except urllib.error.HTTPError as erro:
            assert erro.code == 405
    finally:
        httpd.shutdown(); httpd.server_close(); thread.join(timeout=2)

    servidor = SERVIDOR.read_text(encoding="utf-8")
    assert "bonificador_contexto_fila_v5" in servidor
    assert "bonificador_resultados_v1" in servidor
    assert '"clube_novo"' not in servidor
    assert "responder_arquivo" not in servidor
    assert not (SERVIDOR.parent / "index.html").exists()
    assert not (SERVIDOR.parent / "app.js").exists()
    assert not (SERVIDOR.parent / "style.css").exists()
    lancador = LANCADOR.read_text(encoding="utf-8")
    assert "c.Encoding = Encoding.UTF8" in lancador
    assert "using System.Text;" in lancador
    print("INTERFACE_LOCAL_OK simulacao=casillas fila_canonica=1 utf8=sim pipeline_inicio_parada_assincronos=sim post=405 sem_web=sim")


if __name__ == "__main__":
    main()
