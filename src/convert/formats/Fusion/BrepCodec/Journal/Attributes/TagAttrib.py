from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks

from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


@MakeDataClass(frozen=True, slots=True)
class TagAttrib:
    Links: AttribLinks
    Groups: tuple[FeatureTag, ...]
    Attribute: int = -1
