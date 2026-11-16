from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismVec import ReadPrismVec
from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmNum,
    RequireAsm,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# the prism line operation needs a distinct decoding boundary so profile topology remains connected to its extrusion history
def ReadPrismLine(Table: AsmTable, Identity: int) -> PrismLine:
    Record = RequireAsm(Table, Identity, "straight-curve")
    if len(Record.Tokens) not in (7, 9):
        raise ValueError("Unsupported prism straight-curve interval")
    Bounded = len(Record.Tokens) == 9
    if (
        IsAsmFlag(Record, 5) != Bounded
        or IsAsmFlag(Record, 7 if Bounded else 6) != Bounded
    ):
        raise ValueError("Unsupported prism straight-curve bound flags")
    return PrismLine(
        ReadPrismVec(Record, 3, 19),
        ReadPrismVec(Record, 4, 20),
        ReadAsmNum(Record, 6) if Bounded else None,
        ReadAsmNum(Record, 8) if Bounded else None,
    )
