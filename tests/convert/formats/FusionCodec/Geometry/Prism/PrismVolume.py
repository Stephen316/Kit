from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.convert.formats.FusionCodec.Geometry.Prism.PrismEvidence import PrismEvidence


def PrismVertices(Value: PrismEvidence, FaceId: int) -> tuple[SpaceVector, ...]:
    return tuple(
        Value.Points[Value.Edges[UseValue.EdgeId].Vertices[int(UseValue.Reverse)]]
        for UseValue in Value.Prism.Rings[FaceId]
    )


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
