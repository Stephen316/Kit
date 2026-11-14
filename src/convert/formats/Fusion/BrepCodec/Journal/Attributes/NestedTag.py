from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger

KTagHead = ((4, 3), (4, 3), (4, -1), (7, "generic_tag_attrib_def "))
KNestedHead = (*KTagHead, (4, 1), (4, 0), (7, ""), (4, 0), (4, 1))


@MakeDataClass(frozen=True, slots=True)
class NestedTag:
    OwnerRef: int
    OperationId: int

    def __post_init__(self) -> None:
        CheckInteger(self.OwnerRef, "nested tag owner", Lower=-1, Upper=(1 << 31) - 1)
        CheckInteger(
            self.OperationId, "nested tag operation", Lower=0, Upper=(1 << 31) - 1
        )
