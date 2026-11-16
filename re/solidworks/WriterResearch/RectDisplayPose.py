from dataclasses import dataclass as Dataclass
from math import cos as Cosine, isfinite as IsFinite, pi as Pi
from struct import pack as PackFields

from Display.Compose import DisplayDraft
from DisplayTail import KExtraLeader, KLabelCount, KOrigin, KRadius, KSmartArrows
from RectangleDims import RectangleLength, RectLengthSlots
from convert.adapters.solidworks.Container.Archive import EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# annotation placement remains independent of the driving value and its archive slot
@Dataclass(frozen=True, slots=True)
class SketchDisplayPose:
    TextWorld: tuple[float, float, float]
    TextRatio: float
    WitnessMetres: float
    Direction: tuple[float, float, float]


# a displayed length selects the same anchored local edge as its driving dimension
def DisplayRefPoint(
    Corners: tuple[tuple[float, float], ...],
    Length: RectangleLength,
    Pose: SketchDisplayPose,
) -> tuple[float, float, float]:
    Metres = Length.Millimetres / 1000.0
    _, End = RectLengthSlots(Corners, Metres)
    XValue, YValue = Corners[End]
    LocalDirection = (XValue, YValue, 0.0)
    RequireArch(
        Pose.Direction,
        tuple(Value / Metres for Value in LocalDirection),
        "display references its owned driving edge",
    )
    return LocalDirection


# rotation of the authored direction gives the same local text direction on XY and YZ
def DisplayTextDirection(
    Direction: tuple[float, float, float], Slot: int
) -> tuple[float, float, float]:
    XValue, YValue, _ = Direction
    SignValue = 1 if Slot == 0 else -1
    CosRight = Cosine(Pi / 2)
    return (
        XValue * CosRight - SignValue * YValue,
        SignValue * XValue + YValue * CosRight,
        0.0,
    )


# the member owns the world text anchor, local witness projection and document precision
def EncodeRectPlacement(
    Corners: tuple[tuple[float, float], ...],
    Length: RectangleLength,
    Pose: SketchDisplayPose,
    Draft: DisplayDraft,
    Slot: int,
) -> bytes:
    RequireArch(
        (Draft.ArrowHead, Draft.Precision, Draft.AltPrecision),
        (0, 2, 2),
        "witnessed local dimension precision and arrows",
    )
    RequireArch(
        len(Pose.TextWorld) == 3
        and all(map(IsFinite, (*Pose.TextWorld, Pose.TextRatio, Pose.WitnessMetres))),
        True,
        "finite independent annotation placement",
    )
    PointValue = DisplayRefPoint(Corners, Length, Pose)
    return (
        PackFields("<3H", Draft.ArrowHead, Draft.ArrowHead, 0)
        + EncodeString("") * KLabelCount
        + PackFields(
            "<22di7H3d",
            *DisplayTextDirection(Pose.Direction, Slot),
            Pose.TextRatio,
            Pose.WitnessMetres,
            KRadius,
            KExtraLeader,
            *KOrigin,
            *KOrigin,
            *PointValue,
            *PointValue,
            *KOrigin,
            0,
            0,
            0,
            0,
            4,
            Draft.Precision,
            Draft.AltPrecision,
            KSmartArrows,
            *Pose.Direction,
        )
    )
