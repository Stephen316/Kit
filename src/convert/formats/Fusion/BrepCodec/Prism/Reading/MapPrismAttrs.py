from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KBodyGeneric,
    KFirstAttribute,
    KFirstFaceTag,
    KFirstSketchTag,
    KSketchOwners,
)
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import KFirstFace
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def MapPrismAttrs(Table: AsmTable, Topology: dict[int, int]) -> dict[int, int]:
    BodyRoot = RequireAsm(Table, 1, "body", 6)
    TimestampId = ReadAsmPtr(BodyRoot, 0)
    Timestamp = RequireAsm(Table, TimestampId, "ATTRIB_CUSTOM-attrib", 8)
    Mapping = {KFirstAttribute: TimestampId, KBodyGeneric: ReadAsmPtr(Timestamp, 2)}
    for Index in range(6):
        FaceValue = RequireAsm(Table, Topology[KFirstFace + Index], "face", 10)
        Mapping[KFirstFaceTag + Index] = ReadAsmPtr(FaceValue, 0)
    for Index, Owners in enumerate(KSketchOwners):
        for Offset, Owner in enumerate(Owners):
            Coedge = RequireAsm(Table, Topology[Owner], "coedge", 11)
            Mapping[KFirstSketchTag + 2 * Index + Offset] = ReadAsmPtr(Coedge, 0)
    return Mapping
