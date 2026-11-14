from collections import Counter
from sys import version_info as PythonVersion

from pytest import mark as MarkTests

from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.convert.formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    FamilySpec,
    KFamilyCases,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KOracleRoot,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    ClassGuids,
    PartRecords,
)

KFaceMark = tuple[tuple[tuple[str, tuple[int, ...]], ...], bool]


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


def DiscHistory(Model: DocumentModel) -> JournalModel:
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    return History


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
