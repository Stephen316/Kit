from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


# the remap entity contract needs a shared interpretation so topology changes retain their native revision relationships
def RemapEntity(Value: KJournalEntity, Mapping: tuple[int, ...]) -> KJournalEntity:
    Record = MakeEntityNode(Value)
    Fields: list[KAsmToken] = []
    for TagValue, Field in Record.Tokens:
        if TagValue == 12 and isinstance(Field, int) and Field >= 0:
            Fields.append((TagValue, Mapping[Field]))
        else:
            Fields.append((TagValue, Field))
    return ReadEntityNode(AsmRecord(Record.Name, tuple(Fields)))
