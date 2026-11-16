from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from ConfigSavedViews import KObjectList
from ConfigScene.Annotation import KAnnotation, KFirstViewId
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KMarkerClass = "moPMarkRecord_c"
KThreadClass = "moCThreadRefMgr_c"
KViewIdSeed = KFirstViewId - 1


@Dataclass(frozen=True, slots=True)
class PartMarker:
    Id: int
    AtomMapMode: int


# the model owns the annotation high-water mark and its separate default view set
def WriteDisplay(Writer: PartArchiveWriter, LastView: int) -> None:
    Writer.raw(PackFields("<2iIi", LastView, KViewIdSeed, 1, KViewIdSeed))
    Writer.raw(EncodeNull())  # flat-pattern color table
    Writer.u32(0)  # model +0xf3c
    Writer.u32(0)  # second view ID set
    for _ in range(8):
        Writer.u16(0)
    Writer.raw(EncodeNull())  # layer manager
    Writer.u16(0)  # inline list owned by model +0x240


# the kernel marker ID precedes the model's separate saved atom-map state
def WriteMarker(Writer: PartArchiveWriter, Marker: PartMarker) -> None:
    Writer.begin_object(KMarkerClass, 1)
    Writer.i32(Marker.Id)
    Writer.i32(Marker.AtomMapMode)
    Writer.i32(0)  # atom map count
    Writer.i32(0)  # secondary solver state absent
    Writer.i32(0)  # dimension map count
    for _ in range(2):
        Writer.i32(20)  # initial dimension increment ID
        Writer.i32(0)  # dimension increment array count
    Writer.i32(0)  # model +0xb00
    Writer.i32(0)  # model +0xd54
    Writer.i32(0)  # 3D print settings absent


# the ordinary model supplies one marker, the empty notes list and the modern thread manager
def WriteModelLists(
    Writer: PartArchiveWriter, Generation: int, Marker: PartMarker
) -> None:
    RequireArch(Generation, 19000, "ordinary model list generation")
    RequireArch(
        type(Marker.Id) is int and 0 < Marker.Id < 2**31,
        True,
        "positive kernel partition mark ID",
    )
    RequireArch(
        type(Marker.AtomMapMode) is int and Marker.AtomMapMode == 1,
        True,
        "witnessed ordinary atom-map mode",
    )
    Views = sum(Name == KAnnotation for Name in Writer.objects.values())
    RequireArch(
        Views in (1, 2)
        and 0 < Writer.next_index <= KBigObjectTag - 5
        and KObjectList in Writer.classes
        and KMarkerClass not in Writer.classes
        and KThreadClass not in Writer.classes,
        True,
        "ordinary model list archive allocation",
    )
    WriteDisplay(Writer, KViewIdSeed + Views)
    WriteMarker(Writer, Marker)
    Writer.begin_object(KObjectList, 1)
    Writer.u16(0)
    Writer.i32(0)  # last notes-area ID
    Writer.string("")
    Writer.string("")
    Writer.begin_object(KThreadClass, 1)
    Writer.i32(0)  # no saved thread entries
    Writer.i32(0)  # default thread-manager state byte stored as a signed long
    Writer.raw(EncodeNull())  # bend note format
