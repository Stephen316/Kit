from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.Container.Archive import KClassRefKind, KObjectRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossChooser import BossChoices
from convert.adapters.solidworks.Resolved.BossEntry import (
    OpNode,
    ReadBodyReturn,
    ReadOpFields,
)
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopeOwner
from convert.adapters.solidworks.Resolved.PlaneAtom import ReadAtomMaps
from convert.adapters.solidworks.Resolved.Scope.BossChoices import ReadScopedChoices
from convert.adapters.solidworks.Resolved.Scope.BossExtent import (
    ScopedExtent,
    ReadScopedExtent,
)
from convert.adapters.solidworks.Resolved.Scope.Profile import ScopeProfile


# a scoped boss binds its actual sketch and extent to both identity namespaces
@Dataclass(frozen=True, slots=True)
class ScopeBoss:
    Profile: ScopeProfile
    Node: OpNode
    Owner: ScopeOwner
    Choices: BossChoices
    Extent: ScopedExtent
    PartitionObject: int
    PartitionState: int


# the boss body identifier follows a one item saved transfer and atom frame
def ReadScopeAtom(Cursor: ArchiveCursor) -> tuple[int, int]:
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, Cursor.ReadNull, Cursor.ReadText)
    RequireArch(Cursor.ReadInts("<i3H"), (0, 0, 0, 0), "witnessed scoped boss frame")
    RequireArch(Cursor.ReadInts("<iH"), (1, 1), "one scoped boss transfer")
    _, _, Transfer = Cursor.TakePointer(("moAtom_c",), KObjectRefKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty secondary scoped boss transfer")
    Cursor.ReadNull()
    Count, BodyId, Mode, Array, Scope = Cursor.ReadInts("<5i")
    RequireArch(
        (Count, Mode, Array, Scope), (1, 3, 0, 1), "witnessed scoped boss atom frame"
    )
    RequireArch(BodyId > 0, True, "positive saved scoped boss body identity")
    return Transfer, BodyId


# the saved boss and its two cap charts establish the owner passed to the cut parser
def ReadScopedBoss(
    Cursor: ArchiveCursor,
    Profile: ScopeProfile,
    FileObject: int | None,
) -> ScopeBoss:
    First = FileObject is None
    ClassName = "moExtrusion_c" if First else "moICE_c"
    Fields = ReadOpFields(Cursor, ClassName, (0x40000140,), Profile.Sketch.ObjectIndex)
    Transfer, BodyId = ReadScopeAtom(Cursor)
    Node, Choices = ReadScopedChoices(
        Cursor, Fields, Profile.Chain["edge_ids"], FileObject
    )
    RequireArch(
        Cursor.ReadInts("<H3i"), (0, 0, 0, 1), "witnessed scoped boss partition"
    )
    _, _, Marker = Cursor.TakePointer(
        ("moPMarkRecord_c",), KClassRefKind, CompactOnly=True
    )
    (State,) = Cursor.ReadInts("<i")
    ReadAtomMaps(Cursor)
    ReadBodyReturn(Cursor)
    Centre = Choices["centre"]["centre_and_scale"]
    Extent = ReadScopedExtent(Cursor, Profile.Datum.Geometry, Centre, First=First)
    FirstCap = Choices["caps"][0]
    Primary = FirstCap["primary"]
    Sides = FirstCap["edges"]
    Owner = ScopeOwner(
        BodyId,
        Node["file_ref_object"],
        Node["native_feature_id"],
        Primary["time_word"],
        Transfer,
        Primary["class"],
        Sides[0]["class"],
        tuple(Side["occurrence"] for Side in Sides),
        Centre,
    )
    return ScopeBoss(Profile, Node, Owner, Choices, Extent, Marker, State)
