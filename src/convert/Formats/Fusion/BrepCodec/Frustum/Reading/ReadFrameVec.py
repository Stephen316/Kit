from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmVec
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the frame vector operation needs a distinct decoding boundary so circular boundaries retain consistent cone and rim geometry
def ReadFrameVec(
    Record: AsmRecord, Index: int, TagValue: int
) -> tuple[float, float, float]:
    Vector = ReadAsmVec(Record, Index, TagValue)
    return Vector.x, Vector.y, Vector.z
