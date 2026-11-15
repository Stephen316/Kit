from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks

# vertedge cap must remain consistent across callers so topology changes retain their native revision relationships
KVertedgeCap = 64


# vertedge attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class VertedgeAttrib:
    Links: AttribLinks
    EdgeSlots: tuple[tuple[int, int], ...]
