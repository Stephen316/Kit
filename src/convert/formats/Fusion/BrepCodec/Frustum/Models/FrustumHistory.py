from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


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
