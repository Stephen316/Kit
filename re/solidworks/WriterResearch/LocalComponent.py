from struct import pack as PackFields

from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KUnitComponent = "moUnitComponent_c"
KPartClass = "moPart_c"
KComponentTail = (0,) * 6 + (-1,) * 4 + (0,) * 5


# The compact ordinary reference inherits the class and the owning part object.
def CheckLocalComponent(
    Writer: PartArchiveWriter,
    Generation: int,
    PartObject: int,
    *,
    GhostBodyId: int = 0,
) -> None:
    RequireArch(Generation, 19000, "ordinary local component generation")
    RequireArch(
        0 < Writer.classes.get(KUnitComponent, 0) < Writer.next_index,
        True,
        "inherited local unit component class",
    )
    RequireArch(
        type(PartObject) is int
        and 0 < PartObject < Writer.next_index
        and Writer.objects.get(PartObject) == KPartClass,
        True,
        "local component owning part alias",
    )
    RequireArch(
        type(GhostBodyId) is int and 0 <= GhostBodyId <= 0x7FFFFFFF,
        True,
        "local component ghost body identity",
    )


# A local component allocates its unit object while the part remains an alias.
def WriteLocalComponent(
    Writer: PartArchiveWriter,
    Generation: int,
    PartObject: int,
    *,
    GhostBodyId: int = 0,
) -> None:
    CheckLocalComponent(Writer, Generation, PartObject, GhostBodyId=GhostBodyId)
    Writer.begin_object(KUnitComponent, 1)
    Writer.ReferenceObject(PartObject, KPartClass)
    Writer.raw(
        PackFields("<B20i", 0, 0, 0, 0, GhostBodyId, *KComponentTail, Generation)
    )
