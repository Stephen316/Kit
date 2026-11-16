from convert.Formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    DefinedName,
    WalkSubtypes,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef


# the list subtypes contract needs a shared interpretation so topology changes retain their native revision relationships
def ListSubtypes(Value: KJournalEntity) -> tuple[tuple[str, int | None], ...]:
    return tuple(
        (
            (Found.Family, Found.Index)
            if isinstance(Found, SubtypeRef)
            else (DefinedName(Found), None)
        )
        for Found in WalkSubtypes(EntitySubtree(Value))
    )
