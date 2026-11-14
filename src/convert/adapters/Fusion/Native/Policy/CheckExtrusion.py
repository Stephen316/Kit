from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext


def CheckExtrusion(Graph: NativeGraph, Context: ExtrudeContext) -> None:
    Feature = Context.Extrude
    RequireFields(
        Feature,
        {
            "booleanOperation": 4,
            "directionType": 1,
            "extendFaceOption": 2,
            "isSolidOperation": True,
            "profileLocaltionType": 0,
            "side1ExtentType": 1,
            "side1SolutionType": 0,
            "side2ExtentType": 0,
            "side2SolutionType": 0,
            "side2ExtendFaceOption": 0,
            "symmetricMeasurementType": 0,
        },
    )
    RequireFields(
        Feature,
        {
            NameValue: False
            for NameValue in (
                "isFlipDirection",
                "side2FlipDirection",
                "startDirectionFlip",
                "thinExtrude",
                "bIsAGDExtrudeFeature",
            )
        },
    )
    RequireFields(
        Feature,
        {
            NameValue: None
            for NameValue in (
                "ProfileFromEntityRef",
                "profileOffset",
                "rAgainstDistance",
                "rFromEntityRef",
                "rToEntityRef",
                "side1Offset",
                "side2Offset",
                "side2TaperAngle",
                "thinExtrudeSide1WallThickness",
                "thinExtrudeSide2WallThickness",
            )
        },
    )
    EmptyFields(Feature, ("cachedDcBodies", "removedBodies", "targetDataRefs"))
    SameNumbers(PointCoords(Feature.Fields["profileNormal"]), (0.0, 0.0, 1.0))
    ToolBody = ResolveField(Graph, Feature, "rExtrudeToolBody", "DcExtrudeToolBody")
    if Graph.Resolve(ToolBody.Fields["rExtrudeFeature"]) != Feature:
        raise ValueError("Native extrusion tool references another feature")
