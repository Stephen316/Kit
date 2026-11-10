# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace
from math import tau as FullTurn

from convert.adapters.freecad.EditAxisRev.AxisEditSketch import SyncAxisSketch
from convert.adapters.freecad.EditAxisRev.AxisEndpoints import (
    ReadAxisLine,
    WorldAxisLine,
)
from convert.adapters.freecad.EditAxisRev.AxisProfile import ReadAxisProfile
from convert.adapters.freecad.EditAxisRev.AxisRevPlan import AxisRevPlan
from convert.adapters.freecad.EditAxisRev.AxisRevScope import ReadAxisScope
from convert.adapters.freecad.EditRev.ApplyRevEdit import SetRevAngle
from convert.adapters.freecad.EditRev.RebuildRevDoc import RebuildRevDoc
from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.formats.Fusion.Revolves.ProfileMeridian import CalcMeridian
from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.VectorSpace import SpaceVector


# angle and source geometry edits regenerate the same native solid and selected axis identities
def ApplyAxisEdit(
    DocValue: CadDocument,
    PlanValue: AxisRevPlan,
    Profile: Sketch,
    AxisSketch: Sketch,
    Along: tuple[float, str],
) -> CadDocument:
    if not DocValue.feature_timeline:
        raise ValueError(
            "FreeCAD editable sketch axis Revolve source history is unavailable"
        )
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    if (
        not isinstance(Definition, AngularRevolve)
        or Definition.SideMode != "one_sided"
        or Definition.AlongParameterId != PlanValue.Revolve.AngleParamId
    ):
        raise ValueError("FreeCAD editable sketch axis Revolve source controls changed")
    Source, Guide, _ = ReadAxisScope(DocValue, Feature)
    Original, OriginalAxis = Source.SketchValue, Guide.SketchValue
    if (
        Original.id != PlanValue.Revolve.SketchId
        or OriginalAxis.id != PlanValue.AxisSketchId
        or Source.PlaneValue.transform != PlanValue.ProfileFrame
        or Guide.PlaneValue.transform != PlanValue.AxisFrame
    ):
        raise ValueError("FreeCAD editable sketch axis Revolve source frames changed")
    Profile = SyncAxisSketch(
        Original, Profile, Original.closed_profile_entity_ids[0], PlanValue.ProfilePairs
    )
    AxisSketch = SyncAxisSketch(OriginalAxis, AxisSketch, (PlanValue.AxisLineId,))
    Parameters = tuple(
        SetRevAngle(Value, *Along) if Value.id == Definition.AlongParameterId else Value
        for Value in DocValue.parameters
    )
    if (
        Profile is Original
        and AxisSketch is OriginalAxis
        and Parameters == DocValue.parameters
    ):
        return DocValue
    return RebuildAxisEdit(
        Replace(DocValue, parameters=Parameters),
        PlanValue,
        Definition,
        Profile,
        AxisSketch,
    )


# edited geometry is admissible only if it retains the source ring and a valid meridian
def RebuildAxisEdit(
    DocValue: CadDocument,
    PlanValue: AxisRevPlan,
    Definition: AngularRevolve,
    Profile: Sketch,
    AxisSketch: Sketch,
) -> CadDocument:
    Feature = DocValue.feature_timeline[-1]
    Geometry, PointIds = ReadAxisLine(AxisSketch, PlanValue.AxisLineId)
    if (
        PointIds != PlanValue.AxisPointIds
        or ReadAxisProfile(Feature, Profile) != PlanValue.ProfilePairs
    ):
        raise ValueError(
            "FreeCAD editable sketch axis Revolve original incidence changed"
        )
    Origin, _, Direction = WorldAxisLine(Geometry, PlanValue.AxisFrame)
    Lines = ReadRevProfile(Feature, Profile)
    if not isinstance(Lines, tuple):
        raise ValueError("FreeCAD editable sketch axis Revolve requires a line profile")
    Effective, _ = CalcMeridian(PlanValue.ProfileFrame, Lines, Origin, Direction)
    Updated = Replace(
        Definition, AxisOrigin=Origin, AxisDirection=SpaceVector(*Effective)
    )
    Along, Against = ReadRevAngles(Feature, Updated, DocValue.parameters)
    Interval = GetAngleSpan(Along, Against, Updated.SideMode)
    if Interval[1] - Interval[0] > FullTurn:
        raise ValueError("FreeCAD editable sketch axis Revolve exceeds one turn")
    NewFeature = Replace(Feature, definition=Updated)
    Sketches = tuple(
        AxisSketch if Value.id == AxisSketch.id else Profile
        for Value in DocValue.sketches
    )
    Edited = Replace(
        DocValue,
        sketches=Sketches,
        feature_timeline=(*DocValue.feature_timeline[:-1], NewFeature),
    )
    Rebuilt = RebuildRevDoc(Edited, Profile, PlanValue.ProfileFrame, Interval)
    return Replace(Rebuilt, sketches=Sketches)


# stable feature specific entry point keeps mutation distinct from angular origin axis edits
ApplyAxisRevEdit = ApplyAxisEdit
