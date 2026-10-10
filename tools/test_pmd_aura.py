"""Meaningful invariants for source preservation and SpriteCollab packaging."""
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from pmd_aura import batch, build, color_ramp, parser, render_frame


class AuraTests(unittest.TestCase):
    def frame(self):
        source = np.zeros((20, 20, 4), np.uint8)
        source[6:13, 6:11] = (120, 90, 180, 255)
        source[8, 10] = (240, 50, 30, 255)
        return source

    def test_foreground_and_deterministic_loop(self):
        source = self.frame(); mask = source[:, :, 3] > 0
        ramp = color_ramp([(168, 184, 32), (168, 144, 240)], 3)
        a, info = render_frame(source, mask, ramp, 0, 3, 4, 8)
        b, _ = render_frame(source, mask, ramp, 1, 3, 4, 8)
        c, _ = render_frame(source, mask, ramp, .25, 3, 4, 8)
        self.assertTrue(np.array_equal(a, b))
        self.assertFalse(np.array_equal(a, c))
        self.assertTrue(np.array_equal(a[8:28, 8:28][mask], source[mask]))
        self.assertEqual(info['clipped_aura_pixels'], 0)
        self.assertGreater(info['added_pixels'], 0)
        self.assertEqual(set(np.unique(a[:, :, 3])), {0, 255})

    def test_anchor_translation_and_body_only_mask(self):
        source = self.frame()
        shifted = np.zeros_like(source); shifted[1:, 2:] = source[:-1, :-2]
        ramp = color_ramp([(90, 200, 230)], 3)
        a, _ = render_frame(source, source[:, :, 3] > 0, ramp, .4, 2, 3, 7, anchor=(8, 9))
        b, _ = render_frame(shifted, shifted[:, :, 3] > 0, ramp, .4, 2, 3, 7, anchor=(10, 10))
        self.assertTrue(np.array_equal(a[:-1, :-2], b[1:, 2:]))
        # Excluded effect pixels remain intact, but do not generate their own halo.
        source[0, 0] = (255, 255, 255, 255)
        body = source[:, :, 3] > 0; body[0, 0] = False
        a, _ = render_frame(source, body, ramp, .4, 2, 3, 7)
        self.assertEqual(a[7, 7].tolist(), [255, 255, 255, 255])
        self.assertEqual(int(a[7, 6, 3]), 0)

    def fixture(self, root, edge=False):
        root.mkdir()
        sheet = np.zeros((10, 32, 4), np.uint8)
        # Deliberately nonzero invisible RGB verifies indexed transparency handling.
        sheet[:, :, :3] = 123
        offsets = np.zeros_like(sheet); shadow = np.zeros_like(sheet)
        for c in range(4):
            x = c * 8 + (0 if edge else 3)
            sheet[3:7, x:x + 2] = (140, 60, 80, 255)
            offsets[4, c * 8 + 4] = (0, 0, 0, 255)
            shadow[8, c * 8 + 4] = (255, 255, 255, 255)
        for name, image in [('Anim', sheet), ('Offsets', offsets), ('Shadow', shadow)]:
            Image.fromarray(image).save(root / f'Idle-{name}.png')
        (root / 'credits.txt').write_text('TEST CREDIT', encoding='utf-8')
        (root / 'AnimData.xml').write_text('''<AnimData><ShadowSize>1</ShadowSize><Anims>
<Anim><Name>Idle</Name><Index>7</Index><FrameWidth>8</FrameWidth><FrameHeight>10</FrameHeight>
<Durations><Duration>8</Duration><Duration>8</Duration><Duration>8</Duration><Duration>8</Duration></Durations></Anim>
<Anim><Name>Alias</Name><Index>8</Index><CopyOf>Idle</CopyOf></Anim>
</Anims></AnimData>''', encoding='utf-8')

    def test_package_offsets_xml_palette_and_read_only_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); src = root / 'source'; out = root / 'output'
            self.fixture(src)
            before = {p.name: p.read_bytes() for p in src.iterdir()}
            args = parser().parse_args(['--sprite-dir', str(src), '--output', str(out),
                                       '--types', '벌레', '비행', '--no-previews'])
            report = build(args)
            self.assertTrue(report['source_unchanged'])
            self.assertEqual(before, {p.name: p.read_bytes() for p in src.iterdir()})
            self.assertEqual((out / 'credits.txt').read_bytes(), before['credits.txt'])
            tree = ET.parse(out / 'AnimData.xml')
            anim = tree.find('./Anims/Anim')
            self.assertEqual(anim.findtext('FrameWidth'), '24')
            self.assertEqual(anim.findtext('FrameHeight'), '26')
            self.assertEqual(anim.findtext('Index'), '7')
            self.assertEqual(tree.findall('./Anims/Anim')[1].findtext('CopyOf'), 'Idle')
            for suffix in ['Offsets', 'Shadow']:
                old = np.array(Image.open(src / f'Idle-{suffix}.png').convert('RGBA'))
                new = np.array(Image.open(out / f'Idle-{suffix}.png').convert('RGBA'))
                for c in range(4):
                    self.assertTrue(np.array_equal(old[:, c * 8:c * 8 + 8], new[8:18, c * 24 + 8:c * 24 + 16]))
            self.assertLessEqual(len(Image.open(out / 'Idle-Anim.png').convert('RGBA').getcolors(256)), 16)

    def test_clipping_and_palette_errors_write_no_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); src = root / 'source'; self.fixture(src, edge=True)
            out = root / 'clipped'
            args = parser().parse_args(['--sprite-dir', str(src), '--output', str(out),
                                       '--types', 'bug', 'flying', '--padding', '0', '--no-previews'])
            with self.assertRaisesRegex(ValueError, 'would clip'): build(args)
            self.assertFalse(out.exists())
            args.padding = 'auto'; args.palette_limit = 3
            with self.assertRaisesRegex(ValueError, 'at least two'): build(args)
            self.assertFalse(out.exists())

    def test_batch_variants_resume_missing_and_modified_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); sprites = root / 'sprites'; sprites.mkdir()
            self.fixture(sprites / '0012')
            shiny = sprites / '0012/0000'; shiny.mkdir()
            self.fixture(shiny / '0001')
            csv_path = root / 'targets.csv'
            csv_path.write_text('dex_id,type1,type2,enabled\n0012,bug,flying,1\n0003,grass,poison,1\n', encoding='utf-8-sig')
            args = parser().parse_args(['--sprite-root', str(sprites), '--csv', str(csv_path),
                                       '--output', str(root / 'out'), '--variants', 'normal'])
            args.dry_run = True
            self.assertEqual(batch(args)['summary'], {'ready': 1, 'skipped_missing': 1})
            self.assertFalse(args.output.exists())
            args.dry_run = False
            self.assertEqual(batch(args)['summary'], {'created': 1, 'skipped_missing': 1})
            self.assertFalse((args.output / '0012/AltMeta/previews').exists())
            args.resume = True
            self.assertEqual(batch(args)['summary'], {'skipped_completed': 1, 'skipped_missing': 1})
            (args.output / '0012/AltMeta/credits.txt').write_text('modified')
            self.assertEqual(batch(args)['summary']['failed'], 1)
            args.width = 2
            self.assertEqual(batch(args)['summary']['failed'], 1)

    def test_batch_duplicate_csv_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); sprites = root / 'sprites'; sprites.mkdir()
            csv_path = root / 'targets.csv'
            csv_path.write_text('dex_id,type1,type2,enabled\n12,bug,flying,1\n0012,bug,flying,1\n')
            args = parser().parse_args(['--sprite-root', str(sprites), '--csv', str(csv_path),
                                       '--output', str(root / 'out')])
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                batch(args)
            self.assertFalse(args.output.exists())


if __name__ == '__main__':
    unittest.main()
