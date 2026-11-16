from math import radians as Radians

from pytest import approx as ApproxValue

from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.Convert.Formats.FusionCodec.Documents.NamedGroups import NamedGroups


# the taper references contract needs boundary coverage so stored document relationships remain consistent
def CheckTaperRefs(Model: DocumentModel, Degrees: float) -> None:
    Taper = next(
        Fields
        for Fields in NamedGroups(Model, "Parameter")
        if Fields["name"] == "TaperAngle"
    )
    Reference = Taper["dcParameter"]
    assert isinstance(Reference, LocalRef)
    Feature = NamedGroups(Model, "DcExtrudeFeature")[0]
    assert Feature["rTaperAngle"] == Reference
    Record = next(
        Record
        for Segment in Model.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        if Record.IsPrimary and Record.ObjectId == Reference.ObjectId
    )
    Fields = {
        Field.FieldName: Field.Value
        for Group in Record.Groups
        for Field in Group.Fields
    }
    assert Fields["value"] == ApproxValue(Radians(Degrees))
    assert Fields["rparamId"] == 2
    assert Fields["rrOwnerFeature"] == Fields["rParentFeature"]
