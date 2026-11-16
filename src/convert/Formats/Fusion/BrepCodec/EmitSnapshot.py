from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.BrepCodec.Topology.SnapshotRecords import BuildSnapshot
from convert.Formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepRows import EmitBrepRows
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# the snapshot operation needs a consistent construction rule so topology identity survives native history reconstruction
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
