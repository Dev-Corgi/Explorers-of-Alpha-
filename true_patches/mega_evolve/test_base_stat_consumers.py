"""Guard the dynamically allocated BaseStats consumer hooks without ROM output."""
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from patch_engine.mega_evolve_phase3_runtime import base_stat_consumers
from patch_engine.mega_evolve_runtime import OV29,OV36,branch
from true_patches.base_stats_speed.generate_tables import SENTINEL_OFF,COMBAT_OFF,SPEED_OFF


class BaseStatConsumerTests(unittest.TestCase):
    def fixture(self,offset):
        a,b=bytearray(0x80000),bytearray(0x30000)
        combat,hit=OV36+offset+COMBAT_OFF+0x5c,OV36+offset+SPEED_OFF
        def put(blob,base,address,value):
            struct.pack_into('<I',blob,address-base,value)
        put(a,OV29,0x0230c26c,branch(0x0230c26c,combat))
        put(a,OV29,0x02323f94,branch(0x02323f94,0x020948a0))
        put(b,OV36,OV36+offset+SENTINEL_OFF,0xb5a7e001)
        put(b,OV36,combat,0xe59d1018)
        put(b,OV36,combat+0x18,0xe59d1044)
        put(b,OV36,combat+0x38,0xe3540000)
        put(b,OV36,hit,0xe35a0000)
        return a,b,combat,hit

    def test_consumers_follow_cave_relocation(self):
        for offset in [0x20000,0x20120,0x22000]:
            with self.subTest(offset=hex(offset)):
                a,b,combat,hit=self.fixture(offset)
                self.assertEqual(base_stat_consumers(a,b),{
                    'ME_MagnetDefenseHook':combat+0x38,
                    'ME_AttackStageHook':combat+0x18,
                    'ME_UnawareHitStagesHook':hit})

    def test_changed_consumers_still_fail_closed(self):
        for site_offset in [0,0x18,0x38,SPEED_OFF-COMBAT_OFF-0x5c]:
            a,b,combat,hit=self.fixture(0x20000)
            struct.pack_into('<I',b,combat-OV36+site_offset,0xe1a00000)
            with self.assertRaises(RuntimeError):base_stat_consumers(a,b)

    def test_missing_or_out_of_bounds_branches_are_rejected(self):
        for target in [None,0x02000000]:
            a,b,_,_=self.fixture(0x20000)
            value=0xe1a00000 if target is None else branch(0x0230c26c,target)
            struct.pack_into('<I',a,0x0230c26c-OV29,value)
            with self.assertRaises(RuntimeError):base_stat_consumers(a,b)


if __name__=='__main__':unittest.main(verbosity=2)
