# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.AssemblyHistory import KContainerGuid, HistoryLink
from convert.formats.Fusion.Assembly.ComponentRead import KComponentGuid
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan


# a selected history must prove its own component without borrowing a sibling inventory
def FindBodyScope(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], History: HistoryPart
) -> int | None:
    Components = tuple(
        Span for Span in Spans if Span.IsPrimary and Span.ClassGuid == KComponentGuid
    )
    if not Components:
        return None
    Owner = next(
        (Span for Span in Spans if Span.IsPrimary and Span.ObjectId == History.OwnerId),
        None,
    )
    if (
        Owner is None
        or Owner.ClassGuid != KContainerGuid
        or HistoryLink(BulkData, Owner, 55) != History.HistoryId
    ):
        raise ValueError("Fusion body inventory history owner is unresolved")
    Matches = tuple(
        Span.ObjectId
        for Span in Components
        if HistoryLink(BulkData, Span, 52) == History.OwnerId
    )
    if len(Matches) != 1:
        raise ValueError(
            "Fusion body inventory history component is ambiguous or missing"
        )
    return Matches[0]
