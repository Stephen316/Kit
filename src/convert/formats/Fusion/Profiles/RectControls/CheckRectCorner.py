from convert.formats.Fusion.Profiles.RectControls.SelectedSides import SelectedSide
from convert.formats.Fusion.Sketches.LinePointIds import ReadLineEnds
from convert.formats.Fusion.Sketches.SketchPrimitive import IsSamePoint
from interchange.enums.EnumGeometry import ConstraintKind
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchRelation
from interchange.geometry.models.VectorPlane import PlaneVector


# the shared sized corner must remain the one used by the independent authored placement control
def CheckRectCorner(
    SketchValue: Sketch,
    Sides: tuple[SelectedSide, ...],
    Geometric: tuple[SketchRelation, ...],
    CornerId: int,
    IsCut: bool,
) -> None:
    Expected = ConstraintKind.KMidpoint if IsCut else ConstraintKind.KCoincident
    Matches = tuple(Value for Value in Geometric if Value.kind == Expected)
    if len(Matches) != 1 or len(Matches[0].references) != 2:
        raise ValueError("Fusion selected rectangle lacks its placement relation")
    First, Second = Matches[0].references
    Entities = {Value.id: Value for Value in SketchValue.entities}
    FirstValue, SecondValue = Entities.get(First.entity_id), Entities.get(
        Second.entity_id
    )
    if (
        FirstValue is None
        or SecondValue is None
        or not isinstance(FirstValue.geometry, PointGeometry)
    ):
        raise ValueError("Fusion rectangle placement operands are unresolved")
    VertexIds = {
        Identity for Value in Sides for Identity in (Value.StartId, Value.FinishId)
    }
    CornerName = f"fusion-sketch-entity-{CornerId}"
    if IsCut:
        Geometry = SecondValue.geometry
        if (
            not SecondValue.construction
            or not isinstance(Geometry, LineGeometry)
            or FirstValue.id
            in {f"fusion-sketch-entity-{Identity}" for Identity in VertexIds}
        ):
            raise ValueError("Fusion Cut midpoint does not use an excluded diagonal")
        EndIds = set(ReadLineEnds(SecondValue))
        if (
            CornerId not in EndIds
            or not EndIds <= VertexIds
            or any(EndIds == {Value.StartId, Value.FinishId} for Value in Sides)
            or not IsSamePoint(
                FirstValue.geometry.point,
                PlaneVector(
                    (Geometry.start.x + Geometry.end.x) / 2.0,
                    (Geometry.start.y + Geometry.end.y) / 2.0,
                ),
            )
        ):
            raise ValueError("Fusion Cut placement diagonal and sized corner disagree")
    elif (
        FirstValue.id != CornerName
        or SecondValue.id
        in {f"fusion-sketch-entity-{Identity}" for Identity in VertexIds}
        or not isinstance(SecondValue.geometry, PointGeometry)
        or not all(
            IsSamePoint(Value, PlaneVector(0.0, 0.0))
            for Value in (FirstValue.geometry.point, SecondValue.geometry.point)
        )
    ):
        raise ValueError(
            "Fusion boss sized corner does not coincide with its separate origin"
        )
