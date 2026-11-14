from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubtypeFamily import (
    KSubtypeFamily,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes


def CheckSubtypes(Entities: tuple[KJournalEntity, ...]) -> None:
    Families: list[str] = []
    for Value in Entities:
        for KindName, Index in ListSubtypes(Value):
            if Index is None:
                Families.append(KSubtypeFamily[KindName])
            elif not 0 <= Index < len(Families) or Families[Index] != KindName:
                raise ValueError(
                    "Fusion subtype reference precedes or mismatches its definition"
                )
