# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.adapters.freecad.EditAxisRev.AxisEndpoints import ReadAxisLine
from convert.adapters.freecad.EditAxisRev.AxisRevPlan import AxisRevPlan
from convert.adapters.freecad.EditRead.Sketch.SavedEntity import (
    IsSameCoord,
    ReadSavedEntity,
)
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import ReadRuleRows
from convert.adapters.freecad.EditRead.Sketch.SavedSketchGeom import ReadSketchGeom
from convert.adapters.freecad.EditRead.Sketch.SavedSketchRules import CheckStaticRow
from convert.adapters.freecad.EditRead.XmlField import EditChild
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity


# verified native constraints retain source point links and the derived profile corner joins
def ReadAxisSketch(
    Native: NativeObject,
    Template: NativeObject,
    Original: Sketch,
    TrailingCount: int = 0,
) -> Sketch:
    for RowValue in ReadRuleRows(Native, Template.properties["Constraints"]):
        CheckStaticRow(RowValue)
    return ReadSketchGeom(Native, Original, TrailingCount)


# the extra edge follows the original directed line and stays outside the neutral timeline
def ReadAxisGuide(
    Native: NativeObject, Original: Sketch, Edited: Sketch, PlanValue: AxisRevPlan
) -> SketchEntity:
    Source = next(
        Value for Value in Original.entities if Value.id == PlanValue.AxisLineId
    )
    LineValue, _ = ReadAxisLine(Original, Source.id)
    Reverse = PlanValue.AxisSense < 0
    OriginalGuide = Replace(
        Source,
        id="kit-axis-guide",
        construction=False,
        geometry=LineGeometry(LineValue.end, LineValue.start) if Reverse else LineValue,
    )
    GeometryRows = EditChild(
        Native, "Geometry", "Part::PropertyGeometryList", "GeometryList"
    )
    Guide = ReadSavedEntity(
        GeometryRows[-1], OriginalGuide, str(len(GeometryRows)), False
    )
    EditedLine = next(
        Value.geometry for Value in Edited.entities if Value.id == Source.id
    )
    GuideGeom = Guide.geometry
    if not isinstance(GuideGeom, LineGeometry) or not isinstance(
        EditedLine, LineGeometry
    ):
        raise ValueError("FreeCAD editable sketch axis guide is not a line")
    Start, EndValue = (
        (EditedLine.end, EditedLine.start)
        if Reverse
        else (EditedLine.start, EditedLine.end)
    )
    if not IsSameCoord(Start, GuideGeom.start) or not IsSameCoord(
        EndValue, GuideGeom.end
    ):
        raise ValueError(
            "FreeCAD editable sketch axis guide disagrees with its construction line"
        )
    return Guide
