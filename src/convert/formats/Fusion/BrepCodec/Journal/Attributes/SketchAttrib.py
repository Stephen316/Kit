from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks

from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# sketch attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class SketchAttrib:
    Links: AttribLinks
    SourceLink: SketchLink
