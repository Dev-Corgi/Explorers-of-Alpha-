"""Exercise SkyTemple's adapter boundary without GUI or disk ROM writes."""
import importlib.util
import struct
import sys
from pathlib import Path
from types import ModuleType

from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.hardcoded.fixed_floor import HardcodedFixedFloorTables as Tables,ItemSpawn
from skytemple_files.dungeon_data.fixed_bin.model import TileRule,TileRuleType
from true_patches.trial_tower.fixed_extension import read_extension


def check_plugin(rom):
    def stub(name,**attrs):
        module=ModuleType(name);module.__dict__.update(attrs);sys.modules[name]=module
    class Project:
        def __init__(self):
            self._rom=rom;self._opened_files={};self._file_handlers={};self._file_handler_kwargs={}
        def open_file_in_rom(self,path,handler,threadsafe=False,**kwargs):
            if path not in self._opened_files:
                self._opened_files[path]=handler.deserialize(self._rom.getFileByName(path),**kwargs)
                self._file_handlers[path]=handler;self._file_handler_kwargs[path]=kwargs
            return self._opened_files[path]
        def prepare_save_model(self,name,assert_that=None):
            self._rom.setFileByName(name,self._file_handlers[name].serialize(self._opened_files[name],**self._file_handler_kwargs[name]))
    class Dungeon:
        def __init__(self,project):self.project=project;self.modified=[]
        def get_fixed_floor_properties(self):
            return Tables.get_fixed_floor_properties(self.project._rom.loadArm9Overlays()[10].data,get_ppmdu_config_for_rom(self.project._rom))
        def save_fixed_floor_properties(self,floor_id,value):raise AssertionError('extended property fell through to native table')
        def get_fixed_floor_overrides(self):return [0]*256
        def save_fixed_floor_override(self,floor_id,value):raise AssertionError('extended override fell through')
        def mark_fixed_floor_as_modified(self,floor_id):self.modified.append(floor_id)
        def get_fixed_floor_entity_lists(self):return [],[ItemSpawn(136,0,0,0) for _ in range(63)],[],[],[]
    class Control:
        def set_sensitive(self,value):self.sensitive=value
        def set_tooltip_text(self,value):self.tooltip=value
    class Page:
        def __init__(self,module,item_data):
            self.preview_items=module.get_fixed_floor_entity_lists()[1]
            self.properties=module.get_fixed_floor_properties()[item_data]
            self.override_id=module.get_fixed_floor_overrides()[item_data]
            self.settings_override=Control()
    names=['skytemple.core.abstract_module','skytemple.core.rom_project','skytemple.module.dungeon.module','skytemple.module.dungeon.widget.fixed']
    previous={n:sys.modules.get(n) for n in names+['alpha_fixed_extension','alpha_fixed_extension.format']}
    try:
        stub(names[0],AbstractModule=object);stub(names[1],RomProject=Project)
        stub(names[2],DungeonModule=Dungeon);stub(names[3],StDungeonFixedPage=Page)
        format_path=Path(__file__).resolve().parents[1]/'fixed_extension.py'
        spec=importlib.util.spec_from_file_location('alpha_fixed_extension.format',format_path)
        fmt=importlib.util.module_from_spec(spec);sys.modules[spec.name]=fmt;spec.loader.exec_module(fmt)
        spec=importlib.util.spec_from_file_location('alpha_fixed_extension',Path(__file__).with_name('alpha_fixed_extension.py'),submodule_search_locations=[])
        plugin=importlib.util.module_from_spec(spec);sys.modules[spec.name]=plugin;spec.loader.exec_module(plugin)
        plugin.install();plugin.install()  # idempotent
        project=Project();dungeon=Dungeon(project)
        model=project.open_file_in_rom('BALANCE/fixed.bin',FileType.FIXED_BIN)
        assert len(model.fixed_floors)==264
        assert len(dungeon.get_fixed_floor_properties())==len(dungeon.get_fixed_floor_overrides())==264
        for n in range(256,264):
            page=Page(dungeon,n);assert not page.settings_override.sensitive
            assert page.preview_items[61].item_id==[99,73,103,93,77,136,136,89][n-256]
        assert dungeon.get_fixed_floor_entity_lists()[1][61].item_id==136
        before=bytes(rom.getFileByName('BALANCE/fixed.bin'))
        project.prepare_save_model('BALANCE/fixed.bin');assert bytes(rom.getFileByName('BALANCE/fixed.bin'))==before
        prop=dungeon.get_fixed_floor_properties()[263];prop.exit_floor_when_defeating_enemies=True
        dungeon.save_fixed_floor_properties(263,prop);assert dungeon.modified==[263]
        model.fixed_floors[256].actions[0]=TileRule(TileRuleType.FLOOR_ROOM)
        project.prepare_save_model('BALANCE/fixed.bin')
        saved=bytes(rom.getFileByName('BALANCE/fixed.bin'))
        assert saved==bytes(rom.getFileByName('UTILITY/fixed.bin'))
        assert read_extension(saved)['properties'][7]==prop.to_bytes()
        reopened=FileType.FIXED_BIN.deserialize(saved)
        assert len(reopened.fixed_floors)==264 and reopened.fixed_floors[256].to_bytes()==model.fixed_floors[256].to_bytes()
        project2=Project();opened=project2.open_file_in_rom('BALANCE/fixed.bin',FileType.FIXED_BIN)
        assert len(opened.fixed_floors)==264 and Dungeon(project2).get_fixed_floor_properties()[263].exit_floor_when_defeating_enemies
        try:dungeon.save_fixed_floor_override(256,1)
        except ValueError:pass
        else:raise AssertionError('u8 override silently truncated an extended room')
        # Preserve the shared in-memory fixture for subsequent ARM checks.
        for path in ['BALANCE/fixed.bin','UTILITY/fixed.bin']:rom.setFileByName(path,before)
        print('PASS SkyTemple264-room open/list, all extended properties, editable layout/property save/reopen, prefix preservation and native UTILITY synchronization',flush=True)
    finally:
        for n,module in previous.items():
            if module is None:sys.modules.pop(n,None)
            else:sys.modules[n]=module
