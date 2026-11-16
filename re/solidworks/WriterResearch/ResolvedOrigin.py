from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import (
    ArchiveFeature,
    CheckArcFeature,
    ReadArcFeature,
    WriteArcFeature,
)
from OriginSketch import (
    KObjectList,
    KPointHandle,
    KSketchClass,
    WriteOriginSketch,
    WriteOriginView,
)
from PartArchive import PartArchiveWriter
from ResolvedFolders import CheckFolderMap, KNameClass, WriteFolderName
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    EncodeNull,
    EncodeString,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.NamedNode import ReadNamedNode
from convert.adapters.solidworks.Resolved.OriginDisplay import ReadOrigViewMut
from convert.adapters.solidworks.Resolved.OriginProfile import (
    ReadOrigGeoMut,
    ReadOriginTail,
)

KOriginClass = "moOriginProfileFeature_c"
KOriginName = "Origin"
KOriginTreeId = 5
KOriginFlags = 0xC0000000
KPlaneRef = "moCompRefPlane_c"
KUnitComponent = "moUnitComponent_c"
KPartClass = "moPart_c"
KComponentWords = (0,) * 10 + (-1,) * 4 + (0,) * 5


# The saved profile state follows the feature stamp and local datum's reference time.
@Dataclass(frozen=True, slots=True)
class OriginState:
    Feature: ArchiveFeature
    PartObject: int
    SupportTreeId: int
    SupportTime: int
    ProfileState: int


# The active archive must continue to the first authored profile after reading Origin.
def ReadOriginRec(Cursor: ArchiveCursor, Generation: int) -> OriginState:
    Cursor.TakePointer((KOriginClass,), KDefinitionKind, CompactOnly=True)
    Cursor.TakePointer((KNameClass,), KClassRefKind, CompactOnly=True)
    RequireArch(
        ReadNamedNode(Cursor, (KOriginFlags,)),
        (KOriginName, KOriginTreeId),
        "resolved origin identity",
    )
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "resolved origin node list")
    Feature = ReadArcFeature(Cursor, Generation, AllowRegenTime=True)
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "resolved origin profile opening")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i"), (0,), "resolved origin alternate profile")
    Cursor.TakePointer((KSketchClass,), KDefinitionKind, CompactOnly=True)
    ReadOrigGeoMut(Cursor)
    ReadOrigViewMut(Cursor)
    Support, ProfileState = ReadOriginTail(Cursor, Generation)
    return OriginState(
        Feature, Support.PartIndex, Support.FeatureId, Support.TimeValue, ProfileState
    )


# The local plane keeps the actual part alias, Front Plane identity and saved reference time.
def WriteOriginRef(
    Writer: PartArchiveWriter, Generation: int, State: OriginState
) -> None:
    Writer.raw(EncodeNull())
    Writer.begin_object(KPlaneRef, 1)
    Writer.begin_object(KUnitComponent, 1)
    Writer.ReferenceObject(State.PartObject, KPartClass)
    Writer.raw(PackFields("<B20i", 0, *KComponentWords, Generation))
    Writer.i32(State.SupportTreeId)
    Writer.u32(State.SupportTime)
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<iB4dB2H", 3, 0, 0.0, 0.0, 0.0, 1.0, 0, 0, 4))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<2iIH", -7, 0, State.ProfileState, 0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<2Hi", 0, 0, 0))


# Origin reserves its sketch, handle and support objects on the same resolved archive.
def WriteOriginRec(
    Writer: PartArchiveWriter, Generation: int, State: OriginState
) -> None:
    CheckArcFeature(Generation, State.Feature, AllowRegenTime=True)
    CheckFolderMap(Writer, (KOriginClass, KSketchClass, KPointHandle, KPlaneRef), 12)
    RequireArch(
        all(
            0 < Writer.classes.get(Name, 0) < Writer.next_index
            for Name in (KObjectList, KUnitComponent)
        ),
        True,
        "inherited resolved origin classes",
    )
    RequireArch(
        type(State.PartObject) is int
        and 0 < State.PartObject < Writer.next_index
        and Writer.objects.get(State.PartObject) == KPartClass,
        True,
        "resolved origin local part alias",
    )
    RequireArch(
        type(State.SupportTreeId) is int
        and State.SupportTreeId == 2
        and all(
            type(Word) is int and 0 <= Word <= 0xFFFFFFFF
            for Word in (State.SupportTime, State.ProfileState)
        ),
        True,
        "resolved origin local reference state",
    )
    Writer.begin_object(KOriginClass, 1)
    WriteFolderName(
        Writer, EncodeString(KOriginName), KOriginTreeId, Flags=KOriginFlags
    )
    Writer.raw(PackFields("<Hi", 0, 0))
    WriteArcFeature(Writer, Generation, State.Feature, AllowRegenTime=True)
    Writer.raw(PackFields("<2i", 0, 0))
    Writer.raw(EncodeNull())
    Writer.i32(0)
    WriteOriginSketch(Writer)
    WriteOriginView(Writer)
    WriteOriginRef(Writer, Generation, State)
