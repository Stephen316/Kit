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


# a single independent sketch and solid delimit the verified native revolution graph
def ReadRevScope(
    DocValue: CadDocument, FeatureValue: FeatureStep
) -> tuple[Sketch, SupportPlane, DesignBody]:
    if (
        DocValue.source.format_id != "fusion.f3d"
        or DocValue.units != UnitSystem.KMillimeter
        or DocValue.assembly is not None
        or DocValue.brep is None
        or DocValue.meshes
        or len(DocValue.bodies) != 1
        or len(DocValue.feature_timeline) != 2
        or len(DocValue.sketches) != 1
        or len(DocValue.support_planes) != 1
        or len(DocValue.selections) != 1
        or len(DocValue.configurations) != 1
        or any(Value.role != PayloadRole.KDocument for Value in DocValue.brep_payloads)
    ):
        raise ValueError(
            "FreeCAD editable Revolve requires one independent native solid"
        )
    Config = DocValue.configurations[0]
    SketchStep, Final = DocValue.feature_timeline
    BodyValue = DocValue.bodies[0]
    Origin = SketchStep.provenance
    if (
        not Config.active
        or Config.parent_id
        or Config.overrides
        or Config.suppressed_feature_ids
        or Final != FeatureValue
        or BodyValue.final_feature_id != Final.id
        or SketchStep.order >= Final.order
        or Final.input_feature_ids != (SketchStep.id,)
        or Final.sketch_id != SketchStep.sketch_id
        or Final.kind != FeatureKind.KRevolution
        or Final.operation != BooleanOp.KCreate
        or Final.suppressed
        or Final.configuration_states
        or Final.attributes.get("fusion.state_known") is not True
        or Final.attributes.get("fusion.rolled_back") is not False
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or not Origin.spans
        or Origin.spans[0].record_kind != KSketchFeature
    ):
        raise ValueError("FreeCAD editable Revolve source history is unavailable")
    SketchValue, PlaneValue = DocValue.sketches[0], DocValue.support_planes[0]
    Source = ReadSketchInput(
        SketchStep, {SketchValue.id: SketchValue}, {PlaneValue.id: PlaneValue}
    )
    if Source is None:
        raise ValueError("FreeCAD editable Revolve profile sketch frame is unavailable")
    return SketchValue, PlaneValue, BodyValue
