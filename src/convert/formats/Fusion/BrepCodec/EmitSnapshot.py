from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.formats.Fusion.BrepCodec.Topology.SnapshotRecords import BuildSnapshot
from convert.formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepRows import EmitBrepRows
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def EmitSnapshot(
    Model: CylinderBody,
    TagSet: TopologyTags,
    Stamp: GeometryStamp,
    Vertices: VertexIndices | None = None,
) -> bytes:
    Records = BuildSnapshot(Model, TagSet, Vertices)
    CheckBrepRefs(Records, 4)
    return (
        EmitBrepHeader(Stamp, 4, False, 10.0)
        + EmitBrepRows(Records)
        + EncodeSmbName("End-of-ASM-data")
    )
