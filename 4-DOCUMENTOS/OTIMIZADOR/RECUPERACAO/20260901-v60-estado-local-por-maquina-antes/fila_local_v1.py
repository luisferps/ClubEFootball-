# -*- coding: utf-8 -*-
"""Fila produtiva local V1 do Otimizador.

Este módulo separa transporte de cálculo sem trocar uma única regra do motor:

* a fotografia selada é empacotada uma vez na máquina de origem e acompanha a
  pasta do Otimizador, em blocos de mil linhas;
* o cálculo continua usando literalmente ``roda_lote_v6.trabalha``;
* cada resultado é gravado primeiro no disco local e só então enviado;
* o enviador confirma até 100 resultados por RPC, com repetição idempotente.

O diretório do pacote não contém ``config.txt`` nem qualquer credencial. Ele
pode ser levado a outro Windows junto do aplicativo; a conexão daquele Windows
continua sendo configurada localmente pelo serviço de loopback.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import platform
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable

from fila_producao_v3 import FORMULA_APROVADA, MOTOR_VERSAO, FalhaFilaProducao, formula_fingerprint


# V1 permanece somente para reserva/conclusão em lote, que já são contratos
# atômicos e idempotentes. A fotografia de entrada usa V2 para não repetir
# contagens nem OFFSETs longos ao baixar 184 mil linhas.
CONTRATO_PACOTE_LOCAL_V1 = "otimizador_pacote_local_v1"
CONTRATO_PACOTE_LOCAL_V2 = "otimizador_pacote_local_v2"
VERSAO_PACOTE_LOCAL_V2 = 2
VERSAO_PACOTE_LOCAL_V3 = 3
TAMANHO_PAGINA_PACOTE = 1000
TAMANHO_LOTE_ENVIO = 100
TAMANHO_BLOCO_PORTATIL = 1000
PASTA_PACOTE_PORTATIL = "PACOTE-FILA-INTEGRAL"
AMBIENTE_PACOTE_LOCAL_OBRIGATORIO = "CLUBEF_OTIMIZADOR_PACOTE_LOCAL_OBRIGATORIO"


class FalhaPacoteLocal(FalhaFilaProducao):
    """O pacote local não é suficiente para calcular uma linha com segurança."""


def _json_canonico(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_bytes(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _gravar_json_atomico(caminho: Path, valor: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp-" + uuid.uuid4().hex)
    try:
        temporario.write_text(_json_canonico(valor) + "\n", encoding="utf-8")
        os.replace(temporario, caminho)
    finally:
        if temporario.exists():
            temporario.unlink(missing_ok=True)


def _gravar_jsonl_atomico(caminho: Path, itens: Iterable[dict]) -> tuple[int, str]:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp-" + uuid.uuid4().hex)
    digest = hashlib.sha256()
    total = 0
    try:
        with temporario.open("w", encoding="utf-8", newline="\n") as arquivo:
            for item in itens:
                linha = _json_canonico(item) + "\n"
                arquivo.write(linha)
                digest.update(linha.encode("utf-8"))
                total += 1
        os.replace(temporario, caminho)
        return total, digest.hexdigest()
    finally:
        if temporario.exists():
            temporario.unlink(missing_ok=True)


def _ler_json(caminho: Path) -> dict:
    try:
        valor = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        raise FalhaPacoteLocal(f"arquivo local inválido: {caminho.name}") from erro
    if not isinstance(valor, dict):
        raise FalhaPacoteLocal(f"arquivo local não contém objeto: {caminho.name}")
    return valor


class PacoteLocalV1:
    """Leitor/verificador do pacote portátil e selado de um lote integral."""

    def __init__(self, pasta: Path):
        self.pasta = Path(pasta).resolve()
        self.manifesto = _ler_json(self.pasta / "manifesto.json")
        self._pasta_estado = self._resolver_pasta_estado()
        self._cartas: dict[str, dict] | None = None
        self._validar_manifesto()

    @property
    def lote_id(self) -> str:
        return str(self.manifesto["lote_id"])

    @property
    def estado_path(self) -> Path:
        return self._pasta_estado / "estado-local.json"

    @property
    def pendentes_path(self) -> Path:
        return self._pasta_estado / "spool" / "pendentes"

    @property
    def enviando_path(self) -> Path:
        return self._pasta_estado / "spool" / "enviando"

    @property
    def reservas_path(self) -> Path:
        return self._pasta_estado / "spool" / "reservas"

    @property
    def pasta_estado(self) -> Path:
        """Diretório mutável, separado da fotografia que viaja entre PCs."""
        return self._pasta_estado

    def _resolver_pasta_estado(self) -> Path:
        # O pacote que acompanha o aplicativo é deliberadamente somente-leitura:
        # entradas e selos podem ir para outro computador sem levar resultados,
        # reservas ou qualquer credencial. Todo estado de execução fica em
        # ``runtime``, que pode ser apagado/recriado sem tocar na fotografia.
        if self.pasta.parent.name == PASTA_PACOTE_PORTATIL:
            return self.pasta.parent.parent / "runtime" / "fila-local" / self.lote_id
        return self.pasta

    @classmethod
    def pasta_do_lote(cls, raiz_operacional: Path, lote_id: str) -> Path:
        raiz = Path(raiz_operacional)
        portatil = raiz / PASTA_PACOTE_PORTATIL / str(lote_id)
        # A cópia pronta sempre vence: ela já contém toda a fila e não pode
        # disparar novo download em outra máquina.
        if portatil.is_dir():
            return portatil
        return raiz / "runtime" / "fila-local" / str(lote_id)

    @classmethod
    def existe_pronto(cls, raiz_operacional: Path, lote_id: str) -> bool:
        try:
            pacote = cls(cls.pasta_do_lote(raiz_operacional, lote_id))
            pacote.validar_integridade()
            return True
        except (OSError, FalhaPacoteLocal):
            return False

    @classmethod
    def criar_do_contrato(
        cls,
        gateway,
        lote_id: str,
        raiz_operacional: Path,
        ao_progresso: Callable[[str, int, int], None] | None = None,
        tamanho_pagina: int = TAMANHO_PAGINA_PACOTE,
        cancelar: Callable[[], bool] | None = None,
    ) -> "PacoteLocalV1":
        """Baixa o pacote completo em páginas, sem iniciar uma linha.

        O banco só libera este contrato para lote integral pausado, sem reserva.
        Portanto a fotografia não pode mudar no meio da exportação.
        """
        # O aplicativo entregue para operação diária não pode disparar uma
        # exportação oculta no computador de destino. Ele vem com a fotografia
        # em PACOTE-FILA-INTEGRAL; se ela foi esquecida na cópia, falha com
        # instrução clara em vez de sobrecarregar o banco ou parecer travado.
        if os.environ.get(AMBIENTE_PACOTE_LOCAL_OBRIGATORIO) == "1":
            raise FalhaPacoteLocal(
                "pacote local obrigatório não encontrado; copie a pasta OTIMIZADOR inteira, "
                "incluindo PACOTE-FILA-INTEGRAL"
            )
        tamanho_pagina = int(tamanho_pagina)
        if not 1 <= tamanho_pagina <= TAMANHO_PAGINA_PACOTE:
            raise FalhaPacoteLocal("tamanho de página local inválido")
        resposta = gateway.rpc("otimizador_producao_pacote_local_manifesto_v2", {
            "p_lote_id": str(lote_id),
        }) or {}
        if resposta.get("contrato") != CONTRATO_PACOTE_LOCAL_V2:
            raise FalhaPacoteLocal("o banco não confirmou o manifesto do pacote local")
        if str(resposta.get("lote_id")) != str(lote_id):
            raise FalhaPacoteLocal("manifesto recebido pertence a outro lote")
        if resposta.get("pode_publicar") is not False:
            raise FalhaPacoteLocal("manifesto tentou habilitar publicação")
        if resposta.get("impetos_condicionais") != "desligados":
            raise FalhaPacoteLocal("manifesto tentou habilitar Ímpetos condicionais")
        if resposta.get("formula_fingerprint") != FORMULA_APROVADA:
            raise FalhaPacoteLocal("manifesto não usa a fórmula aprovada")
        if resposta.get("motor_versao") != MOTOR_VERSAO:
            raise FalhaPacoteLocal("manifesto exige outra versão do motor")
        if formula_fingerprint() != FORMULA_APROVADA:
            raise FalhaPacoteLocal("a fórmula local não confere com o selo aprovado")
        regua = resposta.get("regua")
        if not isinstance(regua, dict) or (regua.get("gate") or {}).get("pode_rodar") is not True:
            raise FalhaPacoteLocal("a régua selada do pacote não está apta")

        destino = cls.pasta_do_lote(raiz_operacional, str(lote_id))
        if destino.exists():
            pacote_existente = cls(destino)
            pacote_existente.validar_integridade()
            if pacote_existente.manifesto.get("lote_fingerprint") != resposta.get("lote_fingerprint"):
                raise FalhaPacoteLocal("já existe pacote local de outro selo para este lote")
            return pacote_existente

        temporaria = destino.with_name(destino.name + ".preparando-" + uuid.uuid4().hex)
        temporaria.mkdir(parents=True, exist_ok=False)
        try:
            cartas_path = temporaria / "cartas.jsonl"
            linhas_path = temporaria / "linhas.jsonl"
            cartas_total, cartas_hash = cls._baixar_paginas_por_cursor(
                gateway, "otimizador_producao_pacote_local_cartas_v2", lote_id,
                resposta.get("cartas_total"), cartas_path, tamanho_pagina, ao_progresso, "cartas",
                "p_depois_de_card_id", "proximo_card_id", "card_id", cancelar,
            )
            linhas_total, linhas_hash = cls._baixar_paginas_por_cursor(
                gateway, "otimizador_producao_pacote_local_linhas_v2", lote_id,
                resposta.get("linhas_total"), linhas_path, tamanho_pagina, ao_progresso, "linhas",
                "p_depois_de_ordem", "proxima_ordem_fila", "ordem_fila", cancelar,
            )
            if cartas_total != int(resposta.get("cartas_total") or -1):
                raise FalhaPacoteLocal("contagem de cartas divergiu do manifesto")
            if linhas_total != int(resposta.get("linhas_total") or -1):
                raise FalhaPacoteLocal("contagem de linhas divergiu do manifesto")
            manifesto = dict(resposta)
            manifesto.update({
                "versao_pacote": VERSAO_PACOTE_LOCAL_V2,
                "criado_em_epoch": time.time(),
                "arquivos": {
                    "cartas": {"nome": "cartas.jsonl", "total": cartas_total, "sha256": cartas_hash},
                    "linhas": {"nome": "linhas.jsonl", "total": linhas_total, "sha256": linhas_hash},
                },
            })
            _gravar_json_atomico(temporaria / "manifesto.json", manifesto)
            _gravar_json_atomico(temporaria / "estado-local.json", {
                "contrato": CONTRATO_PACOTE_LOCAL_V2,
                "lote_id": str(lote_id),
                "estado": "pronto",
                "calculadas_local": 0,
                "enviadas": 0,
                "bloqueadas": 0,
                "nao_disponiveis": 0,
                "pendentes_envio": 0,
                "atualizado_em_epoch": time.time(),
            })
            for pasta in ("spool/pendentes", "spool/enviando", "spool/reservas"):
                (temporaria / pasta).mkdir(parents=True, exist_ok=True)
            PacoteLocalV1(temporaria).validar_integridade()
            destino.parent.mkdir(parents=True, exist_ok=True)
            # Não substitui pacote existente: uma troca de selo exige decisão
            # explícita, nunca um overwrite silencioso.
            temporaria.rename(destino)
            return cls(destino)
        except Exception:
            shutil.rmtree(temporaria, ignore_errors=True)
            raise

    @staticmethod
    def _baixar_paginas_por_cursor(
        gateway,
        rpc: str,
        lote_id: str,
        total_esperado: Any,
        destino: Path,
        tamanho_pagina: int,
        ao_progresso: Callable[[str, int, int], None] | None,
        etapa: str,
        campo_cursor_entrada: str,
        campo_cursor_saida: str,
        campo_cursor_item: str,
        cancelar: Callable[[], bool] | None,
    ) -> tuple[int, str]:
        total_esperado = int(total_esperado or 0)
        total_recebido = 0
        cursor: Any = None
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_name(destino.name + ".tmp-" + uuid.uuid4().hex)
        digest = hashlib.sha256()
        try:
            # A fotografia pode ter centenas de milhares de linhas. Escrever
            # cada página diretamente evita que o outro computador precise
            # manter todo o pacote na memória antes de poder usá-lo.
            with temporario.open("w", encoding="utf-8", newline="\n") as arquivo:
                while True:
                    if cancelar and cancelar():
                        raise FalhaPacoteLocal("download do pacote local cancelado antes de iniciar uma linha")
                    corpo = {"p_lote_id": str(lote_id), "p_limite": tamanho_pagina}
                    if cursor is not None:
                        corpo[campo_cursor_entrada] = cursor
                    pagina = gateway.rpc(rpc, corpo) or {}
                    if pagina.get("contrato") != CONTRATO_PACOTE_LOCAL_V2:
                        raise FalhaPacoteLocal(f"contrato inesperado ao baixar {etapa}")
                    if str(pagina.get("lote_id")) != str(lote_id):
                        raise FalhaPacoteLocal(f"página de {etapa} pertence a outro lote")
                    if pagina.get("contagem_no_manifesto") is not True:
                        raise FalhaPacoteLocal(f"página de {etapa} não confirmou a contagem selada")
                    parte = pagina.get("itens")
                    if not isinstance(parte, list):
                        raise FalhaPacoteLocal(f"página de {etapa} não trouxe itens")
                    for item in parte:
                        if not isinstance(item, dict):
                            raise FalhaPacoteLocal(f"página de {etapa} trouxe item inválido")
                        linha = _json_canonico(item) + "\n"
                        arquivo.write(linha)
                        digest.update(linha.encode("utf-8"))
                    total_recebido += len(parte)
                    if ao_progresso:
                        ao_progresso(etapa, total_recebido, total_esperado)
                    if not parte:
                        break
                    proximo = pagina.get(campo_cursor_saida)
                    ultimo = parte[-1].get(campo_cursor_item)
                    if proximo is None or str(proximo) != str(ultimo):
                        raise FalhaPacoteLocal(f"cursor de {etapa} divergiu da última linha recebida")
                    if cursor is not None and str(proximo) == str(cursor):
                        raise FalhaPacoteLocal(f"cursor de {etapa} não avançou")
                    cursor = proximo
                    if total_recebido > total_esperado or len(parte) < tamanho_pagina:
                        break
            if total_recebido != total_esperado:
                raise FalhaPacoteLocal(f"download de {etapa} terminou com contagem incompleta")
            os.replace(temporario, destino)
            return total_recebido, digest.hexdigest()
        finally:
            if temporario.exists():
                temporario.unlink(missing_ok=True)

    def _validar_manifesto(self) -> None:
        m = self.manifesto
        if m.get("contrato") != CONTRATO_PACOTE_LOCAL_V2:
            raise FalhaPacoteLocal("manifesto local usa outro contrato")
        if int(m.get("versao_pacote") or 0) not in {VERSAO_PACOTE_LOCAL_V2, VERSAO_PACOTE_LOCAL_V3}:
            raise FalhaPacoteLocal("versão do pacote local não suportada")
        if not m.get("lote_id") or m.get("formula_fingerprint") != FORMULA_APROVADA:
            raise FalhaPacoteLocal("selo de lote/fórmula inválido no pacote local")
        if m.get("motor_versao") != MOTOR_VERSAO:
            raise FalhaPacoteLocal("pacote local exige outra versão do motor")
        if m.get("pode_publicar") is not False or m.get("impetos_condicionais") != "desligados":
            raise FalhaPacoteLocal("pacote local não preserva os gates obrigatórios")
        regua = m.get("regua")
        if not isinstance(regua, dict) or (regua.get("gate") or {}).get("pode_rodar") is not True:
            raise FalhaPacoteLocal("régua ausente ou recusada no pacote local")

        if int(m.get("versao_pacote") or 0) == VERSAO_PACOTE_LOCAL_V3:
            for chave in ("cartas", "linhas"):
                meta = (m.get("arquivos") or {}).get(chave)
                if not isinstance(meta, dict) or not isinstance(meta.get("fatias"), list):
                    raise FalhaPacoteLocal(f"pacote portátil sem fatias de {chave}")
                if not meta.get("diretorio"):
                    raise FalhaPacoteLocal(f"pacote portátil sem diretório de {chave}")

    def _fatias_do_arquivo(self, chave: str) -> list[tuple[Path, dict]]:
        """Lista os arquivos físicos do contrato, em ordem canônica."""
        meta = (self.manifesto.get("arquivos") or {}).get(chave)
        if not isinstance(meta, dict):
            raise FalhaPacoteLocal(f"manifesto sem metadado de {chave}")
        if int(self.manifesto.get("versao_pacote") or 0) == VERSAO_PACOTE_LOCAL_V3:
            diretorio = meta.get("diretorio")
            fatias = meta.get("fatias")
            if not isinstance(diretorio, str) or not isinstance(fatias, list):
                raise FalhaPacoteLocal(f"fatias inválidas de {chave}")
            resultado = []
            for fatia in fatias:
                if not isinstance(fatia, dict) or not isinstance(fatia.get("nome"), str):
                    raise FalhaPacoteLocal(f"fatia inválida de {chave}")
                resultado.append((self.pasta / diretorio / fatia["nome"], fatia))
            return resultado
        nome = meta.get("nome")
        if not isinstance(nome, str):
            raise FalhaPacoteLocal(f"manifesto sem arquivo de {chave}")
        return [(self.pasta / nome, meta)]

    def validar_integridade(self) -> None:
        arquivos = self.manifesto.get("arquivos")
        if not isinstance(arquivos, dict):
            raise FalhaPacoteLocal("manifesto local não enumera seus arquivos")
        for chave in ("cartas", "linhas"):
            meta = arquivos.get(chave)
            if not isinstance(meta, dict):
                raise FalhaPacoteLocal(f"manifesto sem metadado de {chave}")
            digest = hashlib.sha256()
            total = 0
            for caminho, fatia in self._fatias_do_arquivo(chave):
                if not caminho.is_file() or _hash_bytes(caminho) != fatia.get("sha256"):
                    raise FalhaPacoteLocal(f"integridade inválida em {caminho.name}")
                with caminho.open("rb") as arquivo:
                    for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
                        digest.update(bloco)
                with caminho.open("r", encoding="utf-8") as arquivo:
                    total_fatia = sum(1 for _ in arquivo)
                if total_fatia != int(fatia.get("total") or -1):
                    raise FalhaPacoteLocal(f"contagem inválida em {caminho.name}")
                total += total_fatia
            if total != int(meta.get("total") or -1):
                raise FalhaPacoteLocal(f"contagem inválida em {chave}")
            if digest.hexdigest() != meta.get("sha256"):
                raise FalhaPacoteLocal(f"hash agregado inválido em {chave}")

    def estado(self) -> dict:
        if not self.estado_path.is_file():
            return {"contrato": CONTRATO_PACOTE_LOCAL_V2, "lote_id": self.lote_id}
        estado = _ler_json(self.estado_path)
        if estado.get("contrato") != CONTRATO_PACOTE_LOCAL_V2 or str(estado.get("lote_id")) != self.lote_id:
            raise FalhaPacoteLocal("estado local pertence a outro pacote")
        return estado

    def atualizar_estado(self, **mudancas: Any) -> dict:
        estado = self.estado()
        estado.update(mudancas)
        estado["atualizado_em_epoch"] = time.time()
        _gravar_json_atomico(self.estado_path, estado)
        return estado

    def cartas(self) -> dict[str, dict]:
        if self._cartas is not None:
            return self._cartas
        cartas: dict[str, dict] = {}
        numero = 0
        for caminho, _ in self._fatias_do_arquivo("cartas"):
            with caminho.open("r", encoding="utf-8") as arquivo:
                for texto in arquivo:
                    numero += 1
                    try:
                        item = json.loads(texto)
                    except json.JSONDecodeError as erro:
                        raise FalhaPacoteLocal(f"carta inválida na linha {numero}") from erro
                    card_id = str(item.get("card_id") or "")
                    if not card_id or not isinstance(item.get("carta"), dict):
                        raise FalhaPacoteLocal(f"carta incompleta na linha {numero}")
                    if card_id in cartas:
                        raise FalhaPacoteLocal(f"carta repetida no pacote: {card_id}")
                    cartas[card_id] = item
        self._cartas = cartas
        return cartas

    def iter_linhas(self) -> Iterable[dict]:
        numero = 0
        for caminho, _ in self._fatias_do_arquivo("linhas"):
            with caminho.open("r", encoding="utf-8") as arquivo:
                for texto in arquivo:
                    numero += 1
                    try:
                        item = json.loads(texto)
                    except json.JSONDecodeError as erro:
                        raise FalhaPacoteLocal(f"linha inválida no pacote: {numero}") from erro
                    obrigatorios = ("linha_id", "ordem_fila", "card_id", "funcao_id", "posicao_id", "carta_entrada_fingerprint")
                    if any(item.get(chave) is None for chave in obrigatorios):
                        raise FalhaPacoteLocal(f"linha incompleta no pacote: {numero}")
                    yield item

    def iter_blocos_linhas(self) -> Iterable[tuple[str, list[dict]]]:
        """Entrega no máximo mil linhas por vez ao motor local.

        V3 já é fisicamente fatiado. O caminho V2 continua só para fotografias
        antigas, agrupando sem carregá-las por inteiro na memória.
        """
        if int(self.manifesto.get("versao_pacote") or 0) == VERSAO_PACOTE_LOCAL_V3:
            for indice, (caminho, _) in enumerate(self._fatias_do_arquivo("linhas"), 1):
                linhas = []
                with caminho.open("r", encoding="utf-8") as arquivo:
                    for numero, texto in enumerate(arquivo, 1):
                        try:
                            item = json.loads(texto)
                        except json.JSONDecodeError as erro:
                            raise FalhaPacoteLocal(f"linha inválida em {caminho.name}:{numero}") from erro
                        obrigatorios = ("linha_id", "ordem_fila", "card_id", "funcao_id", "posicao_id", "carta_entrada_fingerprint")
                        if any(item.get(chave) is None for chave in obrigatorios):
                            raise FalhaPacoteLocal(f"linha incompleta em {caminho.name}:{numero}")
                        linhas.append(item)
                if len(linhas) > TAMANHO_BLOCO_PORTATIL:
                    raise FalhaPacoteLocal(f"bloco portátil excede {TAMANHO_BLOCO_PORTATIL} linhas")
                yield f"{indice:06d}", linhas
            return
        iterator = iter(self.iter_linhas())
        indice = 0
        while True:
            linhas = list(itertools.islice(iterator, TAMANHO_BLOCO_PORTATIL))
            if not linhas:
                return
            indice += 1
            yield f"{indice:06d}", linhas

    def carta_da_linha(self, linha: dict) -> dict:
        carta = self.cartas().get(str(linha["card_id"]))
        if carta is None:
            raise FalhaPacoteLocal("linha local aponta para carta inexistente no pacote")
        if carta.get("carta_entrada_fingerprint") != linha.get("carta_entrada_fingerprint"):
            raise FalhaPacoteLocal("selo de carta da linha diverge da fotografia local")
        return carta

    def arquivos_pendentes(self, somente_blocos_prontos: bool = False) -> list[Path]:
        self.pendentes_path.mkdir(parents=True, exist_ok=True)
        self.enviando_path.mkdir(parents=True, exist_ok=True)
        # Uma queda durante o envio deixa arquivos em ``enviando``. Eles não
        # são descartados: a confirmação em lote é idempotente, então voltam a
        # ``pendentes`` para readback seguro.
        for arquivo in sorted(self.enviando_path.rglob("*.json")):
            relativo = arquivo.relative_to(self.enviando_path)
            destino = self.pendentes_path / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.exists():
                raise FalhaPacoteLocal("duas cópias locais do mesmo resultado aguardam envio")
            os.replace(arquivo, destino)
        resultado = []
        for arquivo in sorted(self.pendentes_path.rglob("*.json")):
            if arquivo.name == "BLOCO-PRONTO.json":
                continue
            if somente_blocos_prontos and arquivo.parent != self.pendentes_path:
                if not (arquivo.parent / "BLOCO-PRONTO.json").is_file():
                    continue
            resultado.append(arquivo)
        return resultado

    def marcar_bloco_pronto(self, bloco_id: str, total: int) -> None:
        if not bloco_id or "/" in bloco_id or "\\" in bloco_id:
            raise FalhaPacoteLocal("identificador de bloco local inválido")
        _gravar_json_atomico(self.pendentes_path / bloco_id / "BLOCO-PRONTO.json", {
            "contrato": CONTRATO_PACOTE_LOCAL_V2,
            "lote_id": self.lote_id,
            "bloco_id": bloco_id,
            "total": int(total),
            "pronto_em_epoch": time.time(),
        })

    def gravar_reserva(self, reserva: dict) -> Path:
        linha_id = int(reserva["linha_id"])
        destino = self.reservas_path / f"{linha_id}.json"
        _gravar_json_atomico(destino, reserva)
        return destino

    def apagar_reserva(self, linha_id: int) -> None:
        (self.reservas_path / f"{int(linha_id)}.json").unlink(missing_ok=True)

    def gravar_resultado(self, reserva: dict, resultado: dict, bloco_id: str | None = None) -> Path:
        linha_id = int(reserva["linha_id"])
        conteudo = {"contrato": CONTRATO_PACOTE_LOCAL_V1, "reserva": reserva, "resultado": resultado}
        pasta = self.pendentes_path
        if bloco_id is not None:
            if not bloco_id or "/" in bloco_id or "\\" in bloco_id:
                raise FalhaPacoteLocal("identificador de bloco local inválido")
            pasta = pasta / bloco_id
        destino = pasta / f"{int(reserva['ordem_fila']):09d}-{linha_id}.json"
        _gravar_json_atomico(destino, conteudo)
        self.apagar_reserva(linha_id)
        return destino


class EnviadorLotesLocalV1:
    """Envia resultados já calculados sem bloquear o próximo cálculo local."""

    def __init__(self, gateway, pacote: PacoteLocalV1, ao_progresso=None):
        self.gateway = gateway
        self.pacote = pacote
        self.ao_progresso = ao_progresso
        self._sinal = threading.Event()
        self._parar = threading.Event()
        self._trava = threading.RLock()
        self._erro: Exception | None = None
        self._thread: threading.Thread | None = None

    def iniciar(self) -> None:
        with self._trava:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._executar, name="otimizador-enviador-local-v1", daemon=True)
            self._thread.start()

    def sinalizar(self) -> None:
        self._sinal.set()

    def _emitir(self, etapa: str, detalhe: str | None = None) -> None:
        if self.ao_progresso:
            self.ao_progresso(etapa, detalhe)

    def _executar(self) -> None:
        espera = 1.0
        while not self._parar.is_set():
            self._sinal.wait(timeout=1.0)
            self._sinal.clear()
            try:
                self.enviar_disponiveis(forcar=False)
                self._erro = None
                espera = 1.0
            except Exception as erro:
                self._erro = erro
                self._emitir("envio_aguardando_rede", str(erro))
                self._parar.wait(espera)
                espera = min(30.0, espera * 2)
                self._sinal.set()

    def _mover_para_envio(self, arquivos: list[Path]) -> list[Path]:
        selecionados: list[Path] = []
        for arquivo in arquivos:
            relativo = arquivo.relative_to(self.pacote.pendentes_path)
            destino = self.pacote.enviando_path / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            os.replace(arquivo, destino)
            selecionados.append(destino)
        return selecionados

    def _ler_lote(self, arquivos: list[Path]) -> list[dict]:
        itens: list[dict] = []
        vistos: set[int] = set()
        for arquivo in arquivos:
            item = _ler_json(arquivo)
            reserva = item.get("reserva")
            resultado = item.get("resultado")
            if item.get("contrato") != CONTRATO_PACOTE_LOCAL_V1 or not isinstance(reserva, dict) or not isinstance(resultado, dict):
                raise FalhaPacoteLocal("resultado local pendente está inválido")
            linha_id = int(reserva.get("linha_id"))
            if linha_id in vistos or not reserva.get("reserva_token"):
                raise FalhaPacoteLocal("lote local contém reserva repetida ou sem token")
            vistos.add(linha_id)
            itens.append({
                "linha_id": linha_id,
                "reserva_token": str(reserva["reserva_token"]),
                "resultado": resultado,
            })
        return itens

    def enviar_disponiveis(self, forcar: bool) -> int:
        enviados = 0
        with self._trava:
            while True:
                # O processo de cálculo entrega um bloco físico de até 1.000
                # linhas na pasta. O enviador é outro processo/thread e só
                # começa um bloco concluído; na pausa, ``forcar`` descarrega
                # com segurança o trecho já calculado para não perder trabalho.
                arquivos = self.pacote.arquivos_pendentes(somente_blocos_prontos=not forcar)
                if not arquivos or (not forcar and len(arquivos) < TAMANHO_LOTE_ENVIO):
                    pendentes_totais = len(self.pacote.arquivos_pendentes())
                    self.pacote.atualizar_estado(pendentes_envio=pendentes_totais)
                    return enviados
                origem = arquivos[:TAMANHO_LOTE_ENVIO]
                selecionados = self._mover_para_envio(origem)
                try:
                    itens = self._ler_lote(selecionados)
                    self._emitir("enviando_lote", f"{len(itens)} resultados")
                    resposta = self.gateway.rpc("otimizador_producao_concluir_lote_local_v1", {
                        "p_lote_id": self.pacote.lote_id,
                        "p_resultados": itens,
                    }) or {}
                    if resposta.get("contrato") != CONTRATO_PACOTE_LOCAL_V1:
                        raise FalhaPacoteLocal("contrato não confirmou o lote de resultados local")
                    confirmados = resposta.get("itens")
                    if not isinstance(confirmados, list) or len(confirmados) != len(itens):
                        raise FalhaPacoteLocal("confirmação do lote local está incompleta")
                    for arquivo in selecionados:
                        arquivo.unlink(missing_ok=True)
                    enviados += len(itens)
                    estado = self.pacote.estado()
                    self.pacote.atualizar_estado(
                        enviadas=int(estado.get("enviadas") or 0) + len(itens),
                        pendentes_envio=len(self.pacote.arquivos_pendentes()),
                        estado="calculando",
                    )
                    self._emitir("lote_enviado", f"{len(itens)} resultados confirmados")
                except Exception:
                    for arquivo in selecionados:
                        relativo = arquivo.relative_to(self.pacote.enviando_path)
                        destino = self.pacote.pendentes_path / relativo
                        destino.parent.mkdir(parents=True, exist_ok=True)
                        if arquivo.exists() and not destino.exists():
                            os.replace(arquivo, destino)
                    raise

    def esvaziar(self) -> None:
        # Não marca a pausa como concluída enquanto um resultado calculado não
        # tiver confirmação durável no banco. Em falha de rede, os arquivos
        # permanecem no pacote e a próxima abertura retoma o mesmo envio.
        while True:
            self.enviar_disponiveis(forcar=True)
            if not self.pacote.arquivos_pendentes():
                return
            if self._erro:
                raise self._erro

    def encerrar(self, esvaziar: bool) -> None:
        if esvaziar:
            self.esvaziar()
        self._parar.set()
        self._sinal.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=3.0)


class WorkerFilaLocalV1:
    """Consumidor de pacote local; fórmula e resultado permanecem V6."""

    def __init__(
        self,
        gateway,
        pacote: PacoteLocalV1,
        ao_encerrar=None,
        ao_progresso=None,
        esperar: float = 0.05,
        limite_linhas: int | None = None,
    ):
        self.gateway = gateway
        self.pacote = pacote
        self.lote_id = pacote.lote_id
        self.ao_encerrar = ao_encerrar
        self.ao_progresso = ao_progresso
        self.esperar = max(0.01, float(esperar))
        if limite_linhas is not None and int(limite_linhas) < 1:
            raise FalhaPacoteLocal("o limite controlado deve conter ao menos uma linha")
        # Só o piloto controlado informa um limite. A execução normal deixa
        # este valor em None e preserva exatamente a mesma sequência de cálculo
        # e de resultados do motor V6.
        self.limite_linhas = None if limite_linhas is None else int(limite_linhas)
        self._linhas_calculadas_nesta_execucao = 0
        # O limite do piloto é de tentativas com reserva, não somente de
        # resultados bem-sucedidos. Assim uma linha bloqueada no piloto não
        # faz o worker seguir para uma segunda linha sem autorização.
        self._linhas_tentadas_nesta_execucao = 0
        self.worker_id = self._identidade_da_maquina()
        self._runner = None
        self._reserva_aberta = False
        self._enviador = EnviadorLotesLocalV1(gateway, pacote, self._progresso_envio)

    def _identidade_da_maquina(self) -> str:
        # A identidade é derivada do próprio Windows/host, não viaja no
        # manifesto. Assim duas cópias legítimas do pacote não dividem uma
        # reserva por acidente; o banco continua decidindo exclusividade.
        material = "|".join((self.lote_id, platform.node(), str(uuid.getnode()), os.environ.get("COMPUTERNAME", "")))
        return str(uuid.uuid5(uuid.NAMESPACE_URL, material))

    def _progresso(self, etapa: str, item: dict | None = None, detalhe: str | None = None) -> None:
        if self.ao_progresso:
            self.ao_progresso(self, etapa, item, detalhe)

    def _progresso_envio(self, etapa: str, detalhe: str | None = None) -> None:
        self._progresso(etapa, None, detalhe)

    def _preparar_executor(self) -> None:
        import roda_lote_v6 as runner
        runner.prepara_lote_producao_v3(self.pacote.manifesto["regua"])
        self._runner = runner

    def _controle(self) -> dict:
        resposta = self.gateway.rpc("otimizador_producao_controle_lote_v1", {"p_lote_id": self.lote_id}) or {}
        if resposta.get("contrato") != "otimizador_fila_producao_v3":
            raise FalhaPacoteLocal("contrato de controle inesperado")
        return resposta

    def _reservar(self, linha: dict) -> dict:
        resposta = self.gateway.rpc("otimizador_producao_reservar_linha_local_v1", {
            "p_lote_id": self.lote_id,
            "p_worker_id": self.worker_id,
            "p_linha_id": int(linha["linha_id"]),
            "p_card_id": str(linha["card_id"]),
            "p_funcao_id": int(linha["funcao_id"]),
            "p_posicao_id": int(linha["posicao_id"]),
            "p_carta_entrada_fingerprint": linha["carta_entrada_fingerprint"],
            "p_formula_fingerprint": self.pacote.manifesto["formula_fingerprint"],
            "p_contrato_fingerprint": self.pacote.manifesto["contrato_fingerprint"],
            "p_motor_versao": self.pacote.manifesto["motor_versao"],
            "p_lote_fingerprint": self.pacote.manifesto["lote_fingerprint"],
        }) or {}
        if resposta.get("contrato") != CONTRATO_PACOTE_LOCAL_V1:
            raise FalhaPacoteLocal("contrato de reserva local inesperado")
        return resposta

    def _bloquear(self, reserva: dict, motivo: str) -> None:
        self.gateway.rpc("otimizador_producao_bloquear_linha_v3", {
            "p_lote_id": self.lote_id,
            "p_linha_id": int(reserva["linha_id"]),
            "p_reserva_token": reserva["reserva_token"],
            "p_motivo": str(motivo)[:1000],
        })
        self.pacote.apagar_reserva(int(reserva["linha_id"]))
        estado = self.pacote.estado()
        self.pacote.atualizar_estado(bloqueadas=int(estado.get("bloqueadas") or 0) + 1)

    def _calcular(self, linha: dict, reserva: dict) -> dict:
        if self._runner is None:
            raise FalhaPacoteLocal("executor local não foi preparado")
        carta = self.pacote.carta_da_linha(linha)
        if not isinstance(carta.get("carta"), dict):
            raise FalhaPacoteLocal("fotografia local da carta está ausente")
        self._runner.carrega_carta_snapshot_producao_v3(carta["carta"])
        saida = self._runner.trabalha({
            "n": int(linha["linha_id"]),
            "card_id": str(linha["card_id"]),
            "funcao_id": int(linha["funcao_id"]),
            "posicao_id": int(linha["posicao_id"]),
            "impeto_condicional_codigo": None,
            "impeto_condicional_nivel": None,
            "origem": "fila_local_v1",
        })
        if not isinstance(saida, dict) or saida.get("ERRO"):
            raise FalhaPacoteLocal(str((saida or {}).get("ERRO") or "o motor não devolveu resultado"))
        saida.update({
            "card_id": str(linha["card_id"]),
            "funcao_id": int(linha["funcao_id"]),
            "posicao_id": int(linha["posicao_id"]),
            "formula_fingerprint": self.pacote.manifesto["formula_fingerprint"],
            "contrato_fingerprint": self.pacote.manifesto["contrato_fingerprint"],
            "motor_versao": self.pacote.manifesto["motor_versao"],
            "lote_fingerprint": self.pacote.manifesto["lote_fingerprint"],
            "carta_entrada_fingerprint": linha["carta_entrada_fingerprint"],
            "impeto_condicional_codigo": None,
            "impeto_condicional_nivel": None,
        })
        tecnico_id = saida.get("tecnico_id")
        try:
            saida["tecnico_id"] = int(tecnico_id)
        except (TypeError, ValueError) as erro:
            raise FalhaPacoteLocal("resultado calculado sem tecnico_id canônico persistível") from erro
        return saida

    def _confirmar_pausa_ou_encerramento(self, estado: dict) -> dict:
        lote_estado = estado.get("estado_lote") or estado.get("estado")
        if lote_estado == "pausando":
            self._progresso("esvaziando_resultados", detalhe="pausa segura")
            self._enviador.esvaziar()
            return self.gateway.rpc("otimizador_producao_controlar_lote_v3", {
                "p_lote_id": self.lote_id, "p_acao": "confirmar_pausa", "p_confirmado": False,
            }) or {}
        if lote_estado == "encerrando":
            self._progresso("esvaziando_resultados", detalhe="encerramento seguro")
            self._enviador.esvaziar()
            return self.gateway.rpc("otimizador_producao_controlar_lote_v3", {
                "p_lote_id": self.lote_id, "p_acao": "confirmar_encerramento", "p_confirmado": True,
            }) or {}
        return estado

    def _pausar_apos_limite_controlado(self, linha: dict) -> dict:
        """Fecha o piloto depois da linha reservada, com ou sem resultado."""
        self._progresso("limite_controlado", linha, "pausando após a linha de teste")
        pausa = self.gateway.rpc("otimizador_producao_controlar_lote_v3", {
            "p_lote_id": self.lote_id, "p_acao": "pausar", "p_confirmado": False,
        }) or {}
        if (pausa.get("estado_lote") or pausa.get("estado")) not in {"pausando", "pausado"}:
            raise FalhaPacoteLocal("o contrato não confirmou a pausa do piloto controlado")
        return self._confirmar_pausa_ou_encerramento(pausa)

    def executar(self) -> dict:
        final: dict = {}
        try:
            self.pacote.validar_integridade()
            if formula_fingerprint() != FORMULA_APROVADA:
                raise FalhaPacoteLocal("a fórmula local foi alterada")
            self._progresso("conferindo_pacote")
            self._preparar_executor()
            self._enviador.iniciar()
            # Primeiro confirma qualquer saída durável deixada por queda de
            # processo. Só depois tenta reservar outra linha.
            self._enviador.esvaziar()
            self._progresso("aguardando_linha")
            for bloco_id, linhas_bloco in self.pacote.iter_blocos_linhas():
                # A entrada já está separada fisicamente: o motor recebe uma
                # fatia de no máximo mil linhas e grava suas saídas no diretório
                # do próprio bloco. O enviador, em outra thread, só sobe essa
                # pasta depois de o bloco ser marcado pronto.
                self._progresso(
                    "bloco_local_iniciado", linhas_bloco[0] if linhas_bloco else None,
                    f"bloco local {bloco_id}: {len(linhas_bloco)} linhas",
                )
                bloco_completo = True
                for linha in linhas_bloco:
                    estado = self._controle()
                    lote_estado = estado.get("estado_lote") or estado.get("estado")
                    if lote_estado != "rodando":
                        final = self._confirmar_pausa_ou_encerramento(estado)
                        bloco_completo = False
                        break
                    reserva = self._reservar(linha)
                    if reserva.get("reservada") is not True:
                        # Outro computador pode ter concluído a mesma linha
                        # depois da fotografia local. A exclusividade continua
                        # sendo decidida pelo banco, nunca pela cópia local.
                        estado = reserva.get("estado_lote") or lote_estado
                        if estado != "rodando":
                            final = self._confirmar_pausa_ou_encerramento(reserva)
                            bloco_completo = False
                            break
                        atual = self.pacote.estado()
                        self.pacote.atualizar_estado(nao_disponiveis=int(atual.get("nao_disponiveis") or 0) + 1)
                        continue
                    self._reserva_aberta = True
                    self.pacote.gravar_reserva(reserva)
                    self._linhas_tentadas_nesta_execucao += 1
                    self._progresso("linha_reservada", linha)
                    try:
                        self._progresso("calculando", linha)
                        resultado = self._calcular(linha, reserva)
                    except Exception as erro:
                        motivo = str(erro)
                        self._progresso("bloqueando_linha", linha, motivo)
                        self._bloquear(reserva, motivo)
                        self._reserva_aberta = False
                        if (self.limite_linhas is not None
                                and self._linhas_tentadas_nesta_execucao >= self.limite_linhas):
                            final = self._pausar_apos_limite_controlado(linha)
                            bloco_completo = False
                            break
                        continue
                    self._progresso("gravando_resultado_local", linha)
                    self.pacote.gravar_resultado(reserva, resultado, bloco_id=bloco_id)
                    self._reserva_aberta = False
                    atual = self.pacote.estado()
                    self.pacote.atualizar_estado(
                        estado="calculando",
                        bloco_atual=bloco_id,
                        calculadas_local=int(atual.get("calculadas_local") or 0) + 1,
                        pendentes_envio=len(self.pacote.arquivos_pendentes()),
                    )
                    self._progresso("linha_calculada_local", linha)
                    self._linhas_calculadas_nesta_execucao += 1
                    if (self.limite_linhas is not None
                            and self._linhas_tentadas_nesta_execucao >= self.limite_linhas):
                        # Piloto explícito: pede pausa depois da única linha
                        # reservada, força a persistência da saída e confirma a
                        # pausa antes de o laço poder tentar outra linha.
                        final = self._pausar_apos_limite_controlado(linha)
                        bloco_completo = False
                        break
                    if self.esperar:
                        time.sleep(self.esperar)
                if not bloco_completo:
                    break
                self.pacote.marcar_bloco_pronto(bloco_id, len(linhas_bloco))
                atual = self.pacote.estado()
                self.pacote.atualizar_estado(
                    bloco_atual=bloco_id,
                    blocos_processados=int(atual.get("blocos_processados") or 0) + 1,
                    pendentes_envio=len(self.pacote.arquivos_pendentes()),
                )
                self._progresso("bloco_local_pronto", linhas_bloco[-1] if linhas_bloco else None, f"bloco {bloco_id} pronto para envio")
                self._enviador.sinalizar()
            else:
                # A fotografia pode conter linhas concluídas por outra máquina;
                # o estado oficial final sempre vem do contrato, nunca de uma
                # contagem local inferida.
                final = self._controle()
            self._enviador.esvaziar()
            self._enviador.encerrar(esvaziar=False)
            self.pacote.atualizar_estado(estado="pausado" if (final.get("estado_lote") or final.get("estado")) == "pausado" else "finalizado")
            return final
        except Exception as erro:
            self._progresso("falha_worker_local", detalhe=str(erro))
            try:
                self._enviador.encerrar(esvaziar=False)
            except Exception:
                pass
            final = {
                "ok": False,
                "estado_lote": "processando" if self._reserva_aberta else "rodando",
                "erro": str(erro),
            }
            return final
        finally:
            if self.ao_encerrar:
                self.ao_encerrar(self, final)
