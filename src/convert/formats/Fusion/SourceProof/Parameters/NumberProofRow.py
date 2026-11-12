from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.records.RecordParameter import Parameter


# formula verification needs both the projected and independently reconstructed parameter
@MakeDataClass(frozen=True, slots=True)
class NumberProofRow:
    Span: RecordSpan
    Raw: Parameter
    Actual: Parameter
    Binding: RecordSpan | None
