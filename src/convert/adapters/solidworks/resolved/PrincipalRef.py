from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.container.Archive import KNullKind
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.LocalFrame import (
    ReadLocalPart,
    ReadLocalPose,
)


# the profile attachment must preserve its saved feature identity and complete local frame
@Dataclass(frozen=True, slots=True)
class PrincipalRef:
    Offset: int
    ObjectIndex: int
    UnitIndex: int
    PartIndex: int
    FeatureId: int
    TimeValue: int
    AxisCode: int
    BasisValue: tuple[float, ...] | None
    ShiftScale: tuple[float, ...]


# both profile and origin placements need the actual typed component owner
def ReadPlaneRef(
    Cursor: ArchiveCursor, Generation: int, KindValue: str
) -> PrincipalRef:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moCompRefPlane_c",), KindValue, CompactOnly=True
    )
    UnitIndex, PartIndex = ReadLocalPart(Cursor, Generation)
    FeatureId, TimeValue = Cursor.ReadInts("<iI")
    _ = Cursor.TakePointer((None,), KNullKind, CompactOnly=True)
    (AxisCode,) = Cursor.ReadInts("<i")
    BasisValue, ShiftScale = ReadLocalPose(Cursor)
    return PrincipalRef(
        Offset,
        ObjectIndex,
        UnitIndex,
        PartIndex,
        FeatureId,
        TimeValue,
        AxisCode,
        BasisValue,
        ShiftScale,
    )
