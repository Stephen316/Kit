from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# The caller selects the witnessed thread reference mode and standalone archive lane.
def WriteCmgrBaseEnd(
    Writer: ArchiveWriter,
    *,
    Generation: int,
    ConditionOne: bool,
    AtomCount: int,
    NewThreadRefs: bool,
) -> None:
    RequireArch(
        (type(Generation), Generation, ConditionOne is False, NewThreadRefs is True),
        (int, 19000, True, True),
        "CMgr base return scope",
    )
    RequireArch(
        type(AtomCount) is int and AtomCount in (0, 1),
        True,
        "CMgr base return independent atom count",
    )
    Writer.i32(0)
    Writer.i32(0)
    Writer.i32(0)
    Writer.i32(0)
    Writer.i32(2)
    Writer.i32(0)
    Writer.i32(0)
    Writer.raw(EncodeNull())
    Writer.i32(0)
