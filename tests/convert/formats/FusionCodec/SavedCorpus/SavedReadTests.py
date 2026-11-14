from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as ExpectError

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Topology.ApplyIds import ApplyIds
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Reading.PickBodyView import PickBodyView
from convert.formats.Fusion.DocumentCodec.Reading.ReadTypedBody import ReadTypedBody
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import (
    DocumentCatalog,
)
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import (
    ReadDocSchemas,
)
from convert.formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import (
    AuthorSchemas,
)
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Vocabulary.PickSchema import PickSchema
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GeoValue import GeoValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh

KRoot = FilePath(__file__).resolve().parents[5]

KRequiresCodec = TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KReencoded = (".protein", ".smb", ".smbh", ".paramesh")

KActivePrefix = "FusionAssetName[Active]/"

KOracleBrep = (
    "re/Fusion/LocalOracle/Brep/native_cuboid_12_18_24.f3d",
    "re/Fusion/LocalOracle/Brep/vendor_binary_temporary.f3d",
    "re/Fusion/LocalOracle/Brep/vendor_production_cuboid_smb.f3d",
    "re/Fusion/LocalOracle/Brep/vendor_production_smb.f3d",
    "re/Fusion/LocalOracle/DimensionAuthoring/vendor_DimensionedCuboidEdited.f3d",
    "re/Fusion/LocalOracle/DimensionAuthoring/vendor_DimensionedRectangleEdited.f3d",
    "re/Fusion/LocalOracle/Frustums/vendor_CylindricalLimit_smb.f3d",
    "re/Fusion/LocalOracle/Frustums/vendor_Expanding_smb.f3d",
    "re/Fusion/LocalOracle/Frustums/vendor_Shrinking_smb.f3d",
    "re/Fusion/LocalOracle/JournalStates/DraftPermutedHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/DraftProductionHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/DraftProductionPermutedHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/DraftTypedHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/OffsetCylinderPermutedHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/OffsetCylinderProductionHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/OffsetCylinderProductionPermutedHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/OffsetCylinderTypedHistory.f3d",
    "re/Fusion/LocalOracle/JournalStates/vendor_DraftControlEdited.f3d",
    "re/Fusion/LocalOracle/JournalStates/vendor_DraftReemittedEdited.f3d",
    "re/Fusion/LocalOracle/JournalStates/vendor_PermutationDraftControlEdited.f3d",
    "re/Fusion/LocalOracle/JournalStates/vendor_PermutationDraftPermutedEdited.f3d",
    "re/Fusion/LocalOracle/JournalStates/vendor_ProductionJournalDraftControlEdited.f3d",
    "re/Fusion/LocalOracle/JournalStates/vendor_ProductionJournalDraftProductionEdited.f3d",
    "re/Fusion/LocalOracle/JournalStates/vendor_ProductionJournalDraftProductionPermutedEdited.f3d",
)

KOracleShape = (
    "re/Fusion/LocalOracle/PlanarTopology/TetrahedronPermuted.f3d",
    "re/Fusion/LocalOracle/PlanarTopology/TetrahedronProduction.f3d",
    "re/Fusion/LocalOracle/PlanarTopology/TriangularPipePermuted.f3d",
    "re/Fusion/LocalOracle/PlanarTopology/TriangularPipeProduction.f3d",
    "re/Fusion/LocalOracle/PlanarTopology/vendor_IndependentTetrahedron.f3d",
    "re/Fusion/LocalOracle/PlanarTopology/vendor_IndependentTriangularPrism.f3d",
    "re/Fusion/LocalOracle/PlanarTopology/vendor_PlacedTetrahedron.f3d",
    "re/Fusion/LocalOracle/PublicAdapter/vendor_cuboidEdited.f3d",
    "re/Fusion/LocalOracle/PublicAdapter/vendor_rectangleEdited.f3d",
    "re/Fusion/LocalOracle/RectangleConstraints/EditedDimensions.f3d",
    "re/Fusion/LocalOracle/RectangleConstraints/WidthDepthDimensions.f3d",
    "re/Fusion/LocalOracle/RectangleDimensions/EditedDimensions.f3d",
    "re/Fusion/LocalOracle/RectangleDimensions/WidthDepthDimensions.f3d",
    "re/Fusion/LocalOracle/RotationalDocuments/vendor_NativeCylinderControl.f3d",
    "re/Fusion/LocalOracle/RotationalDocuments/vendor_NativeCylinderReemitted.f3d",
    "re/Fusion/LocalOracle/RotationalDocuments/vendor_NativeFrustumControl.f3d",
    "re/Fusion/LocalOracle/RotationalDocuments/vendor_NativeFrustumReemitted.f3d",
)

KOracleRound = (
    "re/Fusion/LocalOracle/RoundBodies/vendor_AuthoredSphere.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_AuthoredTilted.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_AuthoredTorus.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_DecodedPlacedTorus.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_DecodedSphere.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_DecodedTiltedTorus.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_DecodedTorus.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_RoundFilletsControl.f3d",
    "re/Fusion/LocalOracle/RoundBodies/vendor_RoundFilletsReemitted.f3d",
    "re/Fusion/LocalOracle/RoundCarriers/PlacedTorus.f3d",
    "re/Fusion/LocalOracle/RoundCarriers/Sphere.f3d",
    "re/Fusion/LocalOracle/RoundCarriers/TiltedTorus.f3d",
    "re/Fusion/LocalOracle/RoundCarriers/Torus.f3d",
)

KStudyFiles = (
    "re/Fusion/Study/assembly-acc48a9dc05d/assembly.f3d",
    "re/Fusion/Study/constructionmodes-e355ad6031c0/axis_circular_face.f3d",
    "re/Fusion/Study/constructionmodes-e355ad6031c0/axis_normal_to_face.f3d",
    "re/Fusion/Study/extents-f0f33a9a605f/distance_negative.f3d",
    "re/Fusion/Study/extents-f0f33a9a605f/distance_positive.f3d",
    "re/Fusion/Study/extents-f0f33a9a605f/offset_negative.f3d",
    "re/Fusion/Study/extents-f0f33a9a605f/offset_positive.f3d",
    "re/Fusion/Study/models-b8a640dbddc6/new_body.f3d",
    "re/Fusion/Study/namedbodies-3c7c11fc2924/namedbodies.f3d",
    "re/Fusion/Study/planedefinitions-6cd0820a832e/tangent_at_point.f3d",
    "re/Fusion/Study/profiles-66b0447c28ac/concentric_disk.f3d",
    "re/Fusion/Study/profiles-66b0447c28ac/disjoint_left.f3d",
    "re/Fusion/Study/profiles-66b0447c28ac/disjoint_right.f3d",
    "re/Fusion/Study/silhouettesplits-7d78a686cdbb/faces_axis_x.f3d",
    "re/Fusion/Study/silhouettesplits-7d78a686cdbb/faces_axis_y.f3d",
    "re/Fusion/Study/silhouettesplits-7d78a686cdbb/faces_plane_yz.f3d",
    "re/Fusion/Study/silhouettesplits-7d78a686cdbb/solid_axis_x.f3d",
    "re/Fusion/Study/silhouettesplits-f21b83e21695/shelled_hollow_axis_x.f3d",
    "re/Fusion/Study/splitbodyprofiles-be9787c7a7d8/full_profile_one_body.f3d",
    "re/Fusion/Study/splitbodyprofiles-be9787c7a7d8/small_profile_extended.f3d",
    "re/Fusion/Study/thinextrudes-f758eff14202/open_line_side1.f3d",
)

KFixedFiles = KOracleBrep + KOracleShape + KOracleRound + KStudyFiles

KDraftGuid = "F4163A07-9E71-4C46-BD92-ACE5B5B40BED"

KDraftBase = "666BFBBC-2150-4C5F-AAF7-09AB3C3D9E47"

KDraftMembers = (
    ("MovingPartingLineDraftAngleType", "u32", ""),
    ("draftType", "u32", ""),
    ("m_bFlipped", "bool", ""),
    ("m_bTangentPropagation", "bool", ""),
    ("m_directionType", "u32", ""),
    ("m_draftAngle1", "ref", "D91D429C-1BB5-4640-B49F-69AF14F463E9"),
    ("m_draftAngle2", "ref", "D91D429C-1BB5-4640-B49F-69AF14F463E9"),
    ("m_facePickPoint", "struct", ""),
    ("m_facesRef", "ref", "2CA5A1CD-C99B-4C9B-91AF-57989148E841"),
    ("m_fixedPlaneDraftAngleMode", "u32", ""),
    ("m_rFixedEdgesDataRef", "ref", "2CA5A1CD-C99B-4C9B-91AF-57989148E841"),
    ("m_rRefPlaneDataRef", "ref", "2CA5A1CD-C99B-4C9B-91AF-57989148E841"),
    ("rPartingLineToolDataRef", "ref", "2CA5A1CD-C99B-4C9B-91AF-57989148E841"),
)

KDraftValues = (
    ("MovingPartingLineDraftAngleType", 3),
    ("draftType", 1),
    ("m_bFlipped", False),
    ("m_bTangentPropagation", False),
    ("m_directionType", 1),
    ("m_fixedPlaneDraftAngleMode", 1),
)

KHolderGuid = "D87EC2D8-35C1-4AA2-A308-09AF07C490FF"

KHolderBase = "98542EB9-A4F2-4137-A808-DBB5B3CD6159"

KMatrixGuid = "7B6C3C2D-4096-4E6D-B225-699E8C2D9355"

KNewestPairs = (
    (KDraftGuid, (5, 6)),
    (KMatrixGuid, (14, 15, 16)),
    ("7A6A3D31-BE74-4E19-9115-20642944C2E4", (8, 9, 10)),
    ("D4CBC599-0FFB-4d32-BF14-A7F0AFA25013", (10, 11)),
    ("4C835764-5BAB-4421-B5D2-06015BEF6EB2", (4, 5)),
    ("D572415C-6C2C-460B-8C84-265C52D89EDF", (2, 4)),
)

KIdentity = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)

KTrackedFiles = (
    (
        "re/Fusion/LocalOracle/RotationalDocuments/vendor_NativeCylinderControl.f3d",
        HistoryModel,
    ),
    (
        "re/Fusion/LocalOracle/RotationalDocuments/vendor_NativeFrustumControl.f3d",
        FrustumHistory,
    ),
)


def LoadFixture(RelativeName: str) -> bytes:
    return (KRoot / RelativeName).read_bytes()


def ReadMembers(Payload: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(Payload)) as Archive:
        return {Entry: Archive.read(Entry) for Entry in Archive.namelist()}


def CollectMats(Value: object) -> tuple[MatrixValue, ...]:
    if isinstance(Value, MatrixValue):
        return (Value,)
    if isinstance(Value, tuple):
        return tuple(
            Found
            for Entry in CastValue(tuple[object, ...], Value)
            for Found in CollectMats(Entry)
        )
    if IsDataClass(Value) and not isinstance(Value, type):
        return tuple(
            Found
            for FieldInfo in DataFields(Value)
            for Found in CollectMats(getattr(Value, FieldInfo.name))
        )
    return ()


def FindStrips(RelativeName: str) -> tuple[DocumentModel, tuple[int, ...]]:
    Model = ReadDocument(LoadFixture(RelativeName))
    Scene = Model.Graphics
    assert Scene is not None
    Indices = tuple(
        Index
        for Index, Entry in enumerate(Scene.Objects)
        if isinstance(Entry.Value, GeoValue)
        and isinstance(Entry.Value.Geometry, SimpleMesh)
        and Entry.Value.Geometry.Primitive == 5
    )
    return Model, Indices


def PatchFolder(Payload: bytes, Method: int) -> bytes:
    Buffer = bytearray(Payload)
    Cursor = Buffer.find(b"PK\x01\x02")
    while Cursor >= 0:
        NameSize = int.from_bytes(Buffer[Cursor + 28 : Cursor + 30], "little")
        if Buffer[Cursor + 45 + NameSize] == ord("/"):
            Buffer[Cursor + 10 : Cursor + 12] = Method.to_bytes(2, "little")
            return bytes(Buffer)
        Cursor = Buffer.find(b"PK\x01\x02", Cursor + 46)
    raise AssertionError("fixture has no directory entry")


@KRequiresCodec
@TestMarks.parametrize("RelativeName", KFixedFiles)
def TestSavedTrip(RelativeName: str) -> None:
    Payload = LoadFixture(RelativeName)
    Model = ReadDocument(Payload)
    Emitted = EmitParsed(Model)
    assert ReadDocument(Emitted) == Model
    Source = ReadMembers(Payload)
    Output = ReadMembers(Emitted)
    assert Source.keys() == Output.keys()
    for Entry, Content in Source.items():
        if not Entry.endswith(KReencoded):
            assert Output[Entry] == Content, Entry


def TestDraftSchema() -> None:
    Catalog = DocumentCatalog(ReadDocSchemas())
    Newer = PickSchema(KDraftGuid, 6, Catalog)
    Older = PickSchema(KDraftGuid, 5, Catalog)
    assert Newer.BaseGuid == Older.BaseGuid == KDraftBase
    assert (
        tuple(
            (Field.FieldName, Field.ValueType.KindValue, Field.ValueType.ClassGuid)
            for Field in Newer.Members
        )
        == KDraftMembers
    )
    assert {Field.FieldName for Field in Newer.Members} - {
        Field.FieldName for Field in Older.Members
    } == {"m_fixedPlaneDraftAngleMode"}
    assert tuple(Field.FieldName for Field in Older.Members) == tuple(
        Field.FieldName
        for Field in Newer.Members
        if Field.FieldName != "m_fixedPlaneDraftAngleMode"
    )


@KRequiresCodec
def TestDraftValues() -> None:
    Model = ReadDocument(
        LoadFixture("re/Fusion/LocalOracle/JournalStates/vendor_DraftControlEdited.f3d")
    )
    Groups = [
        Group
        for Segment in Model.Segments
        for Record in Segment.Records
        for Group in Record.Groups
        if Group.ClassGuid.upper() == KDraftGuid
    ]
    assert len(Groups) == 1
    Values = {Field.FieldName: Field.Value for Field in Groups[0].Fields}
    for FieldName, Expected in KDraftValues:
        assert Values[FieldName] == Expected


def TestNewestPick() -> None:
    Catalog = DocumentCatalog(ReadDocSchemas())
    for ClassGuid, Expected in KNewestPairs:
        Versions = tuple(
            sorted(
                Schema.SchemaVersion for Schema in Catalog.Classes[ClassGuid.upper()]
            )
        )
        assert Versions == Expected
        Newest = Expected[-1]
        assert PickSchema(ClassGuid, None, Catalog).SchemaVersion == Newest
        assert PickSchema(ClassGuid.lower(), None, Catalog).SchemaVersion == Newest


def TestUnknownPick() -> None:
    Catalog = DocumentCatalog(ReadDocSchemas())
    with ExpectError(ValueError, match="Unqualified Fusion native class"):
        _ = PickSchema(KDraftGuid, 7, Catalog)
    with ExpectError(ValueError, match="Unqualified Fusion native class"):
        _ = PickSchema("00000000-0000-0000-0000-000000000000", None, Catalog)


def TestHolder() -> None:
    Holder = PickSchema(KHolderGuid, 0, DocumentCatalog(ReadDocSchemas()))
    assert Holder.BaseGuid == KHolderBase
    assert Holder.Members == ()
    assert not Holder.IsValue


def TestAuthorScope() -> None:
    for ProfileKind in ("cuboid", "rectangle", "extrusion"):
        Authored = AuthorSchemas(ProfileKind)
        Identities = {Schema.Value.ClassGuid.upper() for Schema in Authored}
        assert KHolderGuid not in Identities
        assert KDraftGuid not in Identities


@KRequiresCodec
def TestMatrixRows() -> None:
    Schema = PickSchema(KMatrixGuid, 16, DocumentCatalog(ReadDocSchemas()))
    Matrices = [
        Field for Field in Schema.Members if Field.ValueType.KindValue == "matrix"
    ]
    assert [Field.FieldName for Field in Matrices] == ["matrix3d"]
    assert Matrices[0].ValueType.HasMatrixRows
    Model = ReadDocument(
        LoadFixture("re/Fusion/LocalOracle/RoundBodies/vendor_RoundFilletsControl.f3d")
    )
    Values = CollectMats(Model.Segments)
    Moved = [
        Value
        for Value in Values
        if Value.Entries is not None and Value.Entries != KIdentity
    ]
    assert len(Moved) == 3
    assert all(len(Value.Entries or ()) == 16 for Value in Moved)


@KRequiresCodec
def TestStripMesh() -> None:
    Model, Indices = FindStrips(
        "re/Fusion/LocalOracle/PublicAdapter/vendor_cuboidEdited.f3d"
    )
    assert len(Indices) == 4
    assert ReadDocument(EmitParsed(Model)) == Model


@KRequiresCodec
def TestStripReject() -> None:
    Model, Indices = FindStrips(
        "re/Fusion/LocalOracle/PublicAdapter/vendor_cuboidEdited.f3d"
    )
    Scene = Model.Graphics
    assert Scene is not None
    Target = Scene.Objects[Indices[0]]
    Shape = Target.Value
    assert isinstance(Shape, GeoValue) and isinstance(Shape.Geometry, SimpleMesh)
    Changed = Replace(
        Target,
        Value=Replace(Shape, Geometry=Replace(Shape.Geometry, Primitive=6)),
    )
    Objects = list(Scene.Objects)
    Objects[Indices[0]] = Changed
    Mutated = Replace(Model, Graphics=Replace(Scene, Objects=tuple(Objects)))
    with ExpectError(ValueError, match="Unsupported graphics primitive topology"):
        _ = EmitParsed(Mutated)


def TestEntityIds() -> None:
    Default = EntityIds()
    assert Default.FaceIds == (-1, -1, -1)
    assert Default.VertexIds == (-1, -1)
    Tracked = EntityIds((14, 15, 16), (12, 13))
    assert Tracked.FaceIds == (14, 15, 16)
    with ExpectError(ValueError, match="three faces and two vertices"):
        _ = EntityIds((1, 2), (3, 4))
    with ExpectError(ValueError, match="three faces and two vertices"):
        _ = EntityIds((-1, -1, -1), (-1, -1, -1))


def TestIdBounds() -> None:
    with ExpectError(ValueError, match="entity identity"):
        _ = EntityIds((-2, -1, -1), (-1, -1))
    with ExpectError(ValueError, match="entity identity"):
        _ = EntityIds((1 << 31, -1, -1), (-1, -1))
    assert EntityIds(((1 << 31) - 1, -1, -1), (-1, -1)).FaceIds[0] == (1 << 31) - 1


def TestSlotReject() -> None:
    Records = (GeometryRecord("face", (-1, -1)),) * 22
    Applied = ApplyIds(Records, EntityIds((7, 8, 9), (10, 11)))
    assert [Applied[Index].Fields[1] for Index in (4, 5, 6, 20, 21)] == [
        7,
        8,
        9,
        10,
        11,
    ]
    assert ApplyIds(Records, EntityIds()) == Records
    with ExpectError(ValueError, match="identity slot is already assigned"):
        _ = ApplyIds(Applied, EntityIds((7, 8, 9), (10, 11)))


@KRequiresCodec
@TestMarks.parametrize("RelativeName,ViewType", KTrackedFiles)
def TestTrackedIds(RelativeName: str, ViewType: type[object]) -> None:
    Model = ReadDocument(LoadFixture(RelativeName))
    assert len(Model.Bodies) == 1
    History = Model.Bodies[0].History
    assert isinstance(History, ViewType)
    assert getattr(History, "Tracking") == EntityIds((14, 15, 16), (12, 13))
    assert ReadDocument(EmitParsed(Model)) == Model


@KRequiresCodec
def TestTypedFall() -> None:
    Payload = LoadFixture("re/Fusion/Study/extents-f0f33a9a605f/offset_negative.f3d")
    Model = ReadDocument(Payload)
    Members = ReadMembers(Payload)
    assert len(Model.Bodies) == 1
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert PickBodyView(History) == "cylinder"
    Content = Members[KActivePrefix + Model.Bodies[0].PartName]
    assert ReadTypedBody(Content, "cylinder") is None
    assert ReadDocument(EmitParsed(Model)) == Model


@KRequiresCodec
def TestFolderRule() -> None:
    Payload = LoadFixture("re/Fusion/LocalOracle/JournalStates/DraftTypedHistory.f3d")
    with ZipFile(BytesIO(Payload)) as Archive:
        Folders = [Entry for Entry in Archive.infolist() if Entry.is_dir()]
    assert Folders
    assert all(
        (Entry.compress_type, Entry.compress_size, Entry.file_size) == (8, 2, 0)
        for Entry in Folders
    )
    assert len(ReadContainer(Payload).Streams) == 3


@KRequiresCodec
def TestFoldReject() -> None:
    Payload = LoadFixture("re/Fusion/LocalOracle/JournalStates/DraftTypedHistory.f3d")
    with ExpectError(ValueError, match="directories must be empty stored or deflated"):
        _ = ReadContainer(PatchFolder(Payload, 0))
