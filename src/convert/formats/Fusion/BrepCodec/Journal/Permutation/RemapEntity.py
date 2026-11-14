from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


def RemapEntity(Value: KJournalEntity, Mapping: tuple[int, ...]) -> KJournalEntity:
    Record = MakeEntityNode(Value)
    Fields: list[KAsmToken] = []
    for TagValue, Field in Record.Tokens:
        if TagValue == 12 and isinstance(Field, int) and Field >= 0:
            Fields.append((TagValue, Mapping[Field]))
        else:
            Fields.append((TagValue, Field))
    return ReadEntityNode(AsmRecord(Record.Name, tuple(Fields)))
