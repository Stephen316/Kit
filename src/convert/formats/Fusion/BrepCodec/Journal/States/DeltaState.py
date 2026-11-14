from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard


@MakeDataClass(frozen=True, slots=True)
class DeltaState:
    StateId: int
    RollsBack: bool
    Hidden: bool
    PreviousNode: int
    NextNode: int
    PartnerNode: int
    MergedWith: int
    OwnerStream: int
    NameValue: str | None
    Boards: tuple[BulletinBoard, ...]
    StateLinks: tuple[int, ...]
