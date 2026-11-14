from struct import pack as PackValue

from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh
from convert.formats.Fusion.MeshCodec.Streams.EmitCorners import EmitCorners
from convert.formats.Fusion.MeshCodec.Streams.EmitTerminal import EmitTerminal


def MakePayloads(Value: ParaMesh) -> dict[str, bytes]:
    Registry = Value.Registry
    return {
        Registry.VertexStream: b"".join(
            PackValue("<fff", Point.XCoord, Point.YCoord, Point.ZCoord)
            for Point in Value.Positions
        ),
        Registry.CornerStream: EmitCorners(Value.Corners, Value.TerminalWord),
        Registry.NormalStream: b"".join(
            PackValue("<ff", Normal.First, Normal.Second) for Normal in Value.Normals
        ),
        Registry.OverrideStream: EmitTerminal(Value.Overrides),
        Registry.EdgeStream: EmitTerminal(
            tuple(
                Number
                for EdgeValue in Value.Edges
                for Number in (EdgeValue.First, EdgeValue.Second)
            )
        ),
        Registry.GroupStream: EmitTerminal(Value.FaceGroups),
    }
