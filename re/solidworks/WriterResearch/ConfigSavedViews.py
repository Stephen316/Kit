from math import cos as Cos, sin as Sin
from struct import pack as PackFields

from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    KClassRefKind,
    KDefinitionKind,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPose

KNames = (
    "*Normal To",
    "*Front",
    "*Back",
    "*Left",
    "*Right",
    "*Top",
    "*Bottom",
    "*Isometric",
    "*Trimetric",
    "*Dimetric",
)
KViewClass = "moView_c"
KObjectList = "suObList"
KColorTable = "moFeatColorTab_c"
KQuarterTurn = 1.5707963267949
KObliqueYaw = 0.78539816339745
KCameraAngles = (
    None,
    None,
    (-3.1415926535898, 0.0),
    (-KQuarterTurn, 0.0),
    (KQuarterTurn, 0.0),
    (0.0, -KQuarterTurn),
    (0.0, KQuarterTurn),
    (KObliqueYaw, -0.6154030942531942),
    (0.4855505979048, -0.5410520681182),
    (KObliqueYaw, -0.2712241657599),
)
KUnitPose = (0.0, 0.0, 0.0, 1.0)
KMatrixTolerance = 4e-16
KViewReturn = "<Hid5id3i"
KModelViewState = (0, 50, 108)
KModelViewEnd = (12, 0, 0)


# The standard camera uses the native yaw and pitch in model coordinates.
def CameraBasis(Yaw: float, Pitch: float) -> tuple[float, ...]:
    Cy, Sy = Cos(Yaw), Sin(Yaw)
    Cx, Sx = Cos(Pitch), Sin(Pitch)
    return (Cy, Sy * Sx, Sy * Cx, 0.0, Cx, -Sx, -Sy, Cy * Sx, Cy * Cx)


# A view inherits identity translation and keeps the second transform neutral.
def WriteCameraPose(
    Writer: PartArchiveWriter, Angles: tuple[float, float] | None
) -> None:
    Writer.u8(int(Angles is not None))
    if Angles is not None:
        Writer.raw(PackFields("<9d", *CameraBasis(*Angles)))
    Writer.raw(PackFields("<4dB", *KUnitPose, 0))


# The local default table keeps each view occurrence and its actual archive schema.
def WriteSavedViews(Writer: PartArchiveWriter, Generation: int) -> None:
    RequireArch(Generation, 19000, "ordinary saved view generation")
    Slots = 14 + int(KObjectList not in Writer.classes)
    RequireArch(
        0 < Writer.next_index <= KBigObjectTag - Slots
        and KViewClass not in Writer.classes
        and KColorTable not in Writer.classes,
        True,
        "ordinary saved view archive allocation",
    )
    Writer.raw(EncodeNull())
    Writer.begin_object(KObjectList, 1)
    Writer.u16(0)
    for Index, (Name, Angles) in enumerate(zip(KNames, KCameraAngles, strict=True)):
        Writer.begin_object(KViewClass, 1)
        Writer.string(Name)
        WriteCameraPose(Writer, Angles)
        WriteCameraPose(Writer, None)
        Writer.raw(
            PackFields(KViewReturn, 0, -1, -1.0, 0, Index, 0, 0, 0, 0.0, 0, 0, 0)
        )
    Writer.raw(PackFields("<B2i", *KModelViewState))
    Writer.begin_object(KColorTable, 0)
    Writer.i32(0)
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<3i", *KModelViewEnd))


# Only the composed rotation doubles allow the native trig rounding difference.
def ReadCameraBasis(
    Cursor: ArchiveCursor, Angles: tuple[float, float] | None
) -> tuple[int, int] | None:
    Start = Cursor.Offset
    Basis, ShiftScale = ReadLocalPose(Cursor)
    RequireArch(ShiftScale, KUnitPose, "ordinary saved camera translation and scale")
    if Angles is None:
        RequireArch(Basis, None, "omitted identity camera basis")
        return None
    RequireArch(
        Basis is not None
        and all(
            abs(Actual - Expected) <= KMatrixTolerance
            for Actual, Expected in zip(Basis, CameraBasis(*Angles), strict=True)
        ),
        True,
        "native standard camera rotation",
    )
    return Start + 1, Start + 73


# The caller can compare all bytes outside the explicitly identified basis doubles.
def ReadSavedViewBases(
    Cursor: ArchiveCursor, Generation: int
) -> tuple[tuple[int, int], ...]:
    RequireArch(Generation, 19000, "ordinary saved view generation")
    Cursor.ReadNull()
    ListKind = (
        KClassRefKind if KObjectList in Cursor.Classes.values() else KDefinitionKind
    )
    _ = Cursor.TakePointer((KObjectList,), ListKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty named view list")
    Ranges = []
    for Index, (Name, Angles) in enumerate(zip(KNames, KCameraAngles, strict=True)):
        Kind = KDefinitionKind if Index == 0 else KClassRefKind
        _ = Cursor.TakePointer((KViewClass,), Kind, CompactOnly=True)
        RequireArch(Cursor.ReadText(), Name, "native standard view name")
        Range = ReadCameraBasis(Cursor, Angles)
        if Range is not None:
            Ranges.append(Range)
        _ = ReadCameraBasis(Cursor, None)
        RequireArch(
            Cursor.ReadValue(KViewReturn),
            (0, -1, -1.0, 0, Index, 0, 0, 0, 0.0, 0, 0, 0),
            "ordinary view inherited settings and empty collections",
        )
    RequireArch(Cursor.ReadInts("<B2i"), KModelViewState, "ordinary model view state")
    _ = Cursor.TakePointer((KColorTable,), KDefinitionKind, 0, CompactOnly=True)
    RequireArch(Cursor.ReadCount(), 0, "empty saved feature color table")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<3i"), KModelViewEnd, "ordinary model view return")
    return tuple(Ranges)
