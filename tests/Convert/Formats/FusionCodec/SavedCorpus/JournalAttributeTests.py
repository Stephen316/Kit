from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import mark as TestMark, raises as Raises

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

# the study cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KStudy = FilePath(__file__).resolve().parents[5] / "re" / "Fusion" / "Study"

# the requires codec cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

# the reencoded cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KReencoded = (".protein", ".smb", ".smbh")

# the edit files cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KEditFiles = (
    "draftmodes-9b1a30f74aed/symmetric.f3d",
    "draftmodes-9b1a30f74aed/two_angles.f3d",
    "moretools-88a2cd6cad0b/MoveRotate.f3d",
    "moretools-88a2cd6cad0b/MoveTranslate.f3d",
    "movemodes-0dd2f72dd9a7/point_to_position_component.f3d",
    "movemodes-0dd2f72dd9a7/point_to_position_nested_design.f3d",
    "movemodes-34cba3ced135/along_axis.f3d",
    "movemodes-34cba3ced135/along_sketch_line.f3d",
    "movemodes-34cba3ced135/free.f3d",
    "movemodes-34cba3ced135/point_to_point.f3d",
    "movemodes-34cba3ced135/point_to_position.f3d",
    "movemodes-34cba3ced135/rotate_axis.f3d",
    "movemodes-34cba3ced135/xyz_component.f3d",
    "movemodes-34cba3ced135/xyz_design.f3d",
    "movemodes-34cba3ced135/xyz_nested_design.f3d",
    "partinglinedrafts-c4d07c76fcd5/fixed_seven.f3d",
    "partinglinedrafts-c4d07c76fcd5/fixed_three.f3d",
    "partinglinedrafts-c4d07c76fcd5/moving_both_three.f3d",
)

# the face files cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KFaceFiles = (
    "splitfacemodes-4fc4adf2a868/along_vector.f3d",
    "splitfacemodes-4fc4adf2a868/closest_point.f3d",
    "splitfacemodes-4fc4adf2a868/line.f3d",
    "splitfacemodes-4fc4adf2a868/line_extended.f3d",
    "splitfacemodes-4fc4adf2a868/multiple_faces.f3d",
    "splitfacemodes-4fc4adf2a868/plane.f3d",
    "splitfacemodes-4fc4adf2a868/plane_extended.f3d",
    "surfacebounds-ac801bb00fae/untrim_all.f3d",
    "surfacebounds-ac801bb00fae/untrim_external.f3d",
    "surfacebounds-ac801bb00fae/untrim_internal.f3d",
    "surfacetools-856ca50cf4c7/reverse_normal.f3d",
    "surfacetrimtools-650ca09579b1/sketch_line_offset_positive.f3d",
    "surfacetrimtools-650ca09579b1/sketch_line_reversed_negative.f3d",
    "surfacetrimtools-ca26d21e7ad9/sketch_line.f3d",
)

# the thread files cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KThreadFiles = (
    "threadfamilies-459264fae49b/ansi_unified_external.f3d",
    "threadfamilies-459264fae49b/bsp_pipe_internal.f3d",
    "threadfamilies-459264fae49b/iso_trapezoidal_external.f3d",
    "threadmodes-6b6a0a9b4a69/partial_high.f3d",
    "threadmodes-6b6a0a9b4a69/partial_low.f3d",
    "threadmodes-9574579d310b/left_handed.f3d",
    "threadmodes-d51d2ae60564/cosmetic_full.f3d",
    "threadmodes-d51d2ae60564/internal.f3d",
    "threadmodes-d51d2ae60564/left_handed.f3d",
    "threadmodes-d51d2ae60564/modeled_full.f3d",
    "threadmodes-d51d2ae60564/partial_high.f3d",
    "threadmodes-d51d2ae60564/partial_low.f3d",
    "threadmultifaces-e4bc4a120fbf/external_two_full.f3d",
    "threadmultifaces-e4bc4a120fbf/external_two_partial.f3d",
    "threadmultifaces-e4bc4a120fbf/internal_two_full.f3d",
)

# the saved files cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSavedFiles = (*KEditFiles, *KFaceFiles, *KThreadFiles)

# the split file cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSplitFile = "splitfacemodes-4fc4adf2a868/along_vector.f3d"

# the move file cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KMoveFile = "moretools-88a2cd6cad0b/MoveRotate.f3d"

# the thread file cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KThreadFile = "threadmodes-d51d2ae60564/modeled_full.f3d"


# shared read members setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadMembers(DataValue: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(DataValue)) as Archive:
        return {Entry: Archive.read(Entry) for Entry in Archive.namelist()}


# shared load journals setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def LoadJournals(FileName: str) -> tuple[JournalModel, ...]:
    Model = ReadDocument((KStudy / FileName).read_bytes())
    return tuple(
        BodyValue.History
        for BodyValue in Model.Bodies
        if isinstance(BodyValue.History, JournalModel)
    )


# shared list entities setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ListEntities(FileName: str) -> tuple[KJournalEntity, ...]:
    return tuple(
        Value for Journal in LoadJournals(FileName) for Value in Journal.Entities
    )


# the saved replay contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
@TestMark.parametrize("FileName", KSavedFiles)
def TestSavedReplay(FileName: str) -> None:
    Source = (KStudy / FileName).read_bytes()
    Model = ReadDocument(Source)
    Output = EmitParsed(Model)
    assert ReadDocument(Output) == Model
    Before, After = ReadMembers(Source), ReadMembers(Output)
    assert set(Before) == set(After)
    Changed = {
        Entry
        for Entry in Before
        if Before[Entry] != After[Entry] and not Entry.endswith(KReencoded)
    }
    assert not Changed
    Journals = {
        Entry for Entry in Before if Entry.endswith(".smbh") and "Breps." in Entry
    }
    assert all(Before[Entry] == After[Entry] for Entry in Journals)


# the typed kinds contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestTypedKinds() -> None:
    SplitValues = ListEntities(KSplitFile)
    assert any(isinstance(Value, WireNode) for Value in SplitValues)
    assert any(isinstance(Value, NoMergeAttrib) for Value in SplitValues)
    assert any(
        isinstance(Value, ShellNode) and Value.FirstWire != -1 for Value in SplitValues
    )
    MoveValues = ListEntities(KMoveFile)
    assert sum(isinstance(Value, NestedTag) for Value in MoveValues) == sum(
        isinstance(Value, TagAttrib) and Value.Attribute != -1 for Value in MoveValues
    )
    ThreadValues = tuple(
        Value for Value in ListEntities(KThreadFile) if isinstance(Value, FeatureAttrib)
    )
    assert any(Value.DataName == "thread_face_data" for Value in ThreadValues)
    assert any(Value.DataName == "feature_data" for Value in ThreadValues)


# the name records contract needs boundary coverage so stored document relationships remain consistent
def TestNameRecords() -> None:
    Values: tuple[KJournalEntity, ...] = (
        NameAttrib(AttribLinks(-1, 3, 7), (2, 1, 1, 2), "SCULPT_WORKPLANE_TOOL", -282),
        NameAttrib(AttribLinks(-1, -1, 9), (2, 3, 1, 2), "sb_split_edge"),
        NoMergeAttrib(AttribLinks(-1, 4, 9)),
    )
    for Value in Values:
        Record = MakeEntityNode(Value)
        _ = EmitWireRecord(Record)
        assert ReadEntityNode(Record) == Value


# the name reject contract needs boundary coverage so stored document relationships remain consistent
def TestNameReject() -> None:
    with Raises(ValueError):
        _ = NameAttrib(AttribLinks(-1, -1, 9), (2, 1, 1, 2), "sb_split_edge")
    with Raises(ValueError):
        _ = NameAttrib(AttribLinks(-1, -1, 9), (2, 3, 1, 2), "")


# the nest reject contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestNestReject() -> None:
    Journal = next(
        Value
        for Value in LoadJournals(KMoveFile)
        if any(isinstance(Entity, NestedTag) for Entity in Value.Entities)
    )
    Position = next(
        Index
        for Index, Entity in enumerate(Journal.Entities)
        if isinstance(Entity, TagAttrib) and Entity.Attribute != -1
    )
    Entities = list(Journal.Entities)
    Parent = Entities[Position]
    assert isinstance(Parent, TagAttrib)
    Entities[Position] = Replace(Parent, Attribute=-1)
    with Raises(ValueError):
        _ = EmitJournal(Replace(Journal, Entities=tuple(Entities)))


# the wire reject contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestWireReject() -> None:
    Journal = next(
        Value
        for Value in LoadJournals(KSplitFile)
        if any(isinstance(Entity, WireNode) for Entity in Value.Entities)
    )
    Position = next(
        Index
        for Index, Entity in enumerate(Journal.Entities)
        if isinstance(Entity, ShellNode) and Entity.FirstWire != -1
    )
    Entities = list(Journal.Entities)
    Shell = Entities[Position]
    assert isinstance(Shell, ShellNode)
    Entities[Position] = Replace(Shell, FirstWire=-1)
    with Raises(ValueError):
        _ = EmitJournal(Replace(Journal, Entities=tuple(Entities)))


# the thread limit contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestThreadLimit() -> None:
    Value = next(
        Entity
        for Entity in ListEntities(KThreadFile)
        if isinstance(Entity, FeatureAttrib) and Entity.DataName == "thread_face_data"
    )
    with Raises(ValueError):
        _ = Replace(Value, FeatureTag=-1)
