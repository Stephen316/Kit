from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmInt,
    ReadAsmText,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadFeatureTag(Table: AsmTable, Identity: int) -> FeatureTag:
    Record = RequireAsm(Table, Identity, "ATTRIB_CUSTOM-attrib")
    Count = ReadAsmInt(Record, 14)
    if not 0 <= Count <= 256 or len(Record.Tokens) != 16 + Count:
        raise ValueError("Unsupported Fusion BRep feature tag group")
    PrimaryId = ReadAsmText(Record, 12)
    if ReadAsmInt(Record, 11) != len(PrimaryId.encode("utf-8")):
        raise ValueError("Fusion BRep primary identifier length disagrees")
    return FeatureTag(
        PrimaryId,
        tuple(ReadAsmInt(Record, Index) for Index in range(15, 15 + Count)),
        ReadAsmInt(Record, 13),
        ReadAsmInt(Record, 15 + Count),
    )
