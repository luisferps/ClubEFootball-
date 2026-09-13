from pathlib import Path


RAIZ = Path(__file__).resolve().parents[3]
MIGRACAO = RAIZ / "4-DOCUMENTOS" / "BONIFICADOR" / "SQL" / (
    "APLICAR-FINALIZACAO-PUBLICACAO-AUTOMATICA-POR-LINHA-V1.sql"
)
TESTE_BANCO = Path(__file__).resolve().with_name(
    "TESTAR-FINALIZACAO-PUBLICACAO-AUTOMATICA-POR-LINHA-V1.sql"
)
EXTENSOES = {".py", ".sql", ".bat", ".cmd", ".md", ".js", ".ps1"}
PROIBIDOS = (
    "clube_novo." + "publicar_e_normalizar_v2",
    "clube_novo." + "atualizar_lista_publicada_v1",
    "clube_novo." + "build_pontuacao_final_v2_mat",
    "bonificador_correcao_" + "cortar_v1",
    "bonificador_correcao_" + "reverter_v1",
)


def arquivos_operacionais():
    for caminho in RAIZ.rglob("*"):
        if not caminho.is_file() or caminho.suffix.lower() not in EXTENSOES:
            continue
        if caminho in {MIGRACAO, TESTE_BANCO, Path(__file__).resolve()}:
            continue
        partes = {parte.upper() for parte in caminho.parts}
        if "RECUPERACAO" in partes or ".GIT" in partes or "__PYCACHE__" in partes:
            continue
        yield caminho


def test_so_existe_uma_finalizadora_operacional():
    ocorrencias = []
    for caminho in arquivos_operacionais():
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        for proibido in PROIBIDOS:
            if proibido in texto:
                ocorrencias.append(f"{caminho.relative_to(RAIZ)}: {proibido}")
    assert not ocorrencias, "rota removida reapareceu:\n" + "\n".join(ocorrencias)


def test_bats_de_cutover_nao_existirem():
    pasta = RAIZ / "2-MOTORES" / "BONIFICADOR" / "OPERACAO-CORRECAO-FISICA"
    antigos = [
        pasta / ("FAZER-" + "CUTOVER.bat"),
        pasta / ("REVERTER-" + "CUTOVER.bat"),
        pasta / ("ENCERRAR-LOTE-" + "V9.bat"),
    ]
    assert not [p.name for p in antigos if p.exists()]


def test_migracao_contem_travas_e_unica_finalizadora():
    texto = MIGRACAO.read_text(encoding="utf-8")
    assert "finalizar_publicar_linha_v1" in texto
    assert "for update skip locked" in texto.lower()
    assert "finalizacao_linha_em_curso" in texto
    assert "bootstrap recusado" in texto
