from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.container.Archive import KClassRefKind, KObjectRefKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.BossDepth import DepthDisplay, ReadBossDepth
from convert.adapters.solidworks.resolved.BossEnd import (
    EndSpec,
    ReadEndHead,
    ReadEndTail,
)
from convert.adapters.solidworks.resolved.BossEntry import (
    BossHead,
    OpNode,
    ReadBodyReturn,
)
from convert.adapters.solidworks.resolved.cut.CutChooser import (
    CutChoices,
    ReadCutChoices,
)
from convert.adapters.solidworks.resolved.cut.CutResultFace import (
    CutSolid,
    ReadCutSolid,
)
from convert.adapters.solidworks.resolved.PlaneAtom import ReadAtomMaps


# the blind and through all branches expose different authored parameter inventories
class CutEnd(EndSpec):
    depth_display: DepthDisplay | None
    from_end_object: int
    end: int
    depth_selector_offset: int


# a cut can expose its authored end only after its target and both result groups close
class CutOperation(OpNode):
    transfer_object: int
    parent_transfer_object: int
    atom_id: int
    solid_body: CutSolid
    choosers: CutChoices
    partition_object: int
    partition_state: int
    atom_end: int
    end_specification: CutEnd


# the through all mode owns a null where the blind mode stores its depth display
def ReadCutEnd(Cursor: ArchiveCursor) -> CutEnd:
    SpecValue = ReadEndHead(Cursor, KClassRefKind)
    Conditions = SpecValue["conditions"]
    RequireArch(Conditions in ((0, 0), (1, 0)), True, "witnessed cut end conditions")
    Depth: DepthDisplay | None = None
    SelectorOffset = Cursor.Offset
    if Conditions[0] == 0:
        Depth = ReadBossDepth(Cursor, KClassRefKind)
        RequireArch(Depth["dimension"]["metres"] > 0, True, "positive blind cut depth")
    else:
        Cursor.ReadNull()
    Origin = ReadEndTail(Cursor, KClassRefKind, 1)
    RequireArch(Cursor.ReadValue("<di"), (0, 1), "guarded cut feature return")
    return {
        **SpecValue,
        "depth_display": Depth,
        "from_end_object": Origin,
        "end": Cursor.Offset,
        "depth_selector_offset": SelectorOffset,
    }


# the cut and its target use distinct configuration atom allocations
def ReadCutXfer(
    Cursor: ArchiveCursor, BossValue: BossHead, TransferIds: frozenset[int]
) -> tuple[int, int]:
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, Cursor.ReadNull, Cursor.ReadText)
    RequireArch(
        Cursor.ReadInts("<i3H"), (0, 0, 0, 0), "guarded cut model and atom fields"
    )
    RequireArch(Cursor.ReadInts("<iH"), (1, 1), "one saved cut transfer")
    _, _, Transfer = Cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<iH"), (1, 1), "one parent boss transfer")
    _, _, Parent = Cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)
    RequireArch(
        Parent, BossValue["transfer_object"], "cut refers to the earlier boss transfer"
    )
    RequireArch(
        Transfer != Parent and frozenset((Transfer, Parent)) == TransferIds,
        True,
        "distinct reached configuration transfers",
    )
    return Transfer, Parent


# the complete cut walk must reach the selected list end before projecting the operation
def ReadCutOp(
    Cursor: ArchiveCursor,
    CutValue: OpNode,
    BossValue: BossHead,
    TransferIds: frozenset[int],
) -> CutOperation:
    Transfer, Parent = ReadCutXfer(Cursor, BossValue, TransferIds)
    Cursor.ReadNull()
    Count, AtomId, ModeValue, Presence, Items = Cursor.ReadInts("<4iH")
    RequireArch(
        (Count, ModeValue, Presence, Items), (1, 3, 1, 1), "one guarded cut result body"
    )
    BodyValue = ReadCutSolid(Cursor, BossValue, CutValue)
    Choosers = ReadCutChoices(Cursor, BossValue, CutValue)
    RequireArch(
        Cursor.ReadInts("<H3i"), (0, 0, 0, 1), "guarded cut partition selection"
    )
    _, _, Marker = Cursor.TakePointer(
        ("moPMarkRecord_c",), KClassRefKind, CompactOnly=True
    )
    (State,) = Cursor.ReadInts("<i")
    ReadAtomMaps(Cursor)
    AtomEnd = Cursor.Offset
    ReadBodyReturn(Cursor)
    SpecValue = ReadCutEnd(Cursor)
    RequireArch(Cursor.ReadInts("<i"), (0,), "resolved list footer")
    RequireArch(Cursor.Offset, len(Cursor.BlobValue), "complete resolved list extent")
    return {
        **CutValue,
        "transfer_object": Transfer,
        "parent_transfer_object": Parent,
        "atom_id": AtomId,
        "solid_body": BodyValue,
        "choosers": Choosers,
        "partition_object": Marker,
        "partition_state": State,
        "atom_end": AtomEnd,
        "end_specification": SpecValue,
    }
