from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Formats.FusionCodec.Geometry.Prism.PrismEvidence import PrismEvidence


# shared prism vertices setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def PrismVertices(Value: PrismEvidence, FaceId: int) -> tuple[SpaceVector, ...]:
    return tuple(
        Value.Points[Value.Edges[UseValue.EdgeId].Vertices[int(UseValue.Reverse)]]
        for UseValue in Value.Prism.Rings[FaceId]
    )


# shared prism volume setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def PrismVolume(Value: PrismEvidence) -> float:
    Anchor = next(iter(Value.Points.values()))
    Result = 0.0
    for FaceId in Value.Prism.Rings:
        Corners = tuple(
            OffsetVector(Point, Anchor, -1) for Point in PrismVertices(Value, FaceId)
        )
        for Index in (1, 2):
            Result += (
                DotVector(Corners[0], CrossVector(Corners[Index], Corners[Index + 1]))
                / 6
            )
    return Result
