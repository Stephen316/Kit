# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditExtScope import ReadSketchInput
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.payloads.PayloadRoles import PayloadRole


# standalone qualification excludes every history input outside the exact sketch and targets
def ReadPlaneScope(
    DocValue: CadDocument, FeatureValue: FeatureStep, TargetCount: int
) -> tuple[Sketch, SupportPlane, DesignBody]:
    if (
        DocValue.source.format_id != "fusion.f3d"
        or DocValue.units != UnitSystem.KMillimeter
        or DocValue.assembly is not None
        or DocValue.brep is None
        or DocValue.meshes
        or len(DocValue.bodies) != 1
        or len(DocValue.feature_timeline) != TargetCount + 2
        or len(DocValue.sketches) != 1
        or len(DocValue.support_planes) != TargetCount + 1
        or len(DocValue.selections) != TargetCount + 1
        or len(DocValue.configurations) != 1
        or any(Value.role != PayloadRole.KDocument for Value in DocValue.brep_payloads)
    ):
        raise ValueError(
            "FreeCAD editable plane Revolve requires one independent solid"
        )
    (Config,) = DocValue.configurations
    (BodyValue,) = DocValue.bodies
    (SketchValue,) = DocValue.sketches
    SketchStep, *Prior, Final = DocValue.feature_timeline
    Planes = {Value.id: Value for Value in DocValue.support_planes}
    Origin = SketchStep.provenance
    if (
        not Config.active
        or Config.parent_id
        or Config.overrides
        or Config.suppressed_feature_ids
        or Final != FeatureValue
        or Final.kind != FeatureKind.KRevolution
        or Final.operation != BooleanOp.KCreate
        or Final.suppressed
        or Final.configuration_states
        or Final.attributes.get("fusion.state_known") is not True
        or Final.attributes.get("fusion.rolled_back") is not False
        or BodyValue.final_feature_id != Final.id
        or Final.sketch_id != SketchStep.sketch_id
        or Final.input_feature_ids
        != (SketchStep.id, *(StepValue.id for StepValue in Prior))
        or any(
            First.order >= Second.order
            for First, Second in zip(
                DocValue.feature_timeline, DocValue.feature_timeline[1:]
            )
        )
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or not Origin.spans
        or Origin.spans[0].record_kind != KSketchFeature
    ):
        raise ValueError("FreeCAD editable plane Revolve source history is unresolved")
    Source = ReadSketchInput(SketchStep, {SketchValue.id: SketchValue}, Planes)
    if Source is None:
        raise ValueError("FreeCAD editable plane Revolve sketch frame is unresolved")
    return SketchValue, Source.PlaneValue, BodyValue
