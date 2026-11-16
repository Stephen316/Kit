from dataclasses import dataclass as Dataclass
from math import isfinite as IsFinite
from struct import pack as PackFields

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# these feature version values describe the pinned generation and application build
KBuildVersion = 2026225
KFileSession = 370108
KFeatureDisplay = (0, 65535, 0, 3, 0xFFFFFFFF, 65535, -1, -1.0)
KFeatureReturn = (0, 4, 0, 0, 0, -1)
KFeatureEnd = (2, KFileSession, 1)


# A feature keeps its update stamp and last update version alongside its FILETIME.
@Dataclass(frozen=True, slots=True)
class ArchiveFeature:
    UpdateStamp: int
    LastGeneration: int
    LastBuild: int
    FileTime: Stamp
    RegenTime: float = 0.0


# manager and part features take independent high and low words from their callers
def RequireCmgrTime(Generation: int, StampValue: Stamp) -> None:
    RequireArch(Generation, 19000, "CMgr inherited feature generation")
    RequireArch(
        all(
            type(Word) is int and 0 <= Word <= 0xFFFFFFFF
            for Word in (StampValue.high, StampValue.low)
        ),
        True,
        "CMgr unsigned FILETIME words",
    )


# callers can validate every feature before changing the live archive allocator
def CheckArcFeature(
    Generation: int, State: ArchiveFeature, *, AllowRegenTime: bool = False
) -> None:
    RequireCmgrTime(Generation, State.FileTime)
    RequireArch(
        type(State.UpdateStamp) is int
        and 0 <= State.UpdateStamp <= 0xFFFFFFFF
        and all(
            type(Word) is int and 0 <= Word <= 0x7FFFFFFF
            for Word in (State.LastGeneration, State.LastBuild)
        ),
        True,
        "ordinary feature update words",
    )
    CheckRegenTime(State.RegenTime, AllowRegenTime)


# the folder and manager paths keep the existing exact zero timing field
def CheckRegenTime(Value: float, Allowed: bool) -> None:
    RequireArch(
        (
            IsFinite(Value) and Value >= 0.0
            if Allowed
            else PackFields("<d", Value) == bytes(8)
        ),
        True,
        "ordinary feature regeneration time",
    )


# the ordinary feature branch saves the version and timestamp fields separately
def WriteArcFeature(
    Writer: ArchiveWriter,
    Generation: int,
    State: ArchiveFeature,
    *,
    AllowRegenTime: bool = False,
) -> None:
    CheckArcFeature(Generation, State, AllowRegenTime=AllowRegenTime)
    Writer.raw(
        PackFields(
            "<iiIBiiiidi",
            0,
            0,
            State.UpdateStamp,
            0,
            0,
            State.LastGeneration,
            State.LastBuild,
            Generation,
            State.RegenTime,
            KBuildVersion,
        )
    )
    Writer.u16(0)
    Writer.string("")
    Writer.raw(PackFields("<BHHBIHhf", *KFeatureDisplay))
    Writer.i32(0)
    Writer.i32(0)
    Writer.u16(0)
    Writer.raw(
        PackFields(
            "<IBBiiiIIHii",
            *KFeatureReturn,
            State.FileTime.high,
            State.FileTime.low,
            *KFeatureEnd,
        )
    )


# the shared feature reader guards the inactive members before returning saved state
def ReadArcFeature(
    Cursor: ArchiveCursor, Generation: int, *, AllowRegenTime: bool = False
) -> ArchiveFeature:
    RequireArch(Generation, 19000, "CMgr inherited feature generation")
    (
        First,
        Second,
        UpdateStamp,
        HasText,
        Fourth,
        LastGeneration,
        LastBuild,
        Version,
    ) = Cursor.ReadInts("<iiIBiiii")
    (RegenTime,) = Cursor.ReadPoint(1)
    (Build,) = Cursor.ReadInts("<i")
    RequireArch(
        (First, Second, HasText, Fourth, Version, Build),
        (0, 0, 0, 0, Generation, KBuildVersion),
        "CMgr inherited feature opening",
    )
    CheckRegenTime(RegenTime, AllowRegenTime)
    RequireArch(
        min(LastGeneration, LastBuild) >= 0, True, "ordinary feature update version"
    )
    Cursor.ReadNull()
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadValue("<BHHBIHhf")),
        ("", KFeatureDisplay),
        "CMgr inherited feature display style",
    )
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "CMgr inherited feature members")
    Cursor.ReadNull()
    Fields = Cursor.ReadInts("<IBBiiiIIHii")
    RequireArch(
        (Fields[:6], Fields[8:]),
        (KFeatureReturn, KFeatureEnd),
        "CMgr inherited feature return",
    )
    return ArchiveFeature(
        UpdateStamp, LastGeneration, LastBuild, Stamp(Fields[6], Fields[7]), RegenTime
    )


# both configuration manager classes start with the native initial update words
def WriteCmgrFeature(Writer: ArchiveWriter, Generation: int, StampValue: Stamp) -> None:
    WriteArcFeature(Writer, Generation, ArchiveFeature(101, 0, 0, StampValue))


# manager and part timestamps vary while their default update words stay fixed
def ReadCmgrFeature(Cursor: ArchiveCursor, Generation: int) -> Stamp:
    State = ReadArcFeature(Cursor, Generation)
    RequireArch(
        (State.UpdateStamp, State.LastGeneration, State.LastBuild),
        (101, 0, 0),
        "CMgr inherited feature update words",
    )
    return State.FileTime
