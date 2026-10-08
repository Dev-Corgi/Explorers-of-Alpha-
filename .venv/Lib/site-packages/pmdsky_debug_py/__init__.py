# Re-exports (you can still access everything 'manually' in the submodules if needed):
# mypy: ignore-errors
#                     <- (see https://github.com/python/mypy/issues/5018#issuecomment-1165828654)

from typing import TYPE_CHECKING

from pmdsky_debug_py.eu import EuSections as _EuSections
from pmdsky_debug_py.na import NaSections as _NaSections
from pmdsky_debug_py.jp import JpSections as _JpSections
from pmdsky_debug_py.eu_itcm import EuItcmSections as _EuItcmSections
from pmdsky_debug_py.na_itcm import NaItcmSections as _NaItcmSections
from pmdsky_debug_py.jp_itcm import JpItcmSections as _JpItcmSections
from pmdsky_debug_py.protocol import AllSymbolsProtocol
from ._release import RELEASE

eu: AllSymbolsProtocol = _EuSections
na: AllSymbolsProtocol = _NaSections
jp: AllSymbolsProtocol = _JpSections
eu_itcm: AllSymbolsProtocol = _EuItcmSections
na_itcm: AllSymbolsProtocol = _NaItcmSections
jp_itcm: AllSymbolsProtocol = _JpItcmSections
# not needed but to clarify these are indeed re-exports:
AllSymbolsProtocol = AllSymbolsProtocol
RELEASE = RELEASE


# mypy tests:
if TYPE_CHECKING:
    def ___():
        # First a general check making sure mypy understands this concept.
        from typing import Protocol

        class AProtocol(Protocol):
            a: str

        class A:
            a = "a"

        a: AProtocol = A

        # Now specific tests
        from pmdsky_debug_py.eu import EuArm9Section, EuArm9Functions, EuArm9Data
        from pmdsky_debug_py.protocol import SectionProtocol, Arm9FunctionsProtocol, Arm9DataProtocol
        eu_arm9: SectionProtocol = EuArm9Section
        eu_arm9_fn: Arm9FunctionsProtocol = EuArm9Functions
        eu_arm9_dt: Arm9DataProtocol = EuArm9Data

        # And if everything works, the lines where `eu`, etc. are defined
        # will also not fail.
