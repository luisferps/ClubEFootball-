"""Teste determinístico da aplicação local, sem banco, lote ou escrita."""
from __future__ import annotations

import importlib.util
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
SERVIDOR = RAIZ / "2-MOTORES" / "BONIFICADOR" / "interface" / "servidor.py"
ESPEC = importlib.util.spec_from_file_location("bonificador_interface", SERVIDOR)
MODULO = importlib.util.module_from_spec(ESPEC)
assert ESPEC and ESPEC.loader
ESPEC.loader.exec_module(MODULO)


class GatewayFalso:
    def rpc(self, nome, corpo=None):
        if nome == "bonificador_regua_v1":
            return {
                "contrato": "bonificador-regua-v1", "pode_rodar": True, "falta_o_que": [],
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
        if nome == "bonificador_carta_v1" and corpo == {"p_card_id": "casillas-teste"}:
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
        raise AssertionError(f"RPC inesperada: {nome} {corpo}")


def obter(url, dados=None):
    pedido = urllib.request.Request(url, data=dados, method="POST" if dados is not None else "GET")
    with urllib.request.urlopen(pedido, timeout=5) as resposta:
        return resposta.status, json.loads(resposta.read().decode("utf-8"))


def main():
    servico = MODULO.ServicoBonificador(GatewayFalso())
    resultado = servico.simular("casillas-teste", 19)
    assert resultado["ok"], resultado
    assert resultado["bonus"]["estilo"] == 1.5, resultado["bonus"]
    assert resultado["bonus"]["total"] is not None
    assert resultado["carta"]["playstyles"][0]["id"] == 291
    assert resultado["carta"]["playstyles"][1]["id"] == 336
    assert "clube_novo" in json.dumps(servico.auditoria(), ensure_ascii=False)

    httpd = MODULO.criar_servidor(servico, 0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        status, saude = obter(base + "/api/saude")
        assert status == 200 and saude["ok"]
        status, simulado = obter(base + "/api/simular?card_id=casillas-teste&funcao_id=19")
        assert status == 200 and simulado["bonus"]["estilo"] == 1.5
        try:
            obter(base + "/api/simular", b"{}")
            raise AssertionError("POST deveria ser bloqueado")
        except urllib.error.HTTPError as erro:
            assert erro.code == 405
    finally:
        httpd.shutdown(); httpd.server_close(); thread.join(timeout=2)

    estaticos = (RAIZ / "2-MOTORES" / "BONIFICADOR" / "interface" / "app.js").read_text(encoding="utf-8")
    assert "SUPABASE_KEY" not in estaticos and "clube_novo" not in estaticos
    print("INTERFACE_LOCAL_OK simulacao=casillas estilo=1.5 post=405 frontend_sem_credencial=sim")


if __name__ == "__main__":
    main()
