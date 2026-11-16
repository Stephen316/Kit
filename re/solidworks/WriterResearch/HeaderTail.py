from collections.abc import Sequence
from dataclasses import dataclass as DataClass
from math import dist, isclose, isfinite
from struct import pack as PackFields

from HeaderLogs import HeaderLogState, WriteHeaderLogs
from HeaderSelf import HeaderSelf, WriteHeaderSelf
from convert.adapters.solidworks.Container.Archive import KClassRefKind, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import KObjectListClass
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

Point = tuple[float, float, float]
KReferenceFlags = (0, 0, 0, 1, 0)
KFrameTolerance = 1e-15


# Save the world bounds in metres and derive the center and sphere from the same box.
@DataClass(frozen=True, slots=True)
class HeaderBounds:
    Minimum: Point
    Maximum: Point


# Keep times and license fields with their actual owners in the document header.
@DataClass(frozen=True, slots=True)
class HeaderTail:
    BodyStamp: int
    CreationTime: int
    UpdateTime: int
    LicenseFlag: int
    LicenseType: int
    RefFlags: tuple[int, ...]
    VisibleSketches: bool
    TerminalFlag: int
    Bounds: HeaderBounds


# The caller supplies evaluated world points for the supported standalone part.
def BoundPoints(Points: Sequence[Point]) -> HeaderBounds:
    RequireArch(bool(Points), True, "ModelHeader world points")
    RequireArch(
        all(isfinite(Value) for Entry in Points for Value in Entry),
        True,
        "ModelHeader finite world points",
    )
    X, Y, Z = zip(*Points, strict=True)
    return HeaderBounds((min(X), min(Y), min(Z)), (max(X), max(Y), max(Z)))


# The radius is the half diagonal of the axis aligned box.
def FrameValues(Bounds: HeaderBounds) -> tuple[float, ...]:
    Low, High = Bounds.Minimum, Bounds.Maximum
    RequireArch(
        all(
            isfinite(Start) and isfinite(End) and Start <= End
            for Start, End in zip(Low, High, strict=True)
        ),
        True,
        "ModelHeader ordered finite bounds",
    )
    Center = tuple((Start + End) * 0.5 for Start, End in zip(Low, High, strict=True))
    Radius = dist(Center, High)
    RequireArch(all(map(isfinite, (*Center, Radius))), True, "ModelHeader finite frame")
    return (*Center, *High, *Low, Radius)


# The research scope preserves the two license words and the saved reference state.
def RequireHdrTail(Generation: int, State: HeaderTail) -> None:
    RequireArch(Generation, 19000, "ModelHeader tail generation")
    RequireArch(
        all(
            0 <= Word <= 0xFFFFFFFF
            for Word in (State.BodyStamp, State.CreationTime, State.UpdateTime)
        ),
        True,
        "ModelHeader body and time words",
    )
    RequireArch(
        (State.LicenseFlag, State.LicenseType), (4, 2), "ModelHeader license profile"
    )
    RequireArch(State.RefFlags, KReferenceFlags, "ModelHeader external reference flags")
    RequireArch(type(State.VisibleSketches), bool, "ModelHeader visible sketch state")
    RequireArch(State.TerminalFlag, 1, "ModelHeader terminal flag")


# The replacement list allocates one real object and the later time words allocate none.
def ReadHeaderTail(Cursor: ArchiveCursor, Generation: int) -> HeaderTail:
    RequireArch(Generation, 19000, "ModelHeader tail generation")
    BodyStamp, Lock, Detachable, CreationTime, Field60, Usage, FieldC0 = (
        Cursor.ReadInts("<7I")
    )
    RequireArch(
        (Lock, Detachable, Field60, Usage, FieldC0),
        (0, 0, 0, 0, 0),
        "ModelHeader standalone words",
    )
    Cursor.ReadNull()
    Components, LicenseFlag, UpdateTime = Cursor.ReadInts("<3I")
    RequireArch(Components, 0, "ModelHeader standalone component count")
    _ = Cursor.TakePointer((KObjectListClass,), KClassRefKind, CompactOnly=True)
    RequireArch(
        Cursor.ReadInts("<H2iI"),
        (0, 0, 0, 1),
        "ModelHeader replaced components copied freeze and frame state",
    )
    Frame = Cursor.ReadPoint(10)
    Bounds = HeaderBounds(
        (Frame[6], Frame[7], Frame[8]), (Frame[3], Frame[4], Frame[5])
    )
    RequireArch(
        all(
            isclose(Saved, Value, rel_tol=0.0, abs_tol=KFrameTolerance)
            for Saved, Value in zip(Frame, FrameValues(Bounds), strict=True)
        ),
        True,
        "ModelHeader frame geometry",
    )
    RequireArch(Cursor.ReadInts("<3i"), (-1, -1, -1), "ModelHeader unset time words")
    (LicenseType,) = Cursor.ReadInts("<I")
    RequireArch(
        Cursor.ReadInts("<7i"), (0, 0, 0, 0, 0, 0, 0), "ModelHeader content flags"
    )
    RefFlags = Cursor.ReadInts("<5i")
    Visible, Annotated, GfxFeature, Terminal = Cursor.ReadInts("<4i")
    RequireArch(Visible in (0, 1), True, "ModelHeader visible sketch state")
    RequireArch((Annotated, GfxFeature), (0, 0), "ModelHeader annotation flags")
    RequireArch(Cursor.Offset, len(Cursor.BlobValue), "ModelHeader end")
    Result = HeaderTail(
        BodyStamp,
        CreationTime,
        UpdateTime,
        LicenseFlag,
        LicenseType,
        RefFlags,
        bool(Visible),
        Terminal,
        Bounds,
    )
    RequireHdrTail(Generation, Result)
    return Result


# Write the standalone members in owner order without introducing a trailer class.
def WriteHeaderTail(Writer: ArchiveWriter, Generation: int, State: HeaderTail) -> None:
    RequireHdrTail(Generation, State)
    Frame = FrameValues(State.Bounds)
    RequireArch(KObjectListClass in Writer.classes, True, "ModelHeader list class")
    Writer.raw(PackFields("<7I", State.BodyStamp, 0, 0, State.CreationTime, 0, 0, 0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<3I", 0, State.LicenseFlag, State.UpdateTime))
    Writer.begin_object(KObjectListClass, 1)
    Writer.raw(PackFields("<H2iI", 0, 0, 0, 1))
    Writer.raw(PackFields("<10d", *Frame))
    Writer.raw(PackFields("<3iI", -1, -1, -1, State.LicenseType))
    Writer.raw(PackFields("<7i", 0, 0, 0, 0, 0, 0, 0))
    Writer.raw(PackFields("<5i", *State.RefFlags))
    Writer.raw(PackFields("<4i", int(State.VisibleSketches), 0, 0, State.TerminalFlag))


# The revision objects self record and replacement list share one archive allocator.
def WriteModelHdr(
    Generation: int, Logs: HeaderLogState, Self: HeaderSelf, Tail: HeaderTail
) -> ArchiveWriter:
    RequireArch(Self.File.SavedTime, Tail.CreationTime, "ModelHeader shared file time")
    Writer = WriteHeaderLogs(Generation, Logs)
    WriteHeaderSelf(Writer, Generation, Self)
    WriteHeaderTail(Writer, Generation, Tail)
    return Writer
