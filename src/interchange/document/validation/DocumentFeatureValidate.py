# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.document.models.DocumentModel import (  # lgtm[py/cyclic-import]
    CadDocument,
)
from interchange.document.validation.AngleRevValidate import GetAngleRevErrs
from interchange.document.validation.PlaneRevValidate import GetPlaneRevErrs
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeaturePlaneRev import PlaneRevolve


# timeline checks protect ordering and every feature dependency from invalid references
def GetFeatureErrs(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    FeatureOrders = {
        FeatureValue.id: FeatureValue.order
        for FeatureValue in DocumentValue.feature_timeline
    }
    if len(FeatureOrders) != len(DocumentValue.feature_timeline):
        ErrorValues.append("feature ids are not unique")
    if len(
        {FeatureValue.order for FeatureValue in DocumentValue.feature_timeline}
    ) != len(DocumentValue.feature_timeline):
        ErrorValues.append("feature order values are not unique")
    Selections = {Value.id: Value for Value in DocumentValue.selections}
    Parameters = {Value.id: Value for Value in DocumentValue.parameters}
    for FeatureValue in DocumentValue.feature_timeline:
        if (
            FeatureValue.sketch_id
            and FeatureValue.sketch_id not in IdentitySets["sketches"]
        ):
            ErrorValues.append(f"feature {FeatureValue.id} references missing sketch")
        for InputId in FeatureValue.input_feature_ids:
            if InputId not in FeatureOrders:
                ErrorValues.append(
                    f"feature {FeatureValue.id} references missing input {InputId}"
                )
            elif FeatureOrders[InputId] >= FeatureValue.order:
                ErrorValues.append(
                    f"feature {FeatureValue.id} has a forward dependency"
                )
        for ParameterId in FeatureValue.parameter_ids:
            if ParameterId not in IdentitySets["parameters"]:
                ErrorValues.append(
                    f"feature {FeatureValue.id} references missing parameter"
                )
        for SelectionId in FeatureValue.selection_ids:
            if SelectionId not in IdentitySets["selections"]:
                ErrorValues.append(
                    f"feature {FeatureValue.id} references missing selection"
                )
        if isinstance(FeatureValue.definition, PlaneRevolve):
            ErrorValues.extend(
                GetPlaneRevErrs(
                    FeatureValue,
                    FeatureValue.definition,
                    Selections,
                    IdentitySets["support_planes"],
                )
            )
        elif isinstance(FeatureValue.definition, AngularRevolve):
            ErrorValues.extend(
                GetAngleRevErrs(
                    FeatureValue, FeatureValue.definition, Selections, Parameters
                )
            )
    for BodyValue in DocumentValue.bodies:
        if BodyValue.final_feature_id not in IdentitySets["feature_timeline"]:
            ErrorValues.append(f"body {BodyValue.id} references missing final feature")
    return tuple(ErrorValues)
