from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KLinkClass
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# This map joins the supplied atom and feature identities without choosing their values.
def WriteCmgrLinks(
    Writer: ArchiveWriter, Generation: int, Links: tuple[tuple[int, int], ...]
) -> None:
    RequireArch(
        (type(Generation), Generation), (int, 19000), "CMgr linked atom generation"
    )
    RequireArch(len(Links) <= 1, True, "CMgr zero or one independent atom link")
    if not Links:
        Writer.i32(0)
        return
    ((AtomId, TreeId),) = Links
    RequireArch(
        all(
            type(Value) is int and 0 < Value <= 0x7FFFFFFF for Value in (AtomId, TreeId)
        ),
        True,
        "CMgr positive atom and feature identities",
    )
    RequireArch(KLinkClass in Writer.classes, False, "first CMgr atom link class")
    RequireArch(
        0 < Writer.next_index < KBigObjectTag - 1,
        True,
        "compact CMgr atom link allocation",
    )
    Writer.i32(len(Links))
    Writer.i32(AtomId)
    Writer.BeginObject(KLinkClass, 1)
    Writer.i32(AtomId)
    Writer.u16(1)
    Writer.u32(TreeId)
    Writer.u16(0)
    for _ in range(4):
        Writer.i32(0)
