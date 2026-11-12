from math import atan2 as ArcTan, hypot as Hypot, isfinite as IsFinite
from math import pi as HalfTurn, sqrt as SquareRoot

from convert.formats.Fusion.Profiles.Trimmed.TrimPortion import TrimPortion
from convert.formats.Fusion.Profiles.Trimmed.TrimSelectors import KTrimMember
from convert.formats.Fusion.Profiles.Trimmed.TrimSources import (
    KTrimDistance,
    KTrimParameter,
)
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import SketchEntity


# proper interior chord intersections locate both limits without using cached edges
def FindChordCuts(
    Circle: CircleGeometry, LineValue: LineGeometry
) -> tuple[tuple[float, float], tuple[float, float]]:
    DeltaX = LineValue.end.x - LineValue.start.x
    DeltaY = LineValue.end.y - LineValue.start.y
    OffsetX = LineValue.start.x - Circle.center.x
    OffsetY = LineValue.start.y - Circle.center.y
    Length = Hypot(DeltaX, DeltaY)
    Radius = Circle.radius
    if (
        not IsFinite(Length)
        or DeltaX <= KTrimDistance
        or abs(DeltaY) > KTrimDistance
        or not KTrimDistance < OffsetY < Radius - KTrimDistance
    ):
        raise ValueError("Unsupported Fusion mixed trimmed profile orientation")
    AxisX, AxisY = DeltaX / Length, DeltaY / Length
    Perpendicular = OffsetY * AxisX - OffsetX * AxisY
    if not KTrimDistance < Perpendicular < Radius - KTrimDistance:
        raise ValueError("Unsupported Fusion mixed trimmed profile tangency")
    Relative = Perpendicular / Radius
    HalfChord = Radius * SquareRoot((1.0 - Relative) * (1.0 + Relative))
    Midpoint = -(OffsetX * AxisX + OffsetY * AxisY)
    Lower, Upper = (Midpoint - HalfChord) / Length, (Midpoint + HalfChord) / Length
    if not KTrimParameter < Lower < Upper < 1.0 - KTrimParameter:
        raise ValueError("Fusion mixed trim requires two interior line cuts")
    Angles = sorted(
        ArcTan(OffsetY + Bound * DeltaY, OffsetX + Bound * DeltaX)
        for Bound in (Lower, Upper)
    )
    if not KTrimParameter < Angles[0] < Angles[1] < HalfTurn - KTrimParameter:
        raise ValueError(
            "Fusion mixed trim requires the captured positive chord segment"
        )
    return (Lower, Upper), (Angles[0], Angles[1])


# mixed selectors identify the middle finite line portion and the matching circle segment
def ReadMixedTrim(
    Circle: CircleGeometry, LineEntity: SketchEntity, Members: tuple[KTrimMember, ...]
) -> tuple[TrimPortion, ...]:
    LineValue = LineEntity.geometry
    if (
        not isinstance(LineValue, LineGeometry)
        or len(Members) != 2
        or len({Entity.id for Entity, _ in Members}) != 2
    ):
        raise ValueError("Unsupported Fusion mixed trimmed profile membership")
    LineBounds, CircleBounds = FindChordCuts(Circle, LineValue)
    Portions: list[TrimPortion] = []
    for Entity, Selector in Members:
        IsLine = Entity.id == LineEntity.id
        if Selector[3:6] != (0, 2, 3 if IsLine else 2):
            raise ValueError("Unsupported Fusion mixed trimmed profile selector")
        Lower, Upper = LineBounds if IsLine else CircleBounds
        Portions.append(TrimPortion(Entity.id, Lower, Upper, Selector))
    return tuple(Portions)
