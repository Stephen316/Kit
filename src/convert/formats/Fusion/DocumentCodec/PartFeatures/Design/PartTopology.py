from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EdgeCurve import EdgeEnds
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.PlanBody import VertexKey
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SolidMass import (
    SolidMass,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanExtent import (
    SpanExtent,
)


@MakeDataClass(frozen=True, slots=True)
class PartTopology:
    FaceCount: int
    EdgeCount: int
    VertexCount: int
    VolumeCm: float
    AreaCm: float
    LowerCm: tuple[float, float, float]
    UpperCm: tuple[float, float, float]


def MeasurePart(Solid: PrismSolid) -> PartTopology:
    Shape = BuildShape(Solid)
    Edges = {
        UseValue.Edge
        for FaceValue in Shape.Faces
        for RingValue in FaceValue.Loops
        for UseValue in RingValue
    }
    Points = {VertexKey(Point) for EdgeValue in Edges for Point in EdgeEnds(EdgeValue)}
    Plane = [
        Point
        for SlabValue in Solid.Slabs
        for RingValue in SlabValue.Loops
        for SpanValue in RingValue
        for Point in SpanExtent(SpanValue)
    ]
    MassValue = SolidMass(Solid)
    return PartTopology(
        len(Shape.Faces),
        len(Edges),
        len(Points),
        MassValue["volume"],
        MassValue["area"],
        (
            min(Point[0] for Point in Plane),
            min(Point[1] for Point in Plane),
            Solid.Slabs[0].LowerCm,
        ),
        (
            max(Point[0] for Point in Plane),
            max(Point[1] for Point in Plane),
            Solid.Slabs[-1].UpperCm,
        ),
    )
