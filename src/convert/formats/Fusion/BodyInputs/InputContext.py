# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import (
    CreatorScope,
    ReadAsmScopes,
)
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyScope import FindBodyScope
from interchange.features.FeatureStep import FeatureStep


# source and consuming steps must share the same reciprocal component scope
@Dataclass(frozen=True, slots=True)
class InputContext:
    Owners: dict[int, RecordSpan]
    Steps: dict[int, FeatureStep]
    Scopes: dict[int, CreatorScope]
    ComponentId: int
    HistoryId: int


# the selected timeline controls ownership before any feature interprets its operands
def ReadInputScope(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    Steps: tuple[FeatureStep, ...],
) -> InputContext:
    ComponentId = FindBodyScope(BulkData, Spans, History)
    if ComponentId is None:
        raise ValueError("Fusion historical body component is missing")
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    ByIdentity = {
        int(StepValue.provenance.native_id): StepValue
        for StepValue in Steps
        if StepValue.provenance is not None
    }
    Scopes = ReadAsmScopes(BulkData, Owners, History.OwnerId, frozenset(ByIdentity))
    return InputContext(Owners, ByIdentity, Scopes, ComponentId, History.HistoryId)
