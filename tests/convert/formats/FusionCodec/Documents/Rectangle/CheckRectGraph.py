from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectFields import RectFields
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectValues import (
    ReadFields,
    ReadPoint,
)


def CheckRectGraph(Model: DocumentModel) -> None:
    Lines = RectFields(Model, "Line3D")
    assert len(Lines) == 4
    assert len(RectFields(Model, "Point3D")) == 5
    Starts = tuple(LineValue["rStartPoint"] for LineValue in Lines)
    Finishes = tuple(LineValue["rEndPoint"] for LineValue in Lines)
    assert all(isinstance(Value, LocalRef) for Value in (*Starts, *Finishes))
    assert len(set(Starts)) == 4
    assert set(Starts) == set(Finishes)
    Curves = tuple(ReadFields(LineValue["lineCurve"]) for LineValue in Lines)
    assert {ReadPoint(Curve["startPoint"]) for Curve in Curves} == {
        (0.0, 0.0, 0.0),
        (1.7, 0.0, 0.0),
        (1.7, 2.3, 0.0),
        (0.0, 2.3, 0.0),
    }
    assert {ReadPoint(Curve["displacement"]) for Curve in Curves} == {
        (1.7, 0.0, 0.0),
        (0.0, 2.3, 0.0),
        (-1.7, 0.0, 0.0),
        (0.0, -2.3, 0.0),
    }
    Sketch = RectFields(Model, "MSketch")[0]
    assert Sketch["constraints"] == ValueSeries(())
    assert Sketch["dimensions"] == ValueSeries(())
