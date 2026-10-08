"""Korean text codec, text_e.str / SSB string I/O and dense glyph re-encoding.

Source encoding (unofficial EoS Korean patch, TOP/ziti font):
  lead 0x88..0x9F + trail byte = ziti code; KS X 1001 syllable index
  idx = (lead - 0x89) * 188 + (trail - 0x40 - (trail > 0x7F)).
Game encoding written by this module (dense): glyph table index
  idx -> lead 0x88 + idx // 127, trail 0x80 + idx % 127 (trail never '[' or 0).
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field

LEAD_MIN = 0x88
LEAD_MAX = 0x9F
ZITI_BASE = 0x8800
ZITI_ENTRY = 0x1C
DENSE_LEAD_MAX = 0x9E
DENSE_PER_LEAD = 127
DENSE_CAPACITY = (DENSE_LEAD_MAX - LEAD_MIN + 1) * DENSE_PER_LEAD

_ESCAPE_RE = re.compile(r"\{([0-9A-F]{2}|[0-9A-F]{4})\}")


def _syllable(idx: int) -> str:
    return bytes([0xB0 + idx // 94, 0xA1 + idx % 94]).decode("euc-kr")


def _build_ziti_tables() -> tuple[dict[int, str], dict[str, list[int]]]:
    to_char: dict[int, str] = {}
    for lead in range(0x89, 0x96):
        for trail in range(0x40, 0xFD):
            if trail == 0x7F:
                continue
            idx = (lead - 0x89) * 188 + trail - 0x40 - (1 if trail > 0x7F else 0)
            if idx < 2350:
                to_char[(lead << 8) | trail] = _syllable(idx)
    # Duplicate glyphs for syllables whose trail byte is '[' (0x5B) or '\' (0x5C).
    for k in range(13):
        to_char[0x88A0 + k] = _syllable(k * 188 + 27)
        to_char[0x9640 + k] = _syllable(k * 188 + 28)
    to_char[0x965C] = "야"
    to_char[0x88AD] = "－"
    to_char[0x88AE] = "／"
    to_char[0x88AF] = "！"
    for i in range(10):
        to_char[0x88B0 + i] = chr(0xFF10 + i)
    for i in range(26):
        to_char[0x88C0 + i] = chr(0xFF21 + i)
        to_char[0x88DA + i] = chr(0xFF41 + i)
    for code, ch in zip(range(0x959F, 0x95A8), "〜→←↑↓♪─～○"):
        to_char[code] = ch
    from_char: dict[str, list[int]] = {}
    for code in sorted(to_char):
        from_char.setdefault(to_char[code], []).append(code)
    return to_char, from_char


ZITI_TO_CHAR, CHAR_TO_ZITI_CANDIDATES = _build_ziti_tables()

# cp1252 characters whose byte collides with Korean lead bytes 0x88..0x9F.
LEAD_BYTE_SANITIZE = {
    "ˆ": "^", "‰": "%", "Š": "S", "‹": "<", "Œ": "OE", "Ž": "Z",
    "‘": "'", "’": "'", "“": '"', "”": '"', "•": "*", "–": "-", "—": "-",
    "˜": "~", "™": "TM", "š": "s", "›": ">", "œ": "oe", "ž": "z", "Ÿ": "Y",
}


def _single_byte_char(b: int) -> str:
    try:
        return bytes([b]).decode("cp1252")
    except UnicodeDecodeError:
        return f"{{{b:02X}}}"


def decode_korean(raw: bytes) -> str:
    """Decode a string from the Korean patch (lead 0x88..0x9F = ziti code)."""
    out: list[str] = []
    i = 0
    n = len(raw)
    while i < n:
        b = raw[i]
        if LEAD_MIN <= b <= LEAD_MAX and i + 1 < n:
            code = (b << 8) | raw[i + 1]
            out.append(ZITI_TO_CHAR.get(code, f"{{{code:04X}}}"))
            i += 2
        elif b == 0x81 and i + 1 < n:
            out.append(_sjis_char(raw[i], raw[i + 1]))
            i += 2
        elif b < 0x80:
            out.append(chr(b))
            i += 1
        else:
            out.append(_single_byte_char(b))
            i += 1
    return "".join(out)


def _sjis_char(lead: int, trail: int) -> str:
    try:
        return bytes([lead, trail]).decode("shift_jis")
    except UnicodeDecodeError:
        return f"{{{(lead << 8) | trail:04X}}}"


def decode_english(raw: bytes) -> str:
    """Decode a vanilla/Alpha string (cp1252, SJIS 0x81xx symbols)."""
    out: list[str] = []
    i = 0
    n = len(raw)
    while i < n:
        b = raw[i]
        if b == 0x81 and i + 1 < n:
            out.append(_sjis_char(b, raw[i + 1]))
            i += 2
        elif b < 0x80:
            out.append(chr(b))
            i += 1
        else:
            out.append(_single_byte_char(b))
            i += 1
    return "".join(out)


def has_hangul(text: str) -> bool:
    return any("\uAC00" <= ch <= "\uD7A3" for ch in text)


# ---------------------------------------------------------------- dense encoder


def dense_code(idx: int) -> int:
    return ((LEAD_MIN + idx // DENSE_PER_LEAD) << 8) | (0x80 + idx % DENSE_PER_LEAD)


def glyph_is_blank(ziti: bytes, code: int) -> bool:
    off = (code - ZITI_BASE) * ZITI_ENTRY
    return not any(ziti[off + 4 : off + ZITI_ENTRY])


def char_ziti_code(ch: str, ziti: bytes) -> int | None:
    cands = CHAR_TO_ZITI_CANDIDATES.get(ch)
    if not cands:
        return None
    for code in cands:
        if not glyph_is_blank(ziti, code):
            return code
    return cands[0]


@dataclass
class EncodeStats:
    sanitized: dict[str, int] = field(default_factory=dict)
    unmapped: dict[str, int] = field(default_factory=dict)

    def bump(self, table: dict[str, int], key: str) -> None:
        table[key] = table.get(key, 0) + 1


class DenseEncoder:
    """Two-pass encoder: collect ziti codes, then assign dense game codes."""

    def __init__(self, ziti: bytes) -> None:
        self.ziti = ziti
        self.stats = EncodeStats()
        self._codes: set[int] = set()
        self._dense: dict[int, int] | None = None
        self._order: list[int] = []

    def _tokens(self, text: str, *, count: bool = True) -> list[int | bytes]:
        stats = self.stats if count else EncodeStats()
        toks: list[int | bytes] = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == "{":
                m = _ESCAPE_RE.match(text, i)
                if m:
                    val = int(m.group(1), 16)
                    if len(m.group(1)) == 4 and LEAD_MIN <= val >> 8 <= LEAD_MAX:
                        toks.append(val)
                    elif len(m.group(1)) == 4:
                        toks.append(bytes([val >> 8, val & 0xFF]))
                    elif LEAD_MIN <= val <= LEAD_MAX:
                        stats.bump(stats.unmapped, m.group(0))
                        toks.append(b"?")
                    else:
                        toks.append(bytes([val]))
                    i = m.end()
                    continue
            o = ord(ch)
            if o < 0x80:
                toks.append(bytes([o]))
                i += 1
                continue
            code = char_ziti_code(ch, self.ziti)
            if code is not None:
                toks.append(code)
                i += 1
                continue
            try:
                enc = ch.encode("cp1252")
            except UnicodeEncodeError:
                enc = b""
            if enc and not (LEAD_MIN <= enc[0] <= LEAD_MAX):
                toks.append(enc)
            elif ch in LEAD_BYTE_SANITIZE:
                stats.bump(stats.sanitized, ch)
                toks.append(LEAD_BYTE_SANITIZE[ch].encode("ascii"))
            else:
                try:
                    sj = ch.encode("shift_jis")
                except UnicodeEncodeError:
                    sj = b""
                if len(sj) == 2 and sj[0] == 0x81:
                    toks.append(sj)
                else:
                    stats.bump(stats.unmapped, ch)
                    toks.append(b"?")
            i += 1
        return toks

    def collect(self, text: str) -> None:
        if self._dense is not None:
            raise RuntimeError("collect after finalize")
        for tok in self._tokens(text, count=False):
            if isinstance(tok, int):
                self._codes.add(tok)

    def finalize(self) -> None:
        self._order = sorted(self._codes)
        if len(self._order) + 1 > DENSE_CAPACITY:
            raise RuntimeError(f"{len(self._order)} glyphs exceed dense capacity {DENSE_CAPACITY}")
        self._dense = {code: dense_code(i + 1) for i, code in enumerate(self._order)}

    def encode(self, text: str) -> bytes:
        if self._dense is None:
            raise RuntimeError("encode before finalize")
        out = bytearray()
        for tok in self._tokens(text):
            if isinstance(tok, int):
                d = self._dense[tok]
                out += bytes([d >> 8, d & 0xFF])
            else:
                out += tok
        return bytes(out)

    @property
    def glyph_count(self) -> int:
        return len(self._order) + 1

    def glyph_table(self) -> bytes:
        if self._dense is None:
            raise RuntimeError("glyph_table before finalize")
        blank = bytearray(ZITI_ENTRY)
        if self._order:
            first = (self._order[0] - ZITI_BASE) * ZITI_ENTRY
            blank[:4] = self.ziti[first : first + 4]
        table = bytearray(blank)
        for code in self._order:
            off = (code - ZITI_BASE) * ZITI_ENTRY
            table += self.ziti[off : off + ZITI_ENTRY]
        return bytes(table)


# ---------------------------------------------------------------- text_e.str


def parse_str_file(data: bytes) -> list[bytes]:
    """Raw strings of a PMD2 .str file (index = n pointers + end marker)."""
    count = struct.unpack_from("<I", data, 0)[0] // 4 - 1
    ptrs = list(struct.unpack_from(f"<{count}I", data, 0))
    out: list[bytes] = []
    for p in ptrs:
        e = data.index(b"\0", p)
        out.append(bytes(data[p:e]))
    return out


def build_str_file(strings: list[bytes]) -> bytes:
    index_len = 4 * (len(strings) + 1)
    head = bytearray()
    body = bytearray()
    for s in strings:
        head += struct.pack("<I", index_len + len(body))
        body += s + b"\0"
    head += struct.pack("<I", index_len + len(body))
    return bytes(head + body)


# ---------------------------------------------------------------- SSB strings

_SSB_HDR = 0x0C


@dataclass
class SsbStrings:
    str_table: int
    start_const_table: int
    end: int
    strings: list[bytes]


def parse_ssb_strings(data: bytes, *, strict: bool = True) -> SsbStrings:
    nconst, nstr, cstart_w = struct.unpack_from("<3H", data, 0)
    start_const_table = _SSB_HDR + struct.unpack_from("<H", data, _SSB_HDR)[0] * 2
    cursor = _SSB_HDR + cstart_w * 2
    for i in range(nconst):
        o = start_const_table + struct.unpack_from("<H", data, start_const_table + i * 2)[0] - nstr * 2
        if strict and cursor != o:
            raise ValueError(f"ssb constant {i} @ {o:#x}, expected {cursor:#x}")
        cursor = data.index(b"\0", o) + 1
    if cursor % 2:
        cursor += 1
    str_table = cursor
    cursor = str_table + nstr * 2
    strings: list[bytes] = []
    for i in range(nstr):
        o = start_const_table + struct.unpack_from("<H", data, str_table + i * 2)[0]
        if strict and cursor != o:
            raise ValueError(f"ssb string {i} @ {o:#x}, expected {cursor:#x}")
        e = data.find(b"\0", o)
        if e == -1:
            if strict:
                raise ValueError(f"ssb string {i} unterminated")
            e = len(data)
        strings.append(bytes(data[o:e]))
        cursor = max(cursor, e + 1)
    return SsbStrings(str_table, start_const_table, cursor, strings)


def rebuild_ssb_strings(data: bytes, strings: list[bytes]) -> bytes:
    p = parse_ssb_strings(data)
    nstr = len(p.strings)
    if len(strings) != nstr:
        raise ValueError(f"ssb string count {len(strings)} != {nstr}")
    table = bytearray()
    body = bytearray()
    cursor = p.str_table + nstr * 2
    for s in strings:
        rel = cursor + len(body) - p.start_const_table
        if rel >= 0x10000:
            raise ValueError("ssb string block exceeds 64 KiB")
        table += struct.pack("<H", rel)
        body += s + b"\0"
    block = table + body
    if len(block) % 2:
        block += b"\0"
    tail = bytes(data[p.end :])
    if (p.end - p.str_table) % 2 and tail[:1] == b"\0":
        tail = tail[1:]
    out = bytearray(data[: p.str_table] + block + tail)
    struct.pack_into("<H", out, 8, len(block) // 2)
    return bytes(out)


def rom_paths(rom, prefix: str = "", suffix: str = "") -> list[str]:
    out: list[str] = []

    def walk(folder, base: str) -> None:
        for name in folder.files:
            path = base + name
            if path.startswith(prefix) and path.endswith(suffix):
                out.append(path)
        for name, sub in folder.folders:
            walk(sub, base + name + "/")

    walk(rom.filenames, "")
    return out
