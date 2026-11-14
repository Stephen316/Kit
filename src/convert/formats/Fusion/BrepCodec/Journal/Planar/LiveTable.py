from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


@MakeDataClass(frozen=True, slots=True)
class LiveTable:
    StateId: int
    Entities: tuple[KJournalEntity | None, ...]
    SlotMap: tuple[int, ...]
    LiveSlots: tuple[int, ...]
    Records: tuple[int, ...] = ()
