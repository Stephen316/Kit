from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmVec
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def ReadFrameVec(
    Record: AsmRecord, Index: int, TagValue: int
) -> tuple[float, float, float]:
    Vector = ReadAsmVec(Record, Index, TagValue)
    return Vector.x, Vector.y, Vector.z
