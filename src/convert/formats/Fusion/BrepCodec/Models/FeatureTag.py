from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class FeatureTag:
    PrimaryId: str
    OperationIds: tuple[int, ...]
    SecondaryId: int = 0
    ApproachId: int = 0

    def __post_init__(self) -> None:
        if (
            type(self.PrimaryId) is not str
            or not self.PrimaryId
            or not self.PrimaryId.isascii()
            or not self.PrimaryId.isprintable()
            or len(self.PrimaryId.encode("ascii")) > 255
        ):
            raise ValueError(
                "Fusion BRep primary identifier must fit a printable ASCII string"
            )
        if type(self.OperationIds) is not tuple or len(self.OperationIds) > 256:
            raise ValueError("Fusion BRep tag permits at most 256 operation identities")
        for Value in (self.SecondaryId, self.ApproachId, *self.OperationIds):
            CheckInteger(Value, "tag integer", Lower=-(1 << 31), Upper=(1 << 31) - 1)
