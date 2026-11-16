from collections.abc import Mapping
from datetime import datetime, timezone

from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KMoVersionPrefix,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import (
    EmitSldprt,
    ResolveBuild,
    ValidateStreams,
)
from convert.adapters.solidworks.Container.Definition import (
    ArchiveWriter,
    KFirstLoadArrayIndex,
)

KPartGeneration = 19000
KZipTimeStart = int(datetime(1980, 1, 1, tzinfo=timezone.utc).timestamp())
KZipTimeEnd = int(datetime(2108, 1, 1, tzinfo=timezone.utc).timestamp())
KBiographyClass = "moBiography_c"


def VersionStorage(Generation: int) -> str:
    RequireArch(
        (type(Generation), Generation),
        (int, KPartGeneration),
        "modern standalone part generation",
    )
    return f"{KMoVersionPrefix}{Generation}"


# The native loader creates current records when these two prior histories are absent.
def EncodeVersionStreams(Generation: int) -> dict[str, bytes]:
    Root = VersionStorage(Generation)
    Writer = ArchiveWriter()
    Writer.begin_object(KBiographyClass, 1)
    Writer.i32(0)
    return {f"{Root}/History": EncodeNull(), f"{Root}/Biography": Writer.build()}


def CheckVersionStreams(Generation: int, Streams: Mapping[str, bytes]) -> None:
    Root = VersionStorage(Generation)
    History = Streams[f"{Root}/History"]
    HistoryCursor = ArchiveCursor(History, 0, KFirstLoadArrayIndex, {}, {})
    HistoryCursor.ReadNull()
    RequireArch(HistoryCursor.Offset, len(History), "absent prior version history")

    Biography = Streams[f"{Root}/Biography"]
    BiographyCursor = ArchiveCursor(Biography, 0, KFirstLoadArrayIndex, {}, {})
    _ = BiographyCursor.TakePointer(
        (KBiographyClass,), KDefinitionKind, CompactOnly=True
    )
    RequireArch(
        (BiographyCursor.ReadInts("<i"), BiographyCursor.Offset),
        ((0,), len(Biography)),
        "fresh biography with no prior session records",
    )


def EncodeRecordTime(ModifiedTime: int) -> int:
    RequireArch(
        type(ModifiedTime) is int and KZipTimeStart <= ModifiedTime < KZipTimeEnd,
        True,
        "UTC modification time in the ZIP field range",
    )
    Time = datetime.fromtimestamp(ModifiedTime, timezone.utc)
    Date = ((Time.year - 1980) << 9) | (Time.month << 5) | Time.day
    Clock = (Time.hour << 11) | (Time.minute << 5) | (Time.second // 2)
    return (Date << 16) | Clock


# This envelopes caller-owned streams without making native document acceptance claims.
def BuildVersionedArchive(
    Generation: int, ModifiedTime: int, Streams: Mapping[str, bytes]
) -> bytes:
    RequireArch(
        all(
            not Name.replace("\\", "/")
            .partition("/")[0]
            .casefold()
            .startswith(KMoVersionPrefix.casefold())
            for Name in Streams
        ),
        True,
        "version stream ownership belongs to the modern envelope",
    )
    Entries = [*Streams.items(), *EncodeVersionStreams(Generation).items()]
    ValidateStreams(Entries)
    Clock = EncodeRecordTime(ModifiedTime)
    FileId, Signatures, _ = ResolveBuild(None, None, None)
    Clocks = dict.fromkeys((Name for Name, _ in Entries), Clock)
    return EmitSldprt(Entries, FileId, 4, Signatures, Clocks)
