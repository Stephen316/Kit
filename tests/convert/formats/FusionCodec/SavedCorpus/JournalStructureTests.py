from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import mark as TestMark, raises as Raises

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import KBoardChanges
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import (
    EmitGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import (
    ReadGeometry,
)
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

# the fixtures cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KFixtures = FilePath(__file__).resolve().parents[5] / "re" / "Fusion" / "Study"

# the requires codec cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

# the reencoded cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KReencoded = (".protein", ".smb", ".smbh")

# the history stems cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KHistoryStems = (
    "embosstext-cd769aa41cdf/two_texts",
    "pathpatterns-de9857f6a1bc/arc_along",
    "pathpatterns-de9857f6a1bc/arc_identical",
    "pathpatterns-de9857f6a1bc/extent",
    "pathpatterns-de9857f6a1bc/flipped",
    "pathpatterns-de9857f6a1bc/multiple_bodies",
    "pathpatterns-de9857f6a1bc/spacing",
    "pathpatterns-de9857f6a1bc/start_offset",
    "pathpatterns-de9857f6a1bc/suppressed_instance",
    "pathpatterns-de9857f6a1bc/symmetric",
    "patterns-35e49809a812/symmetric_one",
    "patterns-35e49809a812/symmetric_two",
    "patterns-35e49809a812/two_extent",
    "patterns-35e49809a812/two_spacing",
    "rectmodes-a069f8f4b8a2/body_multiple_customaxis",
    "rectsymholdouts-cf85ce4a0382/extent_both",
    "rectsymholdouts-cf85ce4a0382/feature_input",
    "rectsymholdouts-cf85ce4a0382/multiple_bodies",
    "rectsymholdouts-cf85ce4a0382/negative_spacing",
    "rectsymholdouts-cf85ce4a0382/oblique_axes",
    "rectsymmetry-f09c57dcfd51/symmetric_both_even",
    "rectsymmetry-f09c57dcfd51/symmetric_both_odd",
    "rectsymmetry-f09c57dcfd51/symmetric_two",
)

# root stems needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KRootStems = (
    "extents-f0f33a9a605f/from_plane",
    "extents-f0f33a9a605f/to_plane",
    "extents-f0f33a9a605f/to_plane_offset",
    "holeplacements-04adf73afe93/sketch_point",
    "pipeedgecontrasts-5bd287323ae7/circle_full",
    "pipeedgecontrasts-5bd287323ae7/circle_partial_two_sided",
    "pipeedgecontrasts-5bd287323ae7/line_full",
    "pipeedgecontrasts-5bd287323ae7/line_offset_negative_partial",
    "pipeedgecontrasts-5bd287323ae7/line_partial",
    "pipepaths-3d11bd427946/brep_edge_circular",
    "revolveto-b1d196f65c46/negative_plane",
    "revolveto-b1d196f65c46/positive_plane",
    "revolveto-b1d196f65c46/two_planes",
    "surfacetools-856ca50cf4c7/unstitch_chain",
)

# the edge stems cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KEdgeStems = (
    "analytic-86a12b291d0a/analytic",
    "holeplacements-04adf73afe93/center_edge",
    "holeplacements-04adf73afe93/reversed_distance",
    "holeplacements-04adf73afe93/sketch_points",
    "holes-926347c1eaa8/counterbore",
    "holes-926347c1eaa8/countersink",
    "holes-926347c1eaa8/simple",
    "holes-926347c1eaa8/to_bottom",
    "loftpointholdouts-bb91509a13e4/construction_sharp_end",
    "loftpointholdouts-bb91509a13e4/construction_sharp_start",
    "loftpointholdouts-bb91509a13e4/vertex_construction_sharp_end",
    "loftpoints-f5bbdb97a568/sharp_end",
    "loftpoints-f5bbdb97a568/sharp_start",
    "specialfillets-d50f7a4f04e0/rule_all_both",
    "thinextrudes-c1632bcb5efe/closed_two_sides_mixed",
    "tools-fda3948848f4/Hole",
)

# the fill stems cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KFillStems = (
    "boundaryfills-a0953038318b/component_middle",
    "boundaryfills-a0953038318b/cut_middle",
    "boundaryfills-a0953038318b/intersect_middle",
    "boundaryfills-a0953038318b/join_middle",
    "boundaryfills-a0953038318b/new_first",
    "boundaryfills-a0953038318b/new_middle",
    "boundaryfills-a0953038318b/new_middle_remove",
    "boundaryfills-a0953038318b/new_two",
    "boundaryfills-a0953038318b/plane_first",
)

# the fixed stems cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KFixedStems = KHistoryStems + KRootStems + KEdgeStems + KFillStems


# shared read members setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadMembers(DataValue: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(DataValue)) as Archive:
        return {Entry: Archive.read(Entry) for Entry in Archive.namelist()}


# shared load fixture setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def LoadFixture(StemName: str) -> bytes:
    return (KFixtures / f"{StemName}.f3d").read_bytes()


# shared load member setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def LoadMember(StemName: str, Suffix: str) -> bytes:
    Found = [
        DataValue
        for Entry, DataValue in ReadMembers(LoadFixture(StemName)).items()
        if Entry.endswith(Suffix)
    ]
    assert len(Found) == 1
    return Found[0]


# shared load journal setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def LoadJournal(StemName: str) -> JournalModel:
    Model = ReadJournal(LoadMember(StemName, ".smbh"))
    assert ReadJournal(EmitJournal(Model)) == Model
    return Model


# shared swap entity setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def SwapEntity(
    Entities: tuple[KJournalEntity, ...], Index: int, Value: KJournalEntity
) -> tuple[KJournalEntity, ...]:
    return Entities[:Index] + (Value,) + Entities[Index + 1 :]


# the journal trip contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
@TestMark.parametrize("StemName", KFixedStems)
def TestJournalTrip(StemName: str) -> None:
    Source = LoadFixture(StemName)
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


# the working open contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestWorkingOpen() -> None:
    Model = LoadJournal("pathpatterns-de9857f6a1bc/arc_along")
    WorkingNode = Model.Stream.WorkingNode
    assert WorkingNode == Model.Stream.ActiveNode
    Working = Model.States[WorkingNode]
    assert Working.StateId == 0
    assert len(Working.Boards) == 1 and not Working.Boards[0].Changes
    Closed = Model.States[Working.NextNode]
    assert Closed.StateId == Model.Stream.CurrentStateId
    Foreign = next(
        Change
        for State in Model.States
        for Board in State.Boards
        for Change in Board.Changes
    )
    Edited = Replace(Working, Boards=(Replace(Working.Boards[0], Changes=(Foreign,)),))
    States = Model.States[:WorkingNode] + (Edited,) + Model.States[WorkingNode + 1 :]
    with Raises(ValueError, match="open working delta state"):
        _ = EmitJournal(Replace(Model, States=States))


# the board bound contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestBoardBound() -> None:
    Model = LoadJournal("patterns-35e49809a812/symmetric_one")

    # ordering by in model states index boards must stay deterministic so native document reconstruction resolves equivalent inputs consistently
    Position = max(
        range(len(Model.States)),
        key=lambda Index: sum(
            len(Board.Changes) for Board in Model.States[Index].Boards
        ),
    )
    State = Model.States[Position]
    Board = State.Boards[0]
    assert 1000 < len(Board.Changes) <= KBoardChanges
    Padded = Board.Changes + (Board.Changes[0],) * (
        KBoardChanges + 1 - len(Board.Changes)
    )
    Edited = Replace(State, Boards=(Replace(Board, Changes=Padded),))
    States = Model.States[:Position] + (Edited,) + Model.States[Position + 1 :]
    with Raises(ValueError, match="Oversized Fusion bulletin change list"):
        _ = EmitJournal(Replace(Model, States=States))


# the root count contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestRootCount() -> None:
    Model = LoadJournal("extents-f0f33a9a605f/from_plane")
    Header = Replace(Model.Header, RootCount=Model.Header.RootCount - 1)
    with Raises(ValueError, match="active bodies disagree with its root count"):
        _ = EmitJournal(Replace(Model, Header=Header))


# the apex edge contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestApexEdge() -> None:
    Model = LoadJournal("holes-926347c1eaa8/simple")
    EdgeIndex = next(
        Index
        for Index, Value in enumerate(Model.Entities)
        if isinstance(Value, EdgeNode) and Value.CurveRef == -1
    )
    EdgeValue = Model.Entities[EdgeIndex]
    assert isinstance(EdgeValue, EdgeNode)
    assert EdgeValue.StartVertex == EdgeValue.EndVertex
    assert (EdgeValue.StartParam, EdgeValue.EndParam) == (1.0, 0.0)
    Edited = SwapEntity(Model.Entities, EdgeIndex, Replace(EdgeValue, EndParam=0.5))
    with Raises(ValueError, match="Missing required Fusion topology reference"):
        _ = EmitJournal(Replace(Model, Entities=Edited))


# the torus ring contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestTorusRing() -> None:
    Model = LoadJournal("specialfillets-d50f7a4f04e0/rule_all_both")
    TorusIndex = next(
        Index
        for Index, Value in enumerate(Model.Entities)
        if isinstance(Value, TorusNode) and Value.MinorRadiusCm < 0
    )
    TorusValue = Model.Entities[TorusIndex]
    assert isinstance(TorusValue, TorusNode)
    assert 0 < -TorusValue.MinorRadiusCm < TorusValue.MajorRadiusCm
    Flattened = Replace(TorusValue, MinorRadiusCm=-TorusValue.MajorRadiusCm)
    Edited = SwapEntity(Model.Entities, TorusIndex, Flattened)
    with Raises(ValueError, match="Fusion horn-torus carriers"):
        _ = EmitJournal(Replace(Model, Entities=Edited))


# the edge ring contract needs boundary coverage so stored document relationships remain consistent
@KRequiresCodec
def TestEdgeRing() -> None:
    Model = ReadGeometry(
        LoadMember("thinextrudes-c1632bcb5efe/closed_two_sides_mixed", ".smb")
    )
    assert ReadGeometry(EmitGeometry(Model)) == Model
    Groups: dict[int, list[int]] = {}
    for Index, Value in enumerate(Model.Entities):
        if isinstance(Value, CoedgeNode):
            Groups.setdefault(Value.EdgeRef, []).append(Index)
    RingUses = [Group for Group in Groups.values() if len(Group) == 4]
    assert len(RingUses) == 4
    Edited = Model.Entities
    for UseIndex in RingUses[0]:
        UseValue = Model.Entities[UseIndex]
        assert isinstance(UseValue, CoedgeNode)
        Edited = SwapEntity(Edited, UseIndex, Replace(UseValue, Reversed=False))
    with Raises(ValueError, match="nonmanifold edge uses need both senses"):
        _ = EmitGeometry(Replace(Model, Entities=Edited))
