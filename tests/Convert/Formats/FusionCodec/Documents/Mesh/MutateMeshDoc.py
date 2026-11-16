from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from tests.Convert.Formats.FusionCodec.Documents.Mesh.AlterMeshGraph import (
    AlterMeshGraph,
)
from tests.Convert.Formats.FusionCodec.Documents.Mesh.AlterMeshParts import (
    AlterMeshParts,
)


# shared mutate mesh doc setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def MutateMeshDoc(Source: bytes, Variant: str) -> bytes:
    Container = ReadContainer(Source)
    Model = ReadDocument(Source)
    if Variant in ("missing", "uuid", "orphan"):
        Parts = AlterMeshParts(Container.Parts, Model, Variant)
        return EmitContainer(ReplaceValue(Container, Parts=Parts))
    Segment = next(
        Value for Value in Model.Segments if Value.Metadata.Header.SegmentId == 0
    )
    Changed = EmitDocSegment(AlterMeshGraph(Segment, Variant))
    Streams = tuple(
        Changed if Value.SegmentId == 0 else Value for Value in Container.Streams
    )
    return EmitContainer(ReplaceValue(Container, Streams=Streams))
