from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# snapshot model needs an explicit state contract so topology identity survives native history reconstruction
@MakeDataClass(frozen=True, slots=True)
class SnapshotModel:
    Model: CylinderBody
    TagSet: TopologyTags
    Stamp: GeometryStamp
    Header: BrepHeader
    Vertices: VertexIndices = VertexIndices()
