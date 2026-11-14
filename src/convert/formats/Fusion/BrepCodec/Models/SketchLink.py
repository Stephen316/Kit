from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class SketchLink:
    PrimaryId: int
    SecondaryId: int
    Direction: int
    SplitSequenceId: int
    SplitTotalNumber: int
    TopologyRoleFlags: int = 0

    def __post_init__(self) -> None:
        for Value in (self.PrimaryId, self.SecondaryId):
            CheckInteger(Value, "sketch curve identity", Lower=0, Upper=(1 << 64) - 1)
        CheckInteger(self.Direction, "sketch direction", Lower=0, Upper=(1 << 32) - 1)
        if self.Direction not in (0, 1, (1 << 32) - 1):
            raise ValueError("Unsupported Fusion BRep sketch direction")
        CheckInteger(
            self.TopologyRoleFlags, "qualified sketch topology roles", Lower=0, Upper=0
        )
        for Value in (self.SplitSequenceId, self.SplitTotalNumber):
            CheckInteger(Value, "sketch split identity", Lower=1, Upper=(1 << 32) - 1)
        if self.SplitSequenceId > self.SplitTotalNumber:
            raise ValueError("Fusion BRep sketch split ordinal exceeds total")
