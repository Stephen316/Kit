from convert.Formats.Fusion.MeshCodec.Envelope.ReadEnvelope import ReadEnvelope
from convert.Formats.Fusion.MeshCodec.Geometry.ReadEdges import ReadEdges
from convert.Formats.Fusion.MeshCodec.Geometry.ReadNormals import ReadNormals
from convert.Formats.Fusion.MeshCodec.Geometry.ReadPoints import ReadPoints
from convert.Formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh
from convert.Formats.Fusion.MeshCodec.Registry.ReadRegistry import ReadRegistry
from convert.Formats.Fusion.MeshCodec.Streams.ReadCorners import ReadCorners
from convert.Formats.Fusion.MeshCodec.Streams.ReadStreams import ReadStreams
from convert.Formats.Fusion.MeshCodec.Streams.ReadTerminal import ReadTerminal
from convert.Formats.Fusion.MeshCodec.Validation.CheckMesh import CheckMesh
from convert.Formats.Fusion.MeshCodec.Validation.CheckRegistry import CheckRegistry


# the para mesh operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadParaMesh(Payload: bytes) -> ParaMesh:
    Metadata, Names, Payloads = ReadEnvelope(Payload)
    Registry = ReadRegistry(Metadata, Names)
    CheckRegistry(Registry)
    Streams = ReadStreams(Registry, Payloads)
    Positions = ReadPoints(Streams[Registry.VertexStream])
    Corners, Terminal = ReadCorners(Streams[Registry.CornerStream], len(Positions))
    Result = ParaMesh(
        Registry,
        Positions,
        Corners,
        Terminal,
        ReadNormals(Streams[Registry.NormalStream]),
        ReadTerminal(Streams[Registry.OverrideStream]),
        ReadEdges(Streams[Registry.EdgeStream]),
        ReadTerminal(Streams[Registry.GroupStream]),
    )
    CheckMesh(Result)
    return Result
