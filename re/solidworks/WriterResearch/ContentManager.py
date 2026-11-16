# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Encode the one-configuration backward compatibility content manager."""

from dataclasses import dataclass

from PartFraming import VersionStorage
from convert.adapters.solidworks.Container.Archive import KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the content manager belongs to a dedicated storage outside contents
CONTENT_MANAGER = "SwDocContentMgr/SwDocContentMgrInfo"

# the compound flags belong to the witnessed ordinary single configuration
ORDINARY_FLAGS = 0x80400180

# the installed density getter supplied this value with no density override
UNSET_DENSITY = -1.0

# these native unit getter triples have independent metric and inch witnesses
OBSERVED_UNITS = ((0, 4, 1), (3, 2, 3))


# the timestamps and update stamp come from the saved part header
@dataclass(frozen=True, slots=True)
class ContentClock:
    Created: int
    Updated: int
    UpdateStamp: int


# the atom supplies the body name and the inverse of its blanked state
@dataclass(frozen=True, slots=True)
class ContentBody:
    AtomId: int
    Name: str
    Visible: bool


# the caller owns the active configuration and file context for the one observed shape
@dataclass(frozen=True, slots=True)
class ContentState:
    ConfigName: str
    MaterialName: str
    MaterialId: str
    ConfigFlags: int
    Density: float
    Units: tuple[int, int, int]
    Clock: ContentClock
    Body: ContentBody | None


# the narrow member cannot represent additional bodies or configuration state
def ValidateContent(Generation: int, State: ContentState) -> None:
    VersionStorage(Generation)
    RequireArch(
        all(
            isinstance(Text, str) and bool(Text) and "\0" not in Text
            for Text in (State.ConfigName, State.MaterialName, State.MaterialId)
        ),
        True,
        "nonempty content configuration and material labels",
    )
    RequireArch(
        type(State.ConfigFlags) is int
        and State.ConfigFlags == ORDINARY_FLAGS
        and type(State.Density) is float
        and State.Density == UNSET_DENSITY
        and all(type(Unit) is int for Unit in State.Units)
        and State.Units in OBSERVED_UNITS,
        True,
        "witnessed ordinary content flags density and native units",
    )
    Clock = State.Clock
    RequireArch(
        all(
            type(Word) is int and 0 <= Word <= 0xFFFFFFFF
            for Word in (Clock.Created, Clock.Updated, Clock.UpdateStamp)
        )
        and Clock.Created <= Clock.Updated,
        True,
        "ordered header times and unsigned content update word",
    )
    Body = State.Body
    if Body is not None:
        RequireArch(
            type(Body.AtomId) is int
            and 0 < Body.AtomId <= 0x7FFFFFFF
            and isinstance(Body.Name, str)
            and bool(Body.Name)
            and "\0" not in Body.Name
            and type(Body.Visible) is bool,
            True,
            "positive owned body atom and explicit visibility",
        )


# each configuration map has one entry owned by the same saved configuration
def WriteConfigKey(Writer: ArchiveWriter, Name: str) -> None:
    Writer.i32(1)
    Writer.string(Name)


# the two folder serializers count independent keyed maps backed by one atom
def WriteFolders(Writer: ArchiveWriter, State: ContentState) -> None:
    Body = State.Body
    Count = int(Body is not None)
    WriteConfigKey(Writer, State.ConfigName)
    Writer.i32(Count)
    if Body is not None:
        Writer.u32(Count)
        Writer.i32(Body.AtomId)
        Writer.string(Body.Name)

    WriteConfigKey(Writer, State.ConfigName)
    Writer.i32(Count)
    if Body is not None:
        Writer.i32(Count)
        Writer.i32(Body.AtomId)
        Writer.i32(int(Body.Visible))


# all fields and map counts are encoded independently from their caller state
def EncodeContentManager(Generation: int, State: ContentState) -> bytes:
    ValidateContent(Generation, State)
    Writer = ArchiveWriter()
    Writer.BeginObject("moBCModeInfo_c", 1)
    Writer.string("")
    Writer.u32(State.Clock.Created)
    Writer.string("")
    Writer.i32(0)
    Writer.u16(0)

    WriteConfigKey(Writer, State.ConfigName)
    Writer.string(State.MaterialName)
    WriteConfigKey(Writer, State.ConfigName)
    Writer.string(State.MaterialId)
    WriteConfigKey(Writer, State.ConfigName)
    Writer.i32(0)

    Writer.string(State.ConfigName)
    Writer.BeginObject("su_CStringArray", 0)
    Writer.u16(0)
    Writer.u32(State.Clock.Updated)

    WriteConfigKey(Writer, State.ConfigName)
    Writer.string("")
    for Unit in State.Units:
        Writer.i32(Unit)
    WriteFolders(Writer, State)

    Writer.u32(State.Clock.UpdateStamp)
    WriteConfigKey(Writer, State.ConfigName)
    Writer.u32(State.ConfigFlags)
    WriteConfigKey(Writer, State.ConfigName)
    Writer.f64(State.Density)
    for _ in range(2):
        WriteConfigKey(Writer, State.ConfigName)
        Writer.i32(0)
    return Writer.Build()


# the native maps must use the reached configuration even when their values are empty
def CheckConfigKey(Cursor: ArchiveCursor, Name: str) -> None:
    RequireArch(
        (Cursor.ReadCount(), Cursor.ReadText()),
        (1, Name),
        "one matching content configuration key",
    )


# a populated folder has one repeated count before the atom payload
def ReadFolderCount(Cursor: ArchiveCursor, Name: str, RepeatedFormat: str) -> int:
    CheckConfigKey(Cursor, Name)
    (Count,) = Cursor.ReadInts("<i")
    RequireArch(Count in (0, 1), True, "empty or single body folder")
    if Count:
        RequireArch(
            Cursor.ReadInts(RepeatedFormat), (Count,), "repeated body folder count"
        )
    return Count


# both folder maps must resolve the same atom before publishing its body state
def ReadFolders(Cursor: ArchiveCursor, Name: str) -> ContentBody | None:
    if not ReadFolderCount(Cursor, Name, "<I"):
        RequireArch(
            ReadFolderCount(Cursor, Name, "<i"), 0, "empty body visibility folder"
        )
        return None
    (Atom,) = Cursor.ReadInts("<i")
    Label = Cursor.ReadText()
    RequireArch(ReadFolderCount(Cursor, Name, "<i"), 1, "one body visibility entry")
    Owner, Visible = Cursor.ReadInts("<2i")
    RequireArch(Owner, Atom, "body folder name and visibility owner")
    RequireArch(Visible in (0, 1), True, "body folder visibility flag")
    return ContentBody(Atom, Label, bool(Visible))


# the first member verifies default constructor fields before reaching its configuration
def ReadContentStart(Cursor: ArchiveCursor) -> tuple[int, str, str, str]:
    Cursor.TakePointer(("moBCModeInfo_c",), KDefinitionKind, CompactOnly=True)
    RequireArch(Cursor.ReadText(), "", "empty leading content label")
    (Created,) = Cursor.ReadInts("<I")
    RequireArch(Cursor.ReadText(), "", "empty compatibility content label")
    RequireArch(Cursor.ReadInts("<iH"), (0, 0), "ordinary part and empty inline list")
    RequireArch(Cursor.ReadCount(), 1, "one material-name map entry")
    Name, Material = Cursor.ReadText(), Cursor.ReadText()
    CheckConfigKey(Cursor, Name)
    MaterialId = Cursor.ReadText()
    CheckConfigKey(Cursor, Name)
    RequireArch(Cursor.ReadInts("<i"), (0,), "single configuration index")
    RequireArch(Cursor.ReadText(), Name, "most recent saved configuration")
    Cursor.TakePointer(
        ("su_CStringArray",), KDefinitionKind, SchemaValue=0, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty saved external references")
    return Created, Name, Material, MaterialId


# the saved member closes after the final configuration flag map
def ReadContentManager(Generation: int, Payload: bytes) -> ContentState:
    VersionStorage(Generation)
    Cursor = ArchiveCursor(Payload, 0, 1, {}, {})
    Created, Name, Material, MaterialId = ReadContentStart(Cursor)
    (Updated,) = Cursor.ReadInts("<I")
    CheckConfigKey(Cursor, Name)
    RequireArch(Cursor.ReadText(), "", "unparented ordinary configuration")
    Length, System, Mass = Cursor.ReadInts("<3i")
    Body = ReadFolders(Cursor, Name)
    (UpdateStamp,) = Cursor.ReadInts("<I")
    CheckConfigKey(Cursor, Name)
    (Flags,) = Cursor.ReadInts("<I")
    CheckConfigKey(Cursor, Name)
    (Density,) = Cursor.ReadPoint(1)
    for Reason in ("no exploded view", "no configuration update request"):
        CheckConfigKey(Cursor, Name)
        RequireArch(Cursor.ReadInts("<i"), (0,), Reason)
    RequireArch(
        (Cursor.Offset, Cursor.NextIndex),
        (len(Payload), 5),
        "complete content-manager extent and object map",
    )
    State = ContentState(
        Name,
        Material,
        MaterialId,
        Flags,
        Density,
        (Length, System, Mass),
        ContentClock(Created, Updated, UpdateStamp),
        Body,
    )
    ValidateContent(Generation, State)
    return State
