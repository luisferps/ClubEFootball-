# -*- coding: utf-8 -*-
"""Testes sem escrita da migração do Bonificador para clube_novo.

Uso:
  python testar_migracao_bonificador.py
  python testar_migracao_bonificador.py --online

O modo padrão valida o executável por AST e exercita somente as funções puras.
O modo --online acrescenta readback das três RPCs v1; nunca chama gravar_bonus.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import urllib.request
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
FONTE = RAIZ / "2-MOTORES" / "motor_bonus.py"
FUNCOES_PURAS = {
    "nota_da_medida",
    "bonus_do_corpo",
    "bonus_do_pe_ruim",
    "_por_id",
    "bonus_do_estilo",
    "bonus_do_estilo_ia",
}


def carregar_funcoes_puras(texto: str):
    arvore = ast.parse(texto, filename=str(FONTE))
    nos = [
        no for no in arvore.body
        if isinstance(no, ast.FunctionDef) and no.name in FUNCOES_PURAS
    ]
    encontrados = {no.name for no in nos}
    assert encontrados == FUNCOES_PURAS, FUNCOES_PURAS - encontrados
    modulo = ast.Module(body=nos, type_ignores=[])
    ast.fix_missing_locations(modulo)
    escopo = {}
    exec(compile(modulo, str(FONTE), "exec"), escopo)
    return arvore, escopo


def validar_portas(arvore: ast.AST):
    chamadas = []
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Call):
            continue
        if isinstance(no.func, ast.Name) and no.func.id == "rpc" and no.args:
            primeiro = no.args[0]
            if isinstance(primeiro, ast.Constant) and isinstance(primeiro.value, str):
                chamadas.append(primeiro.value)

    assert set(chamadas) == {
        "bonificador_regua_v1",
        "bonificador_carta_v1",
        "bonificador_pares_v1",
        "gravar_bonus",
    }, chamadas
    assert "regua_bonus" not in chamadas
    assert "carta_do_motor" not in chamadas
    assert not any(
        isinstance(no, ast.FunctionDef) and no.name == "le_tabela"
        for no in ast.walk(arvore)
    )


def validar_conta(escopo):
    bonus_do_estilo = escopo["bonus_do_estilo"]
    bonus_do_pe_ruim = escopo["bonus_do_pe_ruim"]
    bonus_do_estilo_ia = escopo["bonus_do_estilo_ia"]

    regua = {
        "parametro": {
            "estilo_ativo_principal": 1.0,
            "estilo_ativo_secundario": 0.5,
            "pe_ruim_teto": 1.0,
            "pe_ruim_frequencia_0": 0.0,
            "pe_ruim_frequencia_1": 0.25,
            "pe_ruim_frequencia_2": 0.5,
            "pe_ruim_frequencia_3": 1.0,
            "pe_ruim_precisao_0": 0.0,
            "pe_ruim_precisao_1": 0.25,
            "pe_ruim_precisao_2": 0.5,
            "pe_ruim_precisao_3": 1.0,
            "estilo_ia_ponto": 1.0,
            "estilo_ia_teto": 4,
        },
        "posicao_slot": {"5": "ofensivo"},
        "casa": {"391": {"5": "FUNCAO-A"}},
        "liga": {"256": [5]},
    }
    assert bonus_do_estilo(regua, 391, 256, "FUNCAO-A", 5) == 1.5
    assert bonus_do_estilo(regua, 391, 256, "FUNCAO-B", 5) == 0.5
    assert bonus_do_estilo(regua, None, 391, "FUNCAO-A", 5) == 1.0
    assert bonus_do_pe_ruim(regua["parametro"], 3, 2) == 0.5
    assert bonus_do_pe_ruim(regua["parametro"], None, 2) is None
    assert bonus_do_estilo_ia(regua["parametro"], [616, 647, 680, 678]) == 1.0


def ler_config():
    cfg = {}
    for linha in (RAIZ / "config.txt").read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            cfg[chave.strip()] = valor.strip()
    url = cfg.get("SUPABASE_URL", "").rstrip("/")
    key = cfg.get("SUPABASE_KEY", "")
    assert url and key and "COLE_AQUI" not in key, "config.txt sem credencial operacional"
    return url, key


def rpc_leitura(url: str, key: str, nome: str, corpo=None):
    assert nome in {
        "bonificador_regua_v1",
        "bonificador_carta_v1",
        "bonificador_pares_v1",
    }
    pedido = urllib.request.Request(
        f"{url}/rest/v1/rpc/{nome}",
        data=json.dumps(corpo or {}).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        texto = resposta.read().decode("utf-8")
    return json.loads(texto) if texto.strip() else None


def validar_online(escopo):
    bonus_do_estilo = escopo["bonus_do_estilo"]
    url, key = ler_config()
    regua = rpc_leitura(url, key, "bonificador_regua_v1")
    assert regua["pode_rodar"] is True
    assert regua["falta_o_que"] == []
    assert regua["estilos_bloqueados"] == []

    casos = {
        "176844": {"pode_rodar": True, "precisao": 2, "ia": [616, 647, 680]},
        "155498": {"pode_rodar": True, "corpo_0": 185, "ia": [678]},
        "160233": {"pode_rodar": True, "posicao": 5, "slot1": 391},
        "182363": {"pode_rodar": True, "posicao": 8, "slot1": 261},
    }
    readback = {}
    for card_id, esperado in casos.items():
        carta = rpc_leitura(url, key, "bonificador_carta_v1", {"p_card_id": card_id})
        assert carta["pode_rodar"] is esperado["pode_rodar"]
        assert carta["corpo_cardinalidade"] == 12
        if "precisao" in esperado:
            assert carta["pe_ruim_precisao"] == esperado["precisao"]
        if "corpo_0" in esperado:
            assert carta["corpo"][0] == esperado["corpo_0"]
        if "ia" in esperado:
            assert carta["estilos_ia"] == esperado["ia"]
        if "posicao" in esperado:
            assert carta["posicao_id"] == esperado["posicao"]
        if "slot1" in esperado:
            assert carta["slot1_id_jogo"] == esperado["slot1"]
        readback[card_id] = carta

    casillas = rpc_leitura(
        url, key, "bonificador_carta_v1", {"p_card_id": "88045755827028"}
    )
    assert casillas["pode_rodar"] is True
    assert casillas["slot1_id_jogo"] == 291
    assert casillas["slot2_id_jogo"] == 336
    assert casillas["falta_o_que"] == []
    assert bonus_do_estilo(
        regua, casillas["slot1_id_jogo"], casillas["slot2_id_jogo"],
        5, casillas["posicao_id"],
    ) == 1.5

    ausente = rpc_leitura(
        url, key, "bonificador_carta_v1", {"p_card_id": "card-inexistente"}
    )
    assert ausente["pode_rodar"] is False
    assert ausente["falta_o_que"]

    pares = rpc_leitura(
        url, key, "bonificador_pares_v1", {"p_limit": 1, "p_offset": 0}
    )
    assert isinstance(pares, list)

    # Ponte autorizada: somente a chave externa mudou. O conteudo do molde
    # continua identico e agora resolve pelo ID canônico que o motor consome.
    bonus_do_corpo = escopo["bonus_do_corpo"]
    carta_controle = readback["176844"]
    assert "Centroavante fixo" not in regua["molde_corpo"]
    assert "1" in regua["molde_corpo"]
    assert regua["funcao_molde"]["centroavante_fixo"]["id"] == 1
    assert bonus_do_corpo(
        regua["molde_corpo"], carta_controle["corpo"],
        1, float(regua["parametro"]["bonus_corpo_max"])
    ) is not None

    assert all("funcao_id" in item for item in pares)

    fp = hashlib.sha256(
        json.dumps(readback, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    print("ONLINE_OK readback_sha256=" + fp)
    print("ONLINE_BRIDGE_OK molde_corpo_e_estilo_por_funcao_id_canonico")


def main():
    texto = FONTE.read_text(encoding="utf-8")
    arvore, escopo = carregar_funcoes_puras(texto)
    validar_portas(arvore)
    validar_conta(escopo)
    print("LOCAL_OK fonte_sha256=" + hashlib.sha256(texto.encode("utf-8")).hexdigest())
    if "--online" in sys.argv[1:]:
        validar_online(escopo)


if __name__ == "__main__":
    main()
