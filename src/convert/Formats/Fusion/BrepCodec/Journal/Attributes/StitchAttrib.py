from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks


# stitch attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class StitchAttrib:
    Links: AttribLinks
    HintValues: tuple[float, float, float]
