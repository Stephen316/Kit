from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from dataclasses import replace as Replace
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue

from pytest import mark as TestMark, raises as Raises

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.formats.Fusion.ContainerCodec.Wire.EmitAssetHeader import EmitAssetHeader
from convert.formats.Fusion.ContainerCodec.Wire.ReadAssetHeader import ReadAssetHeader
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.CheckAsmSpec import CheckAsmSpec
from convert.formats.Fusion.LinkAuthor.EmitAssembly import EmitAssembly, LinkDocument
from convert.formats.Fusion.LinkAuthor.MatrixMath import ComposeMatrix
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Model.LinkTarget import LinkTarget
from convert.formats.Fusion.LinkAuthor.Model.PlacedPart import PlacedPart
from convert.formats.Fusion.LinkAuthor.Model.RigidJoint import RigidJoint
from convert.formats.Fusion.LinkAuthor.Reading.ObserverSlots import NextSlot
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KActRefdTable,
    KBaseInstance,
    KDcOccurrence,
)
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import KUnchangedGuid

KFixtures = (
    FilePath(__file__).resolve().parents[5]
    / "re"
    / "Fusion"
    / "LocalOracle"
    / "LinksConfigs"
    / "Fixtures"
)

KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KMasked = "masked"

KFreshFields = frozenset(
    {
        "persistentId",
        "instanceIdentifiers",
        "xAssetLinkName",
        "RefdDocLinkName",
        "timeStamp",
        "computeTime",
        "refedDocAssetsHashCache",
        "isBodyOK",
        "isPredecessorOK",
        "predecessors",
        "bodies",
        "xRefPredecessorsHash",
        "AssetRevGuid",
        "RevisionGuid",
        "revisionGuidForChangeType",
        "revisionGuid",
        "sortIsCurrent",
        "sortedNodesAll",
        "mapsAreCurrent",
        "predecessorMap",
        "successorMap",
        "partName",
    }
)

KFreshData = (3, 9, 13)

KPartInRoot = (0.6, -0.8, 0.0, 5.0, 0.8, 0.6, 0.0, 2.0, 0.0, 0.0, 1.0, 1.0)

KSubInRoot = (1.0, 0.0, 0.0, -3.0, 0.0, 0.0, -1.0, 4.0, 0.0, 1.0, 0.0, 0.5)

KPartInSub = (0.0, -1.0, 0.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0)

KAffineRow = (0.0, 0.0, 0.0, 1.0)

KLineagePrefix = "urn:kit:synthetic:lineage:"

KVersionPrefix = "urn:kit:synthetic:file:"


def LoadFixture(StemName: str) -> DocumentModel:
    return ReadDocument((KFixtures / f"{StemName}.f3d").read_bytes())


def MaskValue(Value: object, Roles: dict[int, tuple[str, int]]) -> object:
    if isinstance(Value, CrossRef):
        return (Value.ObjectId, Roles[Value.Token], Value.TypeGuid.upper())
    if isinstance(Value, NamedValue):
        Named = CastValue(NamedValue[KEntityValue], Value)
        if Named.FieldName in KFreshFields:
            return (Named.FieldName, KMasked)
        if Named.FieldName == "passiveentries" and isinstance(Named.Value, ValueMap):
            Pairs = sorted(
                (MaskValue(Entry, Roles) for Entry in Named.Value.Entries), key=repr
            )
            return (Named.FieldName, tuple(Pairs))
        return (Named.FieldName, MaskValue(Named.Value, Roles))
    if isinstance(Value, EntityRecord):
        return (
            Value.ObjectId,
            Value.IsPrimary,
            MaskValue(Value.Frame, Roles),
            MaskValue(Value.Groups, Roles),
        )
    if isinstance(Value, EntityGroup):
        Group = CastValue(EntityGroup[KEntityValue], Value)
        return (Group.ClassGuid.upper(), MaskValue(Group.Fields, Roles))
    if isinstance(Value, EntityFrame):
        Subjects = None
        if Value.Subjects is not None:
            Subjects = tuple(
                sorted((MaskValue(Entry, Roles) for Entry in Value.Subjects), key=repr)
            )
        return (Value.RootId, Subjects, MaskValue(Value.Metadata, Roles))
    if type(Value) is float:
        return round(Value, 9) + 0.0
    if IsDataClass(Value) and not isinstance(Value, type):
        return (type(Value).__name__,) + tuple(
            MaskValue(getattr(Value, Field.name), Roles) for Field in DataFields(Value)
        )
    if isinstance(Value, tuple):
        Entries = CastValue(tuple[object, ...], Value)
        return tuple(MaskValue(Entry, Roles) for Entry in Entries)
    return Value


def RecordView(
    Model: DocumentModel, Fresh: tuple[int, ...]
) -> dict[tuple[str, int, bool], object]:
    Roles = {
        Context.Token: (Context.AssetId, Context.SegmentId)
        for Segment in Model.Segments
        for Context in Segment.Metadata.Contexts
    }
    Result: dict[tuple[str, int, bool], object] = {}
    for Segment in Model.Segments:
        KindValue = Segment.Metadata.Header.Segment.name
        for Record in Segment.Records:
            Masked = MaskValue(Record, Roles)
            if KindValue == "KAct" and Record.ObjectId in Fresh:
                Masked = KMasked
            Result[(KindValue, Record.ObjectId, Record.IsPrimary)] = Masked
    return Result


def NativeSpec(Native: DocumentModel) -> AssemblySpec:
    Links = {
        dict(Entry.Properties)["toDocDisplayName"]: dict(Entry.Properties)
        for Entry in Native.Document.Links
    }
    Design = Native.Segments[0]
    Matrices: dict[int, tuple[float, ...]] = {}
    for Record in Design.Records:
        for Group in Record.Groups:
            for Field in Group.Fields:
                if Field.FieldName != "transform" or not isinstance(
                    Field.Value, MatrixValue
                ):
                    continue
                if Field.Value.Entries is not None:
                    Matrices[Record.ObjectId] = Field.Value.Entries
    Targets = tuple(
        LinkTarget(
            Title,
            Links[Title]["LineageUrn"],
            Links[Title]["URL"],
            LoadFixture(StemName),
        )
        for Title, StemName in (
            ("KitLinkPartA", "P_A1_saved"),
            ("KitLinkSub", "S1_saved"),
        )
    )
    Placements = (PlacedPart(0, Matrices[203], True), PlacedPart(1, Matrices[219]))
    BaseSpec = DocumentSpec("KitReplay", "rootLength", 10.0, ProfileKind="parameter")
    return AssemblySpec(BaseSpec, Targets, Placements, RigidJoint(0, 1))


@KRequiresCodec
def TestReplay() -> None:
    Native = LoadFixture("R4_joint")
    Request = CheckAsmSpec(NativeSpec(Native))
    Built = ReadDocument(EmitParsed(LinkDocument(LoadFixture("R0_empty"), Request)))
    assert [Segment.Metadata.NextId for Segment in Built.Segments] == [
        Segment.Metadata.NextId for Segment in Native.Segments
    ]
    assert [len(Segment.Metadata.Contexts) for Segment in Built.Segments] == [2, 2, 2]
    Expected, Actual = RecordView(Native, KFreshData), RecordView(Built, KFreshData)
    assert Actual.keys() == Expected.keys()
    Mismatched = sorted(Label for Label in Expected if Expected[Label] != Actual[Label])
    assert not Mismatched


def MakePart(Title: str, Param: str, Length: float, Radius: float) -> bytes:
    Request = DocumentSpec(
        Title, Param, Length, ProfileKind="extrusion", RadiusMm=Radius
    )
    return EncodeDocument(MakeFusionDoc(Request))


def MakeTarget(Title: str, DataValue: bytes) -> LinkTarget:
    return LinkTarget(
        Title,
        f"{KLineagePrefix}{Title}",
        f"{KVersionPrefix}{Title}?version=1",
        ReadDocument(DataValue),
    )


def BuildNested() -> tuple[bytes, bytes, bytes, bytes]:
    PartA = MakePart("KitAsmPartA", "heightA", 5.0, 10.0)
    PartB = MakePart("KitAsmPartB", "lengthB", 12.0, 4.0)
    SubBase = DocumentSpec("KitAsmSub", "subLength", 3.0, ProfileKind="parameter")
    SubData = EmitAssembly(
        AssemblySpec(
            SubBase,
            (MakeTarget("KitAsmPartB", PartB),),
            (PlacedPart(0, KPartInSub + KAffineRow),),
        )
    )
    RootBase = DocumentSpec("KitAsmRoot", "rootLength", 10.0, ProfileKind="parameter")
    RootData = EmitAssembly(
        AssemblySpec(
            RootBase,
            (MakeTarget("KitAsmPartA", PartA), MakeTarget("KitAsmSub", SubData)),
            (
                PlacedPart(0, KPartInRoot + KAffineRow, True),
                PlacedPart(1, KSubInRoot + KAffineRow),
            ),
            RigidJoint(0, 1),
        )
    )
    return PartA, PartB, SubData, RootData


def ClassRecords(Model: DocumentModel, ClassGuid: str) -> tuple[EntityRecord, ...]:
    return tuple(
        Record
        for Segment in Model.Segments
        for Record in Segment.Records
        if Record.IsPrimary
        and any(Group.ClassGuid.upper() == ClassGuid.upper() for Group in Record.Groups)
    )


def FieldOf(Record: EntityRecord, FieldName: str) -> object:
    Values = [
        Field.Value
        for Group in Record.Groups
        for Field in Group.Fields
        if Field.FieldName == FieldName
    ]
    assert len(Values) == 1
    return Values[0]


@KRequiresCodec
def TestKitNested() -> None:
    PartA, PartB, SubData, RootData = BuildNested()
    RootInfo, SubModel, Target = (
        ReadDocument(RootData),
        ReadDocument(SubData),
        ReadDocument(PartA),
    )
    assert ReadDocument(EmitParsed(RootInfo)) == RootInfo
    assert [Entry.AssetId for Entry in RootInfo.Asset.Links] == [
        Target.Asset.AssetId,
        SubModel.Asset.AssetId,
    ]
    assert {Entry.PhysicalGuid for Entry in RootInfo.Asset.Links} == {KUnchangedGuid}
    Revisions = {
        Context.RevisionId
        for Segment in RootInfo.Segments
        for Context in Segment.Metadata.Contexts
    }
    assert Revisions == {Target.Document.DocumentId, SubModel.Document.DocumentId}
    Matrices = [
        FieldOf(Record, "transform") for Record in ClassRecords(RootInfo, KBaseInstance)
    ]
    assert MatrixValue(KPartInRoot + KAffineRow) in Matrices
    assert MatrixValue(KSubInRoot + KAffineRow) in Matrices
    Nested = ComposeMatrix(KSubInRoot + KAffineRow, KPartInSub + KAffineRow)
    States = repr(
        [FieldOf(Record, "states") for Record in ClassRecords(RootInfo, KDcOccurrence)]
    )
    assert repr(MatrixValue(Nested)) in States
    Tables = ClassRecords(RootInfo, KActRefdTable)
    assert {FieldOf(Record, "RefdAssetGuid") for Record in Tables} == {
        Target.Asset.AssetId,
        SubModel.Asset.AssetId,
    }
    assert len(PartB) > 0


def BadSpecs() -> tuple[AssemblySpec, ...]:
    Target = MakeTarget("KitAsmPartA", MakePart("KitAsmPartA", "heightA", 5.0, 10.0))
    BaseSpec = DocumentSpec("KitAsmRoot", "rootLength", 10.0, ProfileKind="parameter")
    Rigid = KPartInRoot + KAffineRow
    Scaled = (2.0,) + Rigid[1:]
    Valid = AssemblySpec(BaseSpec, (Target,), (PlacedPart(0, Rigid),))
    return (
        Replace(Valid, Placements=(PlacedPart(0, Scaled),)),
        Replace(Valid, Placements=()),
        Replace(Valid, Placements=(PlacedPart(0, Rigid), PlacedPart(0, Rigid))),
        Replace(Valid, Joint=RigidJoint(0, 0)),
        Replace(Valid, Base=Replace(BaseSpec, ProfileKind="extrusion")),
        Replace(
            Valid, Targets=(Replace(Target, VersionUrn="urn:kit:synthetic:noversion"),)
        ),
        Replace(Valid, Targets=(Replace(Target, DisplayName="Bad/Name"),)),
        Replace(Valid, Placements=(PlacedPart(0, Rigid[:15]),)),
    )


@KRequiresCodec
def TestSpecReject() -> None:
    for Request in BadSpecs():
        with Raises(ValueError):
            _ = EmitAssembly(Request)


@KRequiresCodec
def TestZeroChange() -> None:
    Asset = LoadFixture("R4_joint").Asset
    Linked = Replace(Asset.Links[0], PhysicalGuid=KUnchangedGuid)
    Header = Replace(Asset, Links=(Linked,) + Asset.Links[1:])
    assert ReadAssetHeader(EmitAssetHeader(Header)) == Header
    Broken = Replace(Header, Links=(Replace(Linked, LinkId=KUnchangedGuid),))
    with Raises(ValueError):
        _ = EmitAssetHeader(Broken)


@KRequiresCodec
def TestSlots() -> None:
    Target = LoadFixture("P_A1_saved")
    Design = Target.Segments[0].Metadata.Header.SegmentId
    assert Target.Segments[0].Metadata.Header.Segment is SegmentKind.KDesign
    assert [NextSlot(Target, Design, Identity) for Identity in (3, 6, 36)] == [2, 3, 1]
