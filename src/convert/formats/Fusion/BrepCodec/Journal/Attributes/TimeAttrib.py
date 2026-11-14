from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks


@MakeDataClass(frozen=True, slots=True)
class TimeAttrib:
    Links: AttribLinks
    UnixMicros: float
