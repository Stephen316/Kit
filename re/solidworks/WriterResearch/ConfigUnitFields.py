from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite
from struct import pack as Pack
from typing import cast as CastValue

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the owning serializer stores several native member types in one fixed order
KFieldOrder = "<iidiidiiiidHi"


# only the measured formatter settings are supported by the research constructor
KAngularStep = 0.78539816339745


# callers need to distinguish the three saved formatter shapes without using raw bytes
KFormats = {
    "primary": (0.1, 4, 8),
    "dual": (1.0, 1, 2),
    "common": (0.01, 10, 1),
}


# the saved display selectors can vary independently of earlier length state
@DataClass(frozen=True)
class UnitDisplay:
    Length: int
    System: int
    Force: int
    Energy: int
    DensityVolume: int
    DensityMass: int
    LegacyVolume: int
    UseLegacyVolume: int


# the research codec covers the two complete measured display settings profiles
KDisplayProfiles = (
    UnitDisplay(0, 4, 2, 0, 3, 1, 3, 0),
    UnitDisplay(3, 2, 5, 2, 8, 3, 3, 0),
)


# retaining the earlier formatter value prevents deriving it from current feature geometry
@DataClass(frozen=True)
class ConfigUnitState:
    Display: UnitDisplay
    PreviousLength: float


# generation and complete settings must be in scope before the archive map changes
def RequireUnitState(Generation: int, State: ConfigUnitState) -> None:
    RequireArch(Generation, KConfigGen, "configuration units generation")
    RequireArch(
        State.Display in KDisplayProfiles, True, "measured unit display profile"
    )
    RequireArch(
        IsFinite(State.PreviousLength) and State.PreviousLength >= 0.0,
        True,
        "supported earlier length formatter value",
    )


# one checked field order keeps the saved formatter shape shared between reads and writes
def UnitFields(Profile: str, Previous: float) -> tuple[int | float, ...]:
    Step, Field20, Field28 = KFormats[Profile]
    return (2, 1, Step, Field20, 1, KAngularStep, Field28, 0, 1, 1, Previous, 0, 0)


# the previous double needs to survive reading while the other profile fields are checked
def ReadUnitFields(Cursor: FieldCursor, Profile: str) -> float:
    Values = Cursor.ReadValue(KFieldOrder)
    Previous = CastValue(float, Values[10])
    RequireArch(Values, UnitFields(Profile, Previous), f"{Profile} unit formatter")
    return Previous


# the native scalar codecs act on caller state and the bounded formatter profile
def WriteUnitFields(Writer: ArchiveWriter, Profile: str, Previous: float = 0.0) -> None:
    Writer.raw(Pack(KFieldOrder, *UnitFields(Profile, Previous)))
