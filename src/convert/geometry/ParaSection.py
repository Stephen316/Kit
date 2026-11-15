from dataclasses import dataclass as DataClass


# para section needs an explicit state contract so native geometry retains a consistent interchange interpretation
@DataClass(frozen=True, slots=True)
class ParaSection:
    Data: bytes
    Start: int
    End: int
    CompressedOffset: int
    CompressedSize: int
