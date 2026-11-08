# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.BodyInputs.HistoricalPick import MakeHistoryPick
from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.BodyInputs.InputReaders import KBodyInputReaders
from convert.formats.Fusion.FeatureLabels import ReadLabelData
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection


# a feature exposes body roles atomically once every authored input is qualified
def ReadBodyInputs(
    BulkData: bytes, Context: InputContext, FeatureId: int, Receiver: FeatureStep
) -> tuple[FeatureStep, tuple[Selection, ...]]:
    Scope = Context.Scopes.get(FeatureId)
    if (
        Scope is None
        or Scope.ComponentId != Context.ComponentId
        or Scope.SnapshotId is not None
    ):
        raise ValueError("Fusion body input feature lacks a local history scope")
    SpanValue = Context.Owners[FeatureId]
    LabelText, KindValue, ReadInputs = KBodyInputReaders[SpanValue.ClassGuid]
    Fields = ReadInputs(BulkData, Context.Owners, FeatureId)
    Picks = tuple(
        MakeHistoryPick(BulkData, Context, Receiver, FeatureId, Scope, Input, Ordinal)
        for Ordinal, Input in enumerate(Fields.Picks)
    )
    if not Picks or len({Pick.query["native_body_id"] for Pick in Picks}) != len(Picks):
        raise ValueError("Fusion body input list is empty or repeats a historical body")
    LabelData = ReadLabelData(
        BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset], LabelText
    )
    Attributes = Receiver.attributes
    if Fields.KeepTools is not None:
        Attributes = FreezeMapping(
            {**Attributes, "fusion.combine.keep_tool_bodies": Fields.KeepTools}
        )
    return (
        Replace(
            Receiver,
            name=LabelData[0] if LabelData is not None else Receiver.name,
            kind=KindValue,
            operation=(
                Fields.Operation if Fields.Operation is not None else Receiver.operation
            ),
            selection_ids=Receiver.selection_ids + tuple(Pick.id for Pick in Picks),
            attributes=Attributes,
        ),
        Picks,
    )
