from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks


# track attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class TrackAttrib:
    Links: AttribLinks
    TrackedId: int
