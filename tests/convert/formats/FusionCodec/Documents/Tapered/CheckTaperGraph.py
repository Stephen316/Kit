from math import radians as Radians, tan as Tangent

from pytest import approx as ApproxValue

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.convert.formats.FusionCodec.Documents.NamedGroups import NamedGroups


def CheckTaperGraph(Model: DocumentModel, Degrees: float) -> None:
    assert len(Model.Bodies) == 1
    History = Model.Bodies[0].History
    if Degrees == 0.0:
        assert isinstance(History, HistoryModel)
        assert History.Model.Radius == ApproxValue(10.0)
    else:
        assert isinstance(History, FrustumHistory)
        assert History.Model.BottomRadius == ApproxValue(10.0)
        assert History.Model.TopRadius == ApproxValue(
            10.0 + 17.0 * Tangent(Radians(Degrees))
        )
    assert History.Model.Height == ApproxValue(17.0)
    Feature = next(
        Fields
        for Fields in NamedGroups(Model, "DcFeature")
        if Fields["featureBaseName"] == "Extrude"
    )
    assert Feature["startModelHS"] == History.History.InitialId
    assert Feature["endModelHS"] == History.History.CurrentId
    assert History.Identity.SecondaryId == 4
    assert History.TagSet.SideFace.OperationIds == (History.Identity.OperationId,)
    Parameters = NamedGroups(Model, "Parameter")
    Along = next(Fields for Fields in Parameters if Fields["name"] == "AlongDistance")
    Taper = next(Fields for Fields in Parameters if Fields["name"] == "TaperAngle")
    assert Along["expression"] == "frustumHeight"
    assert Along["value"] == ApproxValue(1.7)
    assert Taper["value"] == ApproxValue(Radians(Degrees))
    assert Taper["unit"] == "deg"
    assert Taper["userName"] == "d3"
    assert Taper["expression"] == (str(Degrees) if Degrees else "0") + " deg"
    assert len(NamedGroups(Model, "DcExtrudeFeature")) == 1
    assert len(NamedGroups(Model, "MSketch")) == 1
