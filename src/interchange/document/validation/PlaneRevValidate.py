# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection


# plane revolution bounds must retain links to the actual support plane records
def GetPlaneRevErrs(
    StepValue: FeatureStep,
    Definition: PlaneRevolve,
    Selections: TypeMap[str, Selection],
    PlaneIds: set[str],
) -> tuple[str, ...]:
    Errors: list[str] = []
    if StepValue.kind != FeatureKind.KRevolution:
        Errors.append(f"feature {StepValue.id} is not a revolution")
    Links = (Definition.AxisSelectionId, *Definition.PlaneSelectionIds)
    for LinkId in Links:
        if LinkId not in StepValue.selection_ids:
            Errors.append(
                f"plane revolution {StepValue.id} has an unlinked selection {LinkId}"
            )
    Axis = Selections.get(Definition.AxisSelectionId)
    if Axis is None or not (Axis.path or Axis.query):
        Errors.append(
            f"plane revolution {StepValue.id} has an unresolved axis selection"
        )
    TargetIds: set[str] = set()
    for PlaneLink in Definition.PlaneSelectionIds:
        Selected = Selections.get(PlaneLink)
        if (
            Selected is None
            or not Selected.path
            or Selected.path[-1].entity_kind != "support_plane"
            or Selected.path[-1].entity_id not in PlaneIds
        ):
            Errors.append(
                f"plane revolution {StepValue.id} has an unresolved plane selection {PlaneLink}"
            )
            continue
        TargetId = Selected.path[-1].entity_id
        if TargetId in TargetIds:
            Errors.append(f"plane revolution {StepValue.id} repeats a support plane")
        TargetIds.add(TargetId)
    return tuple(Errors)
