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


# one anchor pass associates independent native body results with their exact creators
def IndexBodyLinks(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureIds: frozenset[int]
) -> dict[int, tuple[int, int]]:
    Matches: dict[int, tuple[int, int]] = {}
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
        if SourceId in FeatureIds:
            if SourceId in Matches:
                raise ValueError("Ambiguous Fusion result body anchor")
            BodyId, _ = ReadBodyAnchor(BulkData, Owners, SpanValue.ObjectId)
            Matches[SourceId] = (BodyId, SpanValue.ObjectId)
    if Matches.keys() != FeatureIds:
        raise ValueError("Missing Fusion result body anchor")
    return Matches
