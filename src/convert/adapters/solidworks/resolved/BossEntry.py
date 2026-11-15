from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.BossChooser import (
    BossChoices,
    ChooserOwner,
    ReadBossChoices,
)
from convert.adapters.solidworks.resolved.BossEnd import (
    BlindEnd,
    BossClose,
    ReadBlindEnd,
    ReadBossClose,
)
from convert.adapters.solidworks.resolved.NamedNode import ReadNamedNode
from convert.adapters.solidworks.resolved.PlaneAtom import ReadAtomMaps


# the operation must select the reached profile and identify its native feature slot
class OpNode(ChooserOwner):
    offset: int
    name: str
    profile_object: int
    profile_ref_offset: int


# the outer operation owns its transfer atom, body choosers and signed end specification
class BossHead(OpNode):
    transfer_object: int
    choosers: BossChoices
    partition_object: int
    partition_state: int
    atom_end: int
    end_specification: BlindEnd


# the closed operation records its source end and terminal object map
class RectangleBoss(BossHead, BossClose):
    stream_end: int
    next_map_index: int


# the operation owns exactly one allocated profile reached by the resolved walk
def ReadOpNode(
    Cursor: ArchiveCursor,
    ClassName: str,
    Flags: tuple[int, ...],
    ProfileObject: int,
    FileObject: int,
) -> OpNode:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer((ClassName,), KDefinitionKind, CompactOnly=True)
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    Name, FeatureId = ReadNamedNode(Cursor, Flags)
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
        "name": Name,
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


# the chooser and transfer fields must precede the same extrusion's blind end
def ReadBossHead(
    Cursor: ArchiveCursor, Boss: OpNode, Directions: tuple[int, ...]
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
    Choices = ReadBossChoices(Cursor, Boss)
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
    Spec = ReadBlindEnd(Cursor, Directions)
    return {
        **Boss,
        "transfer_object": Transfer,
        "choosers": Choices,
        "partition_object": Marker,
        "partition_state": State,
        "atom_end": AtomEnd,
        "end_specification": Spec,
    }


# the single boss cannot qualify until every operation field and the list footer close
def ReadRectangleBoss(
    Cursor: ArchiveCursor, ProfileObject: int, FileObject: int, TransferObject: int
) -> RectangleBoss:
    Node = ReadOpNode(
        Cursor, "moExtrusion_c", (0x40000140, 0xC0000140), ProfileObject, FileObject
    )
    Head = ReadBossHead(Cursor, Node, (0, 1))
    RequireArch(
        Head["transfer_object"], TransferObject, "boss uses the configuration atom"
    )
    Close = ReadBossClose(Cursor)
    RequireArch(
        Close["depth_display"]["dimension"]["metres"] > 0, True, "positive boss depth"
    )
    RequireArch(Cursor.ReadInts("<i"), (0,), "resolved boss list footer")
    RequireArch(Cursor.Offset, len(Cursor.BlobValue), "complete boss resolved stream")
    return {
        **Head,
        **Close,
        "stream_end": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
    }
