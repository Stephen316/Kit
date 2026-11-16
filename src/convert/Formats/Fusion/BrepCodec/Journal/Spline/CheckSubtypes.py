from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.SubtypeFamily import (
    KSubtypeFamily,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes


# invalid subtypes input must fail here so topology changes retain their native revision relationships
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
