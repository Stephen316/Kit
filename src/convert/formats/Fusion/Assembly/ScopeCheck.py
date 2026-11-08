# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.ComponentScope import KScopeRecord
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# isolated geometry cannot carry operands or driving controls owned by another component
def CheckScope(Records: tuple[KScopeRecord, ...], ComponentId: int) -> None:
    Steps = tuple(Value for Value in Records if isinstance(Value, FeatureStep))
    StepIds = {Value.id for Value in Steps}
    NativeIds = {
        Value.provenance.native_id for Value in Steps if Value.provenance is not None
    }
    PlanePicks = {
        Identity
        for StepValue in Steps
        if isinstance(StepValue.definition, PlaneRevolve)
        for Identity in StepValue.definition.PlaneSelectionIds
    }
    ProvenPlanes = {
        Value.path[-1].entity_id
        for Value in Records
        if isinstance(Value, Selection)
        and Value.id in PlanePicks
        and Value.path
        and Value.path[-1].entity_kind == "support_plane"
    }
    PlaneSources = set()
    for PlaneValue in (Value for Value in Records if isinstance(Value, SupportPlane)):
        OwnerId = PlaneValue.attributes.get("fusion.component_object_id")
        PlaneSource = str(PlaneValue.attributes.get("fusion.feature_object_id", ""))
        IsLocalDatum = PlaneValue.id in ProvenPlanes and PlaneSource in NativeIds
        if OwnerId != ComponentId and (OwnerId is not None or not IsLocalDatum):
            raise ValueError(f"Fusion component {ComponentId} has a nonlocal frame")
        if PlaneSource in NativeIds:
            PlaneSources.add(PlaneSource)
    if any(
        Value.sketch_id is None
        and (Value.provenance is None or Value.provenance.native_id not in PlaneSources)
        for Value in Steps
    ):
        raise ValueError(
            f"Fusion component {ComponentId} has a nonlocal feature dependency"
        )
    if any(
        Value.owner_id and Value.owner_id not in StepIds
        for Value in Records
        if isinstance(Value, Parameter)
    ):
        raise ValueError(
            f"Fusion component {ComponentId} has a nonlocal parameter owner"
        )
