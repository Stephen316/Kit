from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.convert.formats.FusionCodec.Documents.Dimensions.DimensionFields import (
    DimensionFields,
    DimensionRows,
)
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectValues import ReadPoint


def CheckConstr(Model: DocumentModel) -> None:
    Records = DimensionRows(Model, "SketchGeomConstraint")
    Sketch = DimensionFields(DimensionRows(Model, "MSketch")[0])
    assert len(Records) == 4
    assert tuple(DimensionFields(Record)["constraintType"] for Record in Records) == (
        64,
        128,
        64,
        128,
    )
    assert Sketch["constraints"] == ValueSeries(
        tuple(LocalRef(Record.ObjectId) for Record in Records)
    )
    for Record in Records:
        Fields = DimensionFields(Record)
        Geometries = Fields["geometries"]
        assert isinstance(Geometries, ValueSeries)
        assert len(Geometries.Items) == 1
        assert Record.Frame.Subjects is not None
        assert Record.Frame.Subjects[0].Target == Geometries.Items[0]
        assert Record.Frame.Subjects[0].ObserverIndex == 0
    Corners = tuple(
        DimensionFields(Record)
        for Record in DimensionRows(Model, "Point3D")
        if DimensionFields(Record)["isOrigin"] is False
    )
    assert len(Corners) == 4
    assert sum(Fields["isFixed"] is True for Fields in Corners) == 1
    assert ReadPoint(
        next(Fields["point"] for Fields in Corners if Fields["isFixed"] is True)
    ) == (0.0, 0.0, 0.0)
    assert all(Fields["isFullyConstrained"] is False for Fields in Corners)
