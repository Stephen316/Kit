from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalEntities,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord


def ReadEntitiesMut(
    Cursor: MetaCursor, EndName: str, Width: int = 8
) -> tuple[KJournalEntity, ...]:
    Entities: list[KJournalEntity] = []
    while (NameValue := ReadAsmName(Cursor)) != EndName:
        if len(Entities) >= KJournalEntities:
            raise ValueError("Oversized Fusion journal entity table")
        Entities.append(ReadEntityNode(ReadAsmRecord(Cursor, NameValue, Width)))
    return tuple(Entities)
