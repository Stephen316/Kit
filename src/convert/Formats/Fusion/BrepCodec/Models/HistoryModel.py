from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# history model needs an explicit state contract so topology identity survives native history reconstruction
@MakeDataClass(frozen=True, slots=True)
class HistoryModel:
    Model: CylinderBody
    Identity: BodyIdentity
    TagSet: TopologyTags
    History: HistoryState
    Stamp: GeometryStamp
    Header: BrepHeader
    Vertices: VertexIndices = VertexIndices()
    Tracking: EntityIds = EntityIds()
