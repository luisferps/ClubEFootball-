# -*- coding: utf-8 -*-
"""Operação local do Otimizador, sem painel e sem reservas longas.

Há dois comandos deliberadamente separados:

``processar``
    Lê a fotografia em ``PACOTE-FILA-INTEGRAL`` com até quatro processos.
    Um único escritor grava os resultados duráveis na ordem da fila.

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
import hashlib
import json
import multiprocessing
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
from calculo_paralelo import iter_calculos


CONTRATO_RESULTADO = "otimizador_resultado_local_json_v1"
CONTRATO_RECIBO = "otimizador_recibo_local_json_v1"
CONTRATO_IMPORTACAO = "otimizador_importacao_json_local_v1"
VERSAO = 1
TAMANHO_JSON = 100
PROCESSOS_CONFIGURADOS = 4
NOME_PASTA = "OPERACAO-LOCAL-JSON"
NOME_PACOTE = "PACOTE-FILA-INTEGRAL"
PADRAO_ARQUIVO_RESULTADO = re.compile(r"^resultado-(\d{6})\.json$")
ESPERAS_BANCO_OCUPADO_SEGUNDOS = (5, 10, 20, 30)


class FalhaOperacao(RuntimeError):
    """Erro claro e recuperável para quem opera os batches."""


class FalhaRede(FalhaOperacao):
    """A resposta do banco ficou incerta; não se marca nada como enviado."""


class FalhaBanco(FalhaOperacao):
    """O banco respondeu recusando o resultado; nada é apagado do disco."""


class BancoOcupado(FalhaBanco):
    """Uma trava transitória impediu a transação; a mesma linha pode ser repetida."""


class LinhaJaConcluidaNoBanco(FalhaBanco):
    """A linha já tinha um resultado diferente antes deste envio local."""


class LinhaForaFilaNoBanco(FalhaBanco):
    """A fotografia local ainda contém uma linha que o banco já retirou."""


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
    repetidos_prontos: int = 0,
) -> None:
    total = int(pacote.manifesto.get("linhas_total") or 0)
    cartas = int(pacote.manifesto.get("cartas_total") or 0)
    _cabecalho_painel("FILA LOCAL — PROCESSANDO SEM PAINEL ANTIGO")
    print(f"Cartas neste pacote: {cartas}")
    print(f"Linhas no pacote local: {total}")
    print(f"Linhas com cálculo local salvo: {calculadas}")
    print(f"Resultados locais aguardando envio: {prontas_para_envio}")
    # ENVIADOS contém envelopes cujo envio já recebeu uma decisão terminal.
    # A decisão pode ser confirmação, resultado já existente ou linha retirada
    # da fila. Por isso este número nunca deve ser chamado de "confirmadas".
    print(f"Linhas com envio já encerrado: {enviadas}")
    print(f"Processos de cálculo configurados: {PROCESSOS_CONFIGURADOS}")
    print(f"Linhas ainda sem cálculo local: {max(0, total - calculadas)}")
    print(f"Falhas de cálculo registradas: {falhas}")
    if repetidos_prontos:
        print(f"Repetidos locais ignorados: {repetidos_prontos}")
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
        print("Resultado: aguardando gravação local; ainda não enviado ao banco.")
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
    repetidos_ignorados: int = 0,
) -> None:
    _cabecalho_painel("RESULTADOS LOCAIS — ENVIANDO UMA LINHA POR VEZ")
    print(f"Resultados aguardando envio: {total_prontas}")
    print(f"Confirmadas nesta execução: {confirmadas}")
    print(f"Problemas de envio: {falhas}")
    if repetidos_ignorados:
        print(f"Repetidos locais ignorados: {repetidos_ignorados}")
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
    from fila_local_v1 import FalhaPacoteLocal, PacoteLocalV1

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
    try:
        return PacoteLocalV1(possiveis[0])
    except FalhaPacoteLocal as erro:
        raise FalhaOperacao(f"pacote do lote {lote_id}: {erro}") from erro


def pasta_saida(operacao: Path, lote_id: str) -> Path:
    nome_raiz = os.environ.get("CLUBEFOOTBALL_RESULTADOS_SUBPASTA", "RESULTADOS-JSON").strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", nome_raiz):
        raise FalhaOperacao("subpasta de resultados inválida")
    return operacao / nome_raiz / str(lote_id)


def garantir_estrutura(saida: Path) -> dict[str, Path]:
    nomes = {
        "trabalho": "TRABALHO",
        "pendentes": "PENDENTES",
        "enviados": "ENVIADOS",
        "recibos": "RECIBOS",
        "falhas_calculo": "FALHAS-CALCULO",
        "falhas_envio": "FALHAS-ENVIO",
        "conflitos_banco": "CONFLITOS-NO-BANCO",
        "arquivados": "ARQUIVADOS-COM-CONFLITO",
        "nao_enviados": "ARQUIVADOS-FORA-DA-FILA-ATIVA",
        "historico_renovacoes": "HISTORICO-RENOVACOES",
        "controle": "CONTROLE",
    }
    estrutura = {chave: saida / nome for chave, nome in nomes.items()}
    for caminho in estrutura.values():
        caminho.mkdir(parents=True, exist_ok=True)
    return estrutura


def _selos_resultado(item: dict[str, Any]) -> tuple[str, str, str]:
    resultado = item.get("resultado")
    if not isinstance(resultado, dict):
        return "", "", ""
    return tuple(
        str(resultado.get(chave) or "")
        for chave in ("lote_fingerprint", "formula_fingerprint", "contrato_fingerprint")
    )


def _selos_pacote(pacote: Any) -> tuple[str, str, str]:
    return tuple(
        str(pacote.manifesto.get(chave) or "")
        for chave in ("lote_fingerprint", "formula_fingerprint", "contrato_fingerprint")
    )


def _mover_historico(origem: Path, destino: Path) -> None:
    if not origem.is_file():
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        raise FalhaOperacao(f"o histórico da renovação já contém {destino.name}")
    os.replace(origem, destino)


def _itens_resultado_ou_jornal(caminho: Path) -> list[dict[str, Any]]:
    if caminho.suffix.lower() == ".jsonl":
        itens = ler_jsonl(caminho)
        if not itens:
            raise FalhaOperacao(f"jornal vazio: {caminho.name}")
        for item in itens:
            _validar_item(item, caminho)
        return itens
    return _ler_envelope(caminho)["itens"]


def reconciliar_historico_renovado(estrutura: dict[str, Path], pacote: Any) -> dict[str, Any]:
    """Separa resultados de uma fotografia anterior antes de calcular a atual.

    Lotes renovados preservam ``RESULTADOS-JSON`` para auditoria e podem reutilizar
    os mesmos ``linha_id``. Um resultado só pertence à fotografia carregada quando
    seus selos de lote, fórmula e contrato coincidem com o manifesto atual. Os
    demais são movidos inteiros para um histórico fora do inventário operacional.
    Nenhum arquivo com mistura de fotografias é escolhido automaticamente.
    """
    selos_atuais = _selos_pacote(pacote)
    if any(not selo for selo in selos_atuais):
        raise FalhaOperacao("o pacote atual não possui todos os selos de reconciliação")

    pastas_finais = (
        estrutura["pendentes"], estrutura["enviados"], estrutura["arquivados"],
        estrutura["nao_enviados"],
    )
    arquivos = [
        arquivo
        for pasta in pastas_finais
        for arquivo in _arquivos_resultado(pasta)
    ]
    arquivos.extend(sorted(estrutura["trabalho"].glob("resultado-*.jsonl")))

    sufixo = selos_atuais[0][:16]
    # A sequência resultado-000001 pode reaparecer em outra fotografia ou
    # numa cópia restaurada da máquina dedicada. Cada reconciliação recebe
    # seu próprio destino: nunca substitui nem deduplica o histórico antigo.
    raiz_historico = (
        estrutura["historico_renovacoes"] / sufixo / ("passagem-" + uuid.uuid4().hex)
    )
    movidos_arquivos = 0
    movidos_itens = 0
    mantidos_arquivos = 0
    ids_historicos: set[int] = set()

    for arquivo in arquivos:
        itens = _itens_resultado_ou_jornal(arquivo)
        compativeis = [_selos_resultado(item) == selos_atuais for item in itens]
        if all(compativeis):
            mantidos_arquivos += 1
            continue
        if any(compativeis):
            raise FalhaOperacao(
                f"{arquivo.name} mistura resultados da fotografia atual e anterior; "
                "o arquivo foi preservado sem alteração"
            )

        ids_arquivo = {int(item["linha_id"]) for item in itens}
        ids_historicos.update(ids_arquivo)
        destino_pasta = raiz_historico / arquivo.parent.name
        _mover_historico(arquivo, destino_pasta / arquivo.name)
        movidos_arquivos += 1
        movidos_itens += len(itens)

        # Recibos e resumos têm o mesmo radical do envelope. Eles precisam
        # acompanhar o resultado antigo para não tornarem a nova linha terminal.
        companheiros = list(arquivo.parent.glob(arquivo.stem + ".recibos.jsonl"))
        companheiros.extend(arquivo.parent.glob(arquivo.stem + ".resumo.json"))
        if arquivo.parent == estrutura["pendentes"]:
            companheiros.extend(estrutura["recibos"].glob(arquivo.stem + ".recibos.jsonl"))
        for companheiro in companheiros:
            destino = raiz_historico / companheiro.parent.name / companheiro.name
            _mover_historico(companheiro, destino)

    # Diagnósticos por linha também descrevem a fotografia anterior. Mantê-los
    # nas pastas ativas adulteraria o painel e decisões de uma nova tentativa.
    for chave in ("falhas_calculo", "falhas_envio", "conflitos_banco"):
        pasta = estrutura[chave]
        for linha_id in ids_historicos:
            diagnostico = pasta / f"linha-{linha_id}.json"
            if diagnostico.is_file():
                _mover_historico(
                    diagnostico,
                    raiz_historico / pasta.name / diagnostico.name,
                )

    relatorio = {
        "contrato": "otimizador_reconciliacao_historico_renovado_v1",
        "lote_id": pacote.lote_id,
        "lote_fingerprint": selos_atuais[0],
        "formula_fingerprint": selos_atuais[1],
        "contrato_fingerprint": selos_atuais[2],
        "executado_em_utc": agora_utc(),
        "arquivos_historicos_movidos": movidos_arquivos,
        "resultados_historicos_movidos": movidos_itens,
        "arquivos_atuais_mantidos": mantidos_arquivos,
        "historico_relativo": str(raiz_historico.relative_to(estrutura["historico_renovacoes"].parent)),
    }
    gravar_json_atomico(estrutura["controle"] / "ULTIMA-RECONCILIACAO-RENOVACAO.json", relatorio)
    if movidos_arquivos:
        print(
            f"Renovação reconciliada: {movidos_itens} resultados antigos preservados em "
            f"{raiz_historico.name}; a fotografia atual continuará normalmente.",
            flush=True,
        )
    return relatorio


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


def _arquivos_resultado(pasta: Path) -> list[Path]:
    """Lista somente envelopes de resultado, sem resumos ou recibos.

    O resumo terminal também começa com ``resultado-``. Usar o glob amplo
    ``resultado-*.json`` faria o processador tentar tratá-lo como resultado e
    parar com "contrato de resultado desconhecido".
    """
    return sorted(
        caminho
        for caminho in pasta.iterdir()
        if caminho.is_file() and PADRAO_ARQUIVO_RESULTADO.fullmatch(caminho.name)
    )


def _arquivos_finalizados(estrutura: dict[str, Path]) -> list[Path]:
    return sorted(_arquivos_resultado(estrutura["pendentes"]) +
                  _arquivos_resultado(estrutura["enviados"]) +
                  _arquivos_resultado(estrutura["arquivados"]) +
                  _arquivos_resultado(estrutura["nao_enviados"]))


def _assinatura_resultado(item: dict[str, Any]) -> str:
    """Resume o cálculo, sem incluir a hora local, para detectar repetição.

    A mesma linha pode aparecer de novo depois de uma cópia ou queda anterior.
    Só uma repetição exatamente igual é tolerada; dois cálculos diferentes para
    a mesma linha são uma divergência que deve parar antes de tocar no banco.
    """
    _validar_item(item, Path("resultado"))
    carga = {
        "linha_id": int(item["linha_id"]),
        "card_id": str(item.get("card_id") or ""),
        "funcao_id": item.get("funcao_id"),
        "posicao_id": item.get("posicao_id"),
        "resultado": item["resultado"],
    }
    return hashlib.sha256(texto_json(carga).encode("utf-8")).hexdigest()


def _inventariar_resultados(arquivos: list[Path]) -> tuple[dict[int, tuple[Path, str]], int, int]:
    """Lê resultados finais e devolve únicos, total físico e repetições iguais.

    Não deixa a contagem física esconder uma divergência: se dois arquivos
    trouxerem resultados distintos para a mesma linha, falha fechado antes de
    qualquer cálculo novo ou envio ao banco.
    """
    unicos: dict[int, tuple[Path, str]] = {}
    total_fisico = 0
    repetidos = 0
    for arquivo in arquivos:
        for item in _ler_envelope(arquivo)["itens"]:
            linha_id = _validar_item(item, arquivo)
            assinatura = _assinatura_resultado(item)
            total_fisico += 1
            anterior = unicos.get(linha_id)
            if anterior is None:
                unicos[linha_id] = (arquivo, assinatura)
                continue
            if anterior[1] != assinatura:
                raise FalhaOperacao(
                    f"a linha {linha_id} tem dois resultados diferentes: "
                    f"{anterior[0].name} e {arquivo.name}"
                )
            repetidos += 1
    return unicos, total_fisico, repetidos


def contar_resultados(pasta: Path) -> int:
    total = 0
    for arquivo in _arquivos_resultado(pasta):
        total += len(_ler_envelope(arquivo)["itens"])
    return total


def linhas_ja_calculadas(estrutura: dict[str, Path]) -> set[int]:
    """Linhas já fechadas em JSON final; o jornal aberto é tratado à parte."""
    unicos, _, _ = _inventariar_resultados(_arquivos_finalizados(estrutura))
    return set(unicos)


def contagens_painel_pacote(ids_pacote, concluidas, ids_jornal,
                            pendentes_unicos, enviados_unicos) -> tuple[int, int, int]:
    """Conta somente resultados cujos IDs ainda existem no pacote renovado."""
    atuais = {int(valor) for valor in ids_pacote}
    concluidas_atuais = {int(valor) for valor in concluidas}.intersection(atuais)
    jornal_atual = {int(valor) for valor in ids_jornal}.intersection(atuais)
    pendentes_atuais = {int(valor) for valor in pendentes_unicos}.intersection(atuais)
    enviados_atuais = {int(valor) for valor in enviados_unicos}.intersection(atuais)
    return (
        len(concluidas_atuais.union(jornal_atual)),
        len(pendentes_atuais - enviados_atuais),
        len(enviados_atuais),
    )


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
    """Calcula UMA linha do pacote local.

    ⚠️ Este caminho e uma copia do `fila_local_v1._calcular`. Sao dois codigos
    fazendo a mesma coisa, e e este aqui que o OperacaoLocalJson.exe usa —
    consertar so o outro nao muda nada no que voce clica.

    03/09 — o degrau do Impeto condicional vem DA LINHA. O par codigo+nivel
    estava fixo em None nas duas pontas desta funcao, e o pacote local sempre
    trouxe os dois campos: eram lidos do disco e jogados fora aqui. Cada
    combinacao funcao+posicao tem tres linhas, uma por degrau, e e este par que
    diz qual delas esta sendo calculada — sem ele as tres virariam a mesma
    conta tres vezes.
    """
    carta = pacote.carta_da_linha(linha)
    if not isinstance(carta.get("carta"), dict):
        raise FalhaOperacao("a fotografia local da carta está ausente")
    runner.carrega_carta_snapshot_producao_v3(carta["carta"])
    cond_codigo = linha.get("impeto_condicional_codigo")
    cond_nivel = linha.get("impeto_condicional_nivel")
    cond_codigo = None if cond_codigo is None else int(cond_codigo)
    cond_nivel = None if cond_nivel is None else int(cond_nivel)
    if (cond_codigo is None) != (cond_nivel is None):
        raise FalhaOperacao(
            "linha %s trouxe Ímpeto condicional pela metade: código %r, nível %r"
            % (linha.get("linha_id"), cond_codigo, cond_nivel))
    resultado = runner.trabalha({
        "n": int(linha["linha_id"]),
        "card_id": str(linha["card_id"]),
        "funcao_id": int(linha["funcao_id"]),
        "posicao_id": int(linha["posicao_id"]),
        "impeto_condicional_codigo": cond_codigo,
        "impeto_condicional_nivel": cond_nivel,
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
        # O resultado carimba o degrau calculado. A porta do banco confere
        # este par contra o da linha antes de gravar.
        "impeto_condicional_codigo": cond_codigo,
        "impeto_condicional_nivel": cond_nivel,
    })
    try:
        resultado["tecnico_id"] = int(resultado.get("tecnico_id"))
    except (TypeError, ValueError) as erro:
        raise FalhaOperacao("resultado calculado sem tecnico_id canônico") from erro
    return resultado


def chave_prioridade(linha: dict[str, Any]) -> tuple:
    """Mesma ordem do contrato SQL; desconhecido nunca equivale a nível 1."""
    grupo = linha.get("prioridade_grupo")
    ordenacao = linha.get("prioridade_ordenacao", "prioridade_orcamento_v1")
    if ordenacao not in ("prioridade_orcamento_v1", "novos_orcamento_overall_desc_v2"):
        raise FalhaOperacao("ordenação de prioridade desconhecida; renove a fotografia")
    novos_primeiro = ordenacao == "novos_orcamento_overall_desc_v2"
    nivel = linha.get("nivel_maximo")
    orcamento = linha.get("orcamento_real")
    if type(grupo) is not int or grupo not in ((0, 1, 2) if novos_primeiro else (1, 2, 3)):
        raise FalhaOperacao("pacote sem grupo de prioridade comprovado; renove a fotografia")
    if type(nivel) is not int or nivel < 1 or type(orcamento) is not int or orcamento != 2 * (nivel - 1):
        raise FalhaOperacao("pacote sem nível/orçamento físico válido; renove a fotografia")
    if not linha.get("captura_id") or (grupo == 1 and nivel == 1) or (grupo == 2 and nivel != 1):
        raise FalhaOperacao("prioridade não corresponde à evidência física da linha")
    overall = linha.get("overall_prioridade")
    if overall is not None and type(overall) is not int:
        raise FalhaOperacao("overall da prioridade deve ser inteiro ou ausente")
    # Na rodada atual, o banco identifica as cartas novas pelo grupo 0.
    # Cada grupo usa overall decrescente; ausência de overall não inventa nota.
    # Pacotes históricos mantêm sua ordenação anterior.
    return (
        grupo, (overall is None if novos_primeiro else overall is not None), -overall if overall is not None else 0,
        str(linha["card_id"]), int(linha["funcao_id"]), int(linha["posicao_id"]),
        linha.get("impeto_condicional_codigo") is not None,
        int(linha.get("impeto_condicional_codigo") or 0),
        linha.get("impeto_condicional_nivel") is not None,
        int(linha.get("impeto_condicional_nivel") or 0), int(linha["linha_id"]),
    )


def ordenar_fila_global(pacotes, calculadas_por_lote: dict[str, set[int]], lotes_prioritarios=None):
    """Escolhe linhas entre lotes; cada resultado continua no lote de origem."""
    prioritarios = lotes_prioritarios or []
    if (not isinstance(prioritarios, list) or any(not isinstance(lote, str) for lote in prioritarios)
            or len(set(prioritarios)) != len(prioritarios)
            or not set(prioritarios).issubset({pacote.lote_id for pacote in pacotes})):
        raise FalhaOperacao("lotes prioritários inválidos para a fila ativa")
    fila = []
    vistos = set()
    for pacote in pacotes:
        if pacote.manifesto.get("prioridade_contrato") != "prioridade_orcamento_v1":
            raise FalhaOperacao(f"pacote {pacote.lote_id} anterior à prioridade física; renove o pacote")
        for linha in pacote.iter_linhas():
            if linha.get("prioridade_ordenacao", "prioridade_orcamento_v1") != pacote.manifesto.get("prioridade_ordenacao", "prioridade_orcamento_v1"):
                raise FalhaOperacao("ordenação da linha diverge do manifesto; renove a fotografia")
            linha_id = int(linha["linha_id"])
            if linha_id in vistos:
                raise FalhaOperacao(f"linha {linha_id} repetida entre pacotes ativos")
            vistos.add(linha_id)
            chave = chave_prioridade(linha)
            carta = pacote.carta_da_linha(linha)
            usado = (carta.get("carta") or {}).get("escalares", {}).get("orcamento")
            if usado != linha["orcamento_real"]:
                raise FalhaOperacao(f"linha {linha_id} usa orçamento diferente da prova")
            if linha_id not in calculadas_por_lote.get(pacote.lote_id, set()):
                fila.append((chave, pacote, linha))
    fila.sort(key=lambda item: item[0])
    # Partição estável: somente a correção vai para a frente. A sequência
    # anteriormente calculada de TODOS os demais lotes fica idêntica.
    if prioritarios:
        prioridade = {lote: indice for indice, lote in enumerate(prioritarios)}
        fila.sort(key=lambda item: prioridade.get(item[1].lote_id, len(prioridade)))
    return [(pacote, linha) for _, pacote, linha in fila]


def processar_global(raiz: Path, limite: int | None, cards_alvo: list[str] | None = None,
                     linhas_alvo: list[int] | None = None, processos: int = 4) -> int:
    operacao = pasta_operacao(raiz)
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    selecao = ler_json(operacao / "FILA-ATIVA.json")
    lotes = selecao.get("lotes")
    if selecao.get("contrato") != "prioridade_orcamento_v1" or not isinstance(lotes, list) or not lotes:
        raise FalhaOperacao("fila ativa ausente ou inválida; renove os pacotes antes de processar")
    if len(set(lotes)) != len(lotes):
        raise FalhaOperacao("fila ativa contém lote repetido")
    with trava_exclusiva(operacao / "PROCESSADOR-GLOBAL.lock", "processador global"):
        sem_pendentes = set(selecao.get("lotes_sem_pendentes") or [])
        if not sem_pendentes.issubset(set(lotes)):
            raise FalhaOperacao("lotes sem pendentes fora da fila ativa")
        prioritarios = selecao.get("lotes_prioritarios", [])
        if (not isinstance(prioritarios, list)
                or any(not isinstance(lote, str) for lote in prioritarios)
                or len(set(prioritarios)) != len(prioritarios)
                or not set(prioritarios).issubset(set(lotes))):
            raise FalhaOperacao("lotes prioritários inválidos para a fila ativa")
        # A fotografia pode confirmar que um lote prioritário já terminou.
        # Ele permanece na seleção e na ordem histórica, mas não é montado.
        # A fotografia confirma ausência de linhas elegíveis, não a conclusão
        # de todo o histórico do lote (cartas removidas podem ficar pendentes).
        prioritarios = [lote for lote in prioritarios if lote not in sem_pendentes]
        pacotes = [_mortar_pacote(raiz, operacao, lote) for lote in lotes
                   if lote not in sem_pendentes]
        calculadas = {}
        ids_por_lote = {}
        for pacote in pacotes:
            pacote.validar_integridade()
            ids_por_lote[pacote.lote_id] = {
                int(linha["linha_id"]) for linha in pacote.iter_linhas()
            }
            estrutura = garantir_estrutura(pasta_saida(operacao, pacote.lote_id))
            # A fila global precisa separar a fotografia anterior antes de
            # inventariar o que já foi calculado. Fazer isso apenas dentro de
            # ``processar`` é tarde demais: este inventário global é executado
            # primeiro e encontraria dois resultados legítimos da mesma linha,
            # um de cada fotografia, abortando antes da reconciliação.
            reconciliar_historico_renovado(estrutura, pacote)
            feitas = linhas_ja_calculadas(estrutura)
            _, _, jornal = _jornal_atual(estrutura, pacote)
            feitas.update(int(item["linha_id"]) for item in jornal)
            calculadas[pacote.lote_id] = feitas
        fila = ordenar_fila_global(pacotes, calculadas, prioritarios)
        if cards_alvo:
            ordem_cards = {card_id: indice for indice, card_id in enumerate(cards_alvo)}
            fila = [
                item for item in fila
                if str(item[1].get("card_id")) in ordem_cards
            ]
            fila.sort(key=lambda item: ordem_cards[str(item[1]["card_id"])])
        if linhas_alvo:
            ordem_linhas = {linha_id: indice for indice, linha_id in enumerate(linhas_alvo)}
            fila = [item for item in fila if int(item[1]["linha_id"]) in ordem_linhas]
            fila.sort(key=lambda item: ordem_linhas[int(item[1]["linha_id"])])
        if limite is not None:
            fila = fila[:limite]
        print(f"Fila global conferida: {len(fila)} linhas em {len(pacotes)} lotes.", flush=True)
        # Trechos consecutivos do mesmo lote permitem reaproveitar o protocolo
        # durável existente sem misturar envelopes de lotes diferentes.
        inicio = 0
        codigo_saida = 0
        while inicio < len(fila):
            pacote = fila[inicio][0]
            fim = inicio + 1
            while fim < len(fila) and fila[fim][0].lote_id == pacote.lote_id:
                fim += 1
            codigo_saida = max(codigo_saida, processar(raiz, pacote.lote_id, None, pacote_override=pacote,
                      linhas_override=[linha for _, linha in fila[inicio:fim]],
                      ids_pacote_override=ids_por_lote[pacote.lote_id], processos=processos))
            inicio = fim
        # Também fecha journals parciais de uma execução interrompida, sem
        # recalcular suas linhas, inclusive quando não restou trabalho novo.
        for pacote in pacotes:
            codigo_saida = max(codigo_saida, processar(raiz, pacote.lote_id, None, pacote_override=pacote, linhas_override=[],
                      ids_pacote_override=ids_por_lote[pacote.lote_id]))
        gravar_json_atomico(operacao / "ESTADO-PROCESSAMENTO-GLOBAL.json", {
            "atualizado_em_utc": agora_utc(), "codigo_saida": codigo_saida,
            "estado": "com_falhas" if codigo_saida else "concluido_sem_falhas_nesta_execucao",
            "linhas_selecionadas": len(fila), "lotes": [p.lote_id for p in pacotes],
        })
    if codigo_saida:
        print("Processamento encerrado com falhas. Resultados válidos preservados; consulte FALHAS-CALCULO.", flush=True)
    return codigo_saida


def processar(raiz: Path, lote_id: str | None, limite: int | None,
              *, pacote_override=None, linhas_override=None, ids_pacote_override=None, processos: int = 4) -> int:
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

    pacote = pacote_override or _mortar_pacote(raiz, operacao, lote_id)
    if pacote.manifesto.get("prioridade_contrato") != "prioridade_orcamento_v1":
        raise FalhaOperacao("pacote anterior à correção de orçamento; renove o pacote antes de processar")
    saida = pasta_saida(operacao, pacote.lote_id)
    estrutura = garantir_estrutura(saida)
    with trava_exclusiva(estrutura["controle"] / "PROCESSADOR.lock", "processador"):
        print("Conferindo o pacote local selado...", flush=True)
        pacote.validar_integridade()
        if formula_fingerprint() != FORMULA_APROVADA:
            raise FalhaOperacao("a fórmula local não corresponde à fórmula aprovada")
        reconciliar_historico_renovado(estrutura, pacote)
        # O motor antigo nunca pode gravar por conta própria neste fluxo. O
        # único escritor passa a ser o segundo batch, depois do JSON durável.
        runner._gd.LIGADO = False
        runner.prepara_lote_producao_v3(pacote.manifesto["regua"])
        from complemento_contexto_v14 import carregar_atual
        from complemento_runtime_v14 import ativar
        complemento = carregar_atual(raiz)
        ativar(runner, complemento)
        concluidas = linhas_ja_calculadas(estrutura)
        pendentes_unicos, _, repetidos_pendentes = _inventariar_resultados(
            _arquivos_resultado(estrutura["pendentes"])
        )
        enviados_unicos, _, _ = _inventariar_resultados(
            _arquivos_resultado(estrutura["enviados"])
        )
        sequencia, jornal, itens_jornal = _jornal_atual(estrutura, pacote)
        ids_jornal = {int(item["linha_id"]) for item in itens_jornal}
        if concluidas.intersection(ids_jornal):
            raise FalhaOperacao("uma linha aparece em JSON final e no jornal aberto")

        # Uma renovação remove do pacote as linhas já confirmadas ou invalidadas,
        # mas preserva seus resultados locais para auditoria. O painel deve contar
        # apenas IDs que ainda pertencem à fotografia atual; somar todo o histórico
        # fazia o restante exibido ficar artificialmente menor.
        ids_pacote = (set(ids_pacote_override) if ids_pacote_override is not None else
                      {int(linha["linha_id"]) for linha in pacote.iter_linhas()})
        concluidas_pacote = concluidas.intersection(ids_pacote)
        ids_jornal_pacote = ids_jornal.intersection(ids_pacote)

        novos = 0
        falhas = 0
        tentativas = 0
        falhas_total = len(list(estrutura["falhas_calculo"].glob("linha-*.json")))
        calculadas_no_pacote, prontos_para_envio, enviados_confirmados = contagens_painel_pacote(
            ids_pacote, concluidas, ids_jornal, pendentes_unicos, enviados_unicos
        )
        linhas = linhas_override if linhas_override is not None else [
            linha for _, linha in ordenar_fila_global([pacote], {})
        ]
        linhas = [linha for linha in linhas if int(linha['linha_id']) not in concluidas
                  and int(linha['linha_id']) not in ids_jornal]
        if limite is not None:
            linhas = linhas[:limite]
        for linha, futuro in iter_calculos(raiz, pacote.lote_id, linhas, processos, complemento):
            linha_id = int(linha["linha_id"])
            if linha_id in concluidas or linha_id in ids_jornal:
                continue
            inicio_linha = time.monotonic()
            _mostrar_processamento(
                pacote,
                calculadas_no_pacote,
                prontos_para_envio,
                enviados_confirmados,
                falhas_total,
                linha,
                inicio_linha,
                repetidos_prontos=repetidos_pendentes,
            )
            try:
                resultado = futuro.result() if futuro is not None else calcular_linha(pacote, runner, linha)
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
                ids_jornal_pacote.add(linha_id)
                calculadas_no_pacote += 1
                novos += 1
                tentativas += 1
                if len(itens_jornal) >= TAMANHO_JSON:
                    arquivo = finalizar_jornal(estrutura, pacote, sequencia, jornal, itens_jornal)
                    prontos_para_envio += len(itens_jornal)
                    print(f"JSON pronto para o outro batch: {len(itens_jornal)} resultados.", flush=True)
                    # A partir daqui essas linhas já são finais no disco. Mantê-las
                    # no conjunto da execução impede que o painel diminua a
                    # contagem no corte de 100 e evita qualquer repetição após um
                    # próximo trecho do mesmo processo.
                    concluidas.update(ids_jornal)
                    concluidas_pacote.update(ids_jornal_pacote)
                    sequencia += 1
                    jornal = estrutura["trabalho"] / f"resultado-{sequencia:06d}.jsonl"
                    itens_jornal = []
                    ids_jornal = set()
                    ids_jornal_pacote = set()
                elif novos % 10 == 0:
                    pendentes_agora, _, _ = _inventariar_resultados(
                        _arquivos_resultado(estrutura["pendentes"])
                    )
                    enviados_agora, _, _ = _inventariar_resultados(
                        _arquivos_resultado(estrutura["enviados"])
                    )
                    prontos_para_envio = len(
                        (set(pendentes_agora) - set(enviados_agora)).intersection(ids_pacote)
                    )
                    enviados_confirmados = len(set(enviados_agora).intersection(ids_pacote))

            if limite is not None and tentativas >= limite:
                break

        # Não espera acumular 100 resultados para encerrar a execução. O
        # jornal parcial já é durável, mas precisa virar envelope final para o
        # enviador encontrá-lo. Isso também recupera, sem recalcular, um
        # jornal deixado por uma versão anterior ao fim do lote.
        if itens_jornal:
            finalizar_jornal(estrutura, pacote, sequencia, jornal, itens_jornal)
            prontos_para_envio += len(itens_jornal)
            concluidas.update(ids_jornal)
            concluidas_pacote.update(ids_jornal_pacote)
            itens_jornal = []
            ids_jornal = set()
            ids_jornal_pacote = set()

        gravar_json_atomico(estrutura["controle"] / "ESTADO-PROCESSAMENTO.json", {
            "contrato": "otimizador_estado_processamento_local_json_v1",
            "lote_id": pacote.lote_id,
            "atualizado_em_utc": agora_utc(),
            "calculadas_nesta_execucao": novos,
            "falhas_nesta_execucao": falhas,
            "estado": "com_falhas" if falhas else "concluido_sem_falhas_nesta_execucao",
            "codigo_saida": 2 if falhas else 0,
            "jsons_prontos": len(_arquivos_resultado(estrutura["pendentes"])),
            "resultados_no_jornal": len(itens_jornal),
        })
        _mostrar_processamento(
            pacote,
            calculadas_no_pacote,
            prontos_para_envio,
            enviados_confirmados,
            falhas_total,
            repetidos_prontos=repetidos_pendentes,
        )
        print(
            f"Processamento terminou {'COM FALHAS' if falhas else 'sem falhas nesta execução'}. Novas: {novos}; falhas registradas: {falhas}; "
            f"resultados prontos para envio: {prontos_para_envio}.",
            flush=True,
        )
    return 2 if falhas else 0


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


def _codigo_erro_http(detalhe: str) -> str:
    """Extrai o SQLSTATE devolvido pelo PostgREST sem depender do texto humano."""
    try:
        corpo = json.loads(detalhe)
    except (json.JSONDecodeError, TypeError):
        return ""
    if not isinstance(corpo, dict):
        return ""
    return str(corpo.get("code") or "").strip().upper()


def _mensagem_erro_http(detalhe: str) -> str:
    """Lê a mensagem do PostgREST já com os escapes JSON decodificados."""
    try:
        corpo = json.loads(detalhe)
    except (json.JSONDecodeError, TypeError):
        return str(detalhe or "")
    if not isinstance(corpo, dict):
        return str(detalhe or "")
    return str(corpo.get("message") or "")


def _segundos_banco_ocupado(tentativa: int) -> int:
    indice = min(max(int(tentativa), 1), len(ESPERAS_BANCO_OCUPADO_SEGUNDOS)) - 1
    return ESPERAS_BANCO_OCUPADO_SEGUNDOS[indice]


def _aguardar_banco_ocupado(item: dict[str, Any], tentativa: int) -> None:
    """Espera com contagem visível; Ctrl+C continua sendo uma parada segura."""
    segundos = _segundos_banco_ocupado(tentativa)
    linha_id = int(item["linha_id"])
    print()
    print(
        f"BANCO OCUPADO (55P03). A linha {linha_id} continua pendente e intacta.",
        flush=True,
    )
    print(
        f"Tentativa automática {tentativa}: aguardando a outra operação terminar.",
        flush=True,
    )
    for restante in range(segundos, 0, -1):
        print(
            f"\rNova tentativa da mesma linha em {restante:02d}s. Ctrl+C para parar com segurança.",
            end="",
            flush=True,
        )
        time.sleep(1)
    print("\rTentando novamente a mesma linha agora.                              ", flush=True)


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
        mensagem = _mensagem_erro_http(detalhe)
        if _codigo_erro_http(detalhe) == "55P03":
            raise BancoOcupado(
                f"o banco está ocupado ao receber a linha {item['linha_id']} (HTTP {erro.code}): {detalhe}"
            ) from erro
        if erro.code == 400 and "linha concluída com resultado diferente" in mensagem:
            raise LinhaJaConcluidaNoBanco(
                f"a linha {item['linha_id']} já foi concluída no banco com outro resultado"
            ) from erro
        if erro.code == 400 and "lote ou linha não pertence à fila integral" in mensagem:
            raise LinhaForaFilaNoBanco(
                f"a linha {item['linha_id']} foi retirada da fila integral no banco"
            ) from erro
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


def _recibos_terminais(caminho: Path) -> dict[int, dict[str, Any]]:
    """Lê decisões duráveis: confirmação ou conflito já existente no banco."""
    terminais: dict[int, dict[str, Any]] = {}
    for recibo in ler_jsonl(caminho):
        conflito = recibo.get("confirmado") is False and recibo.get("ignorado_por_banco") is True
        if recibo.get("contrato") != CONTRATO_RECIBO or (recibo.get("confirmado") is not True and not conflito):
            raise FalhaOperacao(f"recibo inválido: {caminho.name}")
        try:
            linha_id = int(recibo["linha_id"])
        except (KeyError, TypeError, ValueError) as erro:
            raise FalhaOperacao(f"recibo sem linha válida: {caminho.name}") from erro
        anterior = terminais.get(linha_id)
        if anterior and anterior != recibo:
            raise FalhaOperacao(f"há dois recibos diferentes para a linha {linha_id}")
        terminais[linha_id] = recibo
    return terminais


def _recibos_confirmados(caminho: Path) -> dict[int, dict[str, Any]]:
    return {
        linha_id: recibo
        for linha_id, recibo in _recibos_terminais(caminho).items()
        if recibo.get("confirmado") is True
    }


def _assinatura_recibo(recibo: dict[str, Any]) -> str:
    """Compara decisão oficial sem confundir horas locais de cálculo."""
    return texto_json({
        "linha_id": int(recibo["linha_id"]),
        "confirmado": recibo.get("confirmado"),
        "ignorado_por_banco": recibo.get("ignorado_por_banco"),
        "enviado_em_utc": recibo.get("enviado_em_utc"),
        "build_otimizador_id": recibo.get("build_otimizador_id"),
        "resultado_fingerprint": recibo.get("resultado_fingerprint"),
        "motivo": recibo.get("motivo"),
    })


def _decisoes_globais(estrutura: dict[str, Path]) -> dict[int, dict[str, Any]]:
    """Reúne decisões de arquivos pendentes, enviados e arquivados.

    Assim uma cópia local repetida nunca gera uma segunda chamada ao banco,
    inclusive quando o banco já tinha uma versão diferente antes deste lote.
    """
    caminhos = sorted(estrutura["recibos"].glob("*.recibos.jsonl")) + sorted(
        estrutura["enviados"].glob("*.recibos.jsonl")
    ) + sorted(estrutura["arquivados"].glob("*.recibos.jsonl")) + sorted(
        estrutura["nao_enviados"].glob("*.recibos.jsonl")
    )
    decisoes: dict[int, dict[str, Any]] = {}
    for caminho in caminhos:
        for linha_id, recibo in _recibos_terminais(caminho).items():
            anterior = decisoes.get(linha_id)
            if anterior is not None and _assinatura_recibo(anterior) != _assinatura_recibo(recibo):
                raise FalhaOperacao(f"há duas decisões diferentes para a linha {linha_id}")
            decisoes[linha_id] = recibo
    return decisoes


def _recibo_repeticao_local(item: dict[str, Any], confirmado: dict[str, Any], origem: str) -> dict[str, Any]:
    """Fecha uma cópia idêntica sem reenviar a mesma linha ao banco."""
    return {
        "contrato": CONTRATO_RECIBO,
        "versao": VERSAO,
        "confirmado": True,
        "lote_id": confirmado.get("lote_id"),
        "linha_id": int(item["linha_id"]),
        "calculado_em_utc": item["calculado_em_utc"],
        "enviado_em_utc": confirmado["enviado_em_utc"],
        "build_otimizador_id": confirmado.get("build_otimizador_id"),
        "resultado_fingerprint": confirmado.get("resultado_fingerprint"),
        "idempotente": True,
        "repeticao_local_ignorada": True,
        "confirmacao_original": origem,
    }


def _decisao_repeticao_conflito(item: dict[str, Any], conflito: dict[str, Any], origem: str) -> dict[str, Any]:
    return {
        "contrato": CONTRATO_RECIBO,
        "versao": VERSAO,
        "confirmado": False,
        "ignorado_por_banco": True,
        "lote_id": conflito.get("lote_id"),
        "linha_id": int(item["linha_id"]),
        "calculado_em_utc": item["calculado_em_utc"],
        "decidido_em_utc": conflito.get("decidido_em_utc"),
        "motivo": conflito.get("motivo"),
        "repeticao_local_ignorada": True,
        "decisao_original": origem,
    }


def _decisao_conflito_banco(lote_id: str, item: dict[str, Any], erro: Exception, arquivo: Path) -> dict[str, Any]:
    return {
        "contrato": CONTRATO_RECIBO,
        "versao": VERSAO,
        "confirmado": False,
        "ignorado_por_banco": True,
        "lote_id": lote_id,
        "linha_id": int(item["linha_id"]),
        "calculado_em_utc": item["calculado_em_utc"],
        "decidido_em_utc": agora_utc(),
        "motivo": str(erro),
        "arquivo_origem": arquivo.name,
    }


def _decisao_fora_fila_ativa(lote_id: str, item: dict[str, Any], arquivo: Path) -> dict[str, Any]:
    """Preserva um cálculo de fotografia anterior sem oferecê-lo ao banco."""
    return {
        "contrato": CONTRATO_RECIBO,
        "versao": VERSAO,
        "confirmado": False,
        "ignorado_por_banco": True,
        "lote_id": lote_id,
        "linha_id": int(item["linha_id"]),
        "calculado_em_utc": item["calculado_em_utc"],
        "decidido_em_utc": agora_utc(),
        "motivo": "linha ausente da fotografia ativa renovada",
        "motivo_codigo": "linha_fora_da_fila_ativa",
        "arquivo_origem": arquivo.name,
    }


def _decisao_fora_fila_no_banco(
    lote_id: str,
    item: dict[str, Any],
    erro: Exception,
    arquivo: Path,
) -> dict[str, Any]:
    """Registra a recusa definitiva sem bloquear os resultados posteriores."""
    return {
        "contrato": CONTRATO_RECIBO,
        "versao": VERSAO,
        "confirmado": False,
        "ignorado_por_banco": True,
        "lote_id": lote_id,
        "linha_id": int(item["linha_id"]),
        "calculado_em_utc": item["calculado_em_utc"],
        "decidido_em_utc": agora_utc(),
        "motivo": str(erro),
        "motivo_codigo": "linha_retirada_da_fila_integral_no_banco",
        "arquivo_origem": arquivo.name,
    }


def _mover_envio_terminal(
    estrutura: dict[str, Path],
    arquivo: Path,
    recibo: Path,
    lote_id: str,
    total_confirmado: int,
    total_ignorado: int,
) -> None:
    # Um envelope pode misturar linhas ainda ativas com linhas retiradas após
    # a renovação. Se ao menos uma foi confirmada, o envelope continua entre
    # os finalizados normais para o processador não recalculá-la. Só um arquivo
    # inteiramente obsoleto vai para o arquivo de evidências não enviadas.
    destino_pasta = (
        estrutura["nao_enviados"]
        if total_confirmado == 0 and total_ignorado > 0
        else estrutura["enviados"]
    )
    destino = destino_pasta / arquivo.name
    destino_recibo = destino_pasta / (arquivo.stem + ".recibos.jsonl")
    if destino.exists() and destino != arquivo:
        raise FalhaOperacao(f"já existe um arquivo terminal com este nome: {arquivo.name}")
    os.replace(arquivo, destino)
    if recibo.is_file():
        os.replace(recibo, destino_recibo)
    gravar_json_atomico(destino_pasta / (arquivo.stem + ".resumo.json"), {
        "contrato": "otimizador_resumo_envio_local_json_v1",
        "lote_id": lote_id,
        "arquivo": arquivo.name,
        "total_confirmado": total_confirmado,
        "total_ignorado_por_banco": total_ignorado,
        "fechado_em_utc": agora_utc(),
    })


def _arquivos_da_formula_atual(arquivos: list[Path], pacote: Any) -> list[Path]:
    """Preserva fórmulas anteriores sem bloquear a remessa da fórmula atual.

    Não compara o agregado do lote: ele pode mudar com novas cartas sem mudar
    o contrato de uma linha. A identidade e os selos da linha continuam sendo
    conferidos pelo importador canônico. Não move arquivos usados pelo cálculo.
    """
    chaves = ("formula_fingerprint", "contrato_fingerprint", "motor_versao")
    esperado = tuple(str(pacote.manifesto.get(chave) or "") for chave in chaves)
    if not all(esperado):
        raise FalhaOperacao("pacote sem selos completos para conferir a fórmula do envio")
    atuais = []
    for arquivo in arquivos:
        envelope = _ler_envelope(arquivo)
        if str(envelope.get("lote_id")) != pacote.lote_id:
            raise FalhaOperacao(f"{arquivo.name} pertence a outro lote")
        compativeis = []
        for item in envelope["itens"]:
            recebido = tuple(str(item["resultado"].get(chave) or "") for chave in chaves)
            if not all(recebido):
                raise FalhaOperacao(f"{arquivo.name} contém resultado sem selos completos")
            compativeis.append(recebido == esperado)
        if all(compativeis):
            atuais.append(arquivo)
        elif any(compativeis):
            raise FalhaOperacao(f"{arquivo.name} mistura fórmulas atual e anterior; arquivo preservado")
        else:
            print(f"Lote {pacote.lote_id}, {arquivo.name}: {len(compativeis)} resultados de outra fórmula "
                  "preservados; não serão enviados nesta execução.", flush=True)
    return atuais


def enviar(raiz: Path, lote_id: str | None, limite: int | None,
           cards_alvo: list[str] | None = None,
           linhas_alvo: list[int] | None = None) -> int:
    operacao = pasta_operacao(raiz)
    if lote_id is None and (operacao / "FILA-ATIVA.json").is_file():
        selecao = ler_json(operacao / "FILA-ATIVA.json")
        ativos = selecao.get("lotes")
        if selecao.get("contrato") != "prioridade_orcamento_v1" or not isinstance(ativos, list) or not ativos:
            raise FalhaOperacao("fila ativa inválida para envio")
        if any(not isinstance(lote, str) or not lote for lote in ativos) or len(set(ativos)) != len(ativos):
            raise FalhaOperacao("fila ativa contém lote inválido ou repetido")
        encerrados = selecao.get("lotes_sem_pendentes", [])
        if (not isinstance(encerrados, list)
                or any(not isinstance(lote, str) for lote in encerrados)
                or len(set(encerrados)) != len(encerrados)
                or not set(encerrados).issubset(set(ativos))):
            raise FalhaOperacao("lotes sem pendentes inválidos para envio")
        if limite is not None:
            raise FalhaOperacao("para limitar um envio de teste, informe também --lote")
        for ativo in ativos:
            if ativo in encerrados:
                print(f"Lote {ativo} sem linhas elegíveis na fotografia atual; histórico local preservado.", flush=True)
                continue
            enviar(raiz, str(ativo), None, cards_alvo=cards_alvo, linhas_alvo=linhas_alvo)
        return 0
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
    enviados_nesta_execucao = 0
    with trava_exclusiva(estrutura["controle"] / "ENVIADOR.lock", "enviador"):
        arquivos = _arquivos_resultado(estrutura["pendentes"])
        if not arquivos:
            print("Não há JSON pronto aguardando envio.", flush=True)
            return 0
        pacote = _mortar_pacote(raiz, operacao, lote)
        pacote.validar_integridade()
        arquivos = _arquivos_da_formula_atual(arquivos, pacote)
        if not arquivos:
            print("Não há JSON da fórmula atual aguardando envio.", flush=True)
            return 0
        ids_fila_ativa = {int(linha["linha_id"]) for linha in pacote.iter_linhas()}
        url, chave, config = _ler_config(raiz, operacao)
        arquivos_enviados = _arquivos_da_formula_atual(_arquivos_resultado(estrutura["enviados"]), pacote)
        for arquivo in [*arquivos_enviados, *arquivos]:
            envelope = _ler_envelope(arquivo)
            if str(envelope.get("lote_id")) != lote:
                raise FalhaOperacao(f"{arquivo.name} pertence a outro lote")
        pendentes_unicos, _, repetidos_pendentes = _inventariar_resultados(arquivos)
        # Também confere o histórico já arquivado: duas versões diferentes da
        # mesma linha nunca são escolhidas por ordem de arquivo.
        _inventariar_resultados([*arquivos_enviados, *arquivos])
        decisoes_globais = _decisoes_globais(estrutura)
        ids_cards_alvo = None
        if cards_alvo:
            cards_alvo_set = set(cards_alvo)
            ids_cards_alvo = {
                int(item["linha_id"])
                for caminho in arquivos
                for item in _ler_envelope(caminho)["itens"]
                if str(item.get("card_id")) in cards_alvo_set
            }
        ids_linhas_alvo = set(linhas_alvo) if linhas_alvo else None
        candidatas = set(pendentes_unicos) & ids_fila_ativa
        if ids_cards_alvo is not None:
            candidatas &= ids_cards_alvo
        if ids_linhas_alvo is not None:
            candidatas &= ids_linhas_alvo
        total_prontas = len(candidatas - set(decisoes_globais))
        falhas_total = sum(
            1 for caminho in estrutura["falhas_envio"].glob("linha-*.json")
            if int(ler_json(caminho).get("linha_id") or 0) in ids_fila_ativa
        )
        ignoradas_nesta_execucao = 0
        fora_fila_nesta_execucao = 0
        for arquivo in arquivos:
            envelope = _ler_envelope(arquivo)
            recibo = estrutura["recibos"] / (arquivo.stem + ".recibos.jsonl")
            terminais = _recibos_terminais(recibo)
            ids = {int(item["linha_id"]) for item in envelope["itens"]}
            if not set(terminais).issubset(ids):
                raise FalhaOperacao(f"recibo contém linha fora do JSON: {arquivo.name}")
            for item in envelope["itens"]:
                linha_id = int(item["linha_id"])
                if cards_alvo and str(item.get("card_id")) not in set(cards_alvo):
                    continue
                if ids_linhas_alvo is not None and linha_id not in ids_linhas_alvo:
                    continue
                if linha_id in terminais:
                    continue
                decisao_anterior = decisoes_globais.get(linha_id)
                if decisao_anterior is not None:
                    if decisao_anterior.get("confirmado") is True:
                        decisao = _recibo_repeticao_local(item, decisao_anterior, "recibo local anterior")
                    else:
                        decisao = _decisao_repeticao_conflito(item, decisao_anterior, "decisão local anterior")
                    acrescentar_jsonl_duravel(recibo, decisao)
                    terminais[linha_id] = decisao
                    print(
                        f"Linha {linha_id} — {_carta_com_id(item)} não foi reenviada: decisão local já registrada.",
                        flush=True,
                    )
                    continue
                if linha_id not in ids_fila_ativa:
                    decisao = _decisao_fora_fila_ativa(lote, item, arquivo)
                    acrescentar_jsonl_duravel(recibo, decisao)
                    terminais[linha_id] = decisao
                    decisoes_globais[linha_id] = decisao
                    fora_fila_nesta_execucao += 1
                    print(
                        f"Linha {linha_id} — {_carta_com_id(item)} pertence a uma fotografia anterior; "
                        "o cálculo foi preservado e não foi enviado ao banco.",
                        flush=True,
                    )
                    continue
                inicio_envio = time.monotonic()
                _mostrar_envio(
                    lote,
                    total_prontas,
                    enviados_nesta_execucao,
                    falhas_total,
                    item,
                    inicio_envio,
                    repetidos_ignorados=repetidos_pendentes,
                )
                tentativas_banco_ocupado = 0
                try:
                    while True:
                        try:
                            resposta = chamar_importacao(url, chave, lote, item)
                            break
                        except BancoOcupado:
                            tentativas_banco_ocupado += 1
                            _aguardar_banco_ocupado(item, tentativas_banco_ocupado)
                except LinhaJaConcluidaNoBanco as erro:
                    decisao = _decisao_conflito_banco(lote, item, erro, arquivo)
                    gravar_json_atomico(estrutura["conflitos_banco"] / f"linha-{linha_id}.json", {
                        "contrato": "otimizador_conflito_resultado_local_json_v1",
                        "lote_id": lote,
                        "linha_id": linha_id,
                        "registrado_em_utc": agora_utc(),
                        "erro": str(erro),
                        "arquivo_origem": arquivo.name,
                    })
                    acrescentar_jsonl_duravel(recibo, decisao)
                    terminais[linha_id] = decisao
                    decisoes_globais[linha_id] = decisao
                    ignoradas_nesta_execucao += 1
                    total_prontas -= 1
                    print(
                        f"Linha {linha_id} — {_carta_com_id(item)} já tinha outro resultado no banco; "
                        "foi arquivada localmente e não será reenviada.",
                        flush=True,
                    )
                    continue
                except LinhaForaFilaNoBanco as erro:
                    decisao = _decisao_fora_fila_no_banco(lote, item, erro, arquivo)
                    acrescentar_jsonl_duravel(recibo, decisao)
                    terminais[linha_id] = decisao
                    decisoes_globais[linha_id] = decisao
                    fora_fila_nesta_execucao += 1
                    total_prontas -= 1
                    falha_anterior = estrutura["falhas_envio"] / f"linha-{linha_id}.json"
                    if falha_anterior.is_file() and falhas_total > 0:
                        falhas_total -= 1
                    print(
                        f"Linha {linha_id} — {_carta_com_id(item)} foi retirada da fila no banco; "
                        "o cálculo foi preservado e o envio continuará na próxima linha.",
                        flush=True,
                    )
                    continue
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
                terminais[linha_id] = recibo_item
                decisoes_globais[linha_id] = recibo_item
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
            if set(terminais) == ids:
                confirmadas_arquivo = sum(1 for decisao in terminais.values() if decisao.get("confirmado") is True)
                ignoradas_arquivo = len(ids) - confirmadas_arquivo
                _mover_envio_terminal(
                    estrutura,
                    arquivo,
                    recibo,
                    lote,
                    confirmadas_arquivo,
                    ignoradas_arquivo,
                )
                print(
                    f"Arquivo finalizado: {confirmadas_arquivo} confirmadas; "
                    f"{ignoradas_arquivo} preservadas sem novo envio.",
                    flush=True,
                )
        gravar_json_atomico(estrutura["controle"] / "ESTADO-ENVIO.json", {
            "contrato": "otimizador_estado_envio_local_json_v1",
            "lote_id": lote,
            "atualizado_em_utc": agora_utc(),
            "confirmadas_nesta_execucao": enviados_nesta_execucao,
            "ignoradas_por_resultado_ja_existente": ignoradas_nesta_execucao,
            "arquivadas_fora_da_fila_ativa": fora_fila_nesta_execucao,
            "jsons_ainda_pendentes": len(_arquivos_resultado(estrutura["pendentes"])),
        })
        _mostrar_envio(
            lote,
            total_prontas,
            enviados_nesta_execucao,
            falhas_total,
            repetidos_ignorados=repetidos_pendentes,
        )
        print(
            f"Envio terminou. Linhas confirmadas: {enviados_nesta_execucao}; "
            f"já concluídas no banco: {ignoradas_nesta_execucao}; "
            f"fora da fila ativa: {fora_fila_nesta_execucao}.",
            flush=True,
        )
    return 0


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Operação local JSON do Otimizador")
    sub = parser.add_subparsers(dest="comando", required=True)
    for nome in ("processar", "enviar"):
        comando = sub.add_parser(nome)
        comando.add_argument("--lote", help="UUID do lote local, se houver mais de um")
        if nome == 'processar':
            comando.add_argument('--processos', type=int, choices=range(1, 5), default=4,
                                 help='processos de cálculo simultâneos (padrão: 4)')
        comando.add_argument("--limite", type=int, help="somente para teste: máximo de linhas nesta execução")
        comando.add_argument(
            "--cards", nargs="+",
            help="processa ou envia somente estes IDs de carta, na ordem informada",
        )
        comando.add_argument(
            "--linhas", nargs="+", type=int,
            help="processa ou envia somente estes IDs exatos de linha, na ordem informada",
        )
    renovacao = sub.add_parser("renovar", help="renova somente fotografias de lotes pausados")
    renovacao.add_argument("--lotes", nargs="+", required=True, help="UUIDs dos lotes que compartilharão a fila")
    renovacao.add_argument("--preservar-ordem", action="store_true", help="mantem a lista e a prioridade da fila existente")
    return parser.parse_args()


def main() -> int:
    global PROCESSOS_CONFIGURADOS
    # Nomes reais podem ter caracteres fora de cp1252, inclusive quando o
    # console e redirecionado para log. Imprimir nao pode interromper o envio.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = argumentos()
    if args.comando == "renovar":
        raiz = raiz_otimizador()
        if str(raiz) not in sys.path:
            sys.path.insert(0, str(raiz))
        from renovar_pacotes_prioridade_v1 import renovar
        return renovar(raiz, args.lotes, sys.modules[__name__], preservar_ordem=args.preservar_ordem)
    if args.limite is not None and args.limite <= 0:
        raise FalhaOperacao("--limite deve ser maior que zero")
    if args.cards:
        args.cards = [str(card_id).strip() for card_id in args.cards]
        if any(not card_id.isdigit() for card_id in args.cards):
            raise FalhaOperacao("--cards aceita somente IDs numéricos de carta")
        if len(set(args.cards)) != len(args.cards):
            raise FalhaOperacao("--cards não aceita ID de carta repetido")
    if args.linhas:
        if any(linha_id <= 0 for linha_id in args.linhas):
            raise FalhaOperacao("--linhas aceita somente IDs positivos")
        if len(set(args.linhas)) != len(args.linhas):
            raise FalhaOperacao("--linhas não aceita ID repetido")
    if args.cards and args.linhas:
        raise FalhaOperacao("use somente um filtro: --cards ou --linhas")
    raiz = raiz_otimizador()
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    if args.comando == "processar":
        PROCESSOS_CONFIGURADOS = args.processos
        if args.lote:
            if args.cards or args.linhas:
                raise FalhaOperacao("use --cards/--linhas sem --lote para localizar na fila ativa")
            with trava_exclusiva(pasta_operacao(raiz) / "PROCESSADOR-GLOBAL.lock", "processador global"):
                return processar(raiz, args.lote, args.limite, processos=args.processos)
        return processar_global(raiz, args.limite, args.cards, args.linhas, processos=args.processos)
    return enviar(raiz, args.lote, args.limite,
                  cards_alvo=args.cards, linhas_alvo=args.linhas)


if __name__ == "__main__":
    multiprocessing.freeze_support()
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
