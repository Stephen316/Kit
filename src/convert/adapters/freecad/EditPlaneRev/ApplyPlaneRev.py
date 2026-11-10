# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
    PlanValue: PlaneRevPlan,
    Profile: Sketch,
    AngleEdits: Mapping[str, tuple[float, str]],
) -> CadDocument:
    Feature = DocValue.feature_timeline[-1]
    Definition = Feature.definition
    if not isinstance(Definition, PlaneRevolve) or set(AngleEdits) != {
        Target.AngleParamId for Target in PlanValue.Targets
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
        for Target in PlanValue.Targets
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
        PlanValue.SketchFrame,
        ProfileLines(Feature, Profile),
        PlanValue.AxisOrigin,
        PlanValue.AxisDirection,
        tuple(PlaneFrames[Target.PlaneId] for Target in PlanValue.Targets),
    )
    if Direction != PlanValue.AxisDirection:
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
    return RebuildRevDoc(Edited, Profile, PlanValue.SketchFrame, (Start, EndValue))
