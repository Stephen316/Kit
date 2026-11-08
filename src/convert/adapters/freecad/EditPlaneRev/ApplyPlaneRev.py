# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from dataclasses import replace as Replace

from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import PlaneRevPlan
from convert.adapters.freecad.EditRev.ApplyRevEdit import SetRevAngle
from convert.adapters.freecad.EditRev.RebuildRevDoc import RebuildRevDoc
from convert.adapters.freecad.EditRing.RingChange import CheckRingEdit
from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import RotatePlane
from convert.formats.Fusion.Revolves.PlaneRevInputs import ProfileLines
from convert.formats.Fusion.Revolves.PlaneSweep import DerivePlaneSpan
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.geometry.models.Sketch import Sketch


# the saved scalars rebuild authored planes before the selected sweep is reevaluated
def ApplyPlaneRev(
    DocValue: CadDocument,
    Plan: PlaneRevPlan,
    Profile: Sketch,
    AngleEdits: Mapping[str, tuple[float, str]],
) -> CadDocument:
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    if not isinstance(Definition, PlaneRevolve) or AngleEdits.keys() != {
        Target.AngleParamId for Target in Plan.Targets
    }:
        raise ValueError("FreeCAD editable plane Revolve source controls disagree")
    Parameters = tuple(
        SetRevAngle(Value, *AngleEdits[Value.id]) if Value.id in AngleEdits else Value
        for Value in DocValue.parameters
    )
    (Original,) = DocValue.sketches
    if Profile == Original and Parameters == DocValue.parameters:
        return DocValue
    if Profile != Original:
        CheckRingEdit(Original, Profile)
    ChangedFrames = {
        Target.PlaneId: RotatePlane(
            Target.ZeroFrame, AngleEdits[Target.AngleParamId][0]
        )
        for Target in Plan.Targets
        if AngleEdits[Target.AngleParamId][0] != Target.AngleRadians
    }
    Planes = tuple(
        (
            Replace(Value, transform=ChangedFrames[Value.id])
            if Value.id in ChangedFrames
            else Value
        )
        for Value in DocValue.support_planes
    )
    PlaneFrames = {Value.id: Value.transform for Value in Planes}
    Direction, Start, EndValue = DerivePlaneSpan(
        Plan.SketchFrame,
        ProfileLines(Feature, Profile),
        Plan.AxisOrigin,
        Plan.AxisDirection,
        tuple(PlaneFrames[Target.PlaneId] for Target in Plan.Targets),
    )
    if Direction != Plan.AxisDirection:
        raise ValueError("FreeCAD editable plane Revolve axis changed with its profile")
    Updated = Replace(
        Feature, definition=Replace(Definition, StartRadians=Start, EndRadians=EndValue)
    )
    Edited = Replace(
        DocValue,
        parameters=Parameters,
        support_planes=Planes,
        feature_timeline=(*DocValue.feature_timeline[:-1], Updated),
    )
    return RebuildRevDoc(Edited, Profile, Plan.SketchFrame, (Start, EndValue))
