from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


@MakeDataClass(frozen=True, slots=True)
class JournalModel:
    Header: BrepHeader
    Stamp: GeometryStamp
    ActiveCount: int
    Entities: tuple[KJournalEntity, ...]
    Stream: StreamState
    States: tuple[DeltaState, ...]
