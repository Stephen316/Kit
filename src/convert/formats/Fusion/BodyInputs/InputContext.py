# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
    ById = {
        int(StepValue.provenance.native_id): StepValue
        for StepValue in Steps
        if StepValue.provenance is not None
    }
    Scopes = ReadAsmScopes(BulkData, Owners, History.OwnerId, frozenset(ById))
    return InputContext(Owners, ById, Scopes, ComponentId, History.HistoryId)
