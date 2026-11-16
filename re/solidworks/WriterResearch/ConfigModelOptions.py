from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the constructor marks the inline entity name map independently of its entry count
KEntityMapMarker = (2, 0, 0xAAAAAAAA, 0xBBBBBBBB)


# dialog flags and rectangles are absent for the supported quiet document state
KEmptyDialogState = (0,) * 12


# model settings must remain separate from its geometry and archive namespace
@DataClass(frozen=True)
class ConfigModelOptions:
    Scale: float
    LengthTolerance: float
    ShowMissingRefs: int


# the independent document settings must fit supported native scalar fields
def RequireOptions(State: ConfigModelOptions) -> None:
    RequireArch(
        all(
            IsFinite(Value) and Value > 0.0
            for Value in (State.Scale, State.LengthTolerance)
        ),
        True,
        "finite positive model scale and tolerance",
    )
    RequireArch(
        type(State.ShowMissingRefs) is int and State.ShowMissingRefs in (0, 1),
        True,
        "missing reference display selector",
    )


# model collections must be empty before reaching the standalone document settings
def ReadModelOptions(Cursor: FieldCursor) -> ConfigModelOptions:
    RequireArch(
        Cursor.ReadInts("<6i"),
        (0,) * 6,
        "regular part flags and empty model visual and detail collections",
    )
    Scale, LengthTolerance = Cursor.ReadPoint(2)
    RequireArch(Cursor.ReadInts("<iH2I"), KEntityMapMarker, "empty entity name map")
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty output coordinate systems")
    (ShowMissingRefs,) = Cursor.ReadInts("<i")
    RequireArch(
        Cursor.ReadInts("<3i"), (0, 0, 0), "no shrink wrap defeature or cosmetic thread"
    )
    RequireArch(
        Cursor.ReadInts("<H2i"),
        (0, 0, 0),
        "empty inline list box flags and sheet flag notes",
    )
    RequireArch(Cursor.ReadInts("<12i"), KEmptyDialogState, "default dialog state")
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "unimported ordinary model")
    State = ConfigModelOptions(Scale, LengthTolerance, ShowMissingRefs)
    RequireOptions(State)
    return State


# this writer admits the empty maps and collections of an ordinary local part
def WriteModelOptions(Writer: ArchiveWriter, State: ConfigModelOptions) -> None:
    for _ in range(6):
        Writer.i32(0)
    Writer.f64(State.Scale)
    Writer.f64(State.LengthTolerance)
    Selector, NameCount, FirstMarker, SecondMarker = KEntityMapMarker
    Writer.i32(Selector)
    Writer.u16(NameCount)
    Writer.u32(FirstMarker)
    Writer.u32(SecondMarker)
    Writer.i32(0)
    Writer.i32(State.ShowMissingRefs)
    for _ in range(3):
        Writer.i32(0)
    Writer.u16(0)
    Writer.i32(0)
    Writer.i32(0)
    for Field in KEmptyDialogState:
        Writer.i32(Field)
    Writer.i32(0)
    Writer.i32(0)
