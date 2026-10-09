"""Build the resident doping codec and inject its one-time import choice."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from skytemple_files.script.ssb.handler import SsbHandler
from skytemple_files.script.ssb.model import SkyTempleSsbOperation

PROMPT = (
    "Which ROM created this save?\nAlpha: reset old stats to zero doping.\nAlpha+: keep existing permanent doping.",
    "Keep Alpha+ doping",
    "Import original Alpha",
)


def build_runtime(module_dir: Path, work: Path, cave: int, calc_stat: int) -> tuple[Path, str]:
    compiler = os.environ.get("ARM_GCC") or shutil.which("arm-none-eabi-gcc")
    if not compiler:
        candidate = Path("C:/msys64/mingw64/bin/arm-none-eabi-gcc.exe")
        if candidate.is_file():
            compiler = str(candidate)
    if not compiler:
        raise RuntimeError("spinda_ev_speed requires arm-none-eabi-gcc (or ARM_GCC)")
    prefix = str(Path(compiler).with_name("arm-none-eabi-"))
    suffix = ".exe" if compiler.endswith(".exe") else ""
    defines = {"STATE_ADDRESS": cave + 0x1D00, "ORIGINAL_READ": cave + 0x800,
               "ORIGINAL_WRITE": cave + 0x810, "ORIGINAL_COPY": cave + 0x820,
               "ORIGINAL_MONSTERS": cave + 0x830, "CALC_STAT": calc_stat}
    (work / "generated.h").write_text(
        "".join(f"#define {name} 0x{addr:X}\n" for name, addr in defines.items()),
        encoding="ascii",
    )
    linker = work / "save_v1.ld"
    linker.write_text(
        f"SECTIONS {{ . = 0x{cave + 0x1000:X}; "
        ".text : { *(.text*) *(.rodata*) } "
        "/DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } }",
        encoding="ascii",
    )
    elf = work / "save_v1.elf"
    command = [compiler, "-mcpu=arm946e-s", "-marm", "-Os", "-ffreestanding",
               "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
               "-nostdlib", "-Wall", "-Wextra", "-Werror", "-I", str(work),
               str(module_dir / "runtime/save_v1.c"), "-Wl,-T," + str(linker),
               "-o", str(elf)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    output = work / "save_v1.bin"
    subprocess.run([prefix + "objcopy" + suffix, "-O", "binary", str(elf), str(output)], check=True)
    if output.stat().st_size > 0xD00:
        raise RuntimeError("doping save runtime exceeds allocated cave")
    symbols = subprocess.check_output([prefix + "nm" + suffix, "--defined-only", str(elf)], text=True)
    labels = []
    for line in symbols.splitlines():
        address, kind, name = line.split()
        if name.startswith("EvSave_") and kind == "T":
            labels.append(f".definelabel {name}, 0x{address}\n")
    return output, "".join(labels)


def patch_import_prompt(rom, config) -> list[int]:
    path = "SCRIPT/COMMON/unionall.ssb"
    ssb = SsbHandler.deserialize(rom.getFileByName(path), static_data=config)
    if any(op.op_code.name == "ProcessSpecial" and op.params[0] == 240
           for ops in ssb.routine_ops for op in ops):
        return []
    opcodes = config.script_data.op_codes__by_name
    start = ssb.routine_ops[68][0].offset
    if ssb.routine_ops[68][0].params != [119, 0, 0]:
        raise RuntimeError("Alpha updater coroutine changed; refusing unsafe insertion")
    # These process IDs must be unused by the input ROM.
    for ops in ssb.routine_ops:
        for op in ops:
            if op.op_code.name == "ProcessSpecial" and op.params[0] in (240, 241, 242):
                raise RuntimeError("doping migration special-process ID collision")
    index = len(next(iter(ssb.strings.values())))
    for strings in ssb.strings.values():
        strings.extend(PROMPT)
    texts = [len(ssb.constants) + index + i for i in range(3)]
    # Menu cancellation loops back; no implicit import choice.
    template = [
        ("ProcessSpecial", [240, 0, 0]), ("Case", [0, "done"]),
        ("message_Mail", [texts[0]]), ("message_SwitchMenu", [0, 2]),
        ("CaseMenu", [texts[1], "keep"]), ("CaseMenu", [texts[2], "import"]),
        ("Jump", ["again"]), ("message_Close", []),
        ("ProcessSpecial", [242, 0, 0]), ("Jump", ["done"]),
        ("message_Close", []), ("ProcessSpecial", [241, 0, 0]),
    ]
    lengths = [1 + len(args) for _, args in template]
    extra = sum(lengths)
    positions = []; position = start
    for size in lengths:
        positions.append(position); position += size
    labels = {"again": start, "keep": positions[7], "import": positions[10], "done": position}
    # Offsets are in words in operations, but bytes in routine_info.
    for ops in ssb.routine_ops:
        for op in ops:
            if op.offset >= start:
                op.offset += extra
            for argument in op.op_code.arguments:
                if argument.name == "jump_address" and op.params[argument.id] >= start:
                    op.params[argument.id] += extra
    ssb.routine_info = [(offset + (extra * 2 if offset > start * 2 else 0), info)
                        for offset, info in ssb.routine_info]
    inserted = [SkyTempleSsbOperation(offset, next(code for code in opcodes[name] if code.params == len(args)),
                [labels.get(value, value) if isinstance(value, str) else value for value in args])
                for offset, (name, args) in zip(positions, template)]
    ssb.routine_ops[68][:0] = inserted
    rom.setFileByName(path, SsbHandler.serialize(ssb, static_data=config))
    return list(range(index, index + len(PROMPT)))
