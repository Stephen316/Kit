from convert.formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadVertices(
    Table: AsmTable, Mapping: dict[int, int], HasHistory: bool
) -> VertexIndices:
    Offset = 0 if HasHistory else 2
    UpperVertex = RequireAsm(Table, Mapping[20 + Offset], "vertex", 6)
    LowerVertex = RequireAsm(Table, Mapping[21 + Offset], "vertex", 6)
    return VertexIndices(ReadAsmInt(UpperVertex, 4), ReadAsmInt(LowerVertex, 4))
