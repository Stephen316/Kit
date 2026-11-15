from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks


# no merge attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class NoMergeAttrib:
    Links: AttribLinks
