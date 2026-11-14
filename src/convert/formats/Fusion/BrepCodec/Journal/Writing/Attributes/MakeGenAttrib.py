from convert.formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeSysAttrib import (
    MakeSysLinks,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


def MakeNameNode(Value: NameAttrib) -> AsmRecord:
    Fields: list[KAsmToken] = [
        *MakeSysLinks(Value.Links),
        *((21, Action) for Action in Value.Actions),
        (7, Value.NameText),
    ]
    if Value.NumberValue is None:
        return AsmRecord("name_attrib-gen-attrib", tuple(Fields))
    Fields.append((23, Value.NumberValue))
    return AsmRecord("int64_attrib-name_attrib-gen-attrib", tuple(Fields))
