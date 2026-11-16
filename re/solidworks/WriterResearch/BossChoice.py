from collections.abc import Sequence
from dataclasses import dataclass as Dataclass
from math import isfinite as IsFinite
from struct import pack as PackFields

from BossOpen import KBossClass
from PartArchive import PartArchiveWriter
from RectangleTrim import KReferenceClass
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Resolved.BossChooser import ChooserOwner
from convert.adapters.solidworks.Resolved.FaceIdentity import KCapClass, KEdgeClass

KChooserClass = "moPerBodyChooserData_c"
KFaceClass = "moFaceRef_c"
KCentreClass = "moBBoxCenterData_c"
KUnsetFaceParam = 1e100


# retain both face traversals and the filed bounding centre as separate state
@Dataclass(frozen=True, slots=True)
class BossChoiceState:
    ReferenceTime: int
    EdgeOrders: tuple[tuple[int, ...], tuple[int, ...]]
    CentreMetres: tuple[float, float, float]
    DiameterMetres: float


# a repeated face points to the first cap and edge objects in their original order
@Dataclass(frozen=True, slots=True)
class CapObjects:
    Cap: int
    Edges: tuple[int, ...]


# make every side identify exactly one saved line of the selected rectangle
def CheckChoiceState(
    Writer: PartArchiveWriter,
    Generation: int,
    Owner: ChooserOwner,
    EdgeIds: Sequence[int],
    State: BossChoiceState,
) -> None:
    RequireArch(Generation, 19000, "ordinary single-boss chooser generation")
    RequireArch(
        Writer.next_index <= KBigObjectTag - 33
        and frozenset(Writer.classes).isdisjoint(
            (KChooserClass, KFaceClass, KCapClass, KEdgeClass, KCentreClass)
        )
        and 0 < Writer.classes.get(KReferenceClass, 0) < Writer.next_index,
        True,
        "first compact boss chooser allocations",
    )
    RequireArch(
        Writer.objects.get(Owner["object_index"]) == KBossClass
        and Writer.objects.get(Owner["file_ref_object"]) == KExtObjectClass
        and type(Owner["native_feature_id"]) is int
        and 0 < Owner["native_feature_id"] <= 0x7FFFFFFF
        and type(State.ReferenceTime) is int
        and 0 <= State.ReferenceTime < 0xFFFFFFFF,
        True,
        "chooser belongs to the same boss and shared file",
    )
    RequireArch(len(State.EdgeOrders), 2, "two ordered cap faces")
    RequireArch(
        len(EdgeIds) == len(set(EdgeIds)) == 4
        and all(
            len(Order) == 4 and set(Order) == set(EdgeIds) for Order in State.EdgeOrders
        )
        and all(type(Id) is int and 0 < Id <= 0x7FFFFFFF for Id in EdgeIds),
        True,
        "two cap traversals over the owned perimeter",
    )
    RequireArch(len(State.CentreMetres), 3, "three centre coordinates")
    RequireArch(
        all(IsFinite(Value) for Value in State.CentreMetres)
        and IsFinite(State.DiameterMetres)
        and State.DiameterMetres > 0,
        True,
        "finite filed bounding centre and diameter",
    )


# both the original face and its repetition have an inline face envelope
def BeginChoiceFace(Writer: PartArchiveWriter, EdgeCount: int) -> None:
    Writer.BeginObject(KFaceClass, 1)
    Writer.raw(
        PackFields(
            "<3IiI2dH", 1, 0, EdgeCount + 2, 768, 0, KUnsetFaceParam, KUnsetFaceParam, 0
        )
    )


# each occurrence has its own feature-reference object but aliases the same file
def WriteChoiceId(
    Writer: PartArchiveWriter,
    Owner: ChooserOwner,
    ReferenceTime: int,
    ClassName: str,
    Occurrence: int,
) -> int:
    Writer.BeginObject(ClassName, 1)
    Object = Writer.next_index - 1
    Writer.u16(0)
    Writer.BeginObject(KReferenceClass, 1)
    Writer.ReferenceObject(Owner["file_ref_object"], KExtObjectClass)
    Writer.raw(
        PackFields("<iIi", Owner["native_feature_id"], ReferenceTime, Occurrence)
    )
    if ClassName == KCapClass:
        Writer.i32(0)
    return Object


# the optional last identity and new-face data are absent in this envelope
def EndChoiceFace(Writer: PartArchiveWriter, Generation: int) -> None:
    Writer.raw(PackFields("<H5I", 0, 0, 0, Generation, 0, 0))


# materialize typed faces before later occurrences can reference their targets
def WriteChoiceCap(
    Writer: PartArchiveWriter,
    Generation: int,
    Owner: ChooserOwner,
    ReferenceTime: int,
    Occurrence: int,
    EdgeOrder: tuple[int, ...],
) -> CapObjects:
    BeginChoiceFace(Writer, len(EdgeOrder))
    Cap = WriteChoiceId(Writer, Owner, ReferenceTime, KCapClass, Occurrence)
    Edges = tuple(
        WriteChoiceId(Writer, Owner, ReferenceTime, KEdgeClass, Edge)
        for Edge in EdgeOrder
    )
    EndChoiceFace(Writer, Generation)
    return CapObjects(Cap, Edges)


# the repeated faces allocate new envelopes but retain the exact old child slots
def WriteCapAlias(
    Writer: PartArchiveWriter, Generation: int, Target: CapObjects
) -> None:
    BeginChoiceFace(Writer, len(Target.Edges))
    Writer.ReferenceObject(Target.Cap, KCapClass)
    for Edge in Target.Edges:
        Writer.ReferenceObject(Edge, KEdgeClass)
    EndChoiceFace(Writer, Generation)


# the repeated chooser writes a fresh centre object with the same cached fields
def WriteChoiceTail(
    Writer: PartArchiveWriter, Owner: ChooserOwner, State: BossChoiceState
) -> None:
    Writer.raw(PackFields("<2H", 0, 1))
    Writer.BeginObject(KCentreClass, 1)
    Writer.raw(PackFields("<i4d", 1, *State.CentreMetres, State.DiameterMetres))
    Writer.raw(PackFields("<2iHIi", 0, 0, 1, 0, 0))
    Writer.ReferenceObject(Owner["object_index"], KBossClass)


# return immediately after the second chooser aliases its enclosing extrusion
def WriteBossChoice(
    Writer: PartArchiveWriter,
    Generation: int,
    Owner: ChooserOwner,
    EdgeIds: Sequence[int],
    State: BossChoiceState,
) -> None:
    CheckChoiceState(Writer, Generation, Owner, EdgeIds, State)
    Writer.raw(PackFields("<2H", 1, 1))
    Writer.BeginObject(KChooserClass, 1)
    Writer.u16(len(State.EdgeOrders))
    Original = tuple(
        WriteChoiceCap(Writer, Generation, Owner, State.ReferenceTime, Slot, Order)
        for Slot, Order in enumerate(State.EdgeOrders)
    )
    WriteChoiceTail(Writer, Owner, State)
    Writer.raw(PackFields("<3H", 1, 1, 0))
    Writer.ReferenceObject(Owner["object_index"], KBossClass)
    Writer.raw(PackFields("<i2H", 1, 1, 1))
    Writer.BeginObject(KChooserClass, 1)
    Writer.u16(len(Original))
    for Target in Original:
        WriteCapAlias(Writer, Generation, Target)
    WriteChoiceTail(Writer, Owner, State)
