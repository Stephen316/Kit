from struct import pack as PackFields

from AuthoredProfile import KSketchClass
from PartArchive import PartArchiveWriter
from RectangleCorners import KLineHandle
from RectangleDims import KDistanceClass
from SketchDimBase import WriteDimBase
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# native codes select the constrained coordinate in the sketch's own frame
def RectAxisType(
    Corners: tuple[tuple[float, float], ...], Slots: tuple[int, int]
) -> int:
    RequireArch(
        len(Corners) == 4 and len(Slots) == 2 and all(0 <= Slot < 4 for Slot in Slots),
        True,
        "rectangular axis endpoints",
    )
    First, Second = (Corners[Slot] for Slot in Slots)
    SameX = First[0] == Second[0]
    SameY = First[1] == Second[1]
    RequireArch(SameX != SameY, True, "nonzero local horizontal or vertical line")
    return 5 if SameX else 4


# each logical relation follows the authored order and uses a new local line handle
def WriteRectAxes(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    Corners: tuple[tuple[float, float], ...],
    Edges: dict[int, tuple[int, int]],
    Order: tuple[int, ...],
) -> None:
    RequireArch(Generation, 19000, "ordinary local axis generation")
    RequireArch(
        Writer.objects.get(Sketch) == KSketchClass
        and Writer.next_index == Sketch + 32
        and KDistanceClass in Writer.classes
        and 0 < Writer.classes.get(KLineHandle, 0) < Writer.next_index
        and Writer.next_index <= KBigObjectTag - 4,
        True,
        "axis group follows both local driving dimensions",
    )
    RequireArch(set(Edges), set(range(1, 5)), "four witnessed local line identities")
    RequireArch(
        (len(Order), set(Order)),
        (4, set(Edges)),
        "one ordered axis constraint per edge",
    )
    AxisTypes = tuple(RectAxisType(Corners, Edges[Identity]) for Identity in Order)
    RequireArch(AxisTypes.count(4), 2, "two horizontal and two vertical sides")
    Writer.raw(PackFields("<3H", 0, 0, len(Order)))
    for Identity, AxisType in zip(Order, AxisTypes, strict=True):
        WriteDimBase(Writer, -1, AxisType)
        # logical RefIndex is unset and Derived is false on these saved axes
        Writer.raw(PackFields("<hH", -2, 0))
        Writer.BeginObject(KLineHandle, 1)
        Writer.raw(PackFields("<H2i", Identity, -1, 0))
