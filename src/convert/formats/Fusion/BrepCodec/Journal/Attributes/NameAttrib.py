from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger

KNameActions = {False: (2, 3, 1, 2), True: (2, 1, 1, 2)}


@MakeDataClass(frozen=True, slots=True)
class NameAttrib:
    Links: AttribLinks
    Actions: tuple[int, int, int, int]
    NameText: str
    NumberValue: int | None = None

    def __post_init__(self) -> None:
        if self.Actions != KNameActions[self.NumberValue is not None]:
            raise ValueError("Unsupported Fusion generic attribute action set")
        if (
            type(self.NameText) is not str
            or not self.NameText
            or not self.NameText.isascii()
            or not self.NameText.isprintable()
            or len(self.NameText) > 255
        ):
            raise ValueError("Fusion generic attribute name must be printable ASCII")
        if self.NumberValue is not None:
            CheckInteger(self.NumberValue, "generic attribute integer")
