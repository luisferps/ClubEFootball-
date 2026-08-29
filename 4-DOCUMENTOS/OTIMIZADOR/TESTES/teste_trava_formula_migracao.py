# -*- coding: utf-8 -*-
"""Prova de que a migração de entradas não alterou trechos matemáticos.

Compara a AST das rotinas de cálculo com o snapshot imediatamente anterior aos
hunks de consumidores. Identidades e portas de entrada podem mudar; fórmulas,
pesos, ordem e busca matemática não.
"""
import ast
import hashlib
from pathlib import Path
import unittest
import zipfile


RAIZ = Path(__file__).resolve().parents[3]
SNAP = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "RECUPERACAO" / \
    "2026-08-28-ANTES-HUNKS-CONSUMIDORES"
ZIP_BASE = RAIZ / "4-DOCUMENTOS" / "OTIMIZADOR" / "RECUPERACAO" / \
    "2026-08-28-ANTES-MIGRACAO-ENTRADAS" / "snapshot-entradas-antes.zip"


def _nos(caminho):
    arvore = ast.parse(Path(caminho).read_text(encoding="utf-8"))
    saida = {}
    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            saida[no.name] = no
        elif isinstance(no, ast.ClassDef):
            for filho in no.body:
                if isinstance(filho, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    saida[f"{no.name}.{filho.name}"] = filho
    return saida


def _ast(caminho, nome):
    return ast.dump(_nos(caminho)[nome], include_attributes=False)


class TravaFormulaMigracaoTest(unittest.TestCase):
    def _iguais(self, atual_relativo, antes_relativo, nomes):
        atual = RAIZ / atual_relativo
        antes = SNAP / antes_relativo
        for nome in nomes:
            with self.subTest(arquivo=atual_relativo, rotina=nome):
                self.assertEqual(_ast(antes, nome), _ast(atual, nome))

    def test_equacao_local_intacta(self):
        self._iguais(Path("2-MOTORES/OTIMIZADOR/equacao.py"), Path("2-MOTORES/equacao.py"), [
            "_mult", "_multv", "nivel_max_barra", "alvo_util",
            "aplica_buff", "base_barras", "cadeia",
        ])

    def test_busca_local_intacta(self):
        self._iguais(Path("2-MOTORES/OTIMIZADOR/motor.py"), Path("2-MOTORES/motor.py"), [
            "Card.ganho", "Card.vals_finais", "Card.nota_final", "Card.dist",
            "Card.aplicar", "Card.sem_add", "Card.base_barras", "Card.gasto",
            "Card.build", "build_mult", "_grupos", "_dp", "_dp_seq",
            "_recupera", "_base_turbo", "_sobra", "build_turbo",
        ])

    def test_equacao_servico_intacta(self):
        self._iguais(Path("6-AVALIADOR-NO-RAILWAY/avaliador.py"), Path("6-AVALIADOR-NO-RAILWAY/avaliador.py"), [
            "nota_de", "_mult", "base_barras", "cadeia",
        ])

    def test_otimizador_servico_inteiro_intacto(self):
        relativo = "6-AVALIADOR-NO-RAILWAY/otimizador.py"
        atual = hashlib.sha256((RAIZ / relativo).read_bytes()).digest()
        with zipfile.ZipFile(ZIP_BASE) as z:
            antes = hashlib.sha256(z.read(relativo)).digest()
        self.assertEqual(antes, atual)

    def test_replicas_de_tela_inteiras_intactas(self):
        for relativo in [
            Path("1-SISTEMA/motor-e-ficha-base.js"),
            Path("SITE-ATUALIZADO-2026-08-24/motor-e-ficha-base.js"),
            Path("SITE-ATUALIZADO-2026-08-24/TELA-CLUBEFOOTBALL-UNICA.html"),
        ]:
            with self.subTest(arquivo=str(relativo)):
                self.assertEqual((SNAP / relativo).read_bytes(),
                                 (RAIZ / relativo).read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
