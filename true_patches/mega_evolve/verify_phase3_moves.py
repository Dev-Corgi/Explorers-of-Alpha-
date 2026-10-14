"""Check that catalogue parsing cannot depend on earlier modules' globals."""
from pathlib import Path
import sys

from ndspy.rom import NintendoDSRom
import skytemple_files.data.waza_p._model as model
from .phase3_moves import REPO,build,validate_rom


def main():
    supplied=len(sys.argv)>1
    path=Path(sys.argv[1]) if supplied else REPO/'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'
    rom=NintendoDSRom(path.read_bytes())
    initial=model.MOVE_COUNT
    try:
        reference=build(rom)
        for count in (1,559,560):
            model.MOVE_COUNT=count
            assert build(rom)==reference
            assert model.MOVE_COUNT==count
        if supplied:validate_rom(rom)
    finally:
        model.MOVE_COUNT=initial
    print('PASS move catalogue: import-order independent, library global preserved,',
          len(reference['target_rules']),'moves')


if __name__=='__main__':main()
