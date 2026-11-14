from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


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
