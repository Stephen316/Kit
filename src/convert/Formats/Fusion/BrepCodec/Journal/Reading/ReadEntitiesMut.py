from convert.Formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalEntities,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord


# the entities operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadEntitiesMut(
    Cursor: MetaCursor, EndName: str, Width: int = 8
) -> tuple[KJournalEntity, ...]:
    Entities: list[KJournalEntity] = []
    while (NameValue := ReadAsmName(Cursor)) != EndName:
        if len(Entities) >= KJournalEntities:
            raise ValueError("Oversized Fusion journal entity table")
        Entities.append(ReadEntityNode(ReadAsmRecord(Cursor, NameValue, Width)))
    return tuple(Entities)
