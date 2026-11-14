from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmText, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


def ReadSketchLink(Table: AsmTable, Identity: int) -> SketchLink:
    Record = RequireAsm(Table, Identity, "ATTRIB_CUSTOM-attrib", 10)
    Tokens = ReadAsmText(Record, 9).split(" ")
    if len(Tokens) != 6:
        raise ValueError("Unsupported Fusion BRep sketch identity")
    Values = tuple(int(Value) for Value in Tokens)
    if Values[3] != 0 or tuple(str(Value) for Value in Values) != tuple(Tokens):
        raise ValueError("Unsupported Fusion BRep sketch identity form")
    return SketchLink(Values[0], Values[1], Values[2], Values[4], Values[5], Values[3])
