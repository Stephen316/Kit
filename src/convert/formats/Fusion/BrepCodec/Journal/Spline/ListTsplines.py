from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf


def ListTsplines(Entities: tuple[KJournalEntity, ...]) -> tuple[TsplineSurf, ...]:
    return tuple(
        Found
        for Value in Entities
        for Found in WalkSubtypes(EntitySubtree(Value))
        if isinstance(Found, TsplineSurf)
    )
