from __future__ import annotations

import struct
from typing import Any

from .manifest import resolve_symbol


def hook_word_kind(word: int) -> str | None:
    top = word >> 24
    if top == 0xEA:
        return "b"
    if top == 0xEB:
        return "bl"
    return None


def branch_target(pc: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def resolve_prior_target(site: int, word: int, hook: dict[str, Any]) -> int:
    """Prior callee for chain=append. Vanilla non-branches use hook['vanilla_resume']."""
    if hook_word_kind(word) in ("b", "bl"):
        return branch_target(site, word)
    resume = hook.get("vanilla_resume")
    if resume is None:
        raise RuntimeError(
            f"hook {hook.get('name', '?')} @ {site:#x} is not a branch to chain "
            f"({word:#010x})"
        )
    if isinstance(resume, str):
        return int(resume, 16)
    return int(resume)


def assert_hooks_on_binary(
    binary: bytes,
    load_address: int,
    hooks: list[dict[str, Any]],
    profile: dict[str, Any],
    prior_hook_sites: set[int],
) -> None:
    assert_hooks_available(binary, load_address, hooks, profile, prior_hook_sites)


def assert_hooks_available(
    overlay: bytes,
    overlay_load: int,
    hooks: list[dict[str, Any]],
    profile: dict[str, Any],
    prior_hook_sites: set[int],
) -> None:
    for hook in hooks:
        chain = hook.get("chain", "first")
        symbol = hook["symbol"]
        site = resolve_symbol(profile, symbol)
        off = site - overlay_load
        if off < 0 or off + 4 > len(overlay):
            raise RuntimeError(f"hook site {symbol} @ {site:#x} out of overlay range")
        if site in prior_hook_sites and chain == "first":
            raise RuntimeError(
                f"hook {hook['name']} @ {site:#x} already used; need chain=append"
            )
        word = struct.unpack_from("<I", overlay, off)[0]
        if chain == "append" and site in prior_hook_sites:
            kind = hook_word_kind(word)
            if kind not in ("b", "bl"):
                raise RuntimeError(
                    f"hook {hook['name']} @ {site:#x}: chain=append expects prior "
                    f"branch/bl, found {word:#010x}"
                )
            continue
        if "vanilla_word" in hook:
            expected = hook["vanilla_word"]
            if isinstance(expected, str):
                expected = int(expected, 16)
            if word != expected:
                raise RuntimeError(
                    f"hook {hook['name']} @ {site:#x}: expected {expected:#010x}, found {word:#010x}"
                )
            continue
        expected = hook.get("replace")
        if expected:
            kind = hook_word_kind(word)
            if kind != expected:
                raise RuntimeError(
                    f"hook {hook['name']} @ {site:#x}: expected {expected}, "
                    f"found {kind or hex(word)}"
                )


def collect_hook_records(
    hooks: list[dict[str, Any]],
    profile: dict[str, Any],
    cave_load: int,
) -> list[dict[str, Any]]:
    records = []
    for hook in hooks:
        site = resolve_symbol(profile, hook["symbol"])
        records.append(
            {
                "name": hook["name"],
                "site": site,
                "kind": hook.get("replace") or "overwrite",
                "target_symbol": hook.get("target_symbol", hook["name"]),
                "chain": hook.get("chain", "first"),
                "cave_load_hint": cave_load,
            }
        )
    return records
