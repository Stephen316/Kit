from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectFields import RectFields


def CheckPrismGraph(Model: DocumentModel) -> None:
    assert len(Model.Bodies) == 1
    BodyValue = Model.Bodies[0].History
    assert isinstance(BodyValue, PrismHistory)
    assert (BodyValue.Model.Width, BodyValue.Model.Depth, BodyValue.Model.Height) == (
        17.0,
        23.0,
        31.0,
    )
    assert BodyValue.Model.BasePoint == (0.0, 0.0, 0.0)
    Feature = next(
        Fields
        for Fields in RectFields(Model, "DcFeature")
        if Fields["featureBaseName"] == "Extrude"
    )
    assert Feature["startModelHS"] == BodyValue.History.InitialId
    assert Feature["endModelHS"] == BodyValue.History.CurrentId
    assert len(RectFields(Model, "SketchCurveProgenitor")) == 4
    assert BodyValue.Identity.SecondaryId == 7
    assert tuple(TagValue.PrimaryId for TagValue in BodyValue.TagSet.Faces) == (
        "1",
        "2",
        "4",
        "6",
        "3",
        "5",
    )
    for TagValue in BodyValue.TagSet.Faces:
        assert TagValue.OperationIds == (BodyValue.Identity.OperationId,)
    Parameter = next(
        Fields
        for Fields in RectFields(Model, "Parameter")
        if Fields["name"] == "AlongDistance"
    )
    assert Parameter["expression"] == "boxHeight"
    assert Parameter["value"] == 3.1
