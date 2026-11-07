# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyAnchor import KAnchorGuid, ReadBodyAnchor


# a generated result must match one explicit native creator and body anchor
def FindResultBody(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> tuple[int, int]:
    Matches = []
    for SpanValue in Owners.values():
        if (
            SpanValue.ClassGuid != KAnchorGuid
            or SpanValue.EndOffset - SpanValue.PayloadOffset != 106
        ):
            continue
        Tail = MetaCursor(BulkData[SpanValue.EndOffset - 11 : SpanValue.EndOffset])
        try:
            SourceId = ReadNativeRef(Tail)
        except ValueError:
            continue
        if SourceId == FeatureId:
            BodyId, _ = ReadBodyAnchor(BulkData, Owners, SpanValue.ObjectId)
            Matches.append((BodyId, SpanValue.ObjectId))
    if len(Matches) != 1:
        raise ValueError("Missing or ambiguous Fusion result body anchor")
    return Matches[0]
