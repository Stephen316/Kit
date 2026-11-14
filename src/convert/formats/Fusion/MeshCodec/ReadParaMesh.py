from convert.formats.Fusion.MeshCodec.Envelope.ReadEnvelope import ReadEnvelope
from convert.formats.Fusion.MeshCodec.Geometry.ReadEdges import ReadEdges
from convert.formats.Fusion.MeshCodec.Geometry.ReadNormals import ReadNormals
from convert.formats.Fusion.MeshCodec.Geometry.ReadPoints import ReadPoints
from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh
from convert.formats.Fusion.MeshCodec.Registry.ReadRegistry import ReadRegistry
from convert.formats.Fusion.MeshCodec.Streams.ReadCorners import ReadCorners
from convert.formats.Fusion.MeshCodec.Streams.ReadStreams import ReadStreams
from convert.formats.Fusion.MeshCodec.Streams.ReadTerminal import ReadTerminal
from convert.formats.Fusion.MeshCodec.Validation.CheckMesh import CheckMesh
from convert.formats.Fusion.MeshCodec.Validation.CheckRegistry import CheckRegistry


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
