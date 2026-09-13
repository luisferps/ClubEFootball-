"""Falha apos commit e pausa entre lotes: garantias de retomada do executor."""
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[3]
FILE = ROOT / "2-MOTORES/BONIFICADOR/OPERACAO-ESTILOS-V12/executor_estilos.py"
spec = importlib.util.spec_from_file_location("executor_estilos", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SemEspera(threading.Event):
    def wait(self, timeout=None):
        return self.is_set()

def status(concluido=False):
    return {"contrato":"correcao-estilos-v12","preparada":True,"total":1,
            "concluidas":int(concluido),"corrigidas":int(concluido),"erros":0,
            "concluida_em":"2026-09-09" if concluido else None}

class TestExecutor(unittest.TestCase):
    def test_commit_confirmado_apos_timeout_nao_repete_lote(self):
        committed = False
        chamadas = []
        def rpc(nome, corpo=None):
            nonlocal committed
            chamadas.append(nome)
            if nome.endswith("status_v12"):
                return status(committed)
            committed = True
            raise ConnectionError("resposta perdida depois do commit")
        with tempfile.TemporaryDirectory() as tmp:
            executor = mod.Executor(rpc, Path(tmp))
            executor.encerrar = SemEspera()
            executor.trabalhar()
            self.assertEqual(chamadas, ["correcao_estilos_status_v12","correcao_estilos_tick_v12","correcao_estilos_status_v12"])
            self.assertEqual(executor.snapshot()["estado"], "concluido")
    def test_pausa_aguarda_confirmacao_sem_iniciar_outro_lote(self):
        chamadas = []
        with tempfile.TemporaryDirectory() as tmp:
            def rpc(nome, corpo=None):
                chamadas.append(nome)
                if nome.endswith("tick_v12"):
                    executor.controlar("pausar")
                return status(False)
            executor = mod.Executor(rpc, Path(tmp))
            executor.encerrar = SemEspera()
            original = executor.atualizar
            def atualizar(**dados):
                original(**dados)
                if dados.get("estado") == "pausado":
                    executor.encerrar.set()
            executor.atualizar = atualizar
            executor.trabalhar()
            self.assertEqual(chamadas, ["correcao_estilos_status_v12","correcao_estilos_tick_v12"])
            self.assertTrue((Path(tmp)/"recibos.jsonl").is_file())

if __name__ == "__main__":
    unittest.main()
