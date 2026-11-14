from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class HistoryState:
    CurrentId: int
    InitialId: int
    CurrentStateId: int
    NextEntityTag: int
    BoardStatus: int
    MaxStateId: int | None = None

    def __post_init__(self) -> None:
        MaxState = self.CurrentStateId if self.MaxStateId is None else self.MaxStateId
        object.__setattr__(self, "MaxStateId", MaxState)
        Values = (
            self.CurrentId,
            self.InitialId,
            self.CurrentStateId,
            self.NextEntityTag,
            MaxState,
        )
        for Value in Values:
            CheckInteger(Value, "history metadata", Lower=0, Upper=(1 << 31) - 1)
        CheckInteger(self.BoardStatus, "bulletin board status", Lower=0, Upper=3)
        if self.CurrentStateId > MaxState:
            raise ValueError("Fusion BRep current state exceeds its maximum state ID")
        if self.CurrentId <= self.InitialId:
            raise ValueError(
                "Fusion BRep current history state must follow its initial state"
            )
