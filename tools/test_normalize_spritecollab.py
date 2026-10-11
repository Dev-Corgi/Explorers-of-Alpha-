"""Check form/color/gender selection and leaf-only copy behavior."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest

from normalize_spritecollab import run


def package(path: Path, label: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / 'AnimData.xml').write_text(label, encoding='utf-8')
    (path / 'Idle-Anim.png').write_bytes(label.encode())


class NormalizeTests(unittest.TestCase):
    def test_selection_exclusion_and_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            root = home / 'sprite'; root.mkdir()
            tracker = home / 'tracker.json'
            tracker.write_text(json.dumps({'0012': {'subgroups': {
                '0000': {'name': ''}, '0001': {'name': 'Mega_X'},
                '0002': {'name': 'Altcolor'}, '0003': {'name': 'Mega_Altcolor'}}}}))
            package(root / '0012', 'shared-normal')
            package(root / '0012/0000/0000/0001', 'male-normal')
            package(root / '0012/0000/0000/0002', 'female-normal')
            package(root / '0012/0000/0001/0002', 'female-shiny')
            package(root / '0012/0001', 'mega-normal')
            package(root / '0012/0002', 'altcolor')
            package(root / '0012/0003', 'mega-altcolor')
            args = argparse.Namespace(sprite_root=root, tracker=tracker, output=home / 'normalized',
                                      report=home / 'report.json', dry_run=True, resume=False)
            self.assertEqual(run(args)['summary']['ready'], 3)
            self.assertFalse(args.output.exists())
            args.dry_run = False
            report = run(args)
            self.assertEqual(report['summary']['copied'], 3)
            self.assertEqual(report['summary']['female_fallback'], 1)
            self.assertEqual((args.output / '0012/Base/Normal/AnimData.xml').read_text(), 'male-normal')
            self.assertEqual((args.output / '0012/Base/Shiny/AnimData.xml').read_text(), 'female-shiny')
            self.assertEqual((args.output / '0012/0001-Mega_X/Normal/AnimData.xml').read_text(), 'mega-normal')
            self.assertFalse((args.output / '0012/0001-Mega_X/Shiny').exists())
            self.assertEqual(len(list(args.output.rglob('AnimData.xml'))), 3)
            self.assertFalse(any(p.is_file() for p in (args.output / '0012').iterdir()))
            self.assertEqual((root / '0012/AnimData.xml').read_text(), 'shared-normal')
            args.resume = True
            self.assertEqual(run(args)['summary']['already_present'], 3)


if __name__ == '__main__':
    unittest.main()
