"""SkyTemple editing adapter for Alpha+ MFX1 fixed rooms256–263."""
import copy
import struct

from skytemple.core.abstract_module import AbstractModule
from skytemple_files.common.types.file_types import FileType
from skytemple_files.hardcoded.fixed_floor import FixedFloorProperties
from .format import read_extension,serialize_extended

PATH='BALANCE/fixed.bin'
NATIVE='UTILITY/fixed.bin'


class ExtendedFixedHandler(FileType.FIXED_BIN):
    @classmethod
    def deserialize(cls,data,*,alpha_fixed_extension,**kwargs):
        if read_extension(data)!=alpha_fixed_extension:raise ValueError('MFX1 metadata changed while opening')
        return FileType.FIXED_BIN.deserialize(data,**kwargs)

    @classmethod
    def serialize(cls,model,*,alpha_fixed_extension,**kwargs):
        return serialize_extended(model,alpha_fixed_extension)


def metadata(project):
    if not hasattr(project,'_alpha_fixed_extension_metadata'):
        project._alpha_fixed_extension_metadata=read_extension(project._rom.getFileByName(PATH))
    return project._alpha_fixed_extension_metadata


def install():
    from skytemple.core.rom_project import RomProject
    from skytemple.module.dungeon.module import DungeonModule
    from skytemple.module.dungeon.widget.fixed import StDungeonFixedPage
    if getattr(DungeonModule,'_alpha_fixed_extension',False):return
    original_open=RomProject.open_file_in_rom
    original_prepare=RomProject.prepare_save_model
    original_properties=DungeonModule.get_fixed_floor_properties
    original_save_properties=DungeonModule.save_fixed_floor_properties
    original_overrides=DungeonModule.get_fixed_floor_overrides
    original_save_override=DungeonModule.save_fixed_floor_override
    original_init=StDungeonFixedPage.__init__
    original_entities=DungeonModule.get_fixed_floor_entity_lists

    def open_file(self,path,handler,threadsafe=False,**kwargs):
        if path==PATH and path not in self._opened_files and handler is FileType.FIXED_BIN:
            ext=metadata(self)
            if ext:
                handler=ExtendedFixedHandler;kwargs['alpha_fixed_extension']=ext
        return original_open(self,path,handler,threadsafe=threadsafe,**kwargs)

    def prepare(self,name,assert_that=None):
        result=original_prepare(self,name,assert_that)
        if name==PATH and metadata(self):
            # Alpha's game loader reads UTILITY. Saving an editor layout must
            # update that bank too, using the exact same serialized directory.
            self._rom.setFileByName(NATIVE,self._rom.getFileByName(PATH))
        return result

    def properties(self):
        rows=original_properties(self);ext=metadata(self.project)
        if ext:rows.extend(FixedFloorProperties(*struct.unpack('<I8B',p)) for p in ext['properties'])
        return rows

    def save_properties(self,floor_id,value):
        ext=metadata(self.project)
        if ext and ext['first']<=floor_id<ext['first']+ext['count']:
            ext['properties'][floor_id-ext['first']]=bytes(value.to_bytes())
            self.mark_fixed_floor_as_modified(floor_id)
            return
        return original_save_properties(self,floor_id,value)

    def overrides(self):
        rows=original_overrides(self);ext=metadata(self.project)
        return rows+[0]*ext['count'] if ext else rows

    def save_override(self,floor_id,value):
        ext=metadata(self.project)
        if ext and floor_id>=ext['first']:
            if value:raise ValueError('MFX1 rooms use their own layouts; native u8 overrides are unavailable')
            return
        return original_save_override(self,floor_id,value)

    def init_page(self,module,item_data,*args,**kwargs):
        previous=getattr(module,'_alpha_preview_room',None)
        module._alpha_preview_room=item_data
        try:original_init(self,module,item_data,*args,**kwargs)
        finally:module._alpha_preview_room=previous
        ext=metadata(module.project)
        if ext and item_data>=ext['first']:
            self.settings_override.set_sensitive(False)
            self.settings_override.set_tooltip_text('Extended fixed room: physical layout ID256+, selected by Trial Tower')

    def entities(self):
        rows=original_entities(self);ext=metadata(self.project)
        room=getattr(self,'_alpha_preview_room',None)
        if not ext or room is None or not ext['first']<=room<ext['first']+ext['count']:return rows
        # Match the game's room-specific item mapping in this editor page only.
        # The shared entity-table viewer and original rooms retain their rows.
        entities,items,monsters,tiles,stats=rows
        items=list(items);items[61]=copy.copy(items[61])
        items[61].item_id=[99,73,103,93,77,136,136,89][room-ext['first']]
        return entities,items,monsters,tiles,stats

    RomProject.open_file_in_rom=open_file
    RomProject.prepare_save_model=prepare
    DungeonModule.get_fixed_floor_properties=properties
    DungeonModule.save_fixed_floor_properties=save_properties
    DungeonModule.get_fixed_floor_overrides=overrides
    DungeonModule.save_fixed_floor_override=save_override
    DungeonModule.get_fixed_floor_entity_lists=entities
    StDungeonFixedPage.__init__=init_page
    DungeonModule._alpha_fixed_extension=True


class AlphaFixedExtensionModule(AbstractModule):
    @classmethod
    def depends_on(cls):return ['dungeon']
    @classmethod
    def sort_order(cls):return 1002
    @classmethod
    def load(cls):install()
    def __init__(self,rom_project):self.project=rom_project
    def load_tree_items(self,item_tree):pass
