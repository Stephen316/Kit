from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import (
    ArchiveFeature,
    CheckArcFeature,
    ReadArcFeature,
    WriteArcFeature,
)
from PartArchive import PartArchiveWriter
from ResolvedFolders import CheckFolderMap, KNameClass
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    EncodeNull,
    EncodeString,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor

KProfileClass = "moProfileFeature_c"
KSketchClass = "sgSketch"
KNodeFlags = (0x40000000, 0xC0000000)
KPointCount = 5


# the saved display flag and regeneration time belong to the feature, not the loop
@Dataclass(frozen=True, slots=True)
class AuthoredProfile:
    Name: str
    TreeId: int
    Flags: int
    Feature: ArchiveFeature


# the authored sketch allocates another object using the class established by Origin
def ReadAuthoredOpen(
    Cursor: ArchiveCursor, Generation: int, OriginSketch: int
) -> tuple[AuthoredProfile, int, int]:
    RequireArch(Generation, 19000, "authored rectangle generation")
    RequireArch(Cursor.Objects.get(OriginSketch), KSketchClass, "owned Origin sketch")
    Cursor.TakePointer((KProfileClass,), KDefinitionKind, CompactOnly=True)
    Cursor.TakePointer((KNameClass,), KClassRefKind, CompactOnly=True)
    Name = Cursor.ReadText()
    State, Flags, TreeId, Secondary = Cursor.ReadInts("<iIii")
    RequireArch((State, Secondary), (0, 0), "ordinary authored profile state")
    RequireArch(Flags in KNodeFlags, True, "authored profile node flags")
    RequireArch(Cursor.ReadText(), "", "absent separate profile label")
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty lightweight node children")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty profile node list")
    Feature = ReadArcFeature(Cursor, Generation, AllowRegenTime=True)
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "no model or absolute plane override")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i"), (0,), "ordinary profile branch")
    SketchOffset = Cursor.Offset
    _, _, SketchIndex = Cursor.TakePointer(
        (KSketchClass,), KClassRefKind, CompactOnly=True
    )
    RequireArch(
        Cursor.ReadCount(), KPointCount, "four corners and separate Origin proxy"
    )
    return AuthoredProfile(Name, TreeId, Flags, Feature), SketchOffset, SketchIndex


# the caller supplies the clean feature state and count from the authored point graph
def WriteAuthoredOpen(
    Writer: PartArchiveWriter,
    Generation: int,
    OriginSketch: int,
    State: AuthoredProfile,
    PointCount: int,
) -> None:
    RequireArch(Generation, 19000, "authored rectangle generation")
    RequireArch(Writer.objects.get(OriginSketch), KSketchClass, "owned Origin sketch")
    RequireArch(
        0 < Writer.classes.get(KSketchClass, 0) < OriginSketch < Writer.next_index,
        True,
        "authored sketch class allocated by Origin",
    )
    RequireArch(
        bool(State.Name) and "\0" not in State.Name and 0 < State.TreeId <= 0x7FFFFFFF,
        True,
        "authored profile name and tree identity",
    )
    RequireArch(State.Flags in KNodeFlags, True, "authored profile node flags")
    RequireArch(PointCount, KPointCount, "four corners and separate Origin proxy")
    CheckArcFeature(Generation, State.Feature, AllowRegenTime=True)
    CheckFolderMap(Writer, (KProfileClass,), 4)
    Name = EncodeString(State.Name)
    Writer.BeginObject(KProfileClass, 1)
    Writer.BeginObject(KNameClass, 1)
    Writer.raw(Name)
    Writer.raw(PackFields("<iIii", 0, State.Flags, State.TreeId, 0))
    Writer.string("")
    Writer.i32(0)
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<Hi", 0, 0))
    WriteArcFeature(Writer, Generation, State.Feature, AllowRegenTime=True)
    Writer.i32(0)
    Writer.i32(0)
    Writer.raw(EncodeNull())
    Writer.i32(0)
    Writer.BeginObject(KSketchClass, 1)
    Writer.i32(PointCount)
