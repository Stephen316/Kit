from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks


@MakeDataClass(frozen=True, slots=True)
class TrackAttrib:
    Links: AttribLinks
    TrackedId: int
