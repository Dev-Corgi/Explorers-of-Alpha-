"""Headless verification of the installed plugin using real ROM tables."""
from pathlib import Path
import importlib
import os
import sys
from types import ModuleType
from zipfile import ZipFile

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom, get_binary_from_rom
from skytemple_files.hardcoded.fixed_floor import HardcodedFixedFloorTables as Tables
from wheel.wheelfile import WheelFile

ROOT = Path(__file__).resolve().parents[2]
wheel = Path(os.environ['LOCALAPPDATA']) / 'skytemple/plugins/alpha_fixed_room_viewer-1.0.0-py3-none-any.whl'


def stub(name, **attrs):
    module = ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module


class Project:
    def __init__(self, path):
        self._rom = NintendoDSRom.fromFile(path)
        self.saved = False

    def file_exists(self, name):
        return name in self._rom.filenames


class Dungeon:
    def __init__(self, project):
        self.project = project

    def get_fixed_floor_entity_lists(self):
        rom = self.project._rom
        config = get_ppmdu_config_for_rom(rom)
        ov29 = get_binary_from_rom(rom, config.bin_sections.overlay29)
        ov10 = get_binary_from_rom(rom, config.bin_sections.overlay10)
        return (Tables.get_entity_spawn_table(ov29, config),
                Tables.get_item_spawn_list(ov29, config),
                Tables.get_monster_spawn_list(ov29, config),
                Tables.get_tile_spawn_list(ov29, config),
                Tables.get_monster_spawn_stats_table(ov10, config))

    def save_fixed_floor_entity_lists(self, *args):
        self.project.saved = True


class Renderer:
    def __init__(self):
        self.editable = True

    def find_property(self, prop):
        return prop == 'editable'

    def set_property(self, prop, value):
        setattr(self, prop, value)


class Tree:
    def __init__(self):
        self.cell = Renderer()

    def get_columns(self):
        return [self]

    def get_cells(self):
        return [self.cell]

    def set_tooltip_text(self, text):
        self.tooltip = text


class Page:
    def __init__(self, module, item_data):
        for name in ('tree_entities', 'tree_items', 'tree_monsters', 'tree_tiles', 'tree_stats'):
            setattr(self, name, Tree())


def main():
    # Verify wheel integrity and its plugin entry point without GTK.
    with WheelFile(wheel) as archive:
        for path in archive.namelist():
            archive.read(path)
    with ZipFile(wheel) as archive:
        entry = archive.read('alpha_fixed_room_viewer-1.0.0.dist-info/entry_points.txt')
        assert b'[skytemple.module]' in entry
    stub('skytemple.core.abstract_module', AbstractModule=object)
    stub('skytemple.module.dungeon.module', DungeonModule=Dungeon)
    stub('skytemple.module.dungeon.widget.fixed_rooms', StDungeonFixedRoomsPage=Page)
    sys.path.insert(0, str(wheel))
    plugin = importlib.import_module('alpha_fixed_room_viewer')
    plugin.AlphaFixedRoomViewerModule.load()
    original = Dungeon.get_fixed_floor_entity_lists
    plugin.AlphaFixedRoomViewerModule.load()
    assert Dungeon.get_fixed_floor_entity_lists is original  # idempotent
    for name, count in [('Explorers of Alpha/Explorers of Alpha.nds', 99),
                        ('Export Rom/Explorers of Alpha+.nds', 108),
                        ('Export Rom/Explorers of Alpha+_kor.nds', 108)]:
        path = ROOT / 'PatchTesting' / name
        before = path.read_bytes()
        project = Project(path)
        module = Dungeon(project)
        entities, items, monsters, tiles, stats = module.get_fixed_floor_entity_lists()
        assert len(stats) == count
        for entity in entities:
            items[entity.item_id]
            tiles[entity.tile_id]
            stats[monsters[entity.monster_id].stats_entry]
        page = Page(module, 0)
        assert page.tree_stats.cell.editable == (count == 99)
        if count == 108:
            assert b''.join(row.to_bytes() for row in stats) == project._rom.getFileByName(plugin.TABLE_PATH)
            try:
                module.save_fixed_floor_entity_lists(entities, items, monsters, tiles, stats)
            except ValueError:
                pass
            else:
                raise AssertionError('Expanded stats save must be blocked')
            assert not project.saved
        else:
            module.save_fixed_floor_entity_lists(entities, items, monsters, tiles, stats)
            assert project.saved
        assert path.read_bytes() == before
        print(f'PASS: {name}: {len(entities)} entities, {count} stats; all indices readable')


if __name__ == '__main__':
    main()
