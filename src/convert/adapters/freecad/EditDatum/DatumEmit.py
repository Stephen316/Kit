from collections.abc import Mapping as TypeMap
from typing import cast as CastValue

from convert.adapters.freecad.Archive import (
    AddPlaneMut,
    BoolProp,
    DocContext,
    DocFeatures,
    DocGeometry,
    ExpressionProp,
    FeatureOrder,
    IntegerProp,
    JsonProp,
    Quaternion,
    ReplaceNameMut,
    StringProp,
    TextAction,
)
from convert.adapters.freecad.EditDatum.DatumBinding import KDatumBinding, KDatumGroup
from convert.adapters.freecad.EditDatum.DatumExpr import DatumPoseExpr
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.serialization.EncodeData import ToData


# each visible timeline object is the exact support datum with its live native placement
def AddDatumsMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Datums: TypeMap[str, BoundDatum],
) -> None:
    for ItemValue in Features.FeatureItems:
        StepId = TextAction(ItemValue.get("id"))
        Definition = Datums[StepId]
        Alias = Context.Parameters.Aliases[Definition.ScalarParameterId]
        ParamRef = f"{Context.ParamSheet.name}.{Alias}"
        ZeroFrame = CastValue(TypeMap[str, object], ToData(Definition.ReferenceFrame))
        PoseExpr = DatumPoseExpr(Definition, Quaternion(ZeroFrame), ParamRef)
        PlaneObject = AddPlaneMut(
            Context,
            Geometry,
            Geometry.PlaneById[Definition.SupportPlaneId],
            Grouped=False,
        )
        ReplaceNameMut(
            PlaneObject.properties, "Visibility", BoolProp("Visibility", True)
        )
        ReplaceNameMut(
            PlaneObject.properties,
            "ExpressionEngine",
            ExpressionProp([("Placement", PoseExpr)]),
        )
        PlaneObject.properties.extend(
            [
                StringProp("KitFeatureId", StepId, Dynamic=True),
                JsonProp("SourceFeatureJSON", ItemValue),
                IntegerProp("TimelineOrder", FeatureOrder(ItemValue), Dynamic=True),
            ]
        )
        PlaneObject.dependencies.append(Context.ParamSheet.name)
        Features.FeatureNames[StepId] = PlaneObject.name
        Features.FeatureObjects.append(PlaneObject.name)
    Context.MetaObject.properties.append(
        StringProp(KDatumBinding, KDatumGroup, Dynamic=True)
    )
