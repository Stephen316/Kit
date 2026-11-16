from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# geometry state needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class GeometryState:
    Header: BrepHeader
    Stamp: GeometryStamp
    Entities: tuple[KJournalEntity, ...]
