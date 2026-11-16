from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Validation.CheckConeTags import (
    CheckConeTags,
)
from convert.Formats.Fusion.BrepCodec.Frustum.Validation.CheckFrame import CheckFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.EmitFrustumRows import (
    EmitFrustumRows,
)
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FreshFrustum import FreshFrustum
from convert.Formats.Fusion.BrepCodec.Frustum.Writing.FrustumRecords import (
    FrustumRecords,
)
from convert.Formats.Fusion.BrepCodec.History.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# the frustum history operation needs a consistent construction rule so circular boundaries retain consistent cone and rim geometry
def EmitFrustumHist(
    Model: FrustumBody,
    Identity: BodyIdentity,
    TagSet: TopologyTags,
    History: HistoryState,
    Stamp: GeometryStamp,
    Frame: FrustumFrame | None = None,
    Tracking: EntityIds | None = None,
) -> bytes:
    Layout = Frame if Frame is not None else FreshFrustum(Model)
    CheckFrame(Model, Layout)
    CheckConeTags(Identity, TagSet)
    Records = FrustumRecords(Identity, TagSet, Layout, Tracking)
    CheckBrepRefs(Records, 2)
    return (
        EmitBrepHeader(Stamp, 2, True, 50.0)
        + EmitFrustumRows(Records)
        + EmitJournal(History, len(Records))
    )
