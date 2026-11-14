from itertools import accumulate as Accumulate

from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
    SwapSubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    MapSubtypes,
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef


def ShiftSubtypes(
    Entities: tuple[KJournalEntity, ...], Order: tuple[int, ...]
) -> tuple[KJournalEntity, ...]:
    Counts = tuple(
        sum(
            not isinstance(Found, SubtypeRef)
            for Found in WalkSubtypes(EntitySubtree(Entity))
        )
        for Entity in Entities
    )
    OldStarts = (0, *Accumulate(Counts))
    Ordered = tuple(Counts[Index] for Index in Order)
    NewStarts = dict(zip(Order, (0, *Accumulate(Ordered)), strict=False))
    Mapping = {
        OldStarts[Index] + Offset: NewStarts[Index] + Offset
        for Index in range(len(Entities))
        for Offset in range(Counts[Index])
    }
    if all(Source == Target for Source, Target in Mapping.items()):
        return Entities
    return tuple(
        SwapSubtree(Entity, MapSubtypes(EntitySubtree(Entity), Mapping))
        for Entity in Entities
    )
