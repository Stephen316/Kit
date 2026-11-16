from collections import Counter
from sys import version_info as PythonVersion

from pytest import mark as MarkTests

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    FamilySpec,
    KFamilyCases,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KOracleRoot,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    ClassGuids,
    PartRecords,
)

# the face mark shape must stay shared so native document reconstruction uses one contract for compatible values
KFaceMark = tuple[tuple[tuple[str, tuple[int, ...]], ...], bool]


# shared face marks setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def FaceMarks(History: JournalModel) -> dict[int, KFaceMark]:
    Marks: dict[int, KFaceMark] = {}
    for Entity in History.Entities[: History.ActiveCount]:
        if not isinstance(Entity, FaceNode):
            continue
        Names: list[tuple[str, tuple[int, ...]]] = []
        IsTracked = False
        Pointer = Entity.Prefix.Attribute
        while Pointer != -1:
            Attribute = History.Entities[Pointer]
            if not isinstance(
                Attribute, (TagAttrib, TrackAttrib, TimeAttrib, SketchAttrib)
            ):
                break
            if isinstance(Attribute, TagAttrib):
                Names += [
                    (TagValue.PrimaryId, TagValue.OperationIds)
                    for TagValue in Attribute.Groups
                ]
            IsTracked = IsTracked or isinstance(Attribute, TrackAttrib)
            Pointer = Attribute.Links.NextAttrib
        Marks[Entity.Prefix.EntityTag] = (tuple(Names), IsTracked)
    return Marks


# shared disc history setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def DiscHistory(Model: DocumentModel) -> JournalModel:
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    return History


# shared topology caches setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def TopologyCaches(Model: DocumentModel) -> dict[int, dict[str, KEntityValue]]:
    Identity = ClassGuids()["ETCachedTopology"]
    return {
        Record.ObjectId: {
            FieldValue.FieldName: FieldValue.Value
            for Group in Record.Groups
            for FieldValue in Group.Fields
        }
        for Segment in Model.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        if Record.Groups[0].ClassGuid.upper() == Identity
    }


# the copy floors contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion control requires ZIP Zstandard"
)
def TestCopyFloors() -> None:
    Features = KFamilyCases["MultiDiscPart"][0]
    Authored = DiscHistory(ReadDocument(EmitDocument(FamilySpec(Features))))
    Control = (KOracleRoot / "Controls" / "DiscBore.f3d").read_bytes()
    Native = DiscHistory(ReadDocument(Control))
    Expected = Counter(FaceMarks(Native).values())
    CopyFloor = ((("2", (304, 306, 307)),), False)
    assert CopyFloor in Expected
    assert Counter(FaceMarks(Authored).values()) == Expected


# the copy base contract needs boundary coverage so stored document relationships remain consistent
def TestCopyBase() -> None:
    Features = KFamilyCases["MultiDiscPart"][0]
    Model = ReadDocument(EmitDocument(FamilySpec(Features)))
    (Source,) = PartRecords(Model, "DcPatternSource")
    Adjacent = Source["adjacentFaceCaches"]
    assert isinstance(Adjacent, ValueSeries)
    (Pointer,) = Adjacent.Items
    assert isinstance(Pointer, LocalRef)
    Owners = {
        FaceMark: EntityTag
        for EntityTag, FaceMark in FaceMarks(DiscHistory(Model)).items()
    }
    BaseTag = Owners[((("1", (301,)),), False)]
    assert TopologyCaches(Model)[Pointer.ObjectId]["cachedEntityId"] == BaseTag
