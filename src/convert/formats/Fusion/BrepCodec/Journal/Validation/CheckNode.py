from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)


def CheckNode(Value: KJournalEntity) -> None:
    Record = MakeEntityNode(Value)
    _ = EmitWireRecord(Record)
    if ReadEntityNode(Record) != Value:
        raise ValueError(
            "Fusion journal entity is outside the qualified semantic model"
        )
