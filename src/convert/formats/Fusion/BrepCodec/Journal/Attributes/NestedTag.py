from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger

# the tag head order must stay explicit so topology changes retain their native revision relationships
KTagHead = ((4, 3), (4, 3), (4, -1), (7, "generic_tag_attrib_def "))

# the nested head order must stay explicit so topology changes retain their native revision relationships
KNestedHead = (*KTagHead, (4, 1), (4, 0), (7, ""), (4, 0), (4, 1))


# nested tag needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class NestedTag:
    OwnerRef: int
    OperationId: int

    # invalid nested tag state must fail at construction so journal reconstruction never receives an inconsistent contract
    def __post_init__(self) -> None:
        CheckInteger(self.OwnerRef, "nested tag owner", Lower=-1, Upper=(1 << 31) - 1)
        CheckInteger(
            self.OperationId, "nested tag operation", Lower=0, Upper=(1 << 31) - 1
        )
