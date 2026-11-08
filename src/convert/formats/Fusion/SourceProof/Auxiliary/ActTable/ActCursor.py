# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan


# auxiliary payload readers need bounds and namespace before interpreting fields
def ActCursor(ActData: bytes, SpanValue: RecordSpan) -> MetaCursor:
    if (
        not SpanValue.IsPrimary
        or SpanValue.ClassSpace != "ACT"
        or not 0
        <= SpanValue.StartOffset
        < SpanValue.PayloadOffset
        <= SpanValue.EndOffset
        <= len(ActData)
    ):
        raise ValueError("Invalid Fusion ACT primary record")
    return MetaCursor(ActData[SpanValue.PayloadOffset : SpanValue.EndOffset])
