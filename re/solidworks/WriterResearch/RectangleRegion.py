from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from OriginSketch import KObjectList, KSketchClass
from PartArchive import PartArchiveWriter
from RectangleCorners import KLineHandle
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KRegionClass = "moSketchRegion_c"


# the serialized sketch update serial and loop enumeration belong to different owners
@Dataclass(frozen=True, slots=True)
class SketchRegionState:
    UpdateSerial: int
    Outline: tuple[int, ...]


# the supporting lines retain their identities as the ordered contour walks every corner
def CheckRectOutline(
    Edges: dict[int, tuple[int, int]], Outline: tuple[int, ...]
) -> None:
    RequireArch(
        len(Edges) == len(Outline) == 4 and set(Outline) == set(Edges),
        True,
        "one contour over the four authored lines",
    )
    Pairs = tuple(frozenset(Edges[Identity]) for Identity in Outline)
    RequireArch(
        len(set(Pairs)) == 4
        and all(len(Pair) == 2 and Pair <= {0, 1, 2, 3} for Pair in Pairs)
        and all(sum(Slot in Pair for Pair in Pairs) == 2 for Slot in range(4))
        and all(
            len(First & Second) == 1
            for First, Second in zip(Pairs, Pairs[1:] + Pairs[:1], strict=True)
        ),
        True,
        "continuous loop through the actual local point slots",
    )


# ordinary sketch presentation keeps the separately supplied regeneration serial
def WriteRegionEnvironment(Writer: PartArchiveWriter, UpdateSerial: int) -> None:
    Writer.raw(
        PackFields("<7H2Hi15i4H", *(0,) * 7, 2, 1, 5, 6, 5, *(1,) * 11, 0, 1, *(0,) * 4)
    )
    Writer.string("")
    Writer.raw(
        PackFields(
            "<Hf3i3dI2i2H5i",
            65535,
            -1.0,
            -1,
            1,
            -1,
            0.0,
            0.0,
            0.0,
            UpdateSerial,
            1,
            0,
            *(0,) * 7
        )
    )


# the outer region and inner boundary lists each allocate under the existing list class
def WriteRectRegion(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    Edges: dict[int, tuple[int, int]],
    State: SketchRegionState,
) -> None:
    RequireArch(Generation, 19000, "ordinary sketch region generation")
    RequireArch(
        Writer.objects.get(Sketch) == KSketchClass
        and Writer.next_index == Sketch + 48
        and Writer.next_index <= KBigObjectTag - 8
        and all(
            0 < Writer.classes.get(Name, 0) < Writer.next_index
            for Name in (KObjectList, KLineHandle)
        )
        and KRegionClass not in Writer.classes,
        True,
        "first region follows the enclosing sketch's two displays",
    )
    RequireArch(
        type(State.UpdateSerial) is int and 0 < State.UpdateSerial <= 0xFFFFFFFF,
        True,
        "explicit sketch update serial",
    )
    CheckRectOutline(Edges, State.Outline)
    WriteRegionEnvironment(Writer, State.UpdateSerial)
    Writer.BeginObject(KObjectList, 1)
    Writer.u16(1)
    Writer.BeginObject(KRegionClass, 1)
    Writer.BeginObject(KObjectList, 1)
    Writer.u16(len(State.Outline))
    for Identity in State.Outline:
        Writer.BeginObject(KLineHandle, 1)
        Writer.raw(PackFields("<H2i", Identity, -1, 0))
    # silhouettes and the post-contour block, loop and slot managers are empty here
    Writer.raw(PackFields("<H7i", *(0,) * 8))
