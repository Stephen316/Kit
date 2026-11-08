# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

from convert.adapters.freecad.ApplyDepthParams import SetEditDepth
from convert.adapters.freecad.EditAxisRev.AxisEditSketch import SyncAxisSketch
from convert.adapters.freecad.EditAxisRev.AxisProfile import ReadAxisProfile
from convert.adapters.freecad.EditBodyRev.BodyAxisEdit import BindEditedAxis
from convert.adapters.freecad.EditBodyRev.BodyRevParams import (
    ReadSeedDepth,
    SplitBodyParams,
)
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan
from convert.adapters.freecad.EditBodyRev.BodyRevScope import (
    CheckBodyScope,
    ReadBodyInputs,
)
from convert.adapters.freecad.EditBodyRev.RebuildBodyRev import RebuildBodyRev
from convert.adapters.freecad.EditRev.ApplyRevEdit import SetRevAngle
from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.adapters.freecad.EditRing.RingChange import SyncRingEdit
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# exact sketch and control ownership survive native edits to both linked solids
def ApplyBodyRev(
    DocValue: CadDocument,
    PlanValue: BodyRevPlan,
    SourceSketch: Sketch,
    ProfileSketch: Sketch,
    SourceFrame: Transform,
    ProfileFrame: Transform,
    Depth: tuple[float, str],
    Along: tuple[float, str],
) -> CadDocument:
    if len(DocValue.feature_timeline) != 4:
        raise ValueError("FreeCAD editable body axis Revolve source history changed")
    SeedStep, Creator, ProfileStep, Feature = DocValue.feature_timeline
    CheckBodyScope(DocValue, Feature)
    Source, Profile = ReadBodyInputs(DocValue)
    SourceDef, Definition = Creator.definition, Feature.definition
    if (
        not isinstance(SourceDef, DistanceExtrude)
        or not isinstance(Definition, AngularRevolve)
        or SourceDef.AlongParameterId != PlanValue.Extrude.ParameterId
        or Definition.AlongParameterId != PlanValue.Revolve.AngleParamId
        or Creator.id != PlanValue.ExtrudeId
        or Feature.id != PlanValue.RevolveId
        or Source.SketchValue.id != PlanValue.Extrude.SketchId
        or Profile.SketchValue.id != PlanValue.Revolve.SketchId
        or Source.PlaneValue.transform != PlanValue.SourceFrame
        or Profile.PlaneValue.transform != PlanValue.ProfileFrame
    ):
        raise ValueError(
            "FreeCAD editable body axis Revolve source controls or frames changed"
        )
    SourceSketch = SyncRingEdit(Source.SketchValue, SourceSketch)
    ProfileSketch = SyncAxisSketch(
        Profile.SketchValue,
        ProfileSketch,
        Profile.SketchValue.closed_profile_entity_ids[0],
        PlanValue.ProfilePairs,
    )
    if ReadAxisProfile(Feature, ProfileSketch) != PlanValue.ProfilePairs:
        raise ValueError("FreeCAD editable body axis Revolve profile incidence changed")
    CheckPrismFrame(SourceFrame)
    CheckPrismFrame(ProfileFrame)
    ParamValues = tuple(
        (
            SetEditDepth(Value, *Depth)
            if Value.id == PlanValue.Extrude.ParameterId
            and Depth[0] != PlanValue.Extrude.DistanceMm
            else (
                SetRevAngle(Value, *Along)
                if Value.id == PlanValue.Revolve.AngleParamId
                else Value
            )
        )
        for Value in DocValue.parameters
    )
    if (
        SourceSketch is Source.SketchValue
        and ProfileSketch is Profile.SketchValue
        and SourceFrame == PlanValue.SourceFrame
        and ProfileFrame == PlanValue.ProfileFrame
        and ParamValues == DocValue.parameters
    ):
        return DocValue
    Binding = BindEditedAxis(
        Source.SketchValue,
        PlanValue.SourceFrame,
        Definition.AxisSelectionId,
        PlanValue.AxisLineId,
        PlanValue.AxisStart,
        PlanValue.AxisEnd,
    )
    UpdatedSource = Replace(SourceDef, Direction=SourceFrame.z_axis)
    Creator = Replace(Creator, definition=UpdatedSource)
    SourceParams, RevParams = SplitBodyParams(ParamValues, Creator, Feature)
    DepthMm = ReadSeedDepth(Creator, UpdatedSource, SourceParams)
    AlongRad, _ = ReadRevAngles(Feature, Definition, RevParams)
    Sketches = {SourceSketch.id: SourceSketch, ProfileSketch.id: ProfileSketch}
    Frames = {Source.PlaneValue.id: SourceFrame, Profile.PlaneValue.id: ProfileFrame}
    Edited = Replace(
        DocValue,
        feature_timeline=(SeedStep, Creator, ProfileStep, Feature),
        parameters=ParamValues,
        sketches=tuple(Sketches[Value.id] for Value in DocValue.sketches),
        support_planes=tuple(
            Replace(Value, transform=Frames[Value.id])
            for Value in DocValue.support_planes
        ),
    )
    return RebuildBodyRev(
        Edited,
        PlanValue,
        Binding,
        SourceSketch,
        ProfileSketch,
        SourceFrame,
        ProfileFrame,
        DepthMm,
        AlongRad,
    )
