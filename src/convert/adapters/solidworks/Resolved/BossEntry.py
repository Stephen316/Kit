from convert.adapters.solidworks.Config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossChooser import (
    BossChoices,
    ChooserOwner,
    ReadBossChoices,
)
from convert.adapters.solidworks.Resolved.BossEnd import (
    BlindEnd,
    BossClose,
    ReadBlindEnd,
    ReadBossClose,
)
from convert.adapters.solidworks.Resolved.NamedNode import ReadNamedNode
from convert.adapters.solidworks.Resolved.PlaneAtom import ReadAtomMaps


# the operation must select the reached profile and identify its native feature slot
class OpNode(ChooserOwner):
    offset: int
    name: str
    profile_object: int
    profile_ref_offset: int


# the outer operation owns its transfer atom body choosers and signed end specification
class BossHead(OpNode):
    transfer_object: int
    choosers: BossChoices
    partition_object: int
    partition_state: int
    atom_end: int
    end_specification: BlindEnd


# a reached blind boss keeps both its initial owners and its completed end specification
class BossOperation(BossHead, BossClose):
    pass


# a terminal boss additionally records the return of the whole resolved list
class RectangleBoss(BossOperation):
    stream_end: int
    next_map_index: int


# the operation owns exactly one allocated profile reached by the resolved walk
def ReadOpNode(
    Cursor: ArchiveCursor,
    ClassName: str,
    Flags: tuple[int, ...],
    ProfileObject: int,
    FileObject: int,
    *,
    KindValue: str = KDefinitionKind,
) -> OpNode:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer((ClassName,), KindValue, CompactOnly=True)
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId = ReadNamedNode(Cursor, Flags)
    RequireArch(Cursor.ReadInts("<H"), (1,), "one resolved operation profile")
    ProfileRef = Cursor.Offset
    _, _, Profile = Cursor.TakePointer(
        ("moProfileFeature_c",), KObjectRefKind, CompactOnly=True
    )
    RequireArch(Profile, ProfileObject, "operation owns the reached profile")
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded operation node trailer")
    return {
        "offset": Offset,
        "object_index": Index,
        "name": NameValue,
        "native_feature_id": FeatureId,
        "profile_object": Profile,
        "file_ref_object": FileObject,
        "profile_ref_offset": ProfileRef,
    }


# optional body members are absent before the end specification in this layout
def ReadBodyReturn(Cursor: ArchiveCursor) -> None:
    Cursor.ReadNull()
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty modern body feature tail")


# the chooser and transfer fields must precede the blind end of the same extrusion
def ReadBossHead(
    Cursor: ArchiveCursor, BossValue: OpNode, Directions: tuple[int, ...]
) -> BossHead:
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, Cursor.ReadNull, Cursor.ReadText)
    RequireArch(
        Cursor.ReadInts("<i3H"), (0, 0, 0, 0), "guarded boss model and atom fields"
    )
    RequireArch(Cursor.ReadInts("<iH"), (1, 1), "one saved transfer object")
    _, _, Transfer = Cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty secondary transfer array")
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<5i"), (1, 101, 3, 0, 1), "guarded boss atom arrays and mode"
    )
    Choices = ReadBossChoices(Cursor, BossValue)
    RequireArch(
        Cursor.ReadInts("<H3i"), (0, 0, 0, 1), "guarded boss partition selection"
    )
    _, _, Marker = Cursor.TakePointer(
        ("moPMarkRecord_c",), KClassRefKind, CompactOnly=True
    )
    (State,) = Cursor.ReadInts("<i")
    ReadAtomMaps(Cursor)
    AtomEnd = Cursor.Offset
    ReadBodyReturn(Cursor)
    SpecValue = ReadBlindEnd(Cursor, Directions)
    return {
        **BossValue,
        "transfer_object": Transfer,
        "choosers": Choices,
        "partition_object": Marker,
        "partition_state": State,
        "atom_end": AtomEnd,
        "end_specification": SpecValue,
    }


# the single boss cannot qualify until every operation field and the list footer close
def ReadRectBoss(
    Cursor: ArchiveCursor, ProfileObject: int, FileObject: int, TransferObject: int
) -> RectangleBoss:
    NodeValue = ReadOpNode(
        Cursor, "moExtrusion_c", (0x40000140, 0xC0000140), ProfileObject, FileObject
    )
    HeadValue = ReadBossHead(Cursor, NodeValue, (0, 1))
    RequireArch(
        HeadValue["transfer_object"], TransferObject, "boss uses the configuration atom"
    )
    Close = ReadBossClose(Cursor)
    RequireArch(
        Close["depth_display"]["dimension"]["metres"] > 0, True, "positive boss depth"
    )
    RequireArch(Cursor.ReadInts("<i"), (0,), "resolved boss list footer")
    RequireArch(Cursor.Offset, len(Cursor.BlobValue), "complete boss resolved stream")
    return {
        **HeadValue,
        **Close,
        "stream_end": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
    }
