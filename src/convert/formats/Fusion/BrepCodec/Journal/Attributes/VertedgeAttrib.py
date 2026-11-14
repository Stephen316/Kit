from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks

KVertedgeCap = 64


@MakeDataClass(frozen=True, slots=True)
class VertedgeAttrib:
    Links: AttribLinks
    EdgeSlots: tuple[tuple[int, int], ...]
