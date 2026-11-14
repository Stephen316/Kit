from convert.formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.formats.Fusion.BrepCodec.Reading.CheckTopology import CheckTopology
from convert.formats.Fusion.BrepCodec.Reading.GeometryTokens import GeometryTokens
from convert.formats.Fusion.BrepCodec.Reading.MapTopology import MapTopology
from convert.formats.Fusion.BrepCodec.Reading.ProfileRecords import ProfileRecords
from convert.formats.Fusion.BrepCodec.Reading.ReadBrepWire import ReadBrepWire
from convert.formats.Fusion.BrepCodec.Reading.ReadCylinder import ReadCylinder
from convert.formats.Fusion.BrepCodec.Reading.ReadTagSet import ReadTagSet
from convert.formats.Fusion.BrepCodec.Reading.ReadVertices import ReadVertices
from convert.formats.Fusion.BrepCodec.Topology.SnapshotRecords import BuildSnapshot


def ReadSnapshot(Payload: bytes) -> SnapshotModel:
    WireValue = ReadBrepWire(Payload, False)
    Mapping = MapTopology(ProfileRecords(False), WireValue.Table)
    Model = ReadCylinder(WireValue.Table, Mapping, False)
    TagSet = ReadTagSet(WireValue.Table, Mapping, False)
    Vertices = ReadVertices(WireValue.Table, Mapping, False)
    CheckTopology(
        GeometryTokens(BuildSnapshot(Model, TagSet, Vertices)), WireValue.Table, Mapping
    )
    return SnapshotModel(Model, TagSet, WireValue.Stamp, WireValue.Header, Vertices)
