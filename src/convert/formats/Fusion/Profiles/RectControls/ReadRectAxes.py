from math import isclose as IsClose

from convert.formats.Fusion.Profiles.RectControls.SelectedSides import SelectedSide
from interchange.enums.EnumGeometry import ConstraintKind
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchRelation

# exact native axis types distinguish width and height without relying on parameter names
KRectAxes = frozenset(
    (ConstraintKind.KHorizontal.value, ConstraintKind.KVertical.value)
)


# four linked geometric rules corroborate the exact selected rectangle sides
def ReadRectAxes(
    Sides: tuple[SelectedSide, ...], Relations: tuple[SketchRelation, ...]
) -> dict[str, SketchRelation]:
    AxisRules: dict[str, SketchRelation] = {}
    for Relation in Relations:
        if Relation.kind not in KRectAxes:
            continue
        if len(Relation.references) != 1:
            raise ValueError("Fusion rectangle axis rule lacks one native line")
        Identity = Relation.references[0].entity_id
        if Identity in AxisRules:
            raise ValueError("Fusion rectangle axis rules repeat a side")
        AxisRules[Identity] = Relation
    if (
        set(AxisRules) != {Value.Entity.id for Value in Sides}
        or sum(Value.kind == ConstraintKind.KHorizontal for Value in AxisRules.values())
        != 2
    ):
        raise ValueError(
            "Fusion rectangle axis rules do not cover the selected profile"
        )
    for SideValue in Sides:
        Geometry = SideValue.Entity.geometry
        if not isinstance(Geometry, LineGeometry):
            raise ValueError("Fusion rectangle axis rule targets a nonline side")
        Deltas = (Geometry.end.x - Geometry.start.x, Geometry.end.y - Geometry.start.y)
        AxisIndex = int(AxisRules[SideValue.Entity.id].kind == ConstraintKind.KVertical)
        if (
            not IsClose(Deltas[1 - AxisIndex], 0.0, abs_tol=1e-8)
            or abs(Deltas[AxisIndex]) <= 1e-8
        ):
            raise ValueError("Fusion rectangle axis rule disagrees with its saved line")
    return AxisRules
