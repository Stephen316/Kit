# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureStep import FeatureStep
from interchange.payloads.PayloadRoles import PayloadRole


# only a self contained saved feature graph can replace a static representation with live geometry
def IsEditExtScope(DocValue: CadDocument, FeatureValue: FeatureStep) -> bool:
    if (
        DocValue.source.format_id != "fusion.f3d"
        or DocValue.units != UnitSystem.KMillimeter
        or DocValue.assembly is not None
        or DocValue.brep is None
        or DocValue.meshes
        or DocValue.selections
        or len(DocValue.bodies) != 1
        or len(DocValue.feature_timeline) != 2
        or len(DocValue.sketches) != 1
        or len(DocValue.support_planes) != 1
        or len(DocValue.configurations) != 1
        or any(Value.role != PayloadRole.KDocument for Value in DocValue.brep_payloads)
    ):
        return False
    SketchStep, LastStep = DocValue.feature_timeline
    Config = DocValue.configurations[0]
    return (
        LastStep == FeatureValue
        and DocValue.bodies[0].final_feature_id == FeatureValue.id
        and FeatureValue.input_feature_ids == (SketchStep.id,)
        and SketchStep.sketch_id == FeatureValue.sketch_id
        and SketchStep.order < FeatureValue.order
        and SketchStep.kind == FeatureKind.KNative
        and SketchStep.definition is None
        and not (SketchStep.input_feature_ids or SketchStep.parameter_ids)
        and all(
            not (Value.suppressed or Value.configuration_states or Value.selection_ids)
            and Value.attributes.get("fusion.state_known") is True
            and Value.attributes.get("fusion.rolled_back") is False
            for Value in (SketchStep, FeatureValue)
        )
        and Config.active
        and not (Config.parent_id or Config.overrides or Config.suppressed_feature_ids)
    )
