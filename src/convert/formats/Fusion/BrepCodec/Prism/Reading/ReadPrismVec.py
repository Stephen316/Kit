from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmVec
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the prism vector operation needs a distinct decoding boundary so profile topology remains connected to its extrusion history
def ReadPrismVec(
    Record: AsmRecord, Index: int, TagValue: int
) -> tuple[float, float, float]:
    Value = ReadAsmVec(Record, Index, TagValue)
    return (Value.x, Value.y, Value.z)
