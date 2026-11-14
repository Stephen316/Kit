from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def MapRegion(
    Table: AsmTable, BodyRoot: int, Start: int, AttrStart: int
) -> dict[int, int]:
    LumpId = ReadAsmPtr(RequireAsm(Table, BodyRoot, "body", 6), 3)
    ShellId = ReadAsmPtr(RequireAsm(Table, LumpId, "lump", 6), 4)
    FaceId = ReadAsmPtr(RequireAsm(Table, ShellId, "shell", 8), 5)
    FaceValue = RequireAsm(Table, FaceId, "face", 11 if BodyRoot == 2 else 10)
    LoopId = ReadAsmPtr(FaceValue, 4)
    Current = ReadAsmPtr(RequireAsm(Table, LoopId, "loop", 6), 4)
    Mapping = {
        Start: LumpId,
        Start + 1: ShellId,
        Start + 2: FaceId,
        Start + 3: LoopId,
        Start + 4: ReadAsmPtr(FaceValue, 7),
    }
    for Index in range(4):
        Coedge = RequireAsm(Table, Current, "coedge", 11)
        EdgeId = ReadAsmPtr(Coedge, 6)
        EdgeValue = RequireAsm(Table, EdgeId, "edge", 11)
        VertexId = ReadAsmPtr(EdgeValue, 3)
        Mapping.update(
            {
                Start + 5 + Index: Current,
                Start + 9 + Index: EdgeId,
                Start + 13 + Index: VertexId,
                Start + 17 + Index: ReadAsmPtr(EdgeValue, 8),
                Start
                + 21
                + Index: ReadAsmPtr(RequireAsm(Table, VertexId, "vertex", 6), 5),
                AttrStart + Index: ReadAsmPtr(Coedge, 0),
                AttrStart + 4 + Index: ReadAsmPtr(EdgeValue, 0),
            }
        )
        Current = ReadAsmPtr(Coedge, 3)
    if Current != Mapping[Start + 5] or len(set(Mapping.values())) != 33:
        raise ValueError("Unsupported rectangular snapshot region topology")
    return Mapping
