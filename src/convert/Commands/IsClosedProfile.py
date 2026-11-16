from typing import cast as CastValue

from convert.Geometry.Extrude.Polygon.PrismRing import MeasureRing, ReadPrismRing
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Validation.BrepCurveValidate import GetCurveErrors
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# generator qualification requires supported closed analytic profiles rather than declared profile identifiers alone
def IsClosedProfile(Members: tuple[SketchEntity, ...]) -> bool:
    if any(Entity.construction for Entity in Members):
        return False
    if len(Members) == 1:
        Geometry = Members[0].geometry
        if (
            Members[0].kind != GeometryKind.KCircle
            or not isinstance(Geometry, CircleGeometry)
            or not isinstance(CastValue(object, Geometry.center), PlaneVector)
        ):
            return False
        if not all(
            type(Value) in (float, int)
            for Value in (Geometry.center.x, Geometry.center.y, Geometry.radius)
        ):
            return False
        return not GetCurveErrors(
            CircleCurve(
                "profile",
                SpaceVector(Geometry.center.x, Geometry.center.y, 0.0),
                SpaceVector(0.0, 0.0, 1.0),
                SpaceVector(1.0, 0.0, 0.0),
                Geometry.radius,
            ),
            frozenset(),
        )
    if not 3 <= len(Members) <= 4:
        return False
    Lines = tuple(
        Entity.geometry
        for Entity in Members
        if Entity.kind == GeometryKind.KLine
        and isinstance(Entity.geometry, LineGeometry)
    )
    if len(Lines) != len(Members):
        return False
    if any(
        not isinstance(CastValue(object, PointValue), PlaneVector)
        for LineValue in Lines
        for PointValue in (LineValue.start, LineValue.end)
    ):
        return False
    if not all(
        type(Value) in (float, int)
        for LineValue in Lines
        for PointValue in (LineValue.start, LineValue.end)
        for Value in (PointValue.x, PointValue.y)
    ):
        return False
    try:
        _ = MeasureRing(ReadPrismRing(Lines))
    except (ValueError, OverflowError, TypeError):
        return False
    return True
