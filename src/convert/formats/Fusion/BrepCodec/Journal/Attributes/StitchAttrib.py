from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks


@MakeDataClass(frozen=True, slots=True)
class StitchAttrib:
    Links: AttribLinks
    HintValues: tuple[float, float, float]
