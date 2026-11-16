from struct import pack as PackFields

from AuthoredProfile import KSketchClass
from OriginProxy import KPointBackup
from OriginSketch import KPointHandle
from PartArchive import PartArchiveWriter
from SketchDimBase import WriteDimBase
from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KAnchorSlots = (4, 0)


# the two distinct coincident points keep their separate identities in the existing sketch
def WriteRectAnchor(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    Points: tuple[tuple[float, float], ...],
    Slots: tuple[int, int],
) -> None:
    RequireArch(Generation, 19000, "ordinary Origin coincidence generation")
    RequireArch(
        Writer.objects.get(Sketch) == KSketchClass
        and Writer.next_index == Sketch + 36
        and Writer.objects.get(Sketch + 19) == KPointBackup
        and 0 < Writer.classes.get(KPointHandle, 0) < Writer.next_index
        and Writer.next_index <= KBigObjectTag - 2,
        True,
        "coincidence follows the axis handles of the authored sketch",
    )
    RequireArch(
        (len(Points), Slots), (5, KAnchorSlots), "ordered Origin proxy and local corner"
    )
    RequireArch(
        tuple(Points[Slot] for Slot in Slots),
        ((0.0, 0.0), (0.0, 0.0)),
        "two points at the anchored local Origin",
    )
    Writer.u16(1)
    WriteDimBase(Writer, -1, 9)
    Writer.raw(PackFields("<hH", -2, 0))
    for Slot in Slots:
        Writer.BeginObject(KPointHandle, 1)
        Writer.raw(PackFields("<H2i", Slot, -1, 0))
    Writer.raw(PackFields("<2H", 0, 0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<H2i2d", 0, -1, -1, 0.0, 0.0))
    for _ in range(3):
        Writer.raw(EncodeNull())
    Writer.raw(PackFields("<Hi6H", 0, -1, *(0,) * 6))
