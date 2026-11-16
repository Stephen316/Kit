from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossChooser import (
    BossChoices,
    CheckChoiceOwn,
    ReadCap,
    ReadCapAlias,
    ReadChoiceTail,
)
from convert.adapters.solidworks.Resolved.BossEntry import OpFields, OpNode
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.Resolved.Scope.BossCap import (
    CheckScopeCap,
    ReadInitialCap,
    ReadOffsetAlias,
    ReadOffsetCap,
)


# the first chooser establishes the file and both chooser groups must agree on cap slots
def ReadBossChoices(
    Cursor: ArchiveCursor,
    Fields: OpFields,
    EdgeIds: tuple[int, ...],
    FileObject: int | None,
) -> tuple[OpNode, BossChoices]:
    First = FileObject is None
    KindValue = KDefinitionKind if First else KClassRefKind
    ClassName = "moExtrusion_c" if First else "moICE_c"
    RequireArch(Cursor.ReadInts("<2H"), (1, 1), "one scoped boss body chooser")
    _, _, Primary = Cursor.TakePointer(
        ("moPerBodyChooserData_c",), KindValue, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two scoped boss chooser caps")
    FirstCap = ReadInitialCap(Cursor) if First else ReadOffsetCap(Cursor, 0)
    FileIndex, FeatureId, Clock, _ = SurfaceKey(FirstCap["primary"])
    RequireArch(
        FeatureId, Fields["native_feature_id"], "scoped cap uses the reached boss"
    )
    if FileObject is not None:
        RequireArch(FileIndex, FileObject, "offset boss remains in the reached file")
    NodeValue: OpNode = {**Fields, "file_ref_object": FileIndex}
    Other = (
        ReadCap(Cursor, KClassRefKind, 1, NodeValue)
        if First
        else ReadOffsetCap(Cursor, 1)
    )
    for CapValue in (FirstCap, Other):
        CheckScopeCap(CapValue, (FileIndex, FeatureId, Clock), EdgeIds)
    Centre = ReadChoiceTail(Cursor, KindValue, (0,) if First else ())
    CheckChoiceOwn(Cursor, NodeValue, ClassName)
    RequireArch(Cursor.ReadInts("<3H"), (1, 1, 0), "empty secondary scoped chooser")
    CheckChoiceOwn(Cursor, NodeValue, ClassName)
    RequireArch(Cursor.ReadInts("<i2H"), (1, 1, 1), "one repeated scoped chooser")
    _, _, Repeat = Cursor.TakePointer(
        ("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two repeated scoped boss caps")
    ReadAlias = ReadCapAlias if First else ReadOffsetAlias
    Aliases = [ReadAlias(Cursor, CapValue) for CapValue in (FirstCap, Other)]
    RepeatedCentre = ReadChoiceTail(Cursor, KClassRefKind, (0,) if First else ())
    RequireArch(
        RepeatedCentre["centre_and_scale"],
        Centre["centre_and_scale"],
        "scoped chooser centres agree",
    )
    CheckChoiceOwn(Cursor, NodeValue, ClassName)
    return NodeValue, {
        "primary_object": Primary,
        "repeated_object": Repeat,
        "caps": [FirstCap, Other],
        "cap_aliases": Aliases,
        "centre": Centre,
        "repeated_centre_object": RepeatedCentre["centre_object"],
        "end": Cursor.Offset,
    }
