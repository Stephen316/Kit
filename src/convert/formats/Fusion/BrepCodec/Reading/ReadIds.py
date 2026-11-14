from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.BrepCodec.Topology.ApplyIds import (
    KFaceOrdinals,
    KVertexOrdinals,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


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
