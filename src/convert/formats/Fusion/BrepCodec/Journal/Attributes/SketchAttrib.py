from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks

from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


@MakeDataClass(frozen=True, slots=True)
class SketchAttrib:
    Links: AttribLinks
    SourceLink: SketchLink
