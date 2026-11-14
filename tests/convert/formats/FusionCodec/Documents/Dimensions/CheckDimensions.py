from pytest import approx as ApproxValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.convert.formats.FusionCodec.Documents.Dimensions.DimensionFields import (
    DimensionFields,
    DimensionRows,
)


def CheckDimensions(Model: DocumentModel) -> None:
    Records = DimensionRows(Model, "FusionSketchLinearDim")
    Parameters = {
        Record.ObjectId: DimensionFields(Record)
        for Record in DimensionRows(Model, "Parameter")
    }
    Bindings = {
        Record.ObjectId: DimensionFields(Record)
        for Record in DimensionRows(Model, "DcDoubleParameter")
    }
    assert len(Records) == 2
    assert len(DimensionRows(Model, "Dimension")) == 2
    assert all(not Record.IsPrimary for Record in DimensionRows(Model, "Dimension"))
    for Record, UserName, TypeValue, Value in zip(
        Records, ("boxWidth", "boxDepth"), (1 << 22, 1 << 23), (1.7, 2.3), strict=True
    ):
        Fields = DimensionFields(Record)
        assert len(Record.Groups) == 2
        assert Fields["constraintType"] == TypeValue
        assert Fields["RefPositions"] == ValueSeries((0.0, 1.0))
        Reference = Fields["dcParameter"]
        assert isinstance(Reference, LocalRef)
        Binding = Bindings[Reference.ObjectId]
        ParameterRef = Binding["parameter"]
        assert isinstance(ParameterRef, LocalRef)
        Parameter = Parameters[ParameterRef.ObjectId]
        assert Parameter["expression"] == UserName
        assert Parameter["dcParameter"] == Reference
        assert Parameter["value"] == ApproxValue(Value)
        assert Binding["value"] == ApproxValue(Value)
        assert Parameter["isUserDefined"] is False
    assert {
        Fields["userName"]
        for Fields in Parameters.values()
        if Fields["isUserDefined"] is True
    } == {"boxHeight", "boxWidth", "boxDepth"}
