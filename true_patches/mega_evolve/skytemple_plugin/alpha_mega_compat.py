"""SkyTemple adapter for the versioned Alpha+ monster.md trailers."""
import logging
import struct

from skytemple.core.abstract_module import AbstractModule
from skytemple_files.data.md.handler import MdHandler

logger = logging.getLogger(__name__)
MD_PATH = 'BALANCE/monster.md'
ENTRY_SIZE = 68


def split_md(data):
    """Recognize complete MEF4/MEP5 trailers; leave ordinary MDs untouched."""
    data = bytes(data)
    if len(data) < 8 or data[:4] != b'MD\0\0':
        return None
    count = struct.unpack_from('<I', data, 4)[0]
    end = 8 + count * ENTRY_SIZE
    tail = data[end:]
    if not tail.startswith(b'MEF4'):
        return None
    if len(tail) < 16:
        raise ValueError('Truncated Alpha+ MEF4 header')
    magic, version, first, forms = struct.unpack_from('<4I', tail)
    form_end = 16 + forms * 32
    if version != 1 or first + forms != count or form_end > len(tail):
        raise ValueError('Invalid Alpha+ MEF4 trailer')
    if len(tail) != form_end:
        if len(tail) < form_end + 16:
            raise ValueError('Truncated Alpha+ MEP5 header')
        sprite_magic, sprite_version, sprite_first, sprite_count = struct.unpack_from('<4I', tail, form_end)
        if (sprite_magic != 0x3550454D or sprite_version != 1
                or (sprite_first, sprite_count) != (first, forms)
                or len(tail) != form_end + 16 + forms * 8):
            raise ValueError('Invalid Alpha+ MEP5 trailer')
    return data[:end], tail, count


class AlphaMdHandler(MdHandler):
    @classmethod
    def deserialize(cls, data, *, alpha_md_tail, alpha_md_count, **kwargs):
        parts = split_md(data)
        if parts is None or parts[1:] != (alpha_md_tail, alpha_md_count):
            raise ValueError('Alpha+ MD trailer changed while opening')
        return MdHandler.deserialize(parts[0], **kwargs)

    @classmethod
    def serialize(cls, model, *, alpha_md_tail, alpha_md_count, **kwargs):
        # Runtime lookups use fixed IDs and offsets into the appended tables.
        # Normal field edits may round-trip, but structural edits need a rebuild.
        if len(model.entries) != alpha_md_count:
            raise ValueError('Alpha+ species rows cannot be added or removed in SkyTemple')
        data = bytes(MdHandler.serialize(model, **kwargs))
        if len(data) != 8 + alpha_md_count * ENTRY_SIZE:
            raise ValueError('Alpha+ MD serializer changed the entry layout')
        return data + alpha_md_tail


def install():
    from skytemple.core.rom_project import RomProject

    if getattr(RomProject, '_alpha_mega_compat', False):
        return
    original = RomProject.open_file_in_rom

    def open_file(self, file_path_in_rom, file_handler_class, threadsafe=False, **kwargs):
        if file_path_in_rom == MD_PATH and file_path_in_rom not in self._opened_files:
            parts = split_md(self._rom.getFileByName(MD_PATH))
            if parts is not None and file_handler_class is MdHandler:
                kwargs.update(alpha_md_tail=parts[1], alpha_md_count=parts[2])
                file_handler_class = AlphaMdHandler
                logger.info('Alpha+ monster.md: %s native rows, preserving %s trailer bytes',
                            parts[2], len(parts[1]))
        return original(self, file_path_in_rom, file_handler_class, threadsafe=threadsafe, **kwargs)

    RomProject.open_file_in_rom = open_file
    RomProject._alpha_mega_compat = True
    logger.info('Alpha+ Mega Evolution MD compatibility installed')


class AlphaMegaCompatModule(AbstractModule):
    @classmethod
    def depends_on(cls):
        return ['monster']

    @classmethod
    def sort_order(cls):
        return 1001

    @classmethod
    def load(cls):
        install()

    def __init__(self, rom_project):
        self.project = rom_project

    def load_tree_items(self, item_tree):
        pass
