#!/usr/bin/env python3
"""Reconstrui a chave do OnlineSystemHttpAes a partir do eFootball.exe local."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


DEFAULT_EXE = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\eFootball"
    r"\eFootball\Binaries\Win64\eFootball.exe"
)
STATIC_OBJECT_RVA = 0x6E6FA70
DERIVATION_FUNCTION_RVA = 0x46E1C00
INITIALIZER_RVA = 0x46E28B7
HTTP_AES_INITIALIZER_RVA = 0x480DA10
XOR_CONSTANT = 0x75

# Trincas lidas das instrucoes entre RVA 0x46E1C80 e 0x46E1EEB.
# Cada byte de saida e obj[a] ^ obj[b] ^ obj[c] ^ 0x75.
SOURCE_OFFSETS = (
    (0x41, 0x38, 0x08),
    (0x42, 0x39, 0x09),
    (0x43, 0x3A, 0x0A),
    (0x44, 0x3B, 0x0B),
    (0x45, 0x3C, 0x0C),
    (0x46, 0x3D, 0x0D),
    (0x47, 0x3E, 0x0E),
    (0x0F, 0x48, 0x3F),
    (0x49, 0x40, 0x10),
    (0x38, 0x4A, 0x11),
    (0x39, 0x4B, 0x12),
    (0x3A, 0x4C, 0x13),
    (0x41, 0x3B, 0x14),
    (0x42, 0x3C, 0x15),
    (0x43, 0x3D, 0x16),
    (0x44, 0x3E, 0x17),
    (0x45, 0x18, 0x3F),
    (0x46, 0x40, 0x19),
    (0x47, 0x38, 0x1A),
    (0x39, 0x1B, 0x48),
    (0x49, 0x3A, 0x1C),
    (0x4A, 0x3B, 0x1D),
    (0x4B, 0x3C, 0x1E),
    (0x4C, 0x3D, 0x1F),
    (0x41, 0x3E, 0x20),
    (0x42, 0x21, 0x3F),
    (0x43, 0x40, 0x22),
    (0x44, 0x38, 0x23),
    (0x45, 0x39, 0x24),
    (0x46, 0x3A, 0x25),
    (0x47, 0x3B, 0x26),
    (0x3C, 0x27, 0x48),
)


def rva_to_file_offset(image: bytes, rva: int) -> int:
    """Converte RVA em offset lendo apenas os cabecalhos PE necessarios."""
    if image[:2] != b"MZ":
        raise ValueError("Cabecalho DOS MZ ausente.")
    pe_offset = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("Assinatura PE ausente.")

    number_of_sections = struct.unpack_from("<H", image, pe_offset + 6)[0]
    optional_header_size = struct.unpack_from("<H", image, pe_offset + 20)[0]
    section_table = pe_offset + 24 + optional_header_size

    for index in range(number_of_sections):
        section = section_table + index * 40
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<IIII", image, section + 8
        )
        span = max(virtual_size, raw_size)
        if virtual_address <= rva < virtual_address + span:
            delta = rva - virtual_address
            if delta >= raw_size:
                raise ValueError(f"RVA 0x{rva:X} nao possui bytes fisicos no PE.")
            return raw_pointer + delta
    raise ValueError(f"RVA 0x{rva:X} nao pertence a nenhuma secao do PE.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    args = parser.parse_args()

    exe = args.exe.resolve(strict=True)
    before = exe.stat()
    image = exe.read_bytes()
    image_hash = hashlib.sha256(image).hexdigest()

    object_offset = rva_to_file_offset(image, STATIC_OBJECT_RVA)
    static_object = image[object_offset : object_offset + 0x4D]
    if len(static_object) != 0x4D:
        raise ValueError("Objeto estatico incompleto no RVA esperado.")

    key = bytes(
        static_object[a] ^ static_object[b] ^ static_object[c] ^ XOR_CONSTANT
        for a, b, c in SOURCE_OFFSETS
    )
    if len(key) != 32:
        raise AssertionError("A chave reconstruida nao tem 32 bytes.")

    after = exe.stat()
    after_hash = hashlib.sha256(exe.read_bytes()).hexdigest()
    unchanged = (
        image_hash == after_hash
        and before.st_size == after.st_size
        and before.st_mtime_ns == after.st_mtime_ns
    )
    if not unchanged:
        raise RuntimeError("A verificacao de somente leitura do executavel falhou.")

    print(
        json.dumps(
            {
                "executavel": str(exe),
                "sha256_executavel": image_hash,
                "rva_objeto_estatico": f"0x{STATIC_OBJECT_RVA:X}",
                "rva_funcao_derivacao": f"0x{DERIVATION_FUNCTION_RVA:X}",
                "rva_inicializador": f"0x{INITIALIZER_RVA:X}",
                "rva_consumidor_OnlineSystemHttpAes": f"0x{HTTP_AES_INITIALIZER_RVA:X}",
                "chave_aes_256_hex": key.hex(),
                "executavel_permaneceu_inalterado": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
