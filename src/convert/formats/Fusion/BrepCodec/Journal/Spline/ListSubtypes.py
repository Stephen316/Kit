from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    DefinedName,
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef


def ListSubtypes(Value: KJournalEntity) -> tuple[tuple[str, int | None], ...]:
    return tuple(
        (
            (Found.Family, Found.Index)
            if isinstance(Found, SubtypeRef)
            else (DefinedName(Found), None)
        )
        for Found in WalkSubtypes(EntitySubtree(Value))
    )
