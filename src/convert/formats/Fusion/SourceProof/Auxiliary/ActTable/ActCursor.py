# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
