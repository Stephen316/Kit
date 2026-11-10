# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.AssemblyHistory import KContainerGuid, HistoryLink
from convert.formats.Fusion.Assembly.ComponentRead import KComponentGuid
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan


# a selected history must prove its own component without borrowing a sibling inventory
def FindBodyScope(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], History: HistoryPart
) -> int | None:
    Components = tuple(
        SpanValue
        for SpanValue in Spans
        if SpanValue.IsPrimary and SpanValue.ClassGuid == KComponentGuid
    )
    if not Components:
        return None
    Owner = next(
        (
            SpanValue
            for SpanValue in Spans
            if SpanValue.IsPrimary and SpanValue.ObjectId == History.OwnerId
        ),
        None,
    )
    if (
        Owner is None
        or Owner.ClassGuid != KContainerGuid
        or HistoryLink(BulkData, Owner, 55) != History.HistoryId
    ):
        raise ValueError("Fusion body inventory history owner is unresolved")
    Matches = tuple(
        SpanValue.ObjectId
        for SpanValue in Components
        if HistoryLink(BulkData, SpanValue, 52) == History.OwnerId
    )
    if len(Matches) != 1:
        raise ValueError(
            "Fusion body inventory history component is ambiguous or missing"
        )
    return Matches[0]
