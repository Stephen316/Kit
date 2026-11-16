from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks

from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# tag attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class TagAttrib:
    Links: AttribLinks
    Groups: tuple[FeatureTag, ...]
    Attribute: int = -1
