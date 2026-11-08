# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import (
    CreatorScope,
    ReadOwnerScope,
)
from convert.formats.Fusion.Assembly.Solids.SnapshotScope import ReadSnapParent
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.models.DocumentModel import AssemblyData
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.VectorSpace import SpaceVector


# a typed snapshot and a unique preceding path qualify each stored direction rotation
def ResolveAuthAxis(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Assembly: AssemblyData,
    Scope: CreatorScope,
    StepValue: FeatureStep,
    Steps: dict[int, FeatureStep],
    Edits: dict[str, int],
    Direction: SpaceVector,
) -> tuple[SpaceVector, tuple[int, ...]]:
    ByComponent: dict[str, list[tuple[int, ComponentInst]]] = {}
    Earlier = {
        Edits[Step.id]
        for Step in Steps.values()
        if Step.id in Edits and Step.order < StepValue.order
    }
    for Instance in Assembly.instances:
        Origin = Instance.provenance
        if Origin is not None and (NativeId := int(Origin.native_id)) in Earlier:
            ByComponent.setdefault(Instance.definition_id, []).append(
                (NativeId, Instance)
            )
    RootId = Assembly.root_definition_id
    Axis = (Direction.x, Direction.y, Direction.z)
    Path = []
    while (DefinitionId := f"fusion-component-{Scope.ComponentId}") != RootId:
        Creation = None if Scope.SnapshotId is None else Steps.get(Scope.SnapshotId)
        Candidates = ByComponent.get(DefinitionId, ())
        if Creation is None or len(Candidates) != 1:
            raise ValueError(
                "Fusion Extrude has no unique preceding authoring occurrence"
            )
        NativeId, Instance = Candidates[0]
        if NativeId != Edits.get(Creation.id):
            raise ValueError(
                "Fusion Extrude authoring occurrence differs from its creation"
            )
        Parent = ReadOwnerScope(
            BulkData, Owners, ReadSnapParent(BulkData, Owners, Scope)
        )
        if Instance.owner_definition_id != f"fusion-component-{Parent.ComponentId}":
            raise ValueError(
                "Fusion Extrude authoring scope parent disagrees with its occurrence"
            )
        Values = Instance.transform.values
        Axis = tuple(
            sum(Values[Row * 4 + Column] * Axis[Column] for Column in range(3))
            for Row in range(3)
        )
        Path.append(NativeId)
        Scope = Parent
    if not Path or Scope.SnapshotId is not None:
        raise ValueError("Fusion Extrude authoring path does not end at the root scope")
    return SpaceVector(*Axis), tuple(reversed(Path))
