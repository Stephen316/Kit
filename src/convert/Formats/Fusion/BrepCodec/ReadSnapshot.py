from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.Formats.Fusion.BrepCodec.Reading.CheckTopology import CheckTopology
from convert.Formats.Fusion.BrepCodec.Reading.GeometryTokens import GeometryTokens
from convert.Formats.Fusion.BrepCodec.Reading.MapTopology import MapTopology
from convert.Formats.Fusion.BrepCodec.Reading.ProfileRecords import ProfileRecords
from convert.Formats.Fusion.BrepCodec.Reading.ReadBrepWire import ReadBrepWire
from convert.Formats.Fusion.BrepCodec.Reading.ReadCylinder import ReadCylinder
from convert.Formats.Fusion.BrepCodec.Reading.ReadTagSet import ReadTagSet
from convert.Formats.Fusion.BrepCodec.Reading.ReadVertices import ReadVertices
from convert.Formats.Fusion.BrepCodec.Topology.SnapshotRecords import BuildSnapshot


# the snapshot operation needs a distinct decoding boundary so topology identity survives native history reconstruction
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
