from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from tests.convert.formats.FusionCodec.Documents.Mesh.AlterMeshGraph import (
    AlterMeshGraph,
)
from tests.convert.formats.FusionCodec.Documents.Mesh.AlterMeshParts import (
    AlterMeshParts,
)


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
