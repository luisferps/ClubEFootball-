#!/usr/bin/env python3
"""Decodifica, em somente leitura, o manifesto LiveData version.bin do eFootball."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


DEFAULT_INPUT = Path(r"C:\ProgramData\KONAMI\eFootball\ST\Download\version.bin")
INITIAL_STATE = 0xDC46AEE8


def decode_vernam(ciphertext: bytes) -> bytes:
    """Reproduz VernamCipher::encrypt usado pelo executavel (a operacao e simetrica)."""
    state = INITIAL_STATE
    plaintext = bytearray()
    for encrypted_byte in ciphertext:
        mixed = (((((state << 11) & 0xFFFFFFFF) ^ state) << 11) & 0xFFFFFFFF)
        key_byte = (
            ((mixed >> 16) & 0xFF)
            ^ ((mixed >> 8) & 0xFF)
            ^ ((state >> 27) & 0xFF)
            ^ ((state >> 8) & 0xFF)
        )
        plaintext.append(encrypted_byte ^ key_byte)
        state = key_byte
    return bytes(plaintext)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--output",
        type=Path,
        help="Destino opcional do JSON decodificado; sem esta opcao, imprime na tela.",
    )
    args = parser.parse_args()

    source = args.input.resolve(strict=True)
    before_stat = source.stat()
    ciphertext = source.read_bytes()
    before_hash = sha256(ciphertext)

    plaintext = decode_vernam(ciphertext)
    document = json.loads(plaintext.decode("utf-8"))
    required = {"version", "targetAppVersion", "dt870Hash", "dt870FileSize", "dt880"}
    missing = sorted(required.difference(document))
    if missing:
        raise ValueError(f"Campos obrigatorios ausentes: {', '.join(missing)}")

    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.resolve()
        if output == source:
            raise ValueError("O destino nao pode ser o proprio version.bin.")
        if output.exists():
            raise FileExistsError(f"O script nao sobrescreve arquivo existente: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    after_stat = source.stat()
    after_hash = sha256(source.read_bytes())
    unchanged = (
        before_hash == after_hash
        and before_stat.st_size == after_stat.st_size
        and before_stat.st_mtime_ns == after_stat.st_mtime_ns
    )
    if not unchanged:
        raise RuntimeError("A verificacao de somente leitura da origem falhou.")

    print(
        json.dumps(
            {
                "arquivo_origem": str(source),
                "sha256_cifrado": before_hash,
                "tamanho_cifrado_bytes": len(ciphertext),
                "versao": document["version"],
                "targetAppVersion": document["targetAppVersion"],
                "dt870Hash": document["dt870Hash"],
                "quantidade_dt880": len(document["dt880"]),
                "origem_permaneceu_inalterada": True,
                "arquivo_saida": str(args.output.resolve()) if args.output else None,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
