from convert.formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.formats.Fusion.BrepCodec.Frustum.Reading.ReadFrameVec import ReadFrameVec
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmNum,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadConeFrame(Table: AsmTable, Mapping: dict[int, int]) -> ConeFrame:
    Surface = RequireAsm(Table, Mapping[17], "cone-surface", 17)
    return ConeFrame(
        ReadFrameVec(Surface, 3, 19),
        ReadFrameVec(Surface, 4, 20),
        ReadFrameVec(Surface, 5, 20),
        ReadAsmNum(Surface, 6),
        ReadAsmNum(Surface, 9),
        ReadAsmNum(Surface, 10),
        ReadAsmNum(Surface, 11),
        IsAsmFlag(Surface, 12),
    )
