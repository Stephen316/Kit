from Display.Compose import DisplayDraft, KDisplayClass
from Display.Opening import EncodeDisplayOpen
from DisplayBaseFields import EncodeBaseEndFields, EncodeBaseOptFields
from DisplayBaseHead import EncodeBaseHeadFields
from DisplayCache import EncodeDistanceCache, KAuthoredMask, KLoadFixupMask
from DisplayFavorite import EncodeFavoriteFields, KFavoriteClass
from DisplayHandle import EncodeEmptyHandle
from DisplayReturn import EncodeDistReturnFields
from DisplayStyle import EncodeDefaultStyle, EncodeInlineDisplayText
from OriginSketch import KObjectList, KSketchClass
from PartArchive import PartArchiveWriter
from RectDisplayPose import EncodeRectPlacement, SketchDisplayPose
from RectangleDims import KDistanceClass, KDrivingNames, RectangleLength
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KDisplayMode = 200
KSketchHandle = "moSkDimHandleValG2_c"
KSketchCacheBit = 0x40
KDistanceMask = 0x800


# the sketch handle aliases the inline sketch and selects its active dimension slot
def WriteSketchDisplay(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    Slot: int,
    Pose: SketchDisplayPose,
    Placement: bytes,
    Cache: bytes,
    Close: bytes,
) -> None:
    Writer.BeginObject(KDisplayClass, 1)
    Writer.raw(EncodeDisplayOpen(Generation, KDisplayMode, Slot + 10))
    Writer.raw(EncodeDefaultStyle())
    Writer.raw(EncodeInlineDisplayText(Pose.TextWorld, 1))
    Writer.BeginObject(KSketchHandle, 1)
    Writer.raw(EncodeEmptyHandle(Generation))
    Writer.ReferenceObject(Sketch, KSketchClass)
    Writer.i32(Slot)
    Writer.raw(Placement)
    Writer.raw(Cache)
    Writer.BeginObject(KFavoriteClass, 1)
    Writer.raw(EncodeFavoriteFields())
    Writer.raw(Close)


# the typed display order follows the two already allocated distance children
def WriteRectDisplays(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    DistanceObjects: tuple[int, int],
    Corners: tuple[tuple[float, float], ...],
    Lengths: tuple[RectangleLength, RectangleLength],
    Poses: tuple[SketchDisplayPose, SketchDisplayPose],
    Draft: DisplayDraft,
    *,
    Restored: bool = False,
) -> None:
    RequireArch(Generation, 19000, "ordinary sketch display generation")
    RequireArch(type(Restored), bool, "sketch display load-fixup state")
    RequireArch(
        Writer.objects.get(Sketch) == KSketchClass
        and Writer.next_index == Sketch + 38
        and Writer.next_index <= KBigObjectTag - 10
        and 0 < Writer.classes.get(KObjectList, 0) < Writer.next_index
        and all(
            Name not in Writer.classes
            for Name in (KDisplayClass, KSketchHandle, KFavoriteClass)
        ),
        True,
        "first two display objects after the authored logical groups",
    )
    Owned = tuple(
        Index
        for Index, Name in sorted(Writer.objects.items())
        if Index > Sketch and Name == KDistanceClass
    )
    RequireArch(Owned, DistanceObjects, "actual owned distances in display order")
    RequireArch(
        tuple(Length.Name for Length in Lengths),
        KDrivingNames,
        "ordinary sketch display names",
    )
    Placements = tuple(
        EncodeRectPlacement(Corners, Length, Pose, Draft, Slot)
        for Slot, (Length, Pose) in enumerate(zip(Lengths, Poses, strict=True))
    )
    Mask = KAuthoredMask | KSketchCacheBit | (KLoadFixupMask if Restored else 0)
    Caches = tuple(
        EncodeDistanceCache(Length.Millimetres / 1000.0, Mask) for Length in Lengths
    )
    Close = (
        EncodeBaseHeadFields(Draft.Preferences, Draft.Alignment)
        + EncodeBaseOptFields(
            Draft.Preferences, Draft.Standard, Draft.ExtendLeader, Draft.SplitDual
        )
        + EncodeBaseEndFields()
        + EncodeDistReturnFields(KDistanceMask)
    )
    Writer.BeginObject(KObjectList, 1)
    Writer.u16(len(Lengths))
    for Slot, (Pose, Placement, Cache) in enumerate(
        zip(Poses, Placements, Caches, strict=True)
    ):
        WriteSketchDisplay(
            Writer, Generation, Sketch, Slot, Pose, Placement, Cache, Close
        )
