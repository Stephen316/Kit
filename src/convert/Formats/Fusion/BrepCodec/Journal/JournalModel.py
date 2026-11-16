from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.Formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# journal model needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class JournalModel:
    Header: BrepHeader
    Stamp: GeometryStamp
    ActiveCount: int
    Entities: tuple[KJournalEntity, ...]
    Stream: StreamState
    States: tuple[DeltaState, ...]
