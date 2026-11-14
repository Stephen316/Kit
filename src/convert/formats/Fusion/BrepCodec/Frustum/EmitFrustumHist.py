from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckConeTags import (
    CheckConeTags,
)
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckFrame import CheckFrame
from convert.formats.Fusion.BrepCodec.Frustum.Writing.EmitFrustumRows import (
    EmitFrustumRows,
)
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FreshFrustum import FreshFrustum
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumRecords import (
    FrustumRecords,
)
from convert.formats.Fusion.BrepCodec.History.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


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
