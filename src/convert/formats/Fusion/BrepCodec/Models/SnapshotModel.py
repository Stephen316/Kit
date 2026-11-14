from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


@MakeDataClass(frozen=True, slots=True)
class SnapshotModel:
    Model: CylinderBody
    TagSet: TopologyTags
    Stamp: GeometryStamp
    Header: BrepHeader
    Vertices: VertexIndices = VertexIndices()
