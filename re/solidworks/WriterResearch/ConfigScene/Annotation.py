from struct import pack as PackFields

from ConfigSavedViews import KObjectList, WriteViewBase
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KAnnotation = "moAnnotationView_c"
KBlockManager = "moSketchBlockMgr_c"
KFirstViewId = 200
KWorldX = (1.0, 0.0, 0.0)
KWorldY = (0.0, 1.0, 0.0)
KWorldZ = (0.0, 0.0, 1.0)


# cardinal view rows preserve the sign of the negated native depth axis
KFront = ("*Front", None)
KRight = ("*Right", (*KWorldZ, *KWorldY, *(-Value for Value in KWorldX)))
KTop = ("*Top", (*KWorldX, *KWorldZ, *(-Value for Value in KWorldY)))


# the inherited view is followed by four absent archive references in store order
def WriteAnnoTail(Writer: PartArchiveWriter) -> None:
    NullRef = EncodeNull()
    Writer.i32(0)
    Writer.raw(NullRef + NullRef)
    Writer.raw(PackFields("<id", 0, 0.0))
    Writer.raw(NullRef)
    Writer.raw(PackFields("<2i", 0, 1))
    Writer.raw(NullRef)
    Writer.raw(PackFields("<4i", -1, 0, -1, -1))


# the ordinary sketch view selects its cardinal display independently of the standard table
def WriteAnnotViews(
    Writer: PartArchiveWriter, Generation: int, FirstName: str, IncludeTop: bool
) -> None:
    RequireArch(Generation, 19000, "ordinary annotation view generation")
    RequireArch(FirstName in ("*Front", "*Right"), True, "principal annotation view")
    RequireArch(type(IncludeTop) is bool, True, "optional top annotation view")
    Slots = 3 + int(IncludeTop)
    RequireArch(
        0 < Writer.next_index <= KBigObjectTag - Slots
        and KObjectList in Writer.classes
        and KBlockManager in Writer.classes
        and KAnnotation not in Writer.classes,
        True,
        "ordinary annotation view archive allocation",
    )
    FirstView = KFront if FirstName == "*Front" else KRight
    Views = (FirstView, KTop) if IncludeTop else (FirstView,)
    Writer.begin_object(KObjectList, 1)
    Writer.u16(len(Views))
    for ViewId, (Name, Basis) in enumerate(Views, KFirstViewId):
        Writer.begin_object(KAnnotation, 1)
        WriteViewBase(Writer, Name, Basis, ViewId)
        WriteAnnoTail(Writer)
