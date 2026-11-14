from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Reading.ReadFeatureTag import ReadFeatureTag
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmInt,
    ReadAsmNum,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadIdentity(Table: AsmTable, Mapping: dict[int, int]) -> BodyIdentity:
    BodyRoot = RequireAsm(Table, Mapping[1], "body", 6)
    Timestamp = RequireAsm(Table, Mapping[26], "ATTRIB_CUSTOM-attrib", 8)
    Generic = ReadFeatureTag(Table, Mapping[27])
    Number = int(Generic.PrimaryId)
    if str(Number) != Generic.PrimaryId or Generic.OperationIds or Generic.ApproachId:
        raise ValueError("Invalid Fusion BRep body operation identity")
    return BodyIdentity(
        ReadAsmInt(BodyRoot, 1),
        Number,
        Generic.SecondaryId,
        ReadAsmNum(Timestamp, 7),
    )
