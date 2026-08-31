"""Mapeia RTTI/vtables relacionadas ao LiveData no executavel do eFootball.

Ferramenta estritamente somente leitura: abre o PE instalado, resolve os
Complete Object Locators do MSVC x64 e lista as funcoes virtuais apontadas.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

import pefile


DEFAULT_TYPES = (
    "LiveDataManager@onlinemode@@",
    "LiveDataDownloader@onlinemode@@",
    "LiveDataLoader@onlinemode@@",
    "LiveDataBinder@onlinemode@@",
    "LiveDataVersionLoader@onlinemode@@",
    "LiveDataHashChecker@onlinemode@@",
    "LiveDataInfo@onlinemode@@",
    "CommandObjectCmdGetLivedata@command@@",
    "OnlineSystemHttpAes@onlinesystem@@",
)


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def section_for_rva(pe: pefile.PE, rva: int):
    for section in pe.sections:
        start = section.VirtualAddress
        end = start + max(section.Misc_VirtualSize, section.SizeOfRawData)
        if start <= rva < end:
            return section
    return None


def section_name(section) -> str:
    return section.Name.rstrip(b"\x00").decode("ascii", "replace") if section else "?"


def file_offset_to_rva(pe: pefile.PE, offset: int) -> int:
    for section in pe.sections:
        start = section.PointerToRawData
        end = start + section.SizeOfRawData
        if start <= offset < end:
            return section.VirtualAddress + offset - start
    if offset < pe.OPTIONAL_HEADER.SizeOfHeaders:
        return offset
    raise ValueError(f"offset fora das secoes: {offset:#x}")


def find_all(data: bytes, needle: bytes):
    start = 0
    while True:
        found = data.find(needle, start)
        if found < 0:
            return
        yield found
        start = found + 1


def runtime_function(pe: pefile.PE, rva: int) -> tuple[int, int] | None:
    entries = getattr(pe, "DIRECTORY_ENTRY_EXCEPTION", ())
    lo, hi = 0, len(entries)
    while lo < hi:
        mid = (lo + hi) // 2
        begin = entries[mid].struct.BeginAddress
        if begin <= rva:
            lo = mid + 1
        else:
            hi = mid
    if lo:
        item = entries[lo - 1].struct
        if item.BeginAddress <= rva < item.EndAddress:
            return item.BeginAddress, item.EndAddress
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exe", type=Path)
    parser.add_argument("types", nargs="*", default=list(DEFAULT_TYPES))
    args = parser.parse_args()

    data = args.exe.read_bytes()
    pe = pefile.PE(data=data, fast_load=False)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    executable_ranges = [
        (
            section.VirtualAddress,
            section.VirtualAddress + max(section.Misc_VirtualSize, section.SizeOfRawData),
        )
        for section in pe.sections
        if section.Characteristics & 0x20000000  # IMAGE_SCN_MEM_EXECUTE
    ]

    for requested in args.types:
        encoded_names = [
            (".?AV" + requested).encode("ascii"),
            (".?AU" + requested).encode("ascii"),
        ]
        string_offsets = sorted(
            offset for encoded in encoded_names for offset in find_all(data, encoded)
        )
        print(f"TYPE {requested} occurrences={len(string_offsets)}")
        for string_offset in string_offsets:
            string_rva = file_offset_to_rva(pe, string_offset)
            type_descriptor_rva = string_rva - 16
            print(
                f"  name_file={string_offset:#x} name_rva={string_rva:#x} "
                f"type_descriptor_rva={type_descriptor_rva:#x}"
            )
            td_marker = struct.pack("<I", type_descriptor_rva)
            for marker_offset in find_all(data, td_marker):
                if marker_offset < 12:
                    continue
                col_offset = marker_offset - 12
                try:
                    col_rva = file_offset_to_rva(pe, col_offset)
                except ValueError:
                    continue
                if u32(data, col_offset) != 1 or u32(data, col_offset + 20) != col_rva:
                    continue
                col_va = image_base + col_rva
                print(
                    f"    COL file={col_offset:#x} rva={col_rva:#x} "
                    f"class_descriptor_rva={u32(data, col_offset + 16):#x}"
                )
                col_pointer = struct.pack("<Q", col_va)
                for col_ref_offset in find_all(data, col_pointer):
                    try:
                        col_ref_rva = file_offset_to_rva(pe, col_ref_offset)
                    except ValueError:
                        continue
                    holder_section = section_for_rva(pe, col_ref_rva)
                    # Este executavel usa secoes nao convencionais (.xcode/.data2)
                    # e mantem RTTI/vtables nelas; nao limitar a .rdata/.data.
                    if holder_section is None:
                        continue
                    vtable_offset = col_ref_offset + 8
                    vtable_rva = file_offset_to_rva(pe, vtable_offset)
                    entries: list[str] = []
                    for index in range(64):
                        function_va = u64(data, vtable_offset + index * 8)
                        function_rva = function_va - image_base
                        if not any(start <= function_rva < end for start, end in executable_ranges):
                            break
                        bounds = runtime_function(pe, function_rva)
                        bound_text = ""
                        if bounds:
                            bound_text = f" fn={bounds[0]:#x}-{bounds[1]:#x}"
                        entries.append(f"      [{index:02d}] rva={function_rva:#x}{bound_text}")
                    if entries:
                        print(
                            f"    VTABLE holder_file={col_ref_offset:#x} "
                            f"vtable_rva={vtable_rva:#x} "
                            f"section={section_name(holder_section)} entries={len(entries)}"
                        )
                        print("\n".join(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
