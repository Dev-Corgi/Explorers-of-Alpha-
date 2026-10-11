"""Verify sibling aura output and form-specific type selection."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest

from build_normalized_aura import plan, run_job
from test_pmd_aura import AuraTests


class NormalizedAuraTests(unittest.TestCase):
    def test_excluded_form_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp); root = home / 'sprite-normalized'
            (root / '0006/0002-Purple_Cutscene').mkdir(parents=True)
            csv_path = home / 'targets.csv'
            csv_path.write_text('dex_id,type1,type2,enabled\n0006,fire,flying,1\n')
            form_types = home / 'form-types.json'
            form_types.write_text(json.dumps({'types': {}}))
            args = argparse.Namespace(normalized_root=root, csv=csv_path, form_types=form_types,
                                      only_dex=None)
            with self.assertRaisesRegex(ValueError, 'Excluded form still present'):
                plan(args)

    def test_form_types_and_adjacent_output(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp); root = home / 'sprite-normalized'
            source = root / '0006/0001-Mega_X/Normal'
            source.parent.mkdir(parents=True)
            AuraTests().fixture(source)
            csv_path = home / 'targets.csv'
            csv_path.write_text('dex_id,type1,type2,enabled\n0006,fire,flying,1\n')
            form_types = home / 'form-types.json'
            form_types.write_text(json.dumps({'types': {'0006/0001-Mega_X': ['fire', 'dragon']}}))
            args = argparse.Namespace(normalized_root=root, csv=csv_path, form_types=form_types,
                                      only_dex=None)
            jobs, counts = plan(args)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(counts['form_type_override'], 1)
            self.assertEqual(jobs[0]['types'], ['fire', 'dragon'])
            self.assertEqual(Path(jobs[0]['destination']), root / '0006/0001-Mega_X_Aura/Normal')
            settings = dict(palette_limit=32, width=3, flame_height=4, seed=0,
                            animations=None, previews=False, allow_clipping=False,
                            staging_root=str(home / 'staging'), resume=False)
            self.assertEqual(run_job(jobs[0], settings)['status'], 'created')
            self.assertTrue((root / '0006/0001-Mega_X_Aura/Normal/Idle-Anim.png').is_file())
            self.assertFalse((root / '0006/0001-Mega_X_Aura/Shiny').exists())
            settings['resume'] = True
            self.assertEqual(run_job(jobs[0], settings)['status'], 'already_present')


if __name__ == '__main__':
    unittest.main()
