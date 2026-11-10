# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import PlaneRevPlan
from convert.adapters.freecad.EditPlaneRev.PlaneRevScope import ReadPlaneScope
from convert.adapters.freecad.EditRead.PlaneRev.PlaneCells import ReadPlaneCells
from convert.adapters.freecad.EditRead.PlaneRev.PlaneControls import (
    CheckPlaneSweep,
    ReadTargetPoses,
)
from convert.adapters.freecad.EditRead.PlaneRev.PlaneGraph import ReadPlaneGraph
from convert.adapters.freecad.EditRead.Sketch.RingProof import ReadRingProfile
from convert.adapters.freecad.Native import ParseObjects
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.geometry.models.Sketch import Sketch


# saved graph and geometry fields carry only the proven editable neutral values
@MakeDataClass(frozen=True, slots=True)
class PlaneRevFields:
    ProfileSketch: Sketch
    AngleEdits: dict[str, tuple[float, str]]
    ShapeEntry: str
    SketchEntry: str
    EmptyEntries: tuple[str, ...]


# scope and independent controls must agree before the caller can trust native edits
def ReadPlaneFields(
    RootValue: Element, DocValue: CadDocument, PlanValue: PlaneRevPlan
) -> PlaneRevFields:
    if not DocValue.feature_timeline:
        raise ValueError("FreeCAD editable plane Revolve source timeline is missing")
    StepValue = DocValue.feature_timeline[-1]
    Definition = StepValue.definition
    if not isinstance(Definition, PlaneRevolve):
        raise ValueError("FreeCAD editable plane Revolve source definition changed")
    SketchValue, SketchPlane, _ = ReadPlaneScope(
        DocValue, StepValue, len(PlanValue.Targets)
    )
    if (
        SketchValue.id != PlanValue.SketchId
        or SketchPlane.transform != PlanValue.SketchFrame
        or Definition.AxisOrigin != PlanValue.AxisOrigin
        or Definition.AxisDirection != PlanValue.AxisDirection
        or (Definition.StartRadians, Definition.EndRadians)
        != (PlanValue.StartRadians, PlanValue.EndRadians)
    ):
        raise ValueError("FreeCAD editable plane Revolve source plan changed")
    Graph = ReadPlaneGraph(
        ParseObjects(RootValue), DocValue, PlanValue, Definition, SketchPlane
    )
    Profile = ReadRingProfile(Graph.Profile, SketchValue, AllowProfile=True)
    Aliases, AngleEdits = ReadPlaneCells(Graph.Sheet, DocValue.parameters, PlanValue)
    if not Graph.SketchEntry and (
        Profile is not SketchValue
        or any(
            AngleEdits[Target.AngleParamId][0] != Target.AngleRadians
            for Target in PlanValue.Targets
        )
    ):
        raise ValueError(
            "FreeCAD editable plane Revolve edit is missing its saved profile cache"
        )
    Frames = ReadTargetPoses(Graph, PlanValue, Aliases, AngleEdits)
    CheckPlaneSweep(Graph, PlanValue, StepValue, Profile, Frames)
    return PlaneRevFields(
        Profile, AngleEdits, Graph.ShapeEntry, Graph.SketchEntry, Graph.EmptyEntries
    )


# stable feature specific entry point keeps orchestration separate from angular revolutions
ReadPlaneRevFields = ReadPlaneFields
