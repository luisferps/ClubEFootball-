"""Leitura dirigida dos níveis carregados pelo eFootball, sem escrita no jogo.

O layout vem da auditoria do EXE 6.0.0.0. A descoberta usa somente o inventário
de processos/módulos. Não há scanner de memória, injeção, ajuste de privilégio,
rede nem leitura de credenciais. Máscara e valores codificados nunca saem RAM.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import struct
import time
from datetime import datetime, timezone
from typing import Any, Callable
import uuid

READER_VERSION = "card-level-runtime-v2"
SCHEMA = "clubef-niveis-runtime-v1"
SUPPORTED_EXE = {"a6911e9613750df33d10598d6493db629b03195c3ec1d011704cd1e853d8c6e4": "6.0.0.0"}
ROOT_RVA = 0x86C9FC0
REPRESENTATION_RVA = 0x8686608
LAYOUT = {
    "raiz_rva": hex(ROOT_RVA), "colecoes_offset": "0x28",
    "proprias_owner_offset": "0x08", "boxes_owner_offset": "0x20",
    "vetor_cabecalho": {"inicio": 0, "fim": 8, "capacidade": 16},
    "carta_stride": 0xF0, "carta_id_offset": 8,
    "nivel_atual_offset": 0x28, "nivel_maximo_offset": 0x2C,
    "agente_stride": 0x238,
    "listas_agente": [{"offset": 0xE8, "stride": 0xF8}, {"offset": 0x200, "stride": 0xF0}, {"offset": 0x218, "stride": 0xF0}],
    "representacao": "u32_le_xor_representacao_interna",
    "getter_representacao_rva": "0x3b45470", "representacao_rva": hex(REPRESENTATION_RVA),
    "formula_orcamento": "2 * nivel_maximo - 2", "formula_rva": "0x452b499",
    "lista_recrutamento": {"offset": 0x380, "stride": 0xF0, "total_offset": 0x398,
                           "indice_inicial_offset": 0x3D4, "tamanho_pagina_offset": 0x3D0},
}


class LevelsUnavailable(RuntimeError):
    def __init__(self, state: str, message: str):
        super().__init__(message)
        self.state = state


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _api():
    if os.name != "nt" or C.sizeof(C.c_void_p) != 8:
        raise LevelsUnavailable("runtime_incompativel", "A coleta de níveis precisa do Windows e Python de 64 bits.")
    k = C.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateToolhelp32Snapshot": ([W.DWORD, W.DWORD], W.HANDLE),
        "CloseHandle": ([W.HANDLE], W.BOOL),
        "OpenProcess": ([W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
        "QueryFullProcessImageNameW": ([W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)], W.BOOL),
        "ReadProcessMemory": ([W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)], W.BOOL),
    }
    for name, (args, result) in signatures.items():
        fn = getattr(k, name); fn.argtypes = args; fn.restype = result
    return k


class _ProcessEntry(C.Structure):
    _fields_ = [("dwSize", W.DWORD), ("cntUsage", W.DWORD), ("th32ProcessID", W.DWORD),
                ("th32DefaultHeapID", C.c_size_t), ("th32ModuleID", W.DWORD), ("cntThreads", W.DWORD),
                ("th32ParentProcessID", W.DWORD), ("pcPriClassBase", W.LONG), ("dwFlags", W.DWORD), ("szExeFile", W.WCHAR * 260)]


class _ModuleEntry(C.Structure):
    _fields_ = [("dwSize", W.DWORD), ("th32ModuleID", W.DWORD), ("th32ProcessID", W.DWORD),
                ("GlblcntUsage", W.DWORD), ("ProccntUsage", W.DWORD), ("modBaseAddr", C.c_void_p),
                ("modBaseSize", W.DWORD), ("hModule", W.HMODULE),
                ("szModule", W.WCHAR * 256), ("szExePath", W.WCHAR * 260)]


def _snapshot(k, flags: int, pid: int):
    for attempt in range(4):
        handle = k.CreateToolhelp32Snapshot(flags, pid)
        if handle != C.c_void_p(-1).value:
            return handle
        if C.get_last_error() != 24 or attempt == 3:
            raise LevelsUnavailable("processo_indisponivel", "O Windows não disponibilizou o inventário do jogo.")
        time.sleep(0.05)


def discover_game() -> dict[str, Any]:
    """Descobre PID e base de um único eFootball.exe; não lê outros processos."""
    k = _api()
    for name in ("Process32FirstW", "Process32NextW"):
        getattr(k, name).argtypes = [W.HANDLE, C.POINTER(_ProcessEntry)]
        getattr(k, name).restype = W.BOOL
    handle = _snapshot(k, 2, 0); matches = []
    try:
        entry = _ProcessEntry(); entry.dwSize = C.sizeof(entry)
        ok = k.Process32FirstW(handle, C.byref(entry))
        while ok:
            if entry.szExeFile.casefold() == "efootball.exe": matches.append(int(entry.th32ProcessID))
            ok = k.Process32NextW(handle, C.byref(entry))
    finally:
        k.CloseHandle(handle)
    if not matches:
        raise LevelsUnavailable("jogo_fechado", "Abra o eFootball e carregue suas cartas ou a box; depois repita a coleta.")
    if len(matches) != 1:
        raise LevelsUnavailable("processos_ambiguos", "Há mais de um eFootball aberto; não foi escolhido um processo automaticamente.")
    pid = matches[0]
    for name in ("Module32FirstW", "Module32NextW"):
        getattr(k, name).argtypes = [W.HANDLE, C.POINTER(_ModuleEntry)]
        getattr(k, name).restype = W.BOOL
    handle = _snapshot(k, 8 | 16, pid); modules = []
    try:
        entry = _ModuleEntry(); entry.dwSize = C.sizeof(entry)
        ok = k.Module32FirstW(handle, C.byref(entry))
        while ok:
            if entry.szModule.casefold() == "efootball.exe":
                modules.append({"pid": pid, "image_base": int(entry.modBaseAddr), "module_size": int(entry.modBaseSize), "executable_path": str(entry.szExePath)})
            ok = k.Module32NextW(handle, C.byref(entry))
    finally:
        k.CloseHandle(handle)
    if len(modules) != 1:
        raise LevelsUnavailable("modulo_indisponivel", "A base carregada do executável não pôde ser confirmada.")
    game = modules[0]; path = Path(game["executable_path"])
    digest = sha256_file(path)
    if digest not in SUPPORTED_EXE:
        raise LevelsUnavailable("versao_nao_suportada", "O executável do jogo mudou; a coleta de níveis aguarda validação deste layout.")
    game.update(executable_sha256=digest, executable_version=SUPPORTED_EXE[digest])
    return game


class WindowsMemoryReader:
    def __init__(self, game: dict[str, Any], cancel: Callable[[], None] | None = None):
        self.game = game; self.base = game["image_base"]; self.k = _api()
        self.handle = None; self.total = 0; self.ledger = []; self.cancel = cancel or (lambda: None)
        self.handle = self.k.OpenProcess(0x1010, False, game["pid"])
        if not self.handle:
            raise LevelsUnavailable("leitura_indisponivel", "O Windows não permitiu consultar os níveis do jogo. Nenhum privilégio foi alterado.")
        try:
            path = C.create_unicode_buffer(32768); length = W.DWORD(len(path))
            if not self.k.QueryFullProcessImageNameW(self.handle, 0, path, C.byref(length)):
                raise LevelsUnavailable("processo_indisponivel", "O processo encerrou antes da confirmação.")
            if Path(path.value).resolve() != Path(game["executable_path"]).resolve():
                raise LevelsUnavailable("identidade_divergente", "A identidade do processo mudou.")
            with Path(path.value).open("rb") as stream:
                dos = stream.read(64); pe_offset = struct.unpack_from("<I", dos, 60)[0]
                if not 64 <= pe_offset < 1024 * 1024: raise ValueError("Cabeçalho PE inválido.")
                stream.seek(pe_offset); pe = stream.read(88)
            if dos[:2] != b"MZ" or pe[:4] != b"PE\0\0" or struct.unpack_from("<H", pe, 24)[0] != 0x20B:
                raise ValueError("Formato do executável incompatível.")
            if self.read(self.base, 64, "cabecalho_dos") != dos or self.read(self.base + pe_offset, 88, "cabecalho_pe") != pe:
                raise ValueError("Cabeçalhos carregados divergem do executável validado.")
        except Exception:
            self.close(); raise

    def read(self, address: int, size: int, purpose: str) -> bytes:
        self.cancel()
        if not purpose or not isinstance(size, int) or not 0 < size <= 65536:
            raise ValueError("Leitura sem limite ou finalidade.")
        if not 0x10000 <= address < 0x7FFFFFFFFFFF or address + size >= 0x7FFFFFFFFFFF:
            raise ValueError("Ponteiro fora do espaço de usuário.")
        if self.total + size > 16 * 1024 * 1024: raise ValueError("Limite de leitura da sessão excedido.")
        buf = C.create_string_buffer(size); count = C.c_size_t()
        ok = self.k.ReadProcessMemory(self.handle, address, buf, size, C.byref(count))
        self.total += count.value
        self.ledger.append({"endereco": hex(address), "bytes": size, "lidos": count.value, "finalidade": purpose, "ok": bool(ok)})
        if not ok or count.value != size:
            raise LevelsUnavailable("sessao_alterada", "A memória do jogo mudou ou ficou indisponível durante a leitura; repita a coleta.")
        return buf.raw

    def close(self):
        if self.handle: self.k.CloseHandle(self.handle); self.handle = None

    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def vector_bounds(raw: bytes, stride: int, max_count: int) -> tuple[int, int, int, int]:
    begin, end, cap = struct.unpack("<3Q", raw)
    if not (begin <= end <= cap and (end - begin) % stride == 0 and (cap - begin) % stride == 0):
        raise ValueError("Cabeçalho de coleção incompatível.")
    if (not begin and (end or cap)) or (cap - begin) // stride > max_count:
        raise ValueError("Capacidade de coleção incompatível.")
    if begin and (begin < 0x10000 or cap >= 0x7FFFFFFFFFFF): raise ValueError("Coleção fora do espaço de usuário.")
    return begin, end, cap, (end - begin) // stride


def read_loaded_levels(reader, physical_ids: set[str], *, capture_id: str, captured_at: str,
                       progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    """Parser testável sobre um leitor limitado; nunca usa controles para preencher valores."""
    progress = progress or (lambda message: None)
    base = reader.base; collections = []; occurrences = []; pointers = []
    def readptr(at, label):
        raw = reader.read(at, 8, label); value = struct.unpack("<Q", raw)[0]
        pointers.append((at, raw, label)); return value
    g = readptr(base + ROOT_RVA, "raiz_cartas")
    if not g: raise LevelsUnavailable("colecoes_nao_carregadas", "O jogo está aberto; carregue suas cartas ou uma box e repita a coleta.")
    a = readptr(g + 0x28, "gerenciador_colecoes")
    if not a: raise LevelsUnavailable("colecoes_nao_carregadas", "As coleções de cartas ainda não foram carregadas.")
    owned = readptr(a + 8, "colecao_propria_owner")
    boxes = readptr(a + 0x20, "colecao_agentes_owner")
    mask_raw = reader.read(base + REPRESENTATION_RVA, 4, "representacao_interna_niveis")
    mask = struct.unpack("<I", mask_raw)[0]
    try:
        def read_cards(header_address, stride, label, agent_id=None):
            header = reader.read(header_address, 24, "cabecalho_" + label)
            begin, end, cap, count = vector_bounds(header, stride, 100000)
            coll = {"colecao": label, "agente_id": agent_id, "cabecalho_endereco": hex(header_address),
                    "inicio": hex(begin), "fim": hex(end), "limite_alocacao": hex(cap), "stride": stride, "ocorrencias": count}
            digest = hashlib.sha256()
            for i in range(count):
                address = begin + i * stride
                raw_id = reader.read(address + 8, 8, "id_carta")
                stored = reader.read(address + 0x28, 8, "niveis_carta")
                cid = str(struct.unpack("<Q", raw_id)[0]); current_raw, maximum_raw = struct.unpack("<2I", stored)
                current, maximum = current_raw ^ mask, maximum_raw ^ mask
                if reader.read(address + 8, 8, "releitura_id") != raw_id or reader.read(address + 0x28, 8, "releitura_niveis") != stored:
                    raise LevelsUnavailable("sessao_alterada", "Uma carta mudou durante a coleta; nenhum nível desta captura será aplicado.")
                if not 1 <= current <= maximum <= 1000:
                    raise ValueError("Nível fora do domínio validado; captura recusada.")
                digest.update(raw_id)
                occurrences.append({"card_id": cid, "nivel_atual": current, "nivel_maximo": maximum,
                                    "colecao": label, "agente_id": agent_id, "indice": i, "endereco_registro": hex(address),
                                    "id_estavel": True, "niveis_estaveis": True, "id_fisico_confirmado": cid in physical_ids})
                if i and i % 250 == 0: progress(f"Níveis: {len(occurrences)} ocorrências lidas.")
            if reader.read(header_address, 24, "releitura_cabecalho_" + label) != header:
                raise LevelsUnavailable("sessao_alterada", "A coleção de cartas mudou durante a coleta.")
            coll.update(cabecalho_estavel=True, ids_sha256=digest.hexdigest()); collections.append(coll)
        if owned: read_cards(owned, 0xF0, "cartas_proprias")
        if boxes:
            outer = reader.read(boxes, 24, "cabecalho_agentes")
            first, last, cap, count = vector_bounds(outer, 0x238, 1000)
            for agent_index in range(count):
                agent = first + agent_index * 0x238
                agent_raw = reader.read(agent + 8, 8, "id_agente"); agent_id = str(struct.unpack("<Q", agent_raw)[0])
                for offset, stride, name in ((0xE8, 0xF8, "pickup"), (0x200, 0xF0, "banner_a"), (0x218, 0xF0, "banner_c")):
                    read_cards(agent + offset, stride, name, agent_id)
                if reader.read(agent + 8, 8, "releitura_id_agente") != agent_raw: raise ValueError("Identidade do agente mudou.")
            if reader.read(boxes, 24, "releitura_cabecalho_agentes") != outer:
                raise LevelsUnavailable("sessao_alterada", "As boxes mudaram durante a coleta.")
            # Ambos os parsers StandardDraft/Procurable alimentam esta lista.
            # Total/índice não comprovam catálogo completo, nem lista vazia significa ausência.
            total_raw = reader.read(boxes + 0x398, 4, "total_reportado_recrutamento")
            page_raw = reader.read(boxes + 0x3D0, 8, "paginacao_recrutamento")
            read_cards(boxes + 0x380, 0xF0, "lista_recrutamento")
            page_size, first_index = struct.unpack("<2I", page_raw)
            collections[-1].update(total_reportado=struct.unpack("<I", total_raw)[0],
                                   tamanho_pagina_reportado=page_size, indice_inicial_reportado=first_index,
                                   resposta_possivel=["StandardDraft", "Procurable"], modo_resposta_confirmado=False)
            if reader.read(boxes + 0x398, 4, "releitura_total_recrutamento") != total_raw or reader.read(boxes + 0x3D0, 8, "releitura_paginacao_recrutamento") != page_raw:
                raise LevelsUnavailable("sessao_alterada", "A página de recrutamento mudou durante a coleta.")
        for at, raw, label in pointers:
            if reader.read(at, 8, "releitura_" + label) != raw:
                raise LevelsUnavailable("sessao_alterada", "A raiz de cartas mudou durante a coleta.")
        if reader.read(base + REPRESENTATION_RVA, 4, "releitura_representacao") != mask_raw:
            raise LevelsUnavailable("sessao_alterada", "A representação dos níveis mudou durante a coleta.")
    finally:
        mask = None; mask_raw = None
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in occurrences: groups.setdefault(row["card_id"], []).append(row)
    cards = []; conflicts = []; unknown = []
    for cid, rows in sorted(groups.items(), key=lambda x: int(x[0])):
        maxima = sorted({r["nivel_maximo"] for r in rows})
        if cid not in physical_ids:
            unknown.append({"card_id": cid, "motivo": "ID não encontrado na coleta física atual"}); continue
        if len(maxima) != 1:
            conflicts.append({"card_id": cid, "maximos": maxima}); continue
        maximum = maxima[0]
        cards.append({"card_id": cid, "nivel_maximo": maximum, "orcamento_real": 2 * maximum - 2,
                      "origem": "memoria_jogo", "captura_id": capture_id, "capturado_em": captured_at,
                      "leitor_versao": READER_VERSION,
                      "prova_json": {"layout": LAYOUT, "ocorrencias": rows, "representacao_estavel": True, "raizes_estaveis": True,
                                     "limites_conferidos": True, "id_fisico_confirmado": True, "maximo_sem_conflito": True}})
    return {"state": "coletado" if cards else "sem_cartas_observadas", "cards": cards, "collections": collections,
            "conflicts": conflicts, "unknown_ids": unknown,
            "coverage": {"catalogo_fisico": len(physical_ids), "ids_observados": len(groups), "ids_confirmados": len(cards),
                         "ocorrencias": len(occurrences), "ids_em_conflito": len(conflicts), "ids_fisicos_ausentes": len(unknown),
                         "catalogo_completo": False, "ausente_significa": "nao_observado"}}


def capture_levels(physical_ids: set[str], *, cancel: Callable[[], None] | None = None,
                   progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    capture_id = str(uuid.uuid4()); captured_at = datetime.now(timezone.utc).isoformat()
    report = {"schema": SCHEMA, "captura_id": capture_id, "capturado_em": captured_at, "leitor_versao": READER_VERSION,
              "database_write": False, "game_write": False, "representacao_salva": False, "layout": LAYOUT, "cards": []}
    reader = None
    try:
        if cancel: cancel()
        if not physical_ids: raise LevelsUnavailable("identidade_fisica_ausente", "A coleta física atual não forneceu IDs para conferir os níveis.")
        game = discover_game()
        report["session"] = {**game, "image_base": hex(game["image_base"])}
        with WindowsMemoryReader(game, cancel) as reader:
            report.update(read_loaded_levels(reader, physical_ids, capture_id=capture_id, captured_at=captured_at, progress=progress))
        for row in report["cards"]:
            row.update(executavel_sha256=game["executable_sha256"], executavel_versao=game["executable_version"])
            row["prova_json"]["sessao"] = report["session"]
    except LevelsUnavailable as error:
        report.update(state=error.state, message=str(error), cards=[])
    except Exception as error:
        if cancel: cancel()
        report.update(state="captura_recusada", message=str(error), cards=[])
    if reader:
        report.update(read_ledger=reader.ledger, total_bytes_read=reader.total)
    report["artifact_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf8")).hexdigest()
    return report


def collect_for_desktop(canonical_cards_path: Path, run_dir: Path, emit: Callable[..., None],
                        cancel: Callable[[], None]) -> dict[str, Any]:
    emit("family", family="Níveis reais", state="reading", message="Localizando o jogo e conferindo os níveis das coleções carregadas.")
    if canonical_cards_path.is_file():
        cards = json.loads(canonical_cards_path.read_text(encoding="utf-8-sig"))
        ids = {str(row["card_id"]) for row in cards if isinstance(row, dict) and row.get("card_id")}
    else: ids = set()
    report = capture_levels(ids, cancel=cancel, progress=lambda message: emit("log", message=message))
    path = run_dir / "niveis-runtime.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    count = len(report["cards"]); observed = (report.get("coverage") or {}).get("ids_observados", 0)
    message = (f"{count} cartas com nível e orçamento conferidos; {observed} IDs observados. Cobertura das coleções carregadas."
               if count else report.get("message", "Nenhuma carta carregada foi observada; os níveis permanecem pendentes."))
    emit("family", family="Níveis reais", state="ready" if count else "pending", message=message, database_write=False)
    emit("levels", state=report["state"], cards=count, observed=observed, conflicts=len(report.get("conflicts", [])), message=message)
    return {"artifact": str(path), "artifact_sha256": sha256_file(path), "report": report, "message": message}
