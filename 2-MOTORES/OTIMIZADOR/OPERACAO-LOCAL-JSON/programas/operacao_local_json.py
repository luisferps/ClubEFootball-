# -*- coding: utf-8 -*-
"""Operação local do Otimizador, sem painel e sem reservas longas.

Há dois comandos deliberadamente separados:

``processar``
    Lê somente a fotografia em ``PACOTE-FILA-INTEGRAL`` e calcula uma linha por
    vez. O resultado é durável no disco antes de qualquer contato com o banco.

``enviar``
    Lê somente os JSONs prontos, confirma uma linha por chamada e registra o
    recibo local. A hora retornada pelo banco é a hora oficial do envio.

Os dois comandos podem ficar abertos ao mesmo tempo. O processador só cria um
JSON pronto quando junta até 100 resultados; o enviador, porém, envia e
confirma cada resultado separadamente dentro desse JSON.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Iterator


CONTRATO_RESULTADO = "otimizador_resultado_local_json_v1"
CONTRATO_RECIBO = "otimizador_recibo_local_json_v1"
CONTRATO_IMPORTACAO = "otimizador_importacao_json_local_v1"
VERSAO = 1
TAMANHO_JSON = 100
NOME_PASTA = "OPERACAO-LOCAL-JSON"
NOME_PACOTE = "PACOTE-FILA-INTEGRAL"


class FalhaOperacao(RuntimeError):
    """Erro claro e recuperável para quem opera os batches."""


class FalhaRede(FalhaOperacao):
    """A resposta do banco ficou incerta; não se marca nada como enviado."""


class FalhaBanco(FalhaOperacao):
    """O banco respondeu recusando o resultado; nada é apagado do disco."""


def agora_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _limpar_tela() -> None:
    """Atualiza o painel do batch sem despejar 184 mil linhas no console."""
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def _cabecalho_painel(titulo: str) -> None:
    _limpar_tela()
    print("=" * 72)
    print("CLUBEFOOTBALL — OTIMIZADOR")
    print(titulo)
    print("=" * 72)


def _rotulos_linha(linha: dict[str, Any]) -> tuple[str, str, str]:
    """Retorna os rótulos humanos que acompanham cada identificador exibido."""
    carta = str(linha.get("carta_nome") or "Carta sem nome informado")
    funcao = str(linha.get("funcao_rotulo") or "Função sem rótulo")
    posicao = str(linha.get("posicao_rotulo") or "Posição sem rótulo")
    return carta, funcao, posicao


def _carta_com_id(linha: dict[str, Any]) -> str:
    """Nunca deixa o ID da carta aparecer sozinho para quem está operando."""
    carta, _, _ = _rotulos_linha(linha)
    card_id = str(linha.get("card_id") or "não informado")
    return f"{carta} (ID da carta: {card_id})"


def _mostrar_processamento(
    pacote: Any,
    calculadas: int,
    prontas_para_envio: int,
    enviadas: int,
    falhas: int,
    linha_atual: dict[str, Any] | None = None,
    iniciado: float | None = None,
) -> None:
    total = int(pacote.manifesto.get("linhas_total") or 0)
    cartas = int(pacote.manifesto.get("cartas_total") or 0)
    _cabecalho_painel("FILA LOCAL — PROCESSANDO SEM PAINEL ANTIGO")
    print(f"Cartas preparadas: {cartas}/{cartas}")
    print(f"Linhas no pacote local: {total}")
    print(f"Concluídas localmente: {calculadas}")
    print(f"JSONs prontos para envio: {prontas_para_envio}")
    print(f"Enviadas e confirmadas pelo banco: {enviadas}")
    print(f"Em andamento: {1 if linha_atual else 0}")
    print(f"Pendentes de cálculo no pacote: {max(0, total - calculadas)}")
    print(f"Problemas registrados: {falhas}")
    print("-" * 72)
    if linha_atual:
        carta, funcao, posicao = _rotulos_linha(linha_atual)
        segundos = int(max(0, time.monotonic() - (iniciado or time.monotonic())))
        print("AGORA")
        print(f"Linha da fila: {linha_atual.get('linha_id', 'não informada')}")
        print(f"Carta: {_carta_com_id(linha_atual)}")
        print(f"Função: {funcao}")
        print(f"Posição: {posicao}")
        print(f"Em processamento há: {segundos}s")
        print("Resultado: calculando localmente; ainda não enviado ao banco.")
    else:
        print("AGORA")
        print("Nenhuma linha em cálculo neste instante.")
    print("-" * 72)
    print("Ctrl+C para parar com segurança. O que já foi calculado fica salvo.")


def _mostrar_envio(
    lote: str,
    total_prontas: int,
    confirmadas: int,
    falhas: int,
    item_atual: dict[str, Any] | None = None,
    iniciado: float | None = None,
) -> None:
    _cabecalho_painel("RESULTADOS LOCAIS — ENVIANDO UMA LINHA POR VEZ")
    print(f"Resultados aguardando envio: {total_prontas}")
    print(f"Confirmadas nesta execução: {confirmadas}")
    print(f"Problemas de envio: {falhas}")
    print(f"Em andamento: {1 if item_atual else 0}")
    print("-" * 72)
    if item_atual:
        carta, funcao, posicao = _rotulos_linha(item_atual)
        segundos = int(max(0, time.monotonic() - (iniciado or time.monotonic())))
        print("AGORA")
        print(f"Linha da fila: {item_atual.get('linha_id', 'não informada')}")
        print(f"Carta: {_carta_com_id(item_atual)}")
        print(f"Função: {funcao}")
        print(f"Posição: {posicao}")
        print(f"Enviando há: {segundos}s")
        print("Aguardando a confirmação oficial do banco.")
    else:
        print("AGORA")
        print("Nenhum resultado sendo enviado neste instante.")
    print("-" * 72)
    print("Ctrl+C para parar com segurança. Cada confirmação recebe um recibo local.")


def texto_json(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def gravar_json_atomico(caminho: Path, valor: dict[str, Any]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp-" + uuid.uuid4().hex)
    try:
        temporario.write_text(texto_json(valor) + "\n", encoding="utf-8")
        os.replace(temporario, caminho)
    finally:
        if temporario.exists():
            temporario.unlink(missing_ok=True)


def ler_json(caminho: Path) -> dict[str, Any]:
    try:
        valor = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        raise FalhaOperacao(f"JSON inválido: {caminho}") from erro
    if not isinstance(valor, dict):
        raise FalhaOperacao(f"JSON sem objeto principal: {caminho}")
    return valor


def acrescentar_jsonl_duravel(caminho: Path, valor: dict[str, Any]) -> None:
    """Acrescenta exatamente uma linha, sincronizada antes de seguir o motor."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linha = texto_json(valor) + "\n"
    with caminho.open("a", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(linha)
        arquivo.flush()
        os.fsync(arquivo.fileno())


def ler_jsonl(caminho: Path) -> list[dict[str, Any]]:
    itens: list[dict[str, Any]] = []
    if not caminho.is_file():
        return itens
    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            for numero, texto in enumerate(arquivo, 1):
                if not texto.strip():
                    continue
                valor = json.loads(texto)
                if not isinstance(valor, dict):
                    raise FalhaOperacao(f"linha {numero} de {caminho.name} não é objeto JSON")
                itens.append(valor)
    except (OSError, json.JSONDecodeError) as erro:
        raise FalhaOperacao(f"JSONL inválido: {caminho}") from erro
    return itens


def raiz_otimizador() -> Path:
    """Encontra a pasta transportável sem usar caminho fixo de computador."""
    candidatas: list[Path] = []
    informada = os.environ.get("CLUBEF_OTIMIZADOR_ROOT", "").strip()
    if informada:
        candidatas.append(Path(informada))
    if getattr(sys, "frozen", False):
        candidatas.append(Path(sys.executable).resolve().parent)
    candidatas.extend((Path.cwd(), Path(__file__).resolve().parent))
    vistos: set[Path] = set()
    for inicio in candidatas:
        try:
            inicio = inicio.resolve()
        except OSError:
            continue
        for pasta in (inicio, *inicio.parents):
            if pasta in vistos:
                continue
            vistos.add(pasta)
            # A pasta nova pode viajar sozinha. Quando ela e copiada sem a
            # raiz antiga do OTIMIZADOR, o executável encontra o pacote pelo
            # seu próprio diretório e usa os módulos já incluídos no EXE.
            if (pasta / NOME_PASTA / NOME_PACOTE).is_dir():
                return pasta
            if pasta.name == NOME_PASTA and (pasta / NOME_PACOTE).is_dir():
                return pasta.parent
            if (pasta / "roda_lote_v6.py").is_file() and (pasta / NOME_PACOTE).is_dir():
                return pasta
    raise FalhaOperacao(
        "não encontrei a pasta OTIMIZADOR com roda_lote_v6.py e PACOTE-FILA-INTEGRAL; "
        "copie a pasta operacional completa"
    )


def pasta_operacao(raiz: Path) -> Path:
    pasta = raiz / NOME_PASTA
    if not pasta.is_dir():
        raise FalhaOperacao(f"pasta da operação local não encontrada: {pasta}")
    return pasta


def _mortar_pacote(raiz: Path, operacao: Path, lote_id: str | None):
    """Abre o pacote local, preferindo a cópia dentro da operação nova.

    A cópia no local novo é a que viaja sozinha para outro computador. A antiga
    raiz continua sendo aceita enquanto a transferência física da pasta ainda
    não foi feita.
    """
    from fila_local_v1 import PacoteLocalV1

    possiveis: list[Path] = []
    for base in (operacao / NOME_PACOTE, raiz / NOME_PACOTE):
        if not base.is_dir():
            continue
        for candidata in sorted(base.iterdir()):
            if candidata.is_dir() and (candidata / "manifesto.json").is_file():
                if lote_id is None or candidata.name == str(lote_id):
                    possiveis.append(candidata)
        if possiveis:
            break
    if not possiveis:
        alvo = f" do lote {lote_id}" if lote_id else ""
        raise FalhaOperacao(f"pacote local{alvo} não encontrado em {NOME_PACOTE}")
    if len(possiveis) != 1:
        raise FalhaOperacao("há mais de um pacote local; informe o lote pelo parâmetro --lote")
    return PacoteLocalV1(possiveis[0])


def pasta_saida(operacao: Path, lote_id: str) -> Path:
    return operacao / "RESULTADOS-JSON" / str(lote_id)


def garantir_estrutura(saida: Path) -> dict[str, Path]:
    nomes = {
        "trabalho": "TRABALHO",
        "pendentes": "PENDENTES",
        "enviados": "ENVIADOS",
        "recibos": "RECIBOS",
        "falhas_calculo": "FALHAS-CALCULO",
        "falhas_envio": "FALHAS-ENVIO",
        "controle": "CONTROLE",
    }
    estrutura = {chave: saida / nome for chave, nome in nomes.items()}
    for caminho in estrutura.values():
        caminho.mkdir(parents=True, exist_ok=True)
    return estrutura


def _pid_ativo(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@contextlib.contextmanager
def trava_exclusiva(caminho: Path, nome: str) -> Iterator[None]:
    """Impede dois processadores ou dois enviadores na mesma saída local."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    descricao = {"pid": os.getpid(), "iniciado_em_utc": agora_utc(), "nome": nome}
    try:
        descritor = os.open(str(caminho), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            anterior = ler_json(caminho)
            pid_anterior = int(anterior.get("pid") or 0)
        except Exception:
            pid_anterior = 0
        if _pid_ativo(pid_anterior):
            raise FalhaOperacao(f"já existe {nome} em execução nesta pasta (PID {pid_anterior})")
        caminho.unlink(missing_ok=True)
        descritor = os.open(str(caminho), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(texto_json(descricao) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        yield
    finally:
        caminho.unlink(missing_ok=True)


def _validar_item(item: dict[str, Any], origem: Path) -> int:
    try:
        linha_id = int(item["linha_id"])
    except (KeyError, TypeError, ValueError) as erro:
        raise FalhaOperacao(f"resultado sem linha_id válido em {origem.name}") from erro
    if linha_id <= 0 or not isinstance(item.get("resultado"), dict):
        raise FalhaOperacao(f"resultado incompleto em {origem.name}")
    if not isinstance(item.get("calculado_em_utc"), str):
        raise FalhaOperacao(f"resultado sem data de cálculo em {origem.name}")
    return linha_id


def _ler_envelope(caminho: Path) -> dict[str, Any]:
    envelope = ler_json(caminho)
    if envelope.get("contrato") != CONTRATO_RESULTADO or int(envelope.get("versao") or 0) != VERSAO:
        raise FalhaOperacao(f"contrato de resultado desconhecido: {caminho.name}")
    itens = envelope.get("itens")
    if not isinstance(itens, list) or not itens:
        raise FalhaOperacao(f"arquivo sem resultados: {caminho.name}")
    vistos: set[int] = set()
    for item in itens:
        if not isinstance(item, dict):
            raise FalhaOperacao(f"item inválido em {caminho.name}")
        linha_id = _validar_item(item, caminho)
        if linha_id in vistos:
            raise FalhaOperacao(f"linha repetida em {caminho.name}: {linha_id}")
        vistos.add(linha_id)
    return envelope


def _arquivos_finalizados(estrutura: dict[str, Path]) -> list[Path]:
    return sorted(list(estrutura["pendentes"].glob("resultado-*.json")) +
                  list(estrutura["enviados"].glob("resultado-*.json")))


def contar_resultados(pasta: Path) -> int:
    total = 0
    for arquivo in sorted(pasta.glob("resultado-*.json")):
        total += len(_ler_envelope(arquivo)["itens"])
    return total


def linhas_ja_calculadas(estrutura: dict[str, Path]) -> set[int]:
    """Linhas já fechadas em JSON final; o jornal aberto é tratado à parte."""
    vistos: set[int] = set()
    for arquivo in _arquivos_finalizados(estrutura):
        for item in _ler_envelope(arquivo)["itens"]:
            linha_id = _validar_item(item, arquivo)
            if linha_id in vistos:
                raise FalhaOperacao(f"linha {linha_id} aparece em dois JSONs finais")
            vistos.add(linha_id)
    return vistos


def proxima_sequencia(estrutura: dict[str, Path]) -> int:
    maior = 0
    padrao = re.compile(r"^resultado-(\d{6})\.json(?:l)?$")
    for pasta in (estrutura["trabalho"], estrutura["pendentes"], estrutura["enviados"]):
        for arquivo in pasta.glob("resultado-*"):
            encontrado = padrao.match(arquivo.name)
            if encontrado:
                maior = max(maior, int(encontrado.group(1)))
    return maior + 1


def _envelope_resultado(pacote, sequencia: int, itens: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "contrato": CONTRATO_RESULTADO,
        "versao": VERSAO,
        "lote_id": pacote.lote_id,
        "lote_fingerprint": pacote.manifesto["lote_fingerprint"],
        "contrato_fingerprint": pacote.manifesto["contrato_fingerprint"],
        "formula_fingerprint": pacote.manifesto["formula_fingerprint"],
        "motor_versao": pacote.manifesto["motor_versao"],
        "sequencia_arquivo": sequencia,
        "criado_em_utc": agora_utc(),
        "itens": itens,
    }


def _jornal_atual(estrutura: dict[str, Path], pacote) -> tuple[int, Path, list[dict[str, Any]]]:
    jornais = sorted(estrutura["trabalho"].glob("resultado-*.jsonl"))
    if len(jornais) > 1:
        raise FalhaOperacao("há mais de um jornal de cálculo aberto; não é seguro adivinhar a ordem")
    if not jornais:
        sequencia = proxima_sequencia(estrutura)
        return sequencia, estrutura["trabalho"] / f"resultado-{sequencia:06d}.jsonl", []
    jornal = jornais[0]
    encontrado = re.match(r"^resultado-(\d{6})\.jsonl$", jornal.name)
    if not encontrado:
        raise FalhaOperacao(f"nome inválido de jornal: {jornal.name}")
    itens = ler_jsonl(jornal)
    if len(itens) > TAMANHO_JSON:
        raise FalhaOperacao(f"jornal excede {TAMANHO_JSON} resultados: {jornal.name}")
    for item in itens:
        _validar_item(item, jornal)
    return int(encontrado.group(1)), jornal, itens


def finalizar_jornal(estrutura: dict[str, Path], pacote, sequencia: int, jornal: Path, itens: list[dict[str, Any]]) -> Path:
    if not itens:
        raise FalhaOperacao("não há resultado para fechar em JSON")
    destino = estrutura["pendentes"] / f"resultado-{sequencia:06d}.json"
    if destino.exists():
        existente = _ler_envelope(destino)
        existentes = {int(x["linha_id"]) for x in existente["itens"]}
        atuais = {int(x["linha_id"]) for x in itens}
        if existentes != atuais:
            raise FalhaOperacao(f"JSON final já existe com linhas diferentes: {destino.name}")
    else:
        gravar_json_atomico(destino, _envelope_resultado(pacote, sequencia, itens))
    jornal.unlink(missing_ok=True)
    return destino


def calcular_linha(pacote, runner: Any, linha: dict[str, Any]) -> dict[str, Any]:
    carta = pacote.carta_da_linha(linha)
    if not isinstance(carta.get("carta"), dict):
        raise FalhaOperacao("a fotografia local da carta está ausente")
    runner.carrega_carta_snapshot_producao_v3(carta["carta"])
    resultado = runner.trabalha({
        "n": int(linha["linha_id"]),
        "card_id": str(linha["card_id"]),
        "funcao_id": int(linha["funcao_id"]),
        "posicao_id": int(linha["posicao_id"]),
        "impeto_condicional_codigo": None,
        "impeto_condicional_nivel": None,
        "origem": "operacao_local_json_v1",
    })
    if not isinstance(resultado, dict) or resultado.get("ERRO"):
        raise FalhaOperacao(str((resultado or {}).get("ERRO") or "o motor não devolveu resultado"))
    resultado.update({
        "card_id": str(linha["card_id"]),
        "funcao_id": int(linha["funcao_id"]),
        "posicao_id": int(linha["posicao_id"]),
        "formula_fingerprint": pacote.manifesto["formula_fingerprint"],
        "contrato_fingerprint": pacote.manifesto["contrato_fingerprint"],
        "motor_versao": pacote.manifesto["motor_versao"],
        "lote_fingerprint": pacote.manifesto["lote_fingerprint"],
        "carta_entrada_fingerprint": linha["carta_entrada_fingerprint"],
        "impeto_condicional_codigo": None,
        "impeto_condicional_nivel": None,
    })
    try:
        resultado["tecnico_id"] = int(resultado.get("tecnico_id"))
    except (TypeError, ValueError) as erro:
        raise FalhaOperacao("resultado calculado sem tecnico_id canônico") from erro
    return resultado


def processar(raiz: Path, lote_id: str | None, limite: int | None) -> int:
    # A pasta de trabalho fica como diretório atual antes de importar o motor:
    # assim a versão empacotada encontra o config local caso algum módulo o
    # consulte, porém o cálculo em si não abre rede nem usa a chave.
    operacao = pasta_operacao(raiz)
    os.chdir(operacao)
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    from fila_local_v1 import FalhaPacoteLocal
    from fila_producao_v3 import FORMULA_APROVADA, formula_fingerprint
    import roda_lote_v6 as runner

    pacote = _mortar_pacote(raiz, operacao, lote_id)
    saida = pasta_saida(operacao, pacote.lote_id)
    estrutura = garantir_estrutura(saida)
    with trava_exclusiva(estrutura["controle"] / "PROCESSADOR.lock", "processador"):
        print("Conferindo o pacote local selado...", flush=True)
        pacote.validar_integridade()
        if formula_fingerprint() != FORMULA_APROVADA:
            raise FalhaOperacao("a fórmula local não corresponde à fórmula aprovada")
        # O motor antigo nunca pode gravar por conta própria neste fluxo. O
        # único escritor passa a ser o segundo batch, depois do JSON durável.
        runner._gd.LIGADO = False
        runner.prepara_lote_producao_v3(pacote.manifesto["regua"])
        concluidas = linhas_ja_calculadas(estrutura)
        sequencia, jornal, itens_jornal = _jornal_atual(estrutura, pacote)
        ids_jornal = {int(item["linha_id"]) for item in itens_jornal}
        if concluidas.intersection(ids_jornal):
            raise FalhaOperacao("uma linha aparece em JSON final e no jornal aberto")

        novos = 0
        falhas = 0
        tentativas = 0
        falhas_total = len(list(estrutura["falhas_calculo"].glob("linha-*.json")))
        prontos_para_envio = contar_resultados(estrutura["pendentes"])
        enviados_confirmados = contar_resultados(estrutura["enviados"])
        for linha in pacote.iter_linhas():
            linha_id = int(linha["linha_id"])
            if linha_id in concluidas or linha_id in ids_jornal:
                continue
            inicio_linha = time.monotonic()
            _mostrar_processamento(
                pacote,
                len(concluidas) + len(ids_jornal),
                prontos_para_envio,
                enviados_confirmados,
                falhas_total,
                linha,
                inicio_linha,
            )
            try:
                resultado = calcular_linha(pacote, runner, linha)
            except Exception as erro:
                falhas += 1
                tentativas += 1
                falha = {
                    "contrato": "otimizador_falha_calculo_local_json_v1",
                    "lote_id": pacote.lote_id,
                    "linha_id": linha_id,
                    "ordem_fila": int(linha["ordem_fila"]),
                    "registrado_em_utc": agora_utc(),
                    "erro": str(erro),
                }
                gravar_json_atomico(estrutura["falhas_calculo"] / f"linha-{linha_id}.json", falha)
                falhas_total += 1
                print(
                    f"Erro registrado para Linha {linha_id} — {_carta_com_id(linha)}: {erro}",
                    flush=True,
                )
            else:
                item = {
                    "linha_id": linha_id,
                    "ordem_fila": int(linha["ordem_fila"]),
                    "card_id": str(linha["card_id"]),
                    "funcao_id": int(linha["funcao_id"]),
                    "posicao_id": int(linha["posicao_id"]),
                    "carta_nome": linha.get("carta_nome"),
                    "funcao_rotulo": linha.get("funcao_rotulo"),
                    "posicao_rotulo": linha.get("posicao_rotulo"),
                    "calculado_em_utc": agora_utc(),
                    "resultado": resultado,
                }
                acrescentar_jsonl_duravel(jornal, item)
                itens_jornal.append(item)
                ids_jornal.add(linha_id)
                novos += 1
                tentativas += 1
                if len(itens_jornal) >= TAMANHO_JSON:
                    arquivo = finalizar_jornal(estrutura, pacote, sequencia, jornal, itens_jornal)
                    prontos_para_envio += len(itens_jornal)
                    print(f"JSON pronto para o outro batch: {len(itens_jornal)} resultados.", flush=True)
                    sequencia += 1
                    jornal = estrutura["trabalho"] / f"resultado-{sequencia:06d}.jsonl"
                    itens_jornal = []
                    ids_jornal = set()
                elif novos % 10 == 0:
                    enviados_confirmados = contar_resultados(estrutura["enviados"])

            if limite is not None and tentativas >= limite:
                break

        gravar_json_atomico(estrutura["controle"] / "ESTADO-PROCESSAMENTO.json", {
            "contrato": "otimizador_estado_processamento_local_json_v1",
            "lote_id": pacote.lote_id,
            "atualizado_em_utc": agora_utc(),
            "calculadas_nesta_execucao": novos,
            "falhas_nesta_execucao": falhas,
            "jsons_prontos": len(list(estrutura["pendentes"].glob("resultado-*.json"))),
            "resultados_no_jornal": len(itens_jornal),
        })
        _mostrar_processamento(
            pacote,
            len(concluidas) + len(ids_jornal),
            prontos_para_envio,
            enviados_confirmados,
            falhas_total,
        )
        print(
            f"Processamento terminou. Novas: {novos}; falhas registradas: {falhas}; "
            f"resultados prontos para envio: {prontos_para_envio}.",
            flush=True,
        )
    return 0


def _ler_config(raiz: Path, operacao: Path) -> tuple[str, str, Path]:
    candidatas = (operacao / "config.txt", raiz.parent / "config.txt", raiz / "config.txt")
    for caminho in candidatas:
        if not caminho.is_file():
            continue
        valores: dict[str, str] = {}
        for texto in caminho.read_text(encoding="utf-8").splitlines():
            texto = texto.strip()
            if texto and not texto.startswith("#") and "=" in texto:
                chave, valor = texto.split("=", 1)
                valores[chave.strip()] = valor.strip()
        url = valores.get("SUPABASE_URL", "").strip().strip("[]")
        chave = valores.get("SUPABASE_KEY", "").strip()
        if url and chave:
            return url.rstrip("/"), chave, caminho
    raise FalhaOperacao(
        "config.txt sem SUPABASE_URL e SUPABASE_KEY. Coloque-o dentro de "
        f"{NOME_PASTA} ou na pasta 2-MOTORES desta cópia."
    )


def chamar_importacao(url: str, chave: str, lote_id: str, item: dict[str, Any]) -> dict[str, Any]:
    corpo = {
        "p_lote_id": lote_id,
        "p_linha_id": int(item["linha_id"]),
        "p_resultado": item["resultado"],
        "p_calculado_em_utc": item["calculado_em_utc"],
    }
    dados = texto_json(corpo).encode("utf-8")
    requisicao = urllib.request.Request(
        url + "/rest/v1/rpc/otimizador_producao_importar_json_local_v1",
        data=dados,
        headers={
            "apikey": chave,
            "Authorization": "Bearer " + chave,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=60) as resposta:
            bruto = resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "replace")[:1000]
        raise FalhaBanco(f"o banco recusou a linha {item['linha_id']} (HTTP {erro.code}): {detalhe}") from erro
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise FalhaRede(f"conexão incerta ao enviar a linha {item['linha_id']}: {erro}") from erro
    try:
        resposta = json.loads(bruto)
    except json.JSONDecodeError as erro:
        raise FalhaRede(f"o banco respondeu sem JSON para a linha {item['linha_id']}") from erro
    if not isinstance(resposta, dict):
        raise FalhaBanco(f"resposta inválida do banco para a linha {item['linha_id']}")
    if resposta.get("contrato") != CONTRATO_IMPORTACAO or int(resposta.get("linha_id") or 0) != int(item["linha_id"]):
        raise FalhaBanco(f"o banco não confirmou a linha correta: {item['linha_id']}")
    if not isinstance(resposta.get("enviado_em_utc"), str):
        raise FalhaBanco(f"o banco não devolveu a data/hora do envio da linha {item['linha_id']}")
    return resposta


def _recibos_confirmados(caminho: Path) -> dict[int, dict[str, Any]]:
    confirmados: dict[int, dict[str, Any]] = {}
    for recibo in ler_jsonl(caminho):
        if recibo.get("contrato") != CONTRATO_RECIBO or recibo.get("confirmado") is not True:
            raise FalhaOperacao(f"recibo inválido: {caminho.name}")
        try:
            linha_id = int(recibo["linha_id"])
        except (KeyError, TypeError, ValueError) as erro:
            raise FalhaOperacao(f"recibo sem linha válida: {caminho.name}") from erro
        anterior = confirmados.get(linha_id)
        if anterior and anterior != recibo:
            raise FalhaOperacao(f"há dois recibos diferentes para a linha {linha_id}")
        confirmados[linha_id] = recibo
    return confirmados


def _mover_envio_concluido(estrutura: dict[str, Path], arquivo: Path, recibo: Path, lote_id: str, total: int) -> None:
    destino = estrutura["enviados"] / arquivo.name
    destino_recibo = estrutura["enviados"] / (arquivo.stem + ".recibos.jsonl")
    if destino.exists() and destino != arquivo:
        raise FalhaOperacao(f"já existe um arquivo enviado com este nome: {arquivo.name}")
    os.replace(arquivo, destino)
    if recibo.is_file():
        os.replace(recibo, destino_recibo)
    gravar_json_atomico(estrutura["enviados"] / (arquivo.stem + ".resumo.json"), {
        "contrato": "otimizador_resumo_envio_local_json_v1",
        "lote_id": lote_id,
        "arquivo": arquivo.name,
        "total_confirmado": total,
        "fechado_em_utc": agora_utc(),
    })


def enviar(raiz: Path, lote_id: str | None, limite: int | None) -> int:
    operacao = pasta_operacao(raiz)
    if lote_id:
        lotes = [str(lote_id)]
    else:
        base = operacao / "RESULTADOS-JSON"
        lotes = sorted(p.name for p in base.iterdir()) if base.is_dir() else []
    if not lotes:
        raise FalhaOperacao("não há RESULTADOS-JSON para enviar; rode PROCESSAR-FILA.bat primeiro")
    if len(lotes) != 1:
        raise FalhaOperacao("há mais de uma saída local; informe o lote pelo parâmetro --lote")
    lote = lotes[0]
    estrutura = garantir_estrutura(pasta_saida(operacao, lote))
    url, chave, config = _ler_config(raiz, operacao)
    enviados_nesta_execucao = 0
    with trava_exclusiva(estrutura["controle"] / "ENVIADOR.lock", "enviador"):
        arquivos = sorted(estrutura["pendentes"].glob("resultado-*.json"))
        if not arquivos:
            print("Não há JSON pronto aguardando envio.", flush=True)
            return 0
        total_prontas = contar_resultados(estrutura["pendentes"])
        falhas_total = len(list(estrutura["falhas_envio"].glob("linha-*.json")))
        for arquivo in arquivos:
            envelope = _ler_envelope(arquivo)
            if str(envelope.get("lote_id")) != lote:
                raise FalhaOperacao(f"{arquivo.name} pertence a outro lote")
            recibo = estrutura["recibos"] / (arquivo.stem + ".recibos.jsonl")
            confirmados = _recibos_confirmados(recibo)
            ids = {int(item["linha_id"]) for item in envelope["itens"]}
            if not set(confirmados).issubset(ids):
                raise FalhaOperacao(f"recibo contém linha fora do JSON: {arquivo.name}")
            total_prontas -= len(confirmados)
            for item in envelope["itens"]:
                linha_id = int(item["linha_id"])
                if linha_id in confirmados:
                    continue
                inicio_envio = time.monotonic()
                _mostrar_envio(lote, total_prontas, enviados_nesta_execucao, falhas_total, item, inicio_envio)
                try:
                    resposta = chamar_importacao(url, chave, lote, item)
                except FalhaBanco as erro:
                    gravar_json_atomico(estrutura["falhas_envio"] / f"linha-{linha_id}.json", {
                        "contrato": "otimizador_falha_envio_local_json_v1",
                        "lote_id": lote,
                        "linha_id": linha_id,
                        "registrado_em_utc": agora_utc(),
                        "erro": str(erro),
                        "arquivo_origem": arquivo.name,
                    })
                    falhas_total += 1
                    raise
                recibo_item = {
                    "contrato": CONTRATO_RECIBO,
                    "versao": VERSAO,
                    "confirmado": True,
                    "lote_id": lote,
                    "linha_id": linha_id,
                    "calculado_em_utc": item["calculado_em_utc"],
                    "enviado_em_utc": resposta["enviado_em_utc"],
                    "build_otimizador_id": resposta.get("build_otimizador_id"),
                    "resultado_fingerprint": resposta.get("resultado_fingerprint"),
                    "idempotente": bool(resposta.get("idempotente")),
                }
                acrescentar_jsonl_duravel(recibo, recibo_item)
                confirmados[linha_id] = recibo_item
                enviados_nesta_execucao += 1
                total_prontas -= 1
                print(
                    f"Linha {linha_id} — {_carta_com_id(item)} confirmado em {recibo_item['enviado_em_utc']}"
                    + (" (já existia no banco)." if recibo_item["idempotente"] else "."),
                    flush=True,
                )
                if limite is not None and enviados_nesta_execucao >= limite:
                    print("Limite de teste atingido; tudo o que foi confirmado está registrado.", flush=True)
                    return 0
            if set(confirmados) == ids:
                _mover_envio_concluido(estrutura, arquivo, recibo, lote, len(ids))
                print(f"Arquivo concluído: {len(ids)} envios confirmados.", flush=True)
        gravar_json_atomico(estrutura["controle"] / "ESTADO-ENVIO.json", {
            "contrato": "otimizador_estado_envio_local_json_v1",
            "lote_id": lote,
            "atualizado_em_utc": agora_utc(),
            "confirmadas_nesta_execucao": enviados_nesta_execucao,
            "jsons_ainda_pendentes": len(list(estrutura["pendentes"].glob("resultado-*.json"))),
        })
        _mostrar_envio(lote, total_prontas, enviados_nesta_execucao, falhas_total)
        print(f"Envio terminou. Linhas confirmadas nesta execução: {enviados_nesta_execucao}.", flush=True)
    return 0


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Operação local JSON do Otimizador")
    sub = parser.add_subparsers(dest="comando", required=True)
    for nome in ("processar", "enviar"):
        comando = sub.add_parser(nome)
        comando.add_argument("--lote", help="UUID do lote local, se houver mais de um")
        comando.add_argument("--limite", type=int, help="somente para teste: máximo de linhas nesta execução")
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    if args.limite is not None and args.limite <= 0:
        raise FalhaOperacao("--limite deve ser maior que zero")
    raiz = raiz_otimizador()
    if args.comando == "processar":
        return processar(raiz, args.lote, args.limite)
    return enviar(raiz, args.lote, args.limite)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrompido pelo operador. O JSON/recibo já gravado foi preservado.", flush=True)
        raise SystemExit(130)
    except FalhaOperacao as erro:
        print(f"ERRO: {erro}", file=sys.stderr, flush=True)
        raise SystemExit(2)
    except Exception as erro:  # não mascara a falha: deixa um log técnico local para diagnóstico.
        print(f"ERRO INESPERADO: {erro}", file=sys.stderr, flush=True)
        traceback.print_exc()
        raise SystemExit(3)
