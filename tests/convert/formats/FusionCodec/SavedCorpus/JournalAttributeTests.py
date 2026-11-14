from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import mark as TestMark, raises as Raises

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

KStudy = FilePath(__file__).resolve().parents[5] / "re" / "Fusion" / "Study"

KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KReencoded = (".protein", ".smb", ".smbh")

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

KSavedFiles = (*KEditFiles, *KFaceFiles, *KThreadFiles)

KSplitFile = "splitfacemodes-4fc4adf2a868/along_vector.f3d"
KMoveFile = "moretools-88a2cd6cad0b/MoveRotate.f3d"
KThreadFile = "threadmodes-d51d2ae60564/modeled_full.f3d"


def ReadMembers(DataValue: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(DataValue)) as Archive:
        return {Entry: Archive.read(Entry) for Entry in Archive.namelist()}


def LoadJournals(FileName: str) -> tuple[JournalModel, ...]:
    Model = ReadDocument((KStudy / FileName).read_bytes())
    return tuple(
        BodyValue.History
        for BodyValue in Model.Bodies
        if isinstance(BodyValue.History, JournalModel)
    )


def ListEntities(FileName: str) -> tuple[KJournalEntity, ...]:
    return tuple(
        Value for Journal in LoadJournals(FileName) for Value in Journal.Entities
    )


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


def TestNameReject() -> None:
    with Raises(ValueError):
        _ = NameAttrib(AttribLinks(-1, -1, 9), (2, 1, 1, 2), "sb_split_edge")
    with Raises(ValueError):
        _ = NameAttrib(AttribLinks(-1, -1, 9), (2, 3, 1, 2), "")


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


@KRequiresCodec
def TestThreadLimit() -> None:
    Value = next(
        Entity
        for Entity in ListEntities(KThreadFile)
        if isinstance(Entity, FeatureAttrib) and Entity.DataName == "thread_face_data"
    )
    with Raises(ValueError):
        _ = Replace(Value, FeatureTag=-1)
