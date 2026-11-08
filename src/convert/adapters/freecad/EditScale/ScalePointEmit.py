# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping

from convert.adapters.freecad.Archive import (
    BoolProp,
    DocContext,
    DocFeatures,
    DocGeometry,
    ExpressionProp,
    FeatureMeta,
    GeomProp,
    MakePlacement,
    Object,
    StringProp,
    TextAction,
)
from convert.adapters.freecad.EditScale.ScalePointPlan import ScalePointPlan
from convert.adapters.freecad.Protocol import KSketchTypeId


# the native geometry index must address the same point before the scale graph is emitted
def FindScalePoint(
    Context: DocContext, Geometry: DocGeometry, Plan: ScalePointPlan
) -> tuple[Object, int] | None:
    SketchName = Geometry.SketchNames.get(Plan.SketchId)
    SketchData = next(
        (Value for Value in Geometry.SketchItems if Value.get("id") == Plan.SketchId),
        None,
    )
    SketchObj = next(
        (
            Value
            for Value in Context.Graph.Objects
            if Value.name == SketchName and Value.type_id == KSketchTypeId
        ),
        None,
    )
    if SketchObj is None or SketchData is None:
        return None
    GeometryProp, Indices, Issues = GeomProp(SketchData)
    PointIndex = Indices.get(Plan.PointId)
    NativeProp = next(
        (Value for Value in SketchObj.properties if Value.get("name") == "Geometry"),
        None,
    )
    if (
        PointIndex is None
        or Issues
        or GeometryProp[0][PointIndex].get("type") != "Part::GeomPoint"
        or NativeProp is None
        or len(NativeProp) != 1
        or PointIndex >= len(NativeProp[0])
        or NativeProp[0][PointIndex].get("type") != "Part::GeomPoint"
    ):
        return None
    SourcePoint = GeometryProp[0][PointIndex].find("GeomPoint")
    EmittedPoint = NativeProp[0][PointIndex].find("GeomPoint")
    if (
        SourcePoint is None
        or EmittedPoint is None
        or SourcePoint.attrib != EmittedPoint.attrib
    ):
        return None
    return SketchObj, PointIndex


# a linked datum exposes the selected point without changing any solid or sketch ownership
def AddScalePointMut(
    Context: DocContext,
    Features: DocFeatures,
    Plan: ScalePointPlan,
    SketchObj: Object,
    GeometryIndex: int,
    FeatureItem: Mapping[str, object] | None,
) -> Object:
    if bool(Plan.FeatureId) != (FeatureItem is not None) or (
        FeatureItem is not None and FeatureItem.get("id") != Plan.FeatureId
    ):
        raise ValueError("FreeCAD editable Scale datum feature identity disagrees")
    Label = "Scale center"
    if FeatureItem is not None:
        Label = TextAction(FeatureItem.get("name")) or Label
    PointObj = Context.Graph.add("App::Point", Label, "ScaleCenter", Touched=True)
    SketchName = SketchObj.name
    PathValue = f"{SketchName}.Geometry[{GeometryIndex}]"
    Expression = (
        f"placement({SketchName}.Placement * vector({PathValue}.X; {PathValue}.Y; 0); "
        "rotation(vector(0; 0; 1); 0 deg))"
    )
    Point = Plan.Point
    PointObj.properties.extend(
        [
            StringProp("Label", Label),
            MakePlacement("Placement", {"origin": (Point.x, Point.y, Point.z)}),
            ExpressionProp([("Placement", Expression)]),
            BoolProp("Visibility", False),
        ]
    )
    PointObj.dependencies.append(SketchName)
    if FeatureItem is not None:
        PointObj.properties.extend(FeatureMeta(FeatureItem, "feature"))
        Features.FeatureNames[Plan.FeatureId] = PointObj.name
        Features.FeatureObjects.append(PointObj.name)
    return PointObj
