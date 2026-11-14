from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord

KNativeChanges: dict[str, tuple[str, str, KEntityValue]] = {
    "suppression": ("DcExtrudeFeature", "isSuppressed", True),
    "direction": ("DcExtrudeFeature", "isFlipDirection", True),
    "parameter": ("Parameter", "value", 12.0),
    "formula": ("Parameter", "expression", "1 mm + 2 mm"),
    "sketch": ("MSketch", "flag", 1),
    "owner": ("DcBody", "rOwnFeature", None),
    "region": ("SketchRegionRecipe", "rSketchRegionRef", None),
}


def ChangeNative(Model: DocumentModel, RoleName: str) -> DocumentModel:
    if RoleName in ("body", "operation", "secondary"):
        BodyValue = Model.Bodies[0]
        if not isinstance(BodyValue.History, PrismHistory):
            raise ValueError("Vendor corruption case requires prism history")
        Identity = BodyValue.History.Identity
        Fields = {
            "body": "BodyKey",
            "operation": "OperationId",
            "secondary": "SecondaryId",
        }
        Identity = ReplaceData(Identity, **{Fields[RoleName]: 987})
        History = ReplaceData(BodyValue.History, Identity=Identity)
        if RoleName == "operation":
            TagSet = ReplaceData(
                History.TagSet,
                Faces=tuple(
                    ReplaceData(Value, OperationIds=(987,))
                    for Value in History.TagSet.Faces
                ),
            )
            History = ReplaceData(History, TagSet=TagSet)
        return ReplaceData(Model, Bodies=(ReplaceData(BodyValue, History=History),))
    ClassName, FieldName, Value = KNativeChanges[RoleName]
    NodeValue = BuildGraph(Model).ByClass(ClassName)[0]
    return ChangeField(Model, NodeValue.ObjectId, FieldName, Value)


def ChangeField(
    Model: DocumentModel, ObjectId: int, FieldName: str, Value: KEntityValue
) -> DocumentModel:
    Segments: list[ParsedSegment] = []
    for Segment in Model.Segments:
        Records: list[EntityRecord] = []
        for Record in Segment.Records:
            if Segment.Metadata.Header.SegmentId == 0 and Record.ObjectId == ObjectId:
                Groups = tuple(
                    ReplaceData(
                        Group,
                        Fields=tuple(
                            (
                                ReplaceData(Field, Value=Value)
                                if Field.FieldName == FieldName
                                else Field
                            )
                            for Field in Group.Fields
                        ),
                    )
                    for Group in Record.Groups
                )
                Record = ReplaceData(Record, Groups=Groups)
            Records.append(Record)
        Segments.append(ReplaceData(Segment, Records=tuple(Records)))
    return ReplaceData(Model, Segments=tuple(Segments))
