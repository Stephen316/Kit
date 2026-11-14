from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Frustum.Reading.FrustumTokens import FrustumTokens
from convert.formats.Fusion.BrepCodec.Frustum.Reading.MapFrustum import MapFrustum
from convert.formats.Fusion.BrepCodec.Frustum.Reading.ReadConeFrame import ReadConeFrame
from convert.formats.Fusion.BrepCodec.Frustum.Reading.ReadFrustumBody import (
    ReadFrustumBody,
)
from convert.formats.Fusion.BrepCodec.Frustum.Reading.ReadRimFrame import ReadRimFrame
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckConeTags import (
    CheckConeTags,
)
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckFrame import CheckFrame
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FrustumRecords import (
    FrustumRecords,
)
from convert.formats.Fusion.BrepCodec.Reading.CheckTopology import CheckTopology
from convert.formats.Fusion.BrepCodec.Reading.ProfileRecords import ProfileRecords
from convert.formats.Fusion.BrepCodec.Reading.ReadBrepWire import ReadBrepWire
from convert.formats.Fusion.BrepCodec.Reading.ReadIdentity import ReadIdentity
from convert.formats.Fusion.BrepCodec.Reading.ReadIds import ReadIds
from convert.formats.Fusion.BrepCodec.Reading.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Reading.ReadTagSet import ReadTagSet


def ReadFrustumHist(Payload: bytes) -> FrustumHistory:
    WireValue = ReadBrepWire(Payload, True)
    History = ReadJournal(WireValue.Journal, len(WireValue.Table.Records))
    Mapping = MapFrustum(ProfileRecords(True), WireValue.Table)
    Frame = FrustumFrame(
        ReadConeFrame(WireValue.Table, Mapping),
        ReadRimFrame(WireValue.Table, Mapping, True),
        ReadRimFrame(WireValue.Table, Mapping, False),
    )
    Model = ReadFrustumBody(Frame)
    Identity = ReadIdentity(WireValue.Table, Mapping)
    TagSet = ReadTagSet(WireValue.Table, Mapping, True)
    CheckFrame(Model, Frame)
    CheckConeTags(Identity, TagSet)
    Tracking = ReadIds(WireValue.Table, Mapping)
    Expected = FrustumTokens(FrustumRecords(Identity, TagSet, Frame, Tracking))
    CheckTopology(Expected, WireValue.Table, Mapping)
    return FrustumHistory(
        Model,
        Identity,
        TagSet,
        History,
        WireValue.Stamp,
        WireValue.Header,
        Frame,
        Tracking,
    )
