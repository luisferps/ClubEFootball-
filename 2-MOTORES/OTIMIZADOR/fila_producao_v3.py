# -*- coding: utf-8 -*-
"""Worker local da fila produtiva V3.

O browser nunca chama este módulo. Ele só é criado pelo servidor loopback após
o operador clicar em Iniciar/Retomar e fala exclusivamente com contratos
selados. Na esteira integral, a reserva e a entrada vêm da mesma fotografia
privada V19 que alimenta o painel. Não lê ``clube.*``, não grava direto no
banco e não publica nada.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path


PASTA = Path(__file__).resolve().parent
CONTRATO = "otimizador_fila_producao_v3"
CONTRATO_ENTRADA_V7 = "otimizador_entrada_linha_v1"
MOTOR_VERSAO = "otimizador-fila-producao-v3-local-20260903-goleiro-e-condicional-v11"
FORMULA_APROVADA = "5a7446b3dfa7b6b45ece1f611b1751fc1221f06e76c53cbd0827a83962c76e89"


class FalhaFilaProducao(RuntimeError):
    """Falha fechada: não inicia uma linha com selo ou contrato divergente."""


def formula_fingerprint() -> str:
    """Assina cálculo, tradução canônica e adaptador de saída aprovados."""
    h = hashlib.sha256()
    for nome in ("equacao.py", "motor.py", "regua.py", "fonte_unica.py", "roda_lote_v6.py"):
        h.update(nome.encode("utf-8"))
        h.update((PASTA / nome).read_bytes())
    return h.hexdigest()


def _texto_erro(excecao: BaseException) -> str:
    texto = str(excecao).strip() or type(excecao).__name__
    return texto[:1000]


def _falha_de_transporte(excecao: BaseException) -> bool:
    """Distingue infraestrutura temporária de falha do cálculo/contrato.

    O gateway local marca rede, timeout e autenticação remota como recuperáveis.
    O worker nunca pode transformar isso em ``lote falhou``: antes de haver uma
    linha reservada não existe resultado a invalidar, e depois a reserva segue
    sob autoridade do banco. Falhas matemáticas e selos incompatíveis não têm
    este marcador e preservam o comportamento fail-closed existente.
    """
    return bool(getattr(excecao, "recuperavel", False)) or isinstance(
        excecao, (TimeoutError, ConnectionError, OSError),
    )


def _tentativa_segura_de_repetir(excecao: BaseException) -> bool:
    """Só permite repetir uma chamada que o servidor recusou antes de gravar."""
    return bool(getattr(excecao, "repetivel", False))


class WorkerFilaProducaoV3:
    """Uma reserva por vez; o banco decide exclusividade e estados."""

    def __init__(self, gateway, lote_id: str, ao_encerrar=None, esperar: float = 0.25,
                 esteira: bool = False, ao_progresso=None):
        self.gateway = gateway
        self.lote_id = str(lote_id)
        self.worker_id = str(uuid.uuid4())
        self.ao_encerrar = ao_encerrar
        self.esperar = max(0.05, float(esperar))
        self.esteira = bool(esteira)
        self.ao_progresso = ao_progresso
        self._runner = None
        # Só é verdadeiro entre a reserva confirmada e a conclusão/bloqueio
        # também confirmado. Uma falha nesse intervalo nunca pode derrubar o
        # lote inteiro: o banco preserva a única linha ativa para recuperação
        # explícita.
        self._reserva_aberta = False

    def _progresso(self, etapa: str, item: dict | None = None, detalhe=None) -> None:
        """Espelha marcos já existentes para o painel local; nunca muda o cálculo."""
        if not self.ao_progresso:
            return
        try:
            self.ao_progresso(self, etapa, item, detalhe)
        except Exception:
            # Observabilidade não pode derrubar nem alterar uma linha da fila.
            pass

    def _rpc(self, nome: str, corpo: dict | None = None):
        return self.gateway.rpc(nome, corpo or {}) or {}

    def _contexto(self) -> dict:
        contexto = self._rpc("otimizador_producao_contexto_lote_v3", {
            "p_lote_id": self.lote_id,
        })
        if contexto.get("contrato") != CONTRATO or str(contexto.get("lote_id")) != self.lote_id:
            raise FalhaFilaProducao("contrato de contexto V3 inesperado")
        if contexto.get("formula_fingerprint") != FORMULA_APROVADA:
            raise FalhaFilaProducao("o lote não está selado com a fórmula aprovada")
        if formula_fingerprint() != contexto.get("formula_fingerprint"):
            raise FalhaFilaProducao("a fórmula local mudou depois do selo do lote")
        if contexto.get("motor_versao") != MOTOR_VERSAO:
            raise FalhaFilaProducao("a versão local do worker diverge do lote")
        if (contexto.get("impetos_condicionais") not in ("desligados", "nenhum_no_lote", "por_degrau")
                or contexto.get("pode_publicar") is not False):
            raise FalhaFilaProducao("o contexto V3 tentou habilitar uma saída não autorizada")
        regua = contexto.get("regua")
        if not isinstance(regua, dict) or (regua.get("gate") or {}).get("pode_rodar") is not True:
            raise FalhaFilaProducao("a fotografia da régua não está apta")
        return contexto

    def _contexto_com_reconexao(self) -> dict:
        """Espera a infraestrutura voltar sem mudar o estado selado do lote."""
        tentativas = 0
        while True:
            try:
                self._progresso("conferindo_selo")
                return self._contexto()
            except Exception as erro:
                if not _falha_de_transporte(erro):
                    raise
                tentativas += 1
                espera = min(30.0, 1.0 * (2 ** min(tentativas - 1, 5)))
                self._progresso(
                    "reconectando_contrato",
                    detalhe=f"tentativa {tentativas}; nova tentativa em {int(espera)} s; {_texto_erro(erro)}",
                )
                time.sleep(espera)

    def _preparar_executor(self, contexto: dict) -> None:
        import roda_lote_v6 as runner
        runner.prepara_lote_producao_v3(contexto["regua"])
        self._runner = runner

    def _contexto_da_entrada_v7(self, entrada: dict) -> dict:
        """Valida a fotografia única devolvida pela reserva V7.

        A esteira não consulta mais contexto e carta em contratos separados:
        esta única resposta já é o selo da linha e a entrada do cálculo.
        """
        if entrada.get("contrato") != CONTRATO_ENTRADA_V7:
            raise FalhaFilaProducao("reserva V7 retornou fotografia de entrada inesperada")
        if str(entrada.get("lote_id")) != self.lote_id:
            raise FalhaFilaProducao("a fotografia V7 pertence a outro lote")
        if entrada.get("formula_fingerprint") != FORMULA_APROVADA:
            raise FalhaFilaProducao("a fotografia V7 não está selada com a fórmula aprovada")
        if formula_fingerprint() != entrada.get("formula_fingerprint"):
            raise FalhaFilaProducao("a fórmula local mudou depois do selo do lote")
        if entrada.get("motor_versao") != MOTOR_VERSAO:
            raise FalhaFilaProducao("a versão local do worker diverge da fotografia V7")
        if (entrada.get("impetos_condicionais") not in ("desligados", "nenhum_no_lote", "por_degrau")
                or entrada.get("pode_publicar") is True):
            raise FalhaFilaProducao("a fotografia V7 tentou habilitar uma saída não autorizada")
        regua = entrada.get("regua")
        if not isinstance(regua, dict) or (regua.get("gate") or {}).get("pode_rodar") is not True:
            raise FalhaFilaProducao("a fotografia única da régua não está apta")
        if not isinstance(entrada.get("carta"), dict):
            raise FalhaFilaProducao("a fotografia V7 não trouxe snapshot da carta")
        return {"regua": regua}

    def _reservar(self) -> dict:
        if self.esteira:
            resposta = self._rpc("otimizador_producao_reservar_entrada_v7", {
                "p_lote_id": self.lote_id,
                "p_worker_id": self.worker_id,
                "p_formula_fingerprint": formula_fingerprint(),
                "p_motor_versao": MOTOR_VERSAO,
            })
            if resposta.get("contrato") != CONTRATO_ENTRADA_V7:
                raise FalhaFilaProducao("reserva V7 retornou contrato inesperado")
            return resposta
        resposta = self._rpc("otimizador_producao_reservar_linha_v3", {
            "p_lote_id": self.lote_id,
            "p_worker_id": self.worker_id,
        })
        if resposta.get("contrato") != CONTRATO:
            raise FalhaFilaProducao("reserva retornou contrato inesperado")
        return resposta

    def _reservar_com_reconexao(self) -> dict:
        """Repete apenas recusas confirmadas, nunca um timeout ambíguo.

        Se uma conexão cair depois de o banco aceitar a reserva, não existe
        garantia de que a resposta chegou. Nesse caso o erro sobe para o fim do
        worker, que preserva o lote e deixa a recuperação explícita decidir a
        única linha pendente. Uma resposta 401/403/57014, por outro lado, foi
        recusada pelo servidor e pode ser tentada de novo sem duplicar trabalho.
        """
        tentativas = 0
        while True:
            try:
                return self._reservar()
            except Exception as erro:
                if not (_falha_de_transporte(erro) and _tentativa_segura_de_repetir(erro)):
                    raise
                tentativas += 1
                espera = min(30.0, 1.0 * (2 ** min(tentativas - 1, 5)))
                self._progresso(
                    "reconectando_reserva",
                    detalhe=f"tentativa {tentativas}; nova tentativa em {int(espera)} s; {_texto_erro(erro)}",
                )
                time.sleep(espera)

    def _calcular(self, item: dict) -> dict:
        # 03/09 — o Ímpeto condicional voltou a rodar. O par código+nível vem
        # da linha e diz qual dos três degraus está sendo calculado. Quem
        # confere é `fonte_unica.vetor_impetos_da_linha`: exige os dois quando
        # a carta tem condicional, exige que o código seja o da carta e que o
        # nível caiba no `nivel_maximo` físico dela.
        if self._runner is None:
            raise FalhaFilaProducao("executor V3 não foi preparado")
        carta = item.get("carta")
        if not isinstance(carta, dict):
            raise FalhaFilaProducao("a reserva não trouxe snapshot da carta")
        self._runner.carrega_carta_snapshot_producao_v3(carta)
        saida = self._runner.trabalha({
            "n": item["linha_id"], "card_id": item["card_id"],
            "funcao_id": item["funcao_id"], "posicao_id": item["posicao_id"],
            "impeto_condicional_codigo": item.get("impeto_condicional_codigo"),
            "impeto_condicional_nivel": item.get("impeto_condicional_nivel"),
            "origem": "fila_producao_v3",
        })
        if not isinstance(saida, dict):
            raise FalhaFilaProducao("o Otimizador não devolveu resultado")
        if saida.get("ERRO"):
            raise FalhaFilaProducao(str(saida["ERRO"]))
        saida.update({
            "card_id": str(item["card_id"]), "funcao_id": int(item["funcao_id"]),
            "posicao_id": int(item["posicao_id"]),
            "formula_fingerprint": item["formula_fingerprint"],
            "contrato_fingerprint": item["contrato_fingerprint"],
            "motor_versao": item["motor_versao"],
            "lote_fingerprint": item["lote_fingerprint"],
            "carta_entrada_fingerprint": item["carta_entrada_fingerprint"],
            "impeto_condicional_codigo": item.get("impeto_condicional_codigo"),
            "impeto_condicional_nivel": item.get("impeto_condicional_nivel"),
        })
        self._validar_resultado_persistivel(saida)
        return saida

    @staticmethod
    def _validar_resultado_persistivel(saida: dict) -> None:
        """Impede que uma saída sem FK obrigatória chegue à conclusão.

        ``build_otimizador.tecnico_id`` é uma FK obrigatória. Recusar aqui
        transforma saída incompleta em bloqueio explícito da própria linha,
        antes de chamar a conclusão e sem deixar a reserva presa.
        """
        try:
            tecnico_id = saida.get("tecnico_id")
            if tecnico_id is None:
                raise ValueError("ausente")
            saida["tecnico_id"] = int(tecnico_id)
        except (TypeError, ValueError) as erro:
            raise FalhaFilaProducao(
                "resultado calculado sem tecnico_id canônico persistível"
            ) from erro

    def _concluir(self, item: dict, resultado: dict) -> dict:
        rpc = ("otimizador_producao_concluir_linha_v6"
               if self.esteira else "otimizador_producao_concluir_linha_v3")
        return self._rpc(rpc, {
            "p_lote_id": self.lote_id,
            "p_linha_id": item["linha_id"],
            "p_reserva_token": item["reserva_token"],
            "p_resultado": resultado,
        })

    def _bloquear(self, item: dict, motivo: str) -> dict:
        return self._rpc("otimizador_producao_bloquear_linha_v3", {
            "p_lote_id": self.lote_id,
            "p_linha_id": item["linha_id"],
            "p_reserva_token": item["reserva_token"],
            "p_motivo": motivo,
        })

    def _concluir_ou_bloquear_recusa_confirmada(self, item: dict, resultado: dict) -> bool:
        """Conclui a linha ou fecha somente uma recusa confirmada do banco.

        HTTP 400 é devolvido pelo gateway apenas quando a chamada foi recusada
        antes de gravar. Nesse caso a reserva ainda pertence a este worker e a
        linha pode ser bloqueada com o motivo real. Timeout/queda de conexão
        continuam ambíguos e preservam a reserva para recuperação explícita.
        """
        try:
            self._concluir(item, resultado)
            return True
        except Exception as erro:
            if not getattr(erro, "rejeicao_confirmada_sem_gravacao", False):
                raise
            motivo = "resultado recusado pelo contrato antes da gravação: " + _texto_erro(erro)
            self._progresso("bloqueando_linha", item, motivo)
            self._bloquear(item, motivo)
            return False

    def _fechar_pausa_ou_encerramento(self) -> dict:
        # Esta consulta ocorre após cada linha. Ela precisa ser deliberadamente
        # pequena: controles de pausa/encerramento não dependem de totais,
        # paginação ou resultados. A V1 lê somente o estado selado do lote;
        # o RPC de controle ainda confirma atomicamente que não há linha ativa.
        estado = self._rpc("otimizador_producao_controle_lote_v1", {
            "p_lote_id": self.lote_id,
        })
        if estado.get("contrato") != CONTRATO:
            raise FalhaFilaProducao("status do lote retornou contrato inesperado")
        lote_estado = estado.get("estado_lote")
        if lote_estado == "pausando":
            return self._rpc("otimizador_producao_controlar_lote_v3", {
                "p_lote_id": self.lote_id, "p_acao": "confirmar_pausa", "p_confirmado": False,
            })
        if lote_estado == "encerrando":
            return self._rpc("otimizador_producao_controlar_lote_v3", {
                "p_lote_id": self.lote_id, "p_acao": "confirmar_encerramento", "p_confirmado": True,
            })
        return estado

    def executar(self) -> dict:
        """Roda até concluir/pausar/encerrar, sempre uma linha reservada por vez."""
        final: dict = {}
        try:
            # O lote integral só recebe a régua junto da primeira linha
            # reservada pela entrada V7. Isso elimina a janela entre duas
            # leituras independentes que causava respostas incompatíveis.
            if not self.esteira:
                contexto = self._contexto_com_reconexao()
                self._progresso("preparando_executor")
                self._preparar_executor(contexto)
            self._progresso("aguardando_linha")
            while True:
                item = self._reservar_com_reconexao()
                if item.get("reservada") is not True:
                    estado = item.get("estado_lote")
                    if estado == "rodando":
                        # Outro worker pode estar terminando uma linha. Não calcula
                        # nem duplica; aguarda nova decisão atômica do banco.
                        self._progresso("aguardando_linha")
                        time.sleep(self.esperar)
                        continue
                    final = self._fechar_pausa_ou_encerramento()
                    self._progresso("encerrando", detalhe=final.get("estado_lote") or final.get("estado"))
                    break
                self._progresso("linha_reservada", item)
                self._reserva_aberta = True
                try:
                    if self.esteira:
                        contexto = self._contexto_da_entrada_v7(item)
                        if self._runner is None:
                            self._progresso("preparando_executor", item)
                            self._preparar_executor(contexto)
                    self._progresso("calculando", item)
                    resultado = self._calcular(item)
                    self._validar_resultado_persistivel(resultado)
                except Exception as erro:
                    motivo = _texto_erro(erro)
                    self._progresso("bloqueando_linha", item, motivo)
                    self._bloquear(item, motivo)
                    self._reserva_aberta = False
                else:
                    self._progresso("gravando_resultado", item)
                    concluida = self._concluir_ou_bloquear_recusa_confirmada(item, resultado)
                    self._reserva_aberta = False
                    self._progresso("linha_concluida" if concluida else "linha_bloqueada", item)
                final = self._fechar_pausa_ou_encerramento()
                estado = final.get("estado_lote") or final.get("estado")
                if estado in {"pausado", "encerrado", "concluido", "falhou"}:
                    self._progresso("encerrando", detalhe=estado)
                    break
            return final
        except Exception as erro:
            motivo = _texto_erro(erro)
            self._progresso("falha_worker", detalhe=motivo)
            if self.esteira:
                # A esteira integral não marca o lote inteiro como falho por
                # uma exceção do processo local. Antes da reserva, não há linha
                # a invalidar; depois dela, somente o banco pode decidir o
                # destino da reserva ativa. Assim um computador sem conexão ou
                # com pacote antigo não derruba 184 mil pendências válidas.
                final = {
                    "ok": False,
                    "estado_lote": "processando" if self._reserva_aberta else "rodando",
                    "erro": motivo,
                    "recuperavel": _falha_de_transporte(erro),
                    "reserva_ativa": self._reserva_aberta,
                }
                self._progresso(
                    "conexao_interrompida" if _falha_de_transporte(erro) else "falha_local_sem_lote",
                    detalhe=motivo,
                )
                return final
            if _falha_de_transporte(erro):
                # Infraestrutura não é falha de lote. O estado no banco fica
                # intocado para que este ou outro computador possa reassumir
                # somente o que o contrato ainda declarar pendente. Isso evita
                # perder uma fila por uma oscilação de rede/chave e não publica
                # nem reprocessa uma linha.
                final = {
                    "ok": False,
                    "estado_lote": "rodando",
                    "erro": motivo,
                    "recuperavel": True,
                }
                self._progresso("conexao_interrompida", detalhe=motivo)
                return final
            try:
                final = self._rpc("otimizador_producao_falhar_lote_v3", {
                    "p_lote_id": self.lote_id, "p_motivo": motivo,
                })
            except Exception:
                final = {"ok": False, "estado_lote": "falhou", "erro": motivo}
            return final
        finally:
            if self.ao_encerrar:
                self.ao_encerrar(self, final)


def resultado_serializavel(valor: dict) -> str:
    """Auxiliar de teste: garante que telemetria não leve objetos locais ao RPC."""
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
