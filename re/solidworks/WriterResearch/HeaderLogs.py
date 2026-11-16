from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KStringMarker,
    EncodeNull,
    EncodeString,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass, KObjectListClass
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KHeaderClass = "moHeader_c"
KStringArray = "su_CStringArray"
KRevisionList = "moLogs_c"
KRevisionStamp = "moStamp_c"
KDefaultIds = (*range(19), *range(21, 26))
KHeaderCounts = (25, 26, 28)
KMaxWord = 0xFFFFFFFF
KMaxTreeId = 0x7FFFFFFF


# The document and every feature retain their own ordered revision times.
@DataClass(frozen=True, slots=True)
class RevisionLog:
    TreeId: int
    Name: str
    CreatedTime: int
    ModifiedTimes: tuple[int, ...]


# Native tree IDs and the shared archive map advance through different operations.
@DataClass(frozen=True, slots=True)
class HeaderLogState:
    UserName: str
    Revisions: tuple[RevisionLog, ...]
    HeaderTime: int
    NextTreeId: int
    UpdateStamp: int


# The observed profile has one creation followed by at most four edits per log.
def CheckLogState(State: HeaderLogState) -> None:
    TreeIds = tuple(Log.TreeId for Log in State.Revisions)
    RequireArch(len(TreeIds) in KHeaderCounts, True, "ModelHeader log count")
    RequireArch(TreeIds[: len(KDefaultIds)], KDefaultIds, "ModelHeader default log IDs")
    RequireArch(
        len(set(TreeIds)) == len(TreeIds)
        and all(0 <= Id < State.NextTreeId <= KMaxTreeId for Id in TreeIds),
        True,
        "ModelHeader tree ID allocation",
    )
    RequireArch(
        bool(State.UserName)
        and all(Log.Name and "\0" not in Log.Name for Log in State.Revisions)
        and "\0" not in State.UserName,
        True,
        "ModelHeader log text",
    )
    RequireArch(0 <= State.UpdateStamp <= KMaxWord, True, "ModelHeader update stamp")
    RequireArch(
        State.HeaderTime,
        State.Revisions[0].CreatedTime,
        "ModelHeader document log time",
    )
    for Log in State.Revisions:
        RequireArch(
            len(Log.ModifiedTimes) <= 4
            and all(
                0 <= Time <= KMaxWord for Time in (Log.CreatedTime, *Log.ModifiedTimes)
            ),
            True,
            "ModelHeader revision times",
        )


# The modern profile stores these names and comments in wide archive strings.
def ReadLogText(Cursor: ArchiveCursor) -> str:
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset),
        True,
        "ModelHeader wide log text",
    )
    return Cursor.ReadText()


# The status enum follows the event kind even when later edits repeat it.
def ReadRevision(Cursor: ArchiveCursor, First: bool) -> RevisionLog:
    _ = Cursor.TakePointer(
        (KRevisionList,), KDefinitionKind if First else KClassRefKind, CompactOnly=True
    )
    (Count,) = Cursor.ReadInts("<H")
    RequireArch(1 <= Count <= 5, True, "ModelHeader revision count")
    Times = []
    for Index in range(Count):
        _ = Cursor.TakePointer(
            (KRevisionStamp,),
            KDefinitionKind if First and Index == 0 else KClassRefKind,
            CompactOnly=True,
        )
        Status, Second, Third, Time = Cursor.ReadInts("<3HI")
        RequireArch(
            (Status, Second, Third, ReadLogText(Cursor)),
            (1, 0, 0, "Modified") if Index else (0, 0, 0, "Created"),
            "ModelHeader revision fields",
        )
        Times.append(Time)
    (TreeId,) = Cursor.ReadInts("<I")
    return RevisionLog(TreeId, ReadLogText(Cursor), Times[0], tuple(Times[1:]))


# Independent root and stamp allocation leaves the live map ready for the self reference.
def ReadHeaderLogs(
    Stream: bytes, Generation: int
) -> tuple[ArchiveCursor, HeaderLogState]:
    RequireArch(Generation, 19000, "ModelHeader log generation")
    Cursor = ArchiveCursor(Stream, 0, 1, {}, {})
    _ = Cursor.TakePointer((KHeaderClass,), KDefinitionKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<I"), (1,), "ModelHeader archive context")
    _ = Cursor.TakePointer((KStringArray,), KDefinitionKind, 0, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (1,), "ModelHeader user count")
    UserName = ReadLogText(Cursor)
    _ = Cursor.TakePointer((KStringArray,), KClassRefKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (1,), "ModelHeader company count")
    RequireArch(ReadLogText(Cursor), "", "ModelHeader empty company name")
    _ = Cursor.TakePointer((KObjectListClass,), KDefinitionKind, CompactOnly=True)
    (Count,) = Cursor.ReadInts("<H")
    RequireArch(Count in KHeaderCounts, True, "ModelHeader log count")
    Revisions = tuple(ReadRevision(Cursor, Index == 0) for Index in range(Count))
    HeaderTime, NextTreeId = Cursor.ReadInts("<2I")
    Cursor.ReadNull()
    (UpdateStamp,) = Cursor.ReadInts("<I")
    Next = ReadTag(Stream, Cursor.Offset)
    RequireArch(
        (Next.kind, Next.class_name, Next.schema),
        (KDefinitionKind, KExtObjectClass, 1),
        "ModelHeader self reference boundary",
    )
    State = HeaderLogState(UserName, Revisions, HeaderTime, NextTreeId, UpdateStamp)
    CheckLogState(State)
    return Cursor, State


# Each log uses a normal class allocation and an inline counted stamp collection.
def WriteRevision(Writer: ArchiveWriter, Log: RevisionLog) -> None:
    Writer.begin_object(KRevisionList, 1)
    Writer.u16(1 + len(Log.ModifiedTimes))
    for Index, Time in enumerate((Log.CreatedTime, *Log.ModifiedTimes)):
        Writer.begin_object(KRevisionStamp, 1)
        Writer.u16(int(Index > 0))
        Writer.u16(0)
        Writer.u16(0)
        Writer.u32(Time)
        Writer.string("Modified" if Index else "Created")
    Writer.u32(Log.TreeId)
    Writer.raw(EncodeString(Log.Name))


# The fresh writer preserves all log allocations for continuation by its caller.
def WriteHeaderLogs(Generation: int, State: HeaderLogState) -> ArchiveWriter:
    RequireArch(Generation, 19000, "ModelHeader log generation")
    CheckLogState(State)
    Writer = ArchiveWriter()
    Writer.SetNextIndex(1)
    Writer.begin_object(KHeaderClass, 1)
    Writer.u32(1)
    Writer.begin_object(KStringArray, 0)
    Writer.u16(1)
    Writer.raw(EncodeString(State.UserName))
    Writer.begin_object(KStringArray, 0)
    Writer.u16(1)
    Writer.string("")
    Writer.begin_object(KObjectListClass, 1)
    Writer.u16(len(State.Revisions))
    for Log in State.Revisions:
        WriteRevision(Writer, Log)
    Writer.u32(State.HeaderTime)
    Writer.u32(State.NextTreeId)
    Writer.raw(EncodeNull())
    Writer.u32(State.UpdateStamp)
    return Writer
