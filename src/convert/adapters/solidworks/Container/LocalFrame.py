from convert.adapters.solidworks.Container.Archive import KClassRefKind, KObjectRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)


# a saved pose keeps the fallback identity separate from explicit axes and translation
def ReadLocalPose(
    Cursor: FieldCursor,
) -> tuple[tuple[float, ...] | None, tuple[float, ...]]:
    (FlagValue,) = Cursor.ReadInts("<B")
    RequireArch(FlagValue in (0, 1), True, "transform basis selector")
    BasisValue = Cursor.ReadPoint(9) if FlagValue else None
    ShiftScale = Cursor.ReadPoint(4)
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent nested transform")
    return BasisValue, ShiftScale


# a local reference must resolve through the part object that owns this archive
def ReadLocalPart(Cursor: ArchiveCursor, Generation: int) -> tuple[int, int]:
    _, _, UnitIndex = Cursor.TakePointer(
        ("moUnitComponent_c",), KClassRefKind, CompactOnly=True
    )
    _, _, PartIndex = Cursor.TakePointer(
        ("moPart_c",), KObjectRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent external unit component")
    WordsValue = Cursor.ReadInts("<20I")
    RequireArch(WordsValue[-1], Generation, "component reference generation")
    RequireArch(
        tuple(WordsValue[Index] for Index in (6, 14, 15, 16, 17, 18)),
        (0,) * 6,
        "absent component extras",
    )
    return UnitIndex, PartIndex
