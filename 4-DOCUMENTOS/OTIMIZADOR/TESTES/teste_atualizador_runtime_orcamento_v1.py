# -*- coding: utf-8 -*-
"""Instala somente arquivos fictícios em diretórios temporários; nunca inicia EXE."""
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[3]
ATUALIZADOR=RAIZ/"2-MOTORES/OTIMIZADOR/ATUALIZAR-RUNTIME-OTIMIZADOR.ps1"


class AtualizadorTest(unittest.TestCase):
    def preparar(self,base):
        pacote=base/"pacote"; runtime=pacote/"RUNTIME"; destino=base/"maquina-motores"
        (runtime/"bin").mkdir(parents=True); (destino/"bin").mkdir(parents=True)
        shutil.copy2(ATUALIZADOR,pacote/ATUALIZADOR.name)
        novos={"bin/OperacaoLocalJson.exe":b"EXE-NOVO-FICTICIO","PROCESSAR-FILA.bat":b"ATALHO-NOVO",
               "FILA-ATIVA.json":b'{"contrato":"prioridade_orcamento_v1","lotes":["teste"]}'}
        arquivos=[]
        for rel,conteudo in novos.items():
            (runtime/rel).write_bytes(conteudo)
            arquivos.append({"caminho":rel,"sha256":hashlib.sha256(conteudo).hexdigest()})
        (pacote/"MANIFESTO-ATUALIZACAO.json").write_text(json.dumps({
            "contrato":"atualizacao_runtime_otimizador_v1","arquivos":arquivos}),encoding="utf-8")
        (destino/"bin/OperacaoLocalJson.exe").write_bytes(b"EXE-ANTERIOR-FICTICIO")
        (destino/"PROCESSAR-FILA.bat").write_bytes(b"ATALHO-ANTERIOR")
        (destino/"config.txt").write_bytes(b"CONFIG-LOCAL-FICTICIO")
        (destino/"RESULTADOS-JSON").mkdir()
        (destino/"RESULTADOS-JSON/resultado.json").write_bytes(b"RESULTADO-PRESERVADO")
        return pacote,destino

    def executar(self,pacote,destino):
        return subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",
              str(pacote/ATUALIZADOR.name),"-Destino",str(destino)],capture_output=True,timeout=45)

    def test_substitui_confere_backup_preserva_config_e_resultados(self):
        with tempfile.TemporaryDirectory() as tmp:
            pacote,destino=self.preparar(Path(tmp))
            result=self.executar(pacote,destino)
            self.assertEqual(result.returncode,0,result.stderr.decode(errors="replace"))
            self.assertEqual((destino/"bin/OperacaoLocalJson.exe").read_bytes(),b"EXE-NOVO-FICTICIO")
            self.assertEqual((destino/"config.txt").read_bytes(),b"CONFIG-LOCAL-FICTICIO")
            self.assertEqual((destino/"RESULTADOS-JSON/resultado.json").read_bytes(),b"RESULTADO-PRESERVADO")
            backups=list((destino/"ATUALIZACOES").glob("backup-*"))
            self.assertEqual(len(backups),1)
            self.assertEqual((backups[0]/"bin/OperacaoLocalJson.exe").read_bytes(),b"EXE-ANTERIOR-FICTICIO")
            self.assertTrue((backups[0]/"APLICADO.json").is_file())

    def test_hash_corrompido_recusa_antes_de_substituir(self):
        with tempfile.TemporaryDirectory() as tmp:
            pacote,destino=self.preparar(Path(tmp))
            (pacote/"RUNTIME/bin/OperacaoLocalJson.exe").write_bytes(b"CORROMPIDO")
            self.assertNotEqual(self.executar(pacote,destino).returncode,0)
            self.assertEqual((destino/"bin/OperacaoLocalJson.exe").read_bytes(),b"EXE-ANTERIOR-FICTICIO")
            self.assertFalse((destino/"ATUALIZACOES").exists())

    def test_pacote_nao_pode_sobrescrever_config_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            pacote,destino=self.preparar(Path(tmp))
            arq=pacote/"MANIFESTO-ATUALIZACAO.json"
            dados=json.loads(arq.read_text())
            dados["arquivos"].append({"caminho":"config.txt","sha256":"0"*64})
            arq.write_text(json.dumps(dados))
            self.assertNotEqual(self.executar(pacote,destino).returncode,0)
            self.assertEqual((destino/"config.txt").read_bytes(),b"CONFIG-LOCAL-FICTICIO")


if __name__=="__main__":
    unittest.main()

