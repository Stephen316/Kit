from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


# live table needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class LiveTable:
    StateId: int
    Entities: tuple[KJournalEntity | None, ...]
    SlotMap: tuple[int, ...]
    LiveSlots: tuple[int, ...]
    Records: tuple[int, ...] = ()
