from interchange import TopologySummary
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.Transform import KTransformIdentity
from interchange.geometry.models.VectorSpace import SpaceVector


# the bounds of linear edges are determined by their saved vertex coordinates
def LinearPartBox(ModelValue: BrepModel) -> BoundingBox | None:
    if not ModelValue.vertices or not ModelValue.edges or not all(
        isinstance(Curve, LineCurve) for Curve in ModelValue.curves
    ) or not all(isinstance(Surface, PlaneSurface) for Surface in ModelValue.surfaces):
        return None
    Points = tuple(Value.point for Value in ModelValue.vertices)
    return BoundingBox(
        SpaceVector(min(Point.x for Point in Points), min(Point.y for Point in Points), min(Point.z for Point in Points)),
        SpaceVector(max(Point.x for Point in Points), max(Point.y for Point in Points), max(Point.z for Point in Points)),
    )


# per body counts require one unambiguous selected body in the current neutral document
def PartTopology(
    ModelValue: BrepModel | None, BodyId: str, Fallback: TopologySummary,
) -> TopologySummary:
    if ModelValue is None or len(ModelValue.bodies) != 1:
        return Fallback
    (BodyValue,) = ModelValue.bodies
    if (
        BodyValue.design_body_id != BodyId
        or set(BodyValue.region_ids) != {Value.id for Value in ModelValue.regions}
        or BodyValue.wire_ids
        or BodyValue.vertex_ids
    ):
        return Fallback
    Bounds = LinearPartBox(ModelValue) if BodyValue.transform == KTransformIdentity else None
    return TopologySummary(
        solid_count=sum(Region.solid for Region in ModelValue.regions),
        shell_count=len(ModelValue.shells),
        face_count=len(ModelValue.faces),
        edge_count=len(ModelValue.edges),
        vertex_count=len(ModelValue.vertices),
        bounding_box=Bounds if Bounds is not None else Fallback.bounding_box,
    )
