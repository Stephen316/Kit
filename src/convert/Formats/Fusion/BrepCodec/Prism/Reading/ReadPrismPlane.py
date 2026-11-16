from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismVec import ReadPrismVec
from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import IsAsmFlag, RequireAsm
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# the prism plane operation needs a distinct decoding boundary so profile topology remains connected to its extrusion history
def ReadPrismPlane(Table: AsmTable, Identity: int) -> PrismPlane:
    Record = RequireAsm(Table, Identity, "plane-surface", 11)
    return PrismPlane(
        ReadPrismVec(Record, 3, 19),
        ReadPrismVec(Record, 4, 20),
        ReadPrismVec(Record, 5, 20),
        IsAsmFlag(Record, 6),
    )
