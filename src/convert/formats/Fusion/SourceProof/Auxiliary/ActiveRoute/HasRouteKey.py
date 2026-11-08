# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackData

from convert.formats.Fusion.RecordSpan import RecordSpan


# route keys must start at their typed slot and stay inside the primary record
def HasRouteKey(
    BulkData: bytes, OwnerSpan: RecordSpan, Offset: int, RouteKey: str
) -> bool:
    TextValue = PackData("<I", len(RouteKey)) + RouteKey.encode("utf-16le")
    Start = OwnerSpan.PayloadOffset + Offset
    return BulkData.startswith(TextValue, Start, OwnerSpan.EndOffset)
