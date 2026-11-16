from dataclasses import dataclass as Dataclass
from math import isclose as IsClose
from struct import pack as PackFields

from AuthoredProfile import KSketchClass
from BlindDepth import DepthFields, WriteDepthMut
from OriginProxy import KPointBackup
from OriginSketch import KPointHandle
from PartArchive import PartArchiveWriter
from ResolvedFolders import KNameClass
from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KDistanceClass = "sgPntPntDist"
KLengthClass = "moLengthParameter_c"
KDrivingNames = ("width_mm", "height_mm")


# both driving dimensions keep their own identity, local name and system length
@Dataclass(frozen=True, slots=True)
class RectangleLength:
    Name: str
    Identity: int
    Millimetres: float


# choose the incident edge by its physical distance, including exchanged local axes on YZ
def RectLengthSlots(
    Corners: tuple[tuple[float, float], ...], Metres: float
) -> tuple[int, int]:
    RequireArch(len(Corners), 4, "four corners for local driving length")
    RequireArch(Corners[0], (0.0, 0.0), "measured anchored rectangle")
    Ends = [
        Slot
        for Slot, (XValue, YValue) in enumerate(Corners[1:], 1)
        if (XValue == 0) != (YValue == 0)
        and IsClose(abs(XValue + YValue), Metres, rel_tol=0.0, abs_tol=1e-15)
    ]
    RequireArch(len(Ends), 1, "one local edge matching the driving length")
    return 0, Ends[0]


# the named scalar remains owned by its distance while both operands allocate new handles
def WriteRectLength(
    Writer: PartArchiveWriter,
    Identity: int,
    Name: bytes,
    Value: bytes,
    Slots: tuple[int, int],
) -> int:
    Writer.BeginObject(KDistanceClass, 1)
    ObjectIndex = Writer.next_index - 1
    Writer.i32(0)
    WriteDepthMut(Writer, Name, Value)
    NullValue = EncodeNull()
    Writer.raw(NullValue)
    Writer.raw(PackFields("<4i", Identity, 0, 0, 0))
    Writer.raw(NullValue)
    Writer.raw(PackFields("<HBi4H", 0, 0, 1, 2, 0, 0, 0))
    for Slot in Slots:
        Writer.BeginObject(KPointHandle, 1)
        Writer.raw(PackFields("<H2i", Slot, -1, 0))
    Writer.raw(PackFields("<4H", 1, 1, 1, 0))
    Writer.raw(NullValue)
    Writer.raw(PackFields("<3d", 0.0, 0.0, 0.0))
    return ObjectIndex


# the ordinary inline sketch owns two independently editable distances and no other geometry
def WriteRectDims(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    Corners: tuple[tuple[float, float], ...],
    Lengths: tuple[RectangleLength, RectangleLength],
) -> tuple[int, int]:
    RequireArch(Generation, 19000, "ordinary rectangle dimension generation")
    RequireArch(
        Writer.objects.get(Sketch) == KSketchClass
        and Writer.next_index == Sketch + 20
        and Writer.objects.get(Writer.next_index - 1) == KPointBackup
        and all(
            0 < Writer.classes.get(Name, 0) < Writer.next_index
            for Name in (KNameClass, KPointHandle)
        )
        and all(Name not in Writer.classes for Name in (KDistanceClass, KLengthClass))
        and Writer.next_index <= KBigObjectTag - 12,
        True,
        "first pair of owned sketch dimensions",
    )
    Width, Height = Lengths
    RequireArch(
        (Width.Name, Height.Name), KDrivingNames, "ordinary driving dimension roles"
    )
    RequireArch(
        all(
            type(Length.Identity) is int and 0 < Length.Identity <= 0x7FFFFFFF
            for Length in Lengths
        )
        and Width.Identity != Height.Identity,
        True,
        "distinct allocated dimension identities",
    )
    WidthName, WidthValue = DepthFields(Width.Name, Width.Millimetres)
    HeightName, HeightValue = DepthFields(Height.Name, Height.Millimetres)
    WidthSlots = RectLengthSlots(Corners, Width.Millimetres / 1000.0)
    HeightSlots = RectLengthSlots(Corners, Height.Millimetres / 1000.0)
    RequireArch(WidthSlots != HeightSlots, True, "distinct width and height edges")
    Writer.raw(PackFields("<11i2H", *(0,) * 12, len(Lengths)))
    return (
        WriteRectLength(Writer, Width.Identity, WidthName, WidthValue, WidthSlots),
        WriteRectLength(Writer, Height.Identity, HeightName, HeightValue, HeightSlots),
    )
