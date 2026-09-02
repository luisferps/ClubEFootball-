# -*- coding: utf-8 -*-
"""Console operacional do lote persistente do Bonificador.

Este programa não contém regra de bônus. Ele apenas chama os contratos do lote
canônico, inicia o motor já aprovado e deixa o progresso visível no terminal.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import importlib.util
from pathlib import Path


PASTA_OPERACAO = Path(__file__).resolve().parent
PASTA_BONIFICADOR = PASTA_OPERACAO.parent
PASTA_RAIZ = PASTA_BONIFICADOR.parents[1]
if str(PASTA_BONIFICADOR) not in sys.path:
    sys.path.insert(0, str(PASTA_BONIFICADOR))

try:
    from interface.servidor import ErroDaInterface, ServicoBonificador  # noqa: E402
except Exception as erro_inicial:
    print("ERRO DE INSTALAÇÃO: não foi possível carregar o componente local do Bonificador.")
    print(f"Detalhe técnico: {type(erro_inicial).__name__}: {erro_inicial}")
    print("Confira se as pastas interface e OPERACAO-LOCAL-LOTE foram copiadas completas.")
    raise SystemExit(1) from erro_inicial


def _numero(valor: object) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _arquivo_parada(lote_id: str) -> Path:
    seguro = "".join(c for c in str(lote_id) if c.isalnum() or c == "-")
    return Path(tempfile.gettempdir()) / f"clubef-bonificador-lote-{seguro}.parar"


def _mostrar_status(lote: dict) -> None:
    estado = str(lote.get("estado") or "desconhecido")
    print()
    print("ESTADO DO LOTE DO BONIFICADOR")
    print(f"  Estado: {estado}")
    print(f"  Lote: {lote.get('lote_id') or 'não informado'}")
    print(f"  Linhas pendentes: {_numero(lote.get('pendentes'))}")
    print(f"  Em processamento: {_numero(lote.get('em_processamento'))}")
    print(f"  Concluídas: {_numero(lote.get('concluidas'))}")
    print(f"  Sem bônus: {_numero(lote.get('sem_bonus'))}")
    print(f"  Falhas bloqueadas: {_numero(lote.get('falhas'))}")
    print(f"  Total elegível do lote: {_numero(lote.get('elegiveis'))}")
    print(f"  Publicação liberada: {'sim' if lote.get('publicacao_liberada') else 'não'}")
    print()


def _servico() -> ServicoBonificador:
    return ServicoBonificador()


def consultar() -> int:
    _mostrar_status(_servico().lote_status())
    print("Consulta somente leitura: nenhum cálculo foi iniciado.")
    return 0


def diagnosticar() -> int:
    """Preflight explícito: só lê arquivos locais e o status do contrato."""
    config = PASTA_RAIZ / "2-MOTORES" / "config.txt"
    motor = PASTA_BONIFICADOR / "motor_bonus.py"
    print("DIAGNÓSTICO DO BATCH DO BONIFICADOR")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Configuração compartilhada: {'encontrada' if config.is_file() else 'ausente'}")
    print(f"  Motor: {'encontrado' if motor.is_file() else 'ausente'}")
    print(f"  Driver psycopg: {'disponível' if importlib.util.find_spec('psycopg') else 'ausente; usará RPC HTTPS'}")
    print("  Testando somente a leitura do contrato do lote...")
    _mostrar_status(_servico().lote_status())
    print("Diagnóstico concluído: nenhuma linha foi reservada ou calculada.")
    return 0


def _ambiente_motor(lote: dict, parada: Path, servico: ServicoBonificador) -> dict[str, str]:
    ambiente = os.environ.copy()
    ambiente["PYTHONUTF8"] = "1"
    ambiente["CLUBEF_BONIFICADOR_LOTE_ID"] = str(lote["lote_id"])
    ambiente["CLUBEF_BONIFICADOR_STOP_FILE"] = str(parada)
    ambiente["CLUBEF_BONIFICADOR_CONFIG"] = str(PASTA_RAIZ / "2-MOTORES" / "config.txt")
    # O motor continua atrás da mesma allowlist de RPCs; quando há DSN local,
    # usa o canal transacional já usado pelo componente local.
    if servico.gateway.banco and importlib.util.find_spec("psycopg") is not None:
        ambiente["CLUBEF_BONIFICADOR_USAR_BANCO_DIRETO"] = "1"
    return ambiente


def processar() -> int:
    servico = _servico()
    motor = PASTA_BONIFICADOR / "motor_bonus.py"
    if not motor.is_file():
        raise RuntimeError("motor_bonus.py não foi encontrado ao lado da operação; o lote não foi iniciado")
    antes = servico.lote_status()
    estado = str(antes.get("estado") or "")
    if estado in {"encerrado", "concluido"}:
        print("O lote está encerrado. Não há início implícito de outro lote.")
        _mostrar_status(antes)
        return 2

    lote = servico.controlar_lote("iniciar")
    lote_id = str(lote.get("lote_id") or "")
    if not lote_id:
        raise ErroDaInterface("o controle não devolveu a identidade do lote", 503)
    parada = _arquivo_parada(lote_id)
    parada.unlink(missing_ok=True)

    print()
    print("PROCESSAMENTO DO BONIFICADOR INICIADO")
    print("  O progresso abaixo vem diretamente do motor e do lote canônico.")
    print("  Para pausar com segurança, pressione Ctrl+C uma vez.")
    print("  A linha em andamento termina antes de a pausa ser assentada.")
    print()

    processo = subprocess.Popen(
        [sys.executable, "-u", str(motor)],
        cwd=str(PASTA_RAIZ / "2-MOTORES"),
        env=_ambiente_motor(lote, parada, servico),
    )
    pausado_pelo_operador = False
    try:
        codigo = processo.wait()
    except KeyboardInterrupt:
        pausado_pelo_operador = True
        parada.touch(exist_ok=True)
        print("\nPAUSA SOLICITADA. Aguardando a linha atual terminar...")
        codigo = processo.wait()
    finally:
        if pausado_pelo_operador:
            try:
                servico.controlar_lote("pausar")
            except Exception:
                pass
        try:
            atual = servico.lote_status()
            estado_atual = str(atual.get("estado") or "")
            if estado_atual == "pausando":
                atual = servico.assentar_lote(lote_id, "pausar")
            elif estado_atual == "encerrando":
                atual = servico.assentar_lote(lote_id, "parar")
            _mostrar_status(atual)
        finally:
            parada.unlink(missing_ok=True)

    if codigo:
        print(f"O motor terminou com código {codigo}. Nenhuma linha sem readback foi confirmada.")
    else:
        print("Processamento encerrado normalmente; o estado acima foi relido do banco.")
    return int(codigo or 0)


def controlar(acao: str) -> int:
    servico = _servico()
    lote = servico.controlar_lote(acao)
    lote_id = str(lote.get("lote_id") or "")
    if lote_id:
        _arquivo_parada(lote_id).touch(exist_ok=True)
    verbo = "pausa" if acao == "pausar" else "encerramento"
    print(f"{verbo.capitalize()} solicitada. O motor termina a linha atual e não reserva outra.")
    _mostrar_status(lote)
    return 0


def main(argumentos: list[str]) -> int:
    comando = (argumentos[0].strip().lower() if argumentos else "status")
    if comando in {"status", "consultar"}:
        return consultar()
    if comando in {"diagnostico", "diagnóstico"}:
        return diagnosticar()
    if comando in {"processar", "iniciar", "retomar"}:
        return processar()
    if comando == "pausar":
        return controlar("pausar")
    if comando in {"parar", "encerrar"}:
        return controlar("parar")
    print("Uso: PROCESSAR-FILA-BONIFICADOR.bat [status|diagnostico|processar|pausar|parar]")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ErroDaInterface as erro:
        print(f"ERRO DE CONTRATO: {erro}")
        raise SystemExit(1)
    except Exception as erro:
        print(f"ERRO OPERACIONAL: {erro}")
        raise SystemExit(1)
