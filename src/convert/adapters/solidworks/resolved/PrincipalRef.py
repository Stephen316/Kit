from dataclasses import dataclass as Dataclass

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
    FeatureOffset: int
    TimeValue: int
    AxisCode: int
    BasisValue: tuple[float, ...] | None
    BasisOffset: int | None
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
    FeatureOffset = Cursor.Offset
    FeatureId, TimeValue = Cursor.ReadInts("<iI")
    Cursor.ReadNull()
    (AxisCode,) = Cursor.ReadInts("<i")
    PoseOffset = Cursor.Offset
    BasisValue, ShiftScale = ReadLocalPose(Cursor)
    return PrincipalRef(
        Offset,
        ObjectIndex,
        UnitIndex,
        PartIndex,
        FeatureId,
        FeatureOffset,
        TimeValue,
        AxisCode,
        BasisValue,
        PoseOffset + 1 if BasisValue is not None else None,
        ShiftScale,
    )
