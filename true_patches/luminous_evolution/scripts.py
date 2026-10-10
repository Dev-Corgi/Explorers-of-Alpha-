"""Reviewable SSB edits. No precompiled/extracted script binaries are bundled."""
from __future__ import annotations

from skytemple_files.script.ssb.handler import SsbHandler
from skytemple_files.script.ssb.model import SkyTempleSsbOperation


def rewrite(ssb, config, edits):
    """Replace word-offset ranges and relocate all engine-declared jump operands.

    An edit is (start, end, [(opcode, params), ...]); routine headers use bytes,
    while operation offsets and branch destinations use words.
    """
    edits = sorted(edits)
    for left, right in zip(edits, edits[1:]):
        if left[1] > right[0]:
            raise ValueError("overlapping SSB edits")
    mapping = {}
    labels = {}
    new_routines = []
    cursor = 2 + 3 * len(ssb.routine_info)
    by_start = {start: (end, items) for start, end, items in edits}
    consumed = set()
    for ops in ssb.routine_ops:
        result = []
        skip_to = -1
        replacement_start = cursor
        for old in ops:
            if old.offset < skip_to:
                mapping[old.offset] = replacement_start
                continue
            mapping[old.offset] = cursor
            if old.offset in by_start:
                skip_to, items = by_start[old.offset]
                replacement_start = cursor
                consumed.add(old.offset)
                for name, params in items:
                    if name == "label":
                        label = params[0]
                        if label in labels:
                            raise ValueError(f"duplicate SSB replacement label: {label}")
                        labels[label] = cursor
                        continue
                    codes = config.script_data.op_codes__by_name[name]
                    code = next(c for c in codes if c.params in (len(params), -1))
                    op = SkyTempleSsbOperation(cursor, code, list(params))
                    result.append(op)
                    cursor += 1 + len(params) + (code.params == -1)
                continue
            result.append(SkyTempleSsbOperation(cursor, old.op_code, list(old.params)))
            cursor += 1 + len(old.params) + (old.op_code.params == -1)
        new_routines.append(result)
    if consumed != set(by_start):
        raise RuntimeError("SSB edit anchor disappeared")
    # Alias routines retain their original target (including empty aliases).
    ssb.routine_info = [(mapping[offset // 2] * 2, info)
                        for offset, info in ssb.routine_info]
    for ops in new_routines:
        for op in ops:
            for arg in op.op_code.arguments:
                if arg.name == "jump_address":
                    destination = op.params[arg.id]
                    if isinstance(destination, str):
                        if destination not in labels:
                            raise RuntimeError(f"undefined SSB replacement label: {destination}")
                        op.params[arg.id] = labels[destination]
                        continue
                    if destination not in mapping:
                        raise RuntimeError(f"invalid SSB branch {destination:#x}")
                    op.params[arg.id] = mapping[destination]
    ssb.routine_ops = new_routines


def first_visit_menu(rom, config):
    """Reuse the actual Spring menu/result handshake and appearance events.

    Menu 21 starts the controller asynchronously. Menu 22 waits for its result;
    results 1..4 request visual/actor work before waiting again. Only result 0
    permits the story to continue after the controller closes its windows.
    """
    native = SsbHandler.deserialize(rom.getFileByName("SCRIPT/P14P01A/evolve.ssb"),
                                    static_data=config)
    ops = [op for op in native.routine_ops[0] if 0x27 <= op.offset < 0x60]
    if ([(op.op_code.name, op.params) for op in ops[:2]] !=
            [("message_Menu", [21]), ("message_Menu", [22])] or
            [(op.op_code.name, op.params[0]) for op in ops[2:6]] !=
            [("Case", i) for i in range(1, 5)]):
        raise RuntimeError("native Spring menu/result sequence changed")
    labels = {0x29: "spring_wait", 0x39: "spring_flash", 0x4D: "spring_fade",
              0x52: "spring_refresh", 0x5A: "spring_resume", 0x60: "spring_done"}
    items = []
    for op in ops:
        if op.offset in labels:
            items.append(("label", [labels[op.offset]]))
        params = list(op.params)
        for arg in op.op_code.arguments:
            if arg.name == "jump_address":
                if params[arg.id] not in labels:
                    raise RuntimeError("native Spring result branch changed")
                params[arg.id] = labels[params[arg.id]]
        items.append((op.op_code.name, params))
    items.append(("label", ["spring_done"]))
    return items


def apply_scripts(rom, config, texts):
    changed = {}
    for path, entries in texts["scripts"].items():
        ssb = SsbHandler.deserialize(rom.getFileByName(path), static_data=config)
        if path in texts.get("constant_dialogues", []):
            # Alpha's mail is stored in the language-neutral constant table.
            # Move its used dialogue into the language string block so the
            # normal Korean exact-match translator can translate it too.
            if any(ssb.strings.values()) or len(ssb.constants) != len(entries):
                raise RuntimeError("Alpha mail constant layout changed")
            for index, entry in entries.items():
                if ssb.constants[int(index)] != entry["before"]:
                    raise RuntimeError("Alpha mail constant text changed")
            for strings in ssb.strings.values():
                strings.extend(ssb.constants)
            for ops in ssb.routine_ops:
                for op in ops:
                    if op.op_code.name == "message_Mail":
                        if str(op.params[0]) not in entries:
                            raise RuntimeError("unexpected Alpha mail dialogue reference")
                        op.params[0] += len(ssb.constants)
        for strings in ssb.strings.values():
            for index, entry in entries.items():
                index = int(index)
                if strings[index] != entry["before"]:
                    raise RuntimeError(f"story text changed: {path}#{index}")
                strings[index] = entry["en"]
        if path == "SCRIPT/P14P01A/s01p1005.ssb":
            ops = {op.offset: op for op in ssb.routine_ops[0]}
            if (ops[0x1A4].op_code.name != "lives" or
                    ops[0x2DF].op_code.name != "message_EmptyActor"):
                raise RuntimeError("first Spring scene changed")
            # Teddiursa's evolution and partner's conditional invitation remain.
            # Wait through the native controller's result/appearance loop before
            # resuming the warning, including its no-eligible-Pokemon dialog.
            items = [
                ("message_Close", []), ("message_EmptyActor", []),
                ("message_Talk", [64]), ("message_Close", []),
            ] + first_visit_menu(rom, config) + [
                ("message_Close", []), ("screen_FadeIn", [1, 30]),
                ("bgm_PlayFadeIn", [14, 0, 256]),
            ]
            rewrite(ssb, config, [(0x1A4, 0x2DF, items)])
        rom.setFileByName(path, SsbHandler.serialize(ssb, static_data=config))
        changed[path] = [int(i) for i in entries]

    for path in ("SCRIPT/COMMON/unionall.ssb", "SCRIPT/D01P11A/us2306.ssb"):
        ssb = SsbHandler.deserialize(rom.getFileByName(path), static_data=config)
        edits = []
        for ops in ssb.routine_ops:
            for j, op in enumerate(ops):
                if op.op_code.name != "item_Set" or op.params[1] not in (427, 428):
                    continue
                pair = ops[j+1:j+3]
                if len(pair) != 2 or any(p.op_code.name != "message_Menu" or
                                        p.params != [64] for p in pair):
                    raise RuntimeError("Ascend Stone reward sequence changed")
                end = pair[-1].offset + 2
                edits.append((op.offset, end, []))
        if not edits:
            raise RuntimeError(f"Ascend Stone reward missing: {path}")
        rewrite(ssb, config, edits)
        rom.setFileByName(path, SsbHandler.serialize(ssb, static_data=config))
        changed[path] = {"removed_stone_rewards": len(edits)}
    return changed
