"""Desmonta trechos do executavel do eFootball por RVA, sem alterar arquivos.

Anota alvos RIP-relative e textos ASCII/UTF-16 para facilitar a auditoria do
fluxo de LiveData. Uso: python desmontar_rva.py eFootball.exe RVA [RVA...].
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP


def rva_to_offset(pe: pefile.PE, rva: int) -> int:
    return pe.get_offset_from_rva(rva)


def printable_ascii(data: bytes, offset: int) -> str | None:
    if not 0 <= offset < len(data):
        return None
    end = data.find(b"\x00", offset, min(len(data), offset + 240))
    if end < 0:
        return None
    raw = data[offset:end]
    if len(raw) < 4 or any(byte < 0x20 or byte > 0x7E for byte in raw):
        return None
    return raw.decode("ascii")


def printable_utf16(data: bytes, offset: int) -> str | None:
    if not 0 <= offset < len(data) - 8:
        return None
    chars = bytearray()
    for pos in range(offset, min(len(data) - 1, offset + 480), 2):
        lo, hi = data[pos], data[pos + 1]
        if lo == 0 and hi == 0:
            break
        if hi != 0 or lo < 0x20 or lo > 0x7E:
            return None
        chars.append(lo)
    return chars.decode("ascii") if len(chars) >= 4 else None


def annotation(pe: pefile.PE, data: bytes, target_rva: int) -> str:
    try:
        offset = rva_to_offset(pe, target_rva)
    except Exception:
        return ""
    value = printable_ascii(data, offset) or printable_utf16(data, offset)
    return f' ; -> {target_rva:#x} "{value}"' if value else f" ; -> {target_rva:#x}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exe", type=Path)
    parser.add_argument("rvas", nargs="+", type=lambda value: int(value, 0))
    parser.add_argument("--bytes", type=lambda value: int(value, 0), default=0x180)
    parser.add_argument("--all", action="store_true", help="continua depois do primeiro ret")
    args = parser.parse_args()

    data = args.exe.read_bytes()
    pe = pefile.PE(data=data, fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True

    for start_rva in args.rvas:
        offset = rva_to_offset(pe, start_rva)
        print(f"RVA {start_rva:#x} FILE {offset:#x}")
        for insn in decoder.disasm(data[offset : offset + args.bytes], image_base + start_rva):
            note = ""
            for operand in insn.operands:
                if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
                    target_va = insn.address + insn.size + operand.mem.disp
                    note = annotation(pe, data, target_va - image_base)
                    break
                if operand.type == X86_OP_IMM and image_base <= operand.imm < image_base + pe.OPTIONAL_HEADER.SizeOfImage:
                    note = annotation(pe, data, operand.imm - image_base)
                    break
            print(f"  {insn.address - image_base:08x}: {insn.mnemonic:8} {insn.op_str}{note}")
            if insn.mnemonic == "ret" and not args.all:
                break
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
