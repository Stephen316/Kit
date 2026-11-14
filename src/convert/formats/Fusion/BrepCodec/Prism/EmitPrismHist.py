from convert.formats.Fusion.BrepCodec.History.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import (
    CheckPrismFrame,
)
from convert.formats.Fusion.BrepCodec.Prism.Validation.CheckPrismTags import (
    CheckPrismTags,
)
from convert.formats.Fusion.BrepCodec.Prism.Writing.EmitPrismRows import EmitPrismRows
from convert.formats.Fusion.BrepCodec.Prism.Writing.FreshPrism import FreshPrism
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismRecords import PrismRecords
from convert.formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


def EmitPrismHist(
    Model: CuboidBody,
    Identity: BodyIdentity,
    TagSet: PrismTags,
    History: HistoryState,
    Stamp: GeometryStamp,
    Frame: PrismFrame | None = None,
) -> bytes:
    Layout = Frame if Frame is not None else FreshPrism(Model)
    CheckPrismFrame(Model, Layout)
    CheckPrismTags(Identity, TagSet)
    Records = PrismRecords(Identity, TagSet, Layout)
    CheckBrepRefs(Records, 2)
    return (
        EmitBrepHeader(Stamp, 2, True, 50.0)
        + EmitPrismRows(Records)
        + EmitJournal(History, len(Records))
    )
