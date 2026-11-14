from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Reading.CheckTopology import CheckTopology
from convert.formats.Fusion.BrepCodec.Reading.GeometryTokens import GeometryTokens
from convert.formats.Fusion.BrepCodec.Reading.MapTopology import MapTopology
from convert.formats.Fusion.BrepCodec.Reading.ProfileRecords import ProfileRecords
from convert.formats.Fusion.BrepCodec.Reading.ReadBrepWire import ReadBrepWire
from convert.formats.Fusion.BrepCodec.Reading.ReadCylinder import ReadCylinder
from convert.formats.Fusion.BrepCodec.Reading.ReadIdentity import ReadIdentity
from convert.formats.Fusion.BrepCodec.Reading.ReadIds import ReadIds
from convert.formats.Fusion.BrepCodec.Reading.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Reading.ReadTagSet import ReadTagSet
from convert.formats.Fusion.BrepCodec.Reading.ReadVertices import ReadVertices
from convert.formats.Fusion.BrepCodec.Topology.HistoryRecords import BuildHistory


def ReadHistory(Payload: bytes) -> HistoryModel:
    WireValue = ReadBrepWire(Payload, True)
    Mapping = MapTopology(ProfileRecords(True), WireValue.Table)
    Model = ReadCylinder(WireValue.Table, Mapping, True)
    Identity = ReadIdentity(WireValue.Table, Mapping)
    TagSet = ReadTagSet(WireValue.Table, Mapping, True)
    Vertices = ReadVertices(WireValue.Table, Mapping, True)
    Tracking = ReadIds(WireValue.Table, Mapping)
    Expected = GeometryTokens(BuildHistory(Model, Identity, TagSet, Vertices, Tracking))
    CheckTopology(Expected, WireValue.Table, Mapping)
    History = ReadJournal(WireValue.Journal, len(WireValue.Table.Records))
    return HistoryModel(
        Model,
        Identity,
        TagSet,
        History,
        WireValue.Stamp,
        WireValue.Header,
        Vertices,
        Tracking,
    )
