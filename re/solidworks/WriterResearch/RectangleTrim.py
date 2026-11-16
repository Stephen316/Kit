from collections.abc import Sequence
from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrExternal import ExternalFile, RequireExtScope, RequireExtState, WriteExtRecord
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Resolved.ContourSurf import KTrimTypes, ProfileOwner

KProfileClass = "moProfileFeature_c"
KSurfaceClass = "moSimpleSurfIdRep_c"
KReferenceClass = "moFR_c"


# preserve native trim side separately from the sketch member's persistent identifier
@Dataclass(frozen=True, slots=True)
class TrimMember:
    ClassName: str
    EdgeId: int


# the feature and saved document keep independent time and rebuild state
@Dataclass(frozen=True, slots=True)
class RectTrimState:
    DerivedStamp: int
    ReferenceTime: int
    File: ExternalFile
    Members: tuple[TrimMember, ...]


# refuse unsupported contours before the first trim allocation or bytes are written
def CheckTrimState(
    Writer: PartArchiveWriter,
    Generation: int,
    Owner: ProfileOwner,
    EdgeIds: Sequence[int],
    ContourMode: int,
    State: RectTrimState,
) -> None:
    ClassNames = frozenset(Writer.classes)
    RequireExtScope(Generation, Writer.next_index, ClassNames)
    RequireArch(
        ClassNames.isdisjoint((KSurfaceClass, KReferenceClass, *KTrimTypes))
        and Writer.next_index <= KBigObjectTag - 19,
        True,
        "first compact trim allocations",
    )
    RequireArch(
        Writer.objects.get(Owner["profile_object"]) == KProfileClass
        and type(Owner["native_feature_id"]) is int
        and 0 < Owner["native_feature_id"] <= 0x7FFFFFFF,
        True,
        "current profile allocation and native feature ID",
    )
    RequireArch(
        type(ContourMode) is int
        and ContourMode in (0, 1)
        and type(State.DerivedStamp) is int
        and 0 <= State.DerivedStamp <= 0xFFFFFFFF
        and type(State.ReferenceTime) is int
        and 0 <= State.ReferenceTime < 0xFFFFFFFF,
        True,
        "ordinary trim mode and time state",
    )
    RequireArch(
        len(State.Members) == len(EdgeIds) == len(set(EdgeIds)) == 4
        and sorted(Member.EdgeId for Member in State.Members) == sorted(EdgeIds)
        and all(
            type(Member.EdgeId) is int and 0 < Member.EdgeId <= 0x7FFFFFFF
            for Member in State.Members
        )
        and all(
            sum(Member.ClassName == Name for Member in State.Members) == 2
            for Name in KTrimTypes
        ),
        True,
        "four owned trim members in the witnessed side classes",
    )
    RequireArch(State.File.ConfigName, "Default", "standalone trim configuration")
    RequireExtState(State.File, SelfReference=False)
    _ = EncodeString(State.File.FilePath), EncodeString(State.File.Title)


# all five feature-reference objects carry the same typed owner and feature stamp
def BeginTrimRef(Writer: PartArchiveWriter, Name: str, ProfileIndex: int) -> None:
    Writer.BeginObject(Name, 1)
    Writer.ReferenceObject(ProfileIndex, KProfileClass)
    Writer.BeginObject(KReferenceClass, 1)


# the caller can reuse the unique document object in the following feature
def WriteRectTrim(
    Writer: PartArchiveWriter,
    Generation: int,
    Owner: ProfileOwner,
    EdgeIds: Sequence[int],
    ContourMode: int,
    State: RectTrimState,
) -> int:
    CheckTrimState(Writer, Generation, Owner, EdgeIds, ContourMode, State)
    ProfileIndex, FeatureId = Owner["profile_object"], Owner["native_feature_id"]
    Writer.raw(
        PackFields("<3H2iI2H", 0, 4, 0, -1, 0, State.DerivedStamp, ContourMode, 0)
    )
    Writer.u16(1)
    BeginTrimRef(Writer, KSurfaceClass, ProfileIndex)
    FileIndex = Writer.next_index + 1
    WriteExtRecord(Writer, Generation, State.File, SelfReference=False, ModifiedTime=0)
    Writer.raw(PackFields("<iIi", FeatureId, State.ReferenceTime, 0))
    Writer.u16(len(State.Members))
    for Member in State.Members:
        BeginTrimRef(Writer, Member.ClassName, ProfileIndex)
        Writer.ReferenceObject(FileIndex, KExtObjectClass)
        Writer.raw(
            PackFields("<iI2i", FeatureId, State.ReferenceTime, Member.EdgeId, 0)
        )
    Writer.i32(0)
    return FileIndex
