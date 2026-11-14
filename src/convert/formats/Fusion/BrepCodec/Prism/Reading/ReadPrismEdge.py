from convert.formats.Fusion.BrepCodec.Prism.Models.PrismEdge import PrismEdge
from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismRoles import PrismRoles
from convert.formats.Fusion.BrepCodec.Prism.Reading.ReadPrismLine import ReadPrismLine
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmNum,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadPrismEdge(Table: AsmTable, Identity: int, Roles: PrismRoles) -> PrismEdge:
    Record = RequireAsm(Table, Identity, "edge", 11)
    Coedge = RequireAsm(Table, ReadAsmPtr(Record, 7), "coedge", 11)
    LoopValue = RequireAsm(Table, ReadAsmPtr(Coedge, 8), "loop", 6)
    return PrismEdge(
        Roles.Corners[ReadAsmPtr(Record, 3)],
        Roles.Corners[ReadAsmPtr(Record, 5)],
        ReadAsmNum(Record, 4),
        ReadAsmNum(Record, 6),
        Roles.Faces[ReadAsmPtr(LoopValue, 5)],
        ReadPrismLine(Table, ReadAsmPtr(Record, 8)),
    )
