# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
    AxisValue = Selections.get(Definition.AxisSelectionId)
    if AxisValue is None or not (AxisValue.path or AxisValue.query):
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
