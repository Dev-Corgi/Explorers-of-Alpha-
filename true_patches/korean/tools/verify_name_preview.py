"""Exercise live name redraw, cursor metrics and keyboard assembly on ARM."""
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
import yaml
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from patch_engine.armips_runner import run_armips_bundle
from patch_engine.apply_korean import check_arm9_patched

MODULE = ROOT / 'true_patches/korean'
ROM = ROOT / 'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds'
KEY, ASCII, WINDOW, RETURN, SP = 0x02100000, 0x02101000, 0x02102000, 0x02103000, 0x02703000
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12]


class Preview:
    def __init__(self, simulate=False):
        rom = NintendoDSRom.fromFile(str(ROM))
        ov = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])[36]
        arm9, overlay = bytes(rom.arm9), bytes(ov.data)
        cfg = yaml.safe_load((MODULE / 'manifest.yaml').read_text(encoding='utf-8'))
        if simulate:
            offset = (len(overlay) + 3) & ~3
            cave = ov.ramAddress + offset
            with tempfile.TemporaryDirectory(prefix='ko_name_preview_') as tmp:
                work = Path(tmp)
                a, o, g = work / 'arm9.bin', work / 'overlay_0036.bin', work / 'generated.inc'
                a.write_bytes(arm9)
                o.write_bytes(overlay.ljust(offset + cfg['cave']['code_bytes'], b'\0'))
                g.write_text(f'.definelabel KoreanCaveAddress, 0x{cave:X}\n'
                             f"KoreanCaveSize equ {cfg['cave']['code_bytes']}\n"
                             '.definelabel KoGlyphTable, 0x023E0000\n'
                             f"KoGlyphCount equ {len(rom.getFileByName('FONT/ko_glyph.bin')) // 28}\n", encoding='utf-8')
                run_armips_bundle(armips=ROOT / 'tools/armips.exe', asm_dir=MODULE / 'asm',
                                  asm_entry='main.asm', binaries={'arm9.bin': a, 'overlay_0036.bin': o}, generated_inc=g)
                arm9, overlay = a.read_bytes(), o.read_bytes()
            check_arm9_patched(arm9, cfg['arm9_sites'], cave, cave + cfg['cave']['code_bytes'])
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x02000000, 0x400000)
        self.uc.mem_map(0x02700000, 0x4000)
        self.uc.mem_write(0x02000000, arm9)
        self.uc.mem_write(ov.ramAddress, overlay)
        self.uc.mem_write(0x020AFDF0, struct.pack('<I', KEY))
        self.uc.mem_write(ASCII, bytes([0, 0, 8, 0]) + bytes(28))
        self.glyphs = rom.getFileByName('FONT/ko_glyph.bin')
        self.draws, self.codes = [], []
        self.uc.hook_add(UC_HOOK_CODE, self.service)

    def ret(self, value=0):
        self.uc.reg_write(UC_ARM_REG_R0, value)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def cstring(self, addr):
        out = bytearray()
        for i in range(128):
            b = self.uc.mem_read(addr + i, 1)[0]
            if not b:
                return bytes(out)
            out.append(b)
        raise AssertionError('unterminated string')

    def service(self, uc, address, _size, _data):
        if address == RETURN:
            uc.emu_stop()
        elif address == 0x02025C80:
            # Real dense lookup runs; supply the stock ASCII font service only.
            sp = uc.reg_read(UC_ARM_REG_SP)
            saved = struct.unpack('<5I', uc.mem_read(sp, 20))
            for reg, val in zip((UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7), saved):
                uc.reg_write(reg, val)
            uc.reg_write(UC_ARM_REG_SP, sp + 20)
            uc.reg_write(UC_ARM_REG_R0, ASCII)
            uc.reg_write(UC_ARM_REG_PC, saved[4])
        elif address in (0x02089584, 0x02037F30):
            # Capture the real redraw's %c argument before the UI formatter.
            code = uc.reg_read(UC_ARM_REG_R2)
            self.codes.append(code)
            text = bytes([code >> 8, code & 255]) if code >= 0x100 else bytes([code])
            uc.mem_write(uc.reg_read(UC_ARM_REG_R0), text + b'\0')
            self.ret(len(text))
        elif address == 0x02026214:
            text = self.cstring(uc.reg_read(UC_ARM_REG_R3))
            if text.startswith(b'[CS:'):
                assert text[5:6] == b']' and text.endswith(b'[CR]'), text
                text = text[6:-4]
            self.draws.append((uc.reg_read(UC_ARM_REG_R1), text))
            self.ret()
        elif address == 0x020264F8:
            # Stock single-character path must only receive ASCII.
            code = uc.reg_read(UC_ARM_REG_R3)
            assert code < 0x8800, hex(code)
            self.draws.append((uc.reg_read(UC_ARM_REG_R1), bytes([code & 255])))
            self.ret()
        elif address in (0x02027B1C, 0x02025D50, 0x02017CCC):
            self.ret()
        elif address == 0x02038B5C:
            self.ret(0)
        elif address == 0x020275F8:
            self.ret(WINDOW)

    def call(self, address, **values):
        for reg in REGS:
            self.uc.reg_write(reg, 0)
        self.uc.reg_write(UC_ARM_REG_SP, SP)
        self.uc.reg_write(UC_ARM_REG_LR, RETURN)
        for name, value in values.items():
            self.uc.reg_write(REGS[int(name[1:])], value)
        self.uc.emu_start(address, RETURN, count=100000)
        assert self.uc.reg_read(UC_ARM_REG_PC) == RETURN
        assert self.uc.reg_read(UC_ARM_REG_SP) == SP

    def reset(self, text, mode=0):
        self.uc.mem_write(KEY, bytes(0x400))
        self.uc.mem_write(KEY + 0xF8, struct.pack('<I', KEY + 0xFC))
        self.uc.mem_write(KEY + 0xFC, text + b'\0')
        self.uc.mem_write(KEY + 0xC, struct.pack('<I', mode))
        self.uc.mem_write(KEY + 0x1B, b'\x0a')
        self.draws, self.codes = [], []


def main():
    p = Preview('--simulate' in sys.argv)
    # All actual glyph codes: byte order and per-byte cursor coordinates.
    count = len(p.glyphs) // 28
    for idx in range(1, count):
        lead, trail = 0x88 + idx // 127, 0x80 + idx % 127
        text = bytes([lead, trail]) + b'A'
        p.reset(text)
        p.call(0x02038ADC)
        positions = struct.unpack('<4H', p.uc.mem_read(KEY + 0x20, 8))
        width = p.glyphs[idx * 28 + 2]
        assert positions == (0, 0, width, width + 8), (idx, positions, width)
        p.call(0x02037F58, r0=0)
        assert p.draws[0][1] == text[:2], (idx, p.draws[:2])
        assert p.draws[1][1] == b'A', (idx, p.draws[:2])
    # Name types select both text and single-glyph paths, including 54-byte layouts.
    for mode in range(10):
        p.reset(b'A\x88\xa7\x89\x80B', mode)
        p.call(0x02037F58, r0=0)
        visible = [text for _, text in p.draws if text and text != b'\0']
        assert visible[:4] == [b'A', b'\x88\xa7', b'\x89\x80', b'B'], (mode, visible)
    # Actual keyboard key handler joins the first symbol pair and redraws immediately.
    p.reset(b'\xa1')
    p.uc.mem_write(KEY + 0x1C, b'\x01')
    key = next(i for i in range(84) if struct.unpack('<H', p.uc.mem_read(0x0209BF18 + i * 10 + 8, 2))[0] == 0xA1)
    p.uc.mem_write(KEY + 0x18, bytes([key]))
    p.call(0x020384B0)
    assert p.cstring(KEY + 0xFC) == b'\x88\xa7'
    assert p.draws[0][1] == b'\x88\xa7'
    p.call(0x020384B0)
    p.call(0x020384B0)
    assert p.cstring(KEY + 0xFC) == b'\x88\xa7\x88\xa7'
    p.draws = []
    p.call(0x02038904)
    assert p.cstring(KEY + 0xFC) == b'\x88\xa7'
    p.call(0x02038904)
    assert p.cstring(KEY + 0xFC) == b''
    assert p.uc.mem_read(KEY + 0x1C, 1) == b'\0'
    print(f'PASS: {count - 1} glyph previews/cursor metrics, 10 layouts, real pair input and deletion')


if __name__ == '__main__':
    main()
