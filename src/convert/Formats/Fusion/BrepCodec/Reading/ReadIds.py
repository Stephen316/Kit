from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Topology.ApplyIds import (
    KFaceOrdinals,
    KVertexOrdinals,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt, RequireAsm
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# the ids operation needs a distinct decoding boundary so topology identity survives native history reconstruction
def ReadIds(Table: AsmTable, Mapping: dict[int, int]) -> EntityIds:
    return EntityIds(
        tuple(
            ReadAsmInt(RequireAsm(Table, Mapping[Ordinal], "face"), 1)
            for Ordinal in KFaceOrdinals
        ),
        tuple(
            ReadAsmInt(RequireAsm(Table, Mapping[Ordinal], "vertex"), 1)
            for Ordinal in KVertexOrdinals
        ),
    )
