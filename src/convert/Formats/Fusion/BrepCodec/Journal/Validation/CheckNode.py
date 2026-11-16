from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)


# invalid node input must fail here so inconsistent revision links fail before history reconstruction
def CheckNode(Value: KJournalEntity) -> None:
    Record = MakeEntityNode(Value)
    _ = EmitWireRecord(Record)
    if ReadEntityNode(Record) != Value:
        raise ValueError(
            "Fusion journal entity is outside the qualified semantic model"
        )
