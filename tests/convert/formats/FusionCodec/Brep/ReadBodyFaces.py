from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


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
