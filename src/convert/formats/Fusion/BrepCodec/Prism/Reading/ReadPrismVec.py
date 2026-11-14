from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmVec
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def ReadPrismVec(
    Record: AsmRecord, Index: int, TagValue: int
) -> tuple[float, float, float]:
    Value = ReadAsmVec(Record, Index, TagValue)
    return (Value.x, Value.y, Value.z)
