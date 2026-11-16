from collections.abc import Callable
from functools import partial as Partial

from convert.adapters.solidworks.Config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.Config.PointerReader import PointerReader
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# scene objects share a concept layout whose absent children delimit the feature fields
def ReadSceneNode(
    Cursor: ArchiveCursor,
    ReadNull: Callable[[], object],
    ExpectedFlags: int,
    ExpectedState: int = 0,
) -> None:
    State, Flags, LinkValue, TrailValue = Cursor.ReadInts("<iIii")
    RequireArch(
        (State, Flags, TrailValue),
        (ExpectedState, ExpectedFlags, 0),
        "witnessed scene concept",
    )
    if ExpectedState == 1:
        RequireArch(LinkValue, -1, "scoped block concept link")
    RequireArch(Cursor.ReadText(), "", "empty scene concept label")
    RequireArch(Cursor.ReadCount(), 0, "empty lightweight scene child list")
    _ = ReadNull()


# scene features must reach their inherited fields before any subclass options
def ReadSceneFeat(
    Cursor: ArchiveCursor,
    ReadNull: Callable[[], object],
    Flags: int,
    ExpectedState: int = 0,
) -> None:
    ReadSceneNode(Cursor, ReadNull, Flags, ExpectedState)
    RequireArch(Cursor.ReadValue("<Hi"), (0, 0), "empty scene feature list and trailer")
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, ReadNull, Cursor.ReadText)


# dated light layouts vary by runtime class and need their own final fields
def ReadLight(
    Cursor: ArchiveCursor,
    ReadPointer: PointerReader,
    ReadNull: Callable[[], object],
    KindValue: str,
    ClassName: str,
) -> None:
    _ = ReadPointer(KindValue, ClassName)
    _ = ReadPointer(KClassRefKind, "moNodeName_c")
    _ = Cursor.ReadText()
    ReadSceneFeat(Cursor, ReadNull, 0xC0000000)
    _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadValue("<3dI4i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<3idid")
    RequireArch(Cursor.ReadValue("<I"), (0,), "empty light user properties")
    if ClassName == "moDirectionLight_c":
        _ = Cursor.ReadPoint(4)


# environment children allocate before the folder returns to the enclosing model
def ReadEnvironment(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    ReadNull = Partial(ReadPointer, KNullKind)
    _ = ReadPointer(KDefinitionKind, "moEnvFolder_c")
    _ = ReadPointer(KClassRefKind, "moNodeName_c")
    _ = Cursor.ReadText()
    ReadSceneNode(Cursor, ReadNull, 0x40000000)
    RequireArch(Cursor.ReadValue("<H"), (4,), "ordinary environment light count")
    ReadLight(Cursor, ReadPointer, ReadNull, KDefinitionKind, "moAmbientLight_c")
    for KindValue in (KDefinitionKind, KClassRefKind, KClassRefKind):
        ReadLight(Cursor, ReadPointer, ReadNull, KindValue, "moDirectionLight_c")
    RequireArch(Cursor.ReadValue("<i"), (0,), "environment child list trailer")
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, ReadNull, Cursor.ReadText)
    _ = Cursor.ReadValue("<2i")


# the block settings must resolve to their own allocated manager
def ReadSketchBlock(
    Cursor: ArchiveCursor, ReadPointer: PointerReader, *, Scoped: bool = False
) -> None:
    ReadNull = Partial(ReadPointer, KNullKind)
    Manager = ReadPointer(KDefinitionKind, "moSketchBlockMgr_c")
    _ = ReadNull()
    ReadSceneFeat(Cursor, ReadNull, 0x40000000, ExpectedState=int(Scoped))
    _ = Cursor.ReadValue("<16s")
    _ = Cursor.ReadValue("<i")
    RequireArch(
        ReadPointer(KObjectRefKind, "moSketchBlockMgr_c"),
        Manager,
        "block settings reference their own manager",
    )
    RequireArch(Cursor.ReadCount(), 0, "empty sketch block table")
    RequireArch(Cursor.ReadCount(), 0, "empty sketch block name table")


# the supported exploded view manager must leave both optional children absent
def ReadExplManager(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    ReadNull = Partial(ReadPointer, KNullKind)
    _ = ReadPointer(KDefinitionKind, "moPrtExplViewManager_c")
    _ = ReadNull()
    ReadSceneFeat(Cursor, ReadNull, 0x40000000)
    _ = ReadNull()
    _ = ReadNull()
    _ = Cursor.ReadValue("<d2i")
    RequireArch(Cursor.ReadValue("<H"), (0,), "empty exploded view word-to-object map")
