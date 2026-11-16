from dataclasses import dataclass

from convert.adapters.solidworks.Config.RootEntry import SeedPartMut
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, KRootClass
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KStringMarker,
    EncodeString,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass, KNodeNameClass
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KRootClasses = {1: KRootClass}
KRootObjects = {2: KRootClass, 3: KExtObjectClass}
KInitialNodeFlags = 0x40000000
KForceRebuilt = 0x20
KModelSave = 0x100
KAppearanceNode = 0x8000
KStoredFlags = KForceRebuilt | KModelSave | KAppearanceNode


# The document's own native node title and graph identity are explicit inputs.
@dataclass(frozen=True)
class ConfigRootState:
    Title: str
    NodeId: int
    Rebuilt: bool
    AppearanceAssigned: bool


def RequireRootState(Generation: int, State: ConfigRootState) -> None:
    RequireArch(
        (type(Generation), Generation, type(State.NodeId), State.NodeId),
        (int, KConfigGen, int, 0),
        "Config-0 standalone first model node",
    )
    RequireArch(
        State.Rebuilt is True and State.AppearanceAssigned is True,
        True,
        "Config-0 clean rebuilt root with assigned appearance",
    )
    RequireArch(
        type(State.Title) is str and bool(State.Title) and "\0" not in State.Title,
        True,
        "Config-0 native model node title",
    )


# The stream begins after its caller has written the root tag and split length.
def WriteConfigRoot(
    Writer: ArchiveWriter, Generation: int, State: ConfigRootState
) -> None:
    RequireRootState(Generation, State)
    RequireArch(
        (Writer.next_index, Writer.classes),
        (4, {KRootClass: 1}),
        "Config-0 initialized root archive and self external object",
    )
    Title = EncodeString(State.Title)
    Writer.i32(0)
    Writer.u32(Generation)
    Writer.BeginObject(KNodeNameClass, 1)
    Writer.raw(Title)
    Writer.i32(0)
    Writer.u32(KInitialNodeFlags)
    Writer.i32(State.NodeId)
    Writer.u32(KStoredFlags)
    Writer.string("")
    Writer.i32(0)


# The split dword bounds the part prefix and the next separately serialized component.
def OpenConfigRoot(BlobValue: bytes) -> tuple[ArchiveCursor, int]:
    Tag = ReadTag(BlobValue, 0)
    Classes: dict[int, str] = {}
    Objects: dict[int, str] = {}
    SeedPartMut(Tag, Classes, Objects)
    RequireArch(Tag.wide, False, "Config-0 compact root class")
    Cursor = ArchiveCursor(BlobValue, Tag.size, 4, Classes, Objects)
    (Length,) = Cursor.ReadInts("<I")
    Split = Cursor.Offset + Length
    RequireArch(
        Cursor.Offset < Split <= len(BlobValue) - 4,
        True,
        "Config-0 bounded first split",
    )
    return Cursor, Split


# The first visual pointer remains available to the enclosing part composition.
def ReadConfigRoot(Cursor: ArchiveCursor, Generation: int) -> ConfigRootState:
    RequireArch(
        (Cursor.NextIndex, Cursor.Classes, Cursor.Objects),
        (4, KRootClasses, KRootObjects),
        "Config-0 first named node archive state",
    )
    RequireArch(Cursor.ReadInts("<iI"), (0, Generation), "Config-0 filed concept words")
    Cursor.TakePointer((KNodeNameClass,), KDefinitionKind, CompactOnly=True)
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset),
        True,
        "Config-0 wide native model title",
    )
    title = Cursor.ReadText()
    update, flags, node_id, stored = Cursor.ReadInts("<iIiI")
    RequireArch(
        (update, flags, stored), (0, KInitialNodeFlags, KStoredFlags), "Config-0 node state"
    )
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset),
        True,
        "Config-0 wide auxiliary node text",
    )
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadInts("<i")), ("", (0,)), "Config-0 absent extras"
    )
    state = ConfigRootState(title, node_id, True, True)
    RequireRootState(Generation, state)
    return state
