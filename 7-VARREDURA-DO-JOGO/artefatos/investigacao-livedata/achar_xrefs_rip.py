"""Localiza referencias RIP-relative a textos no PE do eFootball (somente leitura)."""

from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path

import pefile


def section_name(section) -> str:
    return section.Name.rstrip(b"\x00").decode("ascii", "replace")


def file_offset_to_rva(pe: pefile.PE, offset: int) -> int:
    for section in pe.sections:
        start = section.PointerToRawData
        end = start + section.SizeOfRawData
        if start <= offset < end:
            return section.VirtualAddress + offset - start
    raise ValueError(offset)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exe", type=Path)
    parser.add_argument("needles", nargs="+")
    args = parser.parse_args()

    data = args.exe.read_bytes()
    pe = pefile.PE(data=data, fast_load=True)
    targets: dict[int, tuple[str, int]] = {}
    for needle_text in args.needles:
        needle = needle_text.encode("ascii")
        for match in re.finditer(re.escape(needle), data):
            targets[file_offset_to_rva(pe, match.start())] = (needle_text, match.start())

    # REX + LEA/MOV r64,[RIP+disp32]. O filtro pelo alvo elimina coincidencias.
    candidates: list[tuple[int, int, int]] = []
    pattern = re.compile(rb"[\x40-\x4f][\x8b\x8d][\x05\x0d\x15\x1d\x25\x2d\x35\x3d][\x00-\xff]{4}")
    for section in pe.sections:
        if not (section.Characteristics & 0x20000000):
            continue
        blob = data[section.PointerToRawData : section.PointerToRawData + section.SizeOfRawData]
        for match in pattern.finditer(blob):
            insn_file = section.PointerToRawData + match.start()
            insn_rva = section.VirtualAddress + match.start()
            disp = struct.unpack_from("<i", match.group(), 3)[0]
            target_rva = insn_rva + 7 + disp
            if target_rva in targets:
                candidates.append((insn_rva, insn_file, target_rva))

    for target_rva, (needle, target_file) in sorted(targets.items()):
        print(f'TARGET {needle!r} rva={target_rva:#x} file={target_file:#x}')
        refs = [item for item in candidates if item[2] == target_rva]
        for insn_rva, insn_file, _ in refs:
            print(f"  XREF rva={insn_rva:#x} file={insn_file:#x}")
        if not refs:
            print("  XREF none (pode ser indireta ou receber relocacao)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
