from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.RecordSpan import RecordSpan


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
