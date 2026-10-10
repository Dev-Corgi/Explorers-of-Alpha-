"""Catalog semantics: regional-only evolution does not exclude default forms."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from pmd_aura_catalog import catalog


class CatalogTests(unittest.TestCase):
    def test_form_specific_evolution_and_default_pokemon_type(self):
        data = {
            'pokemon_species': [dict(id='1', identifier='parent', evolves_from_species_id=''),
                                dict(id='2', identifier='child', evolves_from_species_id='1')],
            'pokemon': [dict(id='100', species_id='1', is_default='1'),
                        dict(id='200', species_id='2', is_default='1')],
            'pokemon_forms': [dict(id='10', pokemon_id='100', is_default='1'),
                              dict(id='20', pokemon_id='200', is_default='1')],
            'pokemon_evolution': [dict(evolved_species_id='2', required_pokemon_form_id='99')],
            'languages': [dict(identifier='ko', id='3'), dict(identifier='en', id='9')],
            'pokemon_species_names': [],
            'types': [dict(id='1', identifier='normal')],
            'pokemon_types': [dict(pokemon_id='100', type_id='1', slot='1'),
                              dict(pokemon_id='200', type_id='1', slot='1')],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); sprites = root / 'sprite'; sprites.mkdir()
            (root / 'tracker.json').write_text(json.dumps({'0001': {}, '0002': {}}))
            self.assertEqual([r['dex_id'] for r in catalog(data, sprites)], ['0001', '0002'])
            data['pokemon_evolution'][0]['required_pokemon_form_id'] = '10'
            self.assertEqual([r['dex_id'] for r in catalog(data, sprites)], ['0002'])
            data['pokemon_evolution'] = []
            with self.assertRaisesRegex(ValueError, 'Missing evolution'):
                catalog(data, sprites)

    def test_delivered_catalog_membership_and_paths(self):
        path = Path(__file__).parent / 'data/pmd_aura_targets.csv'
        with path.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        ids = {int(r['dex_id']) for r in rows}
        self.assertEqual(len(rows), len(ids))
        self.assertTrue({12, 83, 122, 211, 222, 264, 550, 865, 866} <= ids)
        self.assertFalse({1, 25, 215, 234} & ids)
        for row in rows:
            self.assertEqual(len(row['dex_id']), 4)
            self.assertEqual(row['normal_form_path'], row['dex_id'])
            self.assertEqual(row['shiny_form_path'], row['dex_id'] + '/0000/0001')


if __name__ == '__main__':
    unittest.main()
