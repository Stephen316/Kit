from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks


# time attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class TimeAttrib:
    Links: AttribLinks
    UnixMicros: float
