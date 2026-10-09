"""SkyTemple plugin: read Alpha+'s relocated fixed-room stats without editing them."""
import logging
import struct

from skytemple.core.abstract_module import AbstractModule

TABLE_PATH = 'BALANCE/fr_mst.bin'
logger = logging.getLogger(__name__)


def expanded_stats(project):
    if not project.file_exists(TABLE_PATH):
        return None
    from skytemple_files.hardcoded.fixed_floor import MonsterSpawnStats

    blob = bytes(project._rom.getFileByName(TABLE_PATH))
    if not blob or len(blob) % 12 or len(blob) // 12 > 256:
        raise ValueError('Alpha+ fixed-room stats file has an invalid size.')
    return [MonsterSpawnStats(*struct.unpack_from('<HHHBBBBH', blob, offset))
            for offset in range(0, len(blob), 12)]


def install():
    from skytemple.module.dungeon.module import DungeonModule
    from skytemple.module.dungeon.widget.fixed_rooms import StDungeonFixedRoomsPage

    if getattr(DungeonModule, '_alpha_fixed_room_viewer', False):
        return
    original_get = DungeonModule.get_fixed_floor_entity_lists
    original_save = DungeonModule.save_fixed_floor_entity_lists
    original_init = StDungeonFixedRoomsPage.__init__

    def get_lists(self):
        lists = original_get(self)
        stats = expanded_stats(self.project)
        if stats is None:
            return lists
        entities, items, monsters, tiles, _ = lists
        for monster in monsters:
            if monster.stats_entry >= len(stats):
                raise ValueError('Alpha+ monster references a missing fixed-room stats row.')
        logger.info('Alpha+ fixed-room viewer: loaded %s stats rows', len(stats))
        return entities, items, monsters, tiles, stats

    def save_lists(self, *args, **kwargs):
        if self.project.file_exists(TABLE_PATH):
            raise ValueError('Alpha+ extended fixed-room entity tables are read-only in this plugin.')
        return original_save(self, *args, **kwargs)

    def init_page(self, module, *args, **kwargs):
        original_init(self, module, *args, **kwargs)
        if not module.project.file_exists(TABLE_PATH):
            return
        # Keep selection, scrolling and the stats tabs available for inspection.
        for name in ('tree_entities', 'tree_items', 'tree_monsters', 'tree_tiles', 'tree_stats'):
            tree = getattr(self, name, None)
            if tree is None:
                continue
            tree.set_tooltip_text('Alpha+ extended fixed-room tables: read-only viewer')
            for column in tree.get_columns():
                for renderer in column.get_cells():
                    for prop in ('editable', 'activatable'):
                        if renderer.find_property(prop) is not None:
                            renderer.set_property(prop, False)

    DungeonModule.get_fixed_floor_entity_lists = get_lists
    DungeonModule.save_fixed_floor_entity_lists = save_lists
    DungeonModule._alpha_fixed_room_viewer = True
    StDungeonFixedRoomsPage.__init__ = init_page
    logger.info('Alpha+ fixed-room read-only viewer installed')


class AlphaFixedRoomViewerModule(AbstractModule):
    @classmethod
    def depends_on(cls):
        return ['dungeon']

    @classmethod
    def sort_order(cls):
        return 1000

    @classmethod
    def load(cls):
        install()

    def __init__(self, rom_project):
        self.project = rom_project

    def load_tree_items(self, item_tree):
        pass
