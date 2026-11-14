from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


@MakeDataClass(frozen=True, slots=True)
class GeometryState:
    Header: BrepHeader
    Stamp: GeometryStamp
    Entities: tuple[KJournalEntity, ...]
