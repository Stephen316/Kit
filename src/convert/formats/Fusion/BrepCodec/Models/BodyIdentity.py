from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class BodyIdentity:
    BodyKey: int
    OperationId: int
    SecondaryId: int
    AuthoredMicros: float

    def __post_init__(self) -> None:
        CheckInteger(self.BodyKey, "body key", Lower=0)
        CheckInteger(
            self.OperationId, "body operation identity", Lower=0, Upper=(1 << 31) - 1
        )
        CheckInteger(
            self.SecondaryId,
            "body tag secondary identity",
            Lower=-(1 << 31),
            Upper=(1 << 31) - 1,
        )
        if (
            isinstance(self.AuthoredMicros, bool)
            or not IsFinite(self.AuthoredMicros)
            or self.AuthoredMicros < 0
        ):
            raise ValueError(
                "Fusion BRep authoring timestamp must be finite and nonnegative"
            )
