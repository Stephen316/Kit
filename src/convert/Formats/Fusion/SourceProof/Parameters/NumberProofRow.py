from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.Records.RecordParameter import Parameter


# formula verification needs both the projected and independently reconstructed parameter
@MakeDataClass(frozen=True, slots=True)
class NumberProofRow:
    Span: RecordSpan
    Raw: Parameter
    Actual: Parameter
    Binding: RecordSpan | None
