from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# frustum history needs an explicit state contract so circular boundaries retain consistent cone and rim geometry
@MakeDataClass(frozen=True, slots=True)
class FrustumHistory:
    Model: FrustumBody
    Identity: BodyIdentity
    TagSet: TopologyTags
    History: HistoryState
    Stamp: GeometryStamp
    Header: BrepHeader
    Frame: FrustumFrame
    Tracking: EntityIds = EntityIds()
