from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KBodyGeneric,
    KFirstAttribute,
    KPrismRecords,
)
from convert.formats.Fusion.BrepCodec.Prism.Reading.MapPrism import MapPrism
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismTokens import PrismTokens
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismFrame import ReadPrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismGraph import ReadPrismGraph
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismRoles import ReadPrismRoles
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismTags import ReadPrismTags
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismWire import ReadPrismWire
from convert.formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import (
    CheckPrismFrame,
)
from convert.formats.Fusion.BrepCodec.Prism.Validation.CheckPrismTags import (
    CheckPrismTags,
)
from convert.formats.Fusion.BrepCodec.Prism.Writing.PrismRecords import PrismRecords
from convert.formats.Fusion.BrepCodec.Reading.CheckTopology import CheckTopology
from convert.formats.Fusion.BrepCodec.Reading.ReadIdentity import ReadIdentity
from convert.formats.Fusion.BrepCodec.Reading.ReadJournal import ReadJournal
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


def ReadPrismHist(Payload: bytes) -> PrismHistory:
    WireValue = ReadPrismWire(Payload)
    Graph = ReadPrismGraph(WireValue.Table)
    Roles = ReadPrismRoles(Graph)
    Mapping = MapPrism(WireValue.Table, Graph, Roles)
    Frame = ReadPrismFrame(WireValue.Table, Graph, Roles, Mapping)
    Lower, Upper = Frame.CornersCm[0], Frame.CornersCm[7]
    Model = CuboidBody(
        (Upper[0] - Lower[0]) * 10,
        (Upper[1] - Lower[1]) * 10,
        (Upper[2] - Lower[2]) * 10,
        (Lower[0] * 10, Lower[1] * 10, Lower[2] * 10),
    )
    Identity = ReadIdentity(
        WireValue.Table,
        {1: Mapping[1], 26: Mapping[KFirstAttribute], 27: Mapping[KBodyGeneric]},
    )
    TagSet = ReadPrismTags(WireValue.Table, Mapping)
    CheckPrismFrame(Model, Frame)
    CheckPrismTags(Identity, TagSet)
    CheckTopology(
        PrismTokens(PrismRecords(Identity, TagSet, Frame)), WireValue.Table, Mapping
    )
    History = ReadJournal(WireValue.Journal, KPrismRecords)
    return PrismHistory(
        Model, Identity, TagSet, History, WireValue.Stamp, Frame, WireValue.Header
    )
