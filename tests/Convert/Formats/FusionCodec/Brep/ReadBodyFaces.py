from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import RequireAsm
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# shared read body faces setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadBodyFaces(Table: AsmTable, RootId: int) -> tuple[AsmRecord, ...]:
    BodyRoot = RequireAsm(Table, RootId, "body", 6)
    LumpRoot = RequireAsm(Table, ReadAsmPtr(BodyRoot, 3), "lump", 6)
    assert ReadAsmPtr(LumpRoot, 5) == RootId
    ShellId = ReadAsmPtr(LumpRoot, 4)
    ShellRoot = RequireAsm(Table, ShellId, "shell", 8)
    Current = ReadAsmPtr(ShellRoot, 5)
    Visited: set[int] = set()
    Faces: list[AsmRecord] = []
    while Current != -1:
        assert Current not in Visited
        Visited.add(Current)
        Record = RequireAsm(Table, Current, "face")
        assert ReadAsmPtr(Record, 5) == ShellId
        Faces.append(Record)
        Current = ReadAsmPtr(Record, 3)
    return tuple(Faces)
