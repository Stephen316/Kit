from convert.Formats.Fusion.Sketches.SketchPrimitive import IsSamePoint
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.VectorPlane import PlaneVector


# two orthogonal center dimensions must share the independently identified construction midpoint
def CheckCenterRim(
    SketchValue: Sketch,
    Origin: SketchEntity,
) -> tuple[SketchRelation, tuple[SketchRelation, ...]]:
    Midpoints = tuple(
        Value
        for Value in SketchValue.constraints
        if Value.kind == ConstraintKind.KMidpoint
    )
    if len(Midpoints) != 1 or len(Midpoints[0].references) != 2:
        raise ValueError("Fusion Cut center lacks a unique construction midpoint")
    (Relation,) = Midpoints
    Entities = {Value.id: Value for Value in SketchValue.entities}
    CenterRef, LineRef = Relation.references
    Center = Entities.get(CenterRef.entity_id)
    Diagonal = Entities.get(LineRef.entity_id)
    if (
        Center is None
        or Center.id == Origin.id
        or not isinstance(Center.geometry, PointGeometry)
        or Diagonal is None
        or not Diagonal.construction
        or not isinstance(Diagonal.geometry, LineGeometry)
        or Diagonal.attributes.get("fusion.entity_genesis") != 2
    ):
        raise ValueError("Fusion Cut center midpoint operands disagree")
    Start, Finish = Diagonal.geometry.start, Diagonal.geometry.end
    if not IsSamePoint(
        Center.geometry.point,
        PlaneVector((Start.x + Finish.x) / 2.0, (Start.y + Finish.y) / 2.0),
    ):
        raise ValueError(
            "Fusion Cut construction midpoint does not lie on its measured center"
        )
    AxisKinds = frozenset(
        (ConstraintKind.KDistanceX.value, ConstraintKind.KDistanceY.value)
    )
    Centers = tuple(
        Value
        for Value in SketchValue.constraints
        if Value.kind in AxisKinds
        and Value.driving
        and tuple(Reference.entity_id for Reference in Value.references)
        == (Origin.id, Center.id)
    )
    if len(Centers) != 2 or frozenset(Value.kind for Value in Centers) != AxisKinds:
        raise ValueError(
            "Fusion Cut center dimensions do not share the saved projected origin"
        )
    return Relation, Centers
