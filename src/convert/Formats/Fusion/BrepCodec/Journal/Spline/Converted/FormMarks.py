from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# form marks needs an explicit state contract so surface geometry retains the control cage shape
@MakeDataClass(frozen=True, slots=True)
class FormMarks:
    Stamp: GeometryStamp
    UnixMicros: int
    FeatureId: int = 300
