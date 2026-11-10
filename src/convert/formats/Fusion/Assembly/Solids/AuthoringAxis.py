# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
        Edits[StepData.id]
        for StepData in Steps.values()
        if StepData.id in Edits and StepData.order < StepValue.order
    }
    for Instance in Assembly.instances:
        Origin = Instance.provenance
        if Origin is not None and (NativeId := int(Origin.native_id)) in Earlier:
            ByComponent.setdefault(Instance.definition_id, []).append(
                (NativeId, Instance)
            )
    RootId = Assembly.root_definition_id
    AxisValue = (Direction.x, Direction.y, Direction.z)
    PathValue: list[int] = []
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
        AxisX, AxisY, AxisZ = (
            sum(
                Values[RowValue * 4 + Column] * AxisValue[Column] for Column in range(3)
            )
            for RowValue in range(3)
        )
        AxisValue = AxisX, AxisY, AxisZ
        PathValue.append(NativeId)
        Scope = Parent
    if not PathValue or Scope.SnapshotId is not None:
        raise ValueError("Fusion Extrude authoring path does not end at the root scope")
    return SpaceVector(*AxisValue), tuple(reversed(PathValue))
