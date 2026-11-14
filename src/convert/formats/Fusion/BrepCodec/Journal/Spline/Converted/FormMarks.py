from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


@MakeDataClass(frozen=True, slots=True)
class FormMarks:
    Stamp: GeometryStamp
    UnixMicros: int
    FeatureId: int = 300
