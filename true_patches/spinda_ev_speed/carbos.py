"""Carbos item data and category-local floor drop redistribution."""
from copy import deepcopy
import struct

from skytemple_files.common.types.file_types import FileType
from skytemple_files.data.data_cd.handler import DataCDHandler

# Alpha disables the Hail TM; its slot is the only unused ordinary item seat.
# Keep within MAPPA's native 0..363 item range, away from exclusive items.
CARBOS = 194
VITAMINS = (100, 101, 102, 108)
ALL_VITAMINS = (*VITAMINS, CARBOS)
NAME_INDEX = 6773 + CARBOS
LONG_INDEX = 10704 + CARBOS
SHORT_INDEX = 12104 + CARBOS


def redistribute(items, categories):
    """MAPPA probabilities are cumulative independently in each category.

    The disabled TM's stale threshold is removed before introducing Carbos;
    its successor retains its threshold, as when the disabled seat is skipped.
    Only floor pools with positive weights for all four vitamins gain Carbos.
    """
    items = dict(items)
    if categories[CARBOS] != 2:
        items.pop(CARBOS, None)
    if not all(0 < items.get(item, 0) <= 10000 for item in VITAMINS):
        return items, False
    weights = {}
    previous = 0
    for item, threshold in sorted(items.items()):
        if categories[item] != 2 or threshold == 0:
            continue
        if threshold > 10000:
            continue  # guaranteed entries are not cumulative random weights
        if threshold < previous:
            raise ValueError("non-monotonic vitamin category thresholds")
        weights[item] = threshold - previous
        previous = threshold
    if not all(weights.get(item, 0) > 0 for item in VITAMINS):
        return items, False
    total = sum(weights.get(item, 0) for item in ALL_VITAMINS)
    share, remainder = divmod(total, 5)
    for n, item in enumerate(ALL_VITAMINS):
        weights[item] = share + (n < remainder)
    threshold = 0
    for item, weight in sorted(weights.items()):
        threshold += weight
        items[item] = threshold
    return dict(sorted(items.items())), True


def install(rom, speed_effect):
    """Patch both native UTILITY and authoring BALANCE banks in memory."""
    counts = {}
    for bank in ('BALANCE', 'UTILITY'):
        path = bank + '/item_p.bin'
        data = FileType.ITEM_P.deserialize(rom.getFileByName(path))
        original = data.item_list[CARBOS]
        if original.is_valid and original.category != 2:
            raise RuntimeError('Carbos item seat is already occupied')
        categories = [int(entry.category) for entry in data.item_list]
        entry = deepcopy(data.item_list[VITAMINS[0]])
        entry.item_id = CARBOS
        data.item_list[CARBOS] = entry
        rom.setFileByName(path, FileType.ITEM_P.serialize(data))

        path = bank + '/item_cd.bin'
        cd = DataCDHandler.deserialize(rom.getFileByName(path))
        # The dynamic item-code loader executes at 0x0231BE50. An absolute
        # call reaches the allocated resident runtime; continue at stock exit.
        code = struct.pack('<9I', 0xE1A00008, 0xE1A01007, 0xE3A02003,
                           0xE59FC008, 0xE12FFF3C, 0xE59FF004, 0xE1A00000,
                           speed_effect, 0x0231CB14)
        effect = next((i for i in range(cd.nb_effects())
                       if bytes(cd.get_effect_code(i)) == code), cd.nb_effects())
        if effect == cd.nb_effects():
            cd.add_effect_code(code)
        cd.set_item_effect_id(CARBOS, effect)
        rom.setFileByName(path, DataCDHandler.serialize(cd))

        path = bank + '/mappa_s.bin'
        mappa = FileType.MAPPA_BIN.deserialize(rom.getFileByName(path))
        count = 0
        for group in mappa.floor_lists:
            for floor in group:
                # All pools can carry stale disabled-TM entries. Do not let
                # those turn into unintended Carbos shop/buried/monster drops.
                for attr in ('shop_items', 'monster_house_items', 'buried_items', 'unk_items1', 'unk_items2'):
                    pool = getattr(floor, attr, None)
                    if pool is not None:
                        pool.items.pop(CARBOS, None)
                floor.floor_items.items, changed = redistribute(floor.floor_items.items, categories)
                count += changed
        rom.setFileByName(path, FileType.MAPPA_BIN.serialize(mappa))
        counts[bank] = count
    return counts


def verify(rom):
    for bank in ('BALANCE', 'UTILITY'):
        data = FileType.ITEM_P.deserialize(rom.getFileByName(bank + '/item_p.bin'))
        assert data.item_list[CARBOS].is_valid
        assert data.item_list[CARBOS].category == 2
        cd = DataCDHandler.deserialize(rom.getFileByName(bank + '/item_cd.bin'))
        code = bytes(cd.get_effect_code(cd.get_item_effect_id(CARBOS)))
        assert len(code) == 36 and struct.unpack_from('<I', code, 8)[0] == 0xE3A02003
        mappa = FileType.MAPPA_BIN.deserialize(rom.getFileByName(bank + '/mappa_s.bin'))
        categories = [int(entry.category) for entry in data.item_list]
        count = 0
        for group in mappa.floor_lists:
            for floor in group:
                items = floor.floor_items.items
                if not items.get(CARBOS):
                    continue
                expected, changed = redistribute(items, categories)
                assert changed and items == expected, 'Carbos vitamin weights are not balanced'
                count += 1
        assert count > 0, 'Carbos has no floor drops'
