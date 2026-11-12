from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import (
    KMaxMetaSize,
    KMaxMetaText,
)


# a bounded sink prevents oversized output even for otherwise valid typed values
class MetaSink:
    __slots__ = ("Buffer",)

    # a single mutable buffer avoids rebuilding the accumulated wire output
    def __init__(self) -> None:
        super().__init__()
        self.Buffer = bytearray()

    # bytes from any field share the same cumulative member limit
    def AddBytes(self, Content: bytes) -> None:
        if len(self.Buffer) + len(Content) > KMaxMetaSize:
            raise ValueError("Oversized Fusion MetaStream")
        self.Buffer.extend(Content)

    # unsigned word validation keeps invalid typed values out of struct packing
    def AddWord(self, Number: int) -> None:
        if type(Number) is not int or not 0 <= Number < 1 << 32:
            raise ValueError("Invalid Fusion MetaStream unsigned word")
        self.AddBytes(PackValue("<I", Number))

    # full width identities and offsets must survive synthetic construction unchanged
    def AddLong(self, Number: int) -> None:
        if type(Number) is not int or not 0 <= Number < 1 << 64:
            raise ValueError("Invalid Fusion MetaStream unsigned long")
        self.AddBytes(PackValue("<Q", Number))

    # text counts describe encoded units rather than unicode scalar values
    def AddText(self, Content: str, *, WideText: bool = False) -> None:
        if (
            type(Content) is not str
            or len(Content) > KMaxMetaText
            or not all(Letter.isprintable() for Letter in Content)
        ):
            raise ValueError("Invalid Fusion MetaStream string")
        DataValue = Content.encode("utf-16le" if WideText else "ascii")
        Count = len(DataValue) // (2 if WideText else 1)
        if Count > KMaxMetaText:
            raise ValueError("Oversized Fusion MetaStream string")
        self.AddWord(Count)
        self.AddBytes(DataValue)

    # sequence lengths are generated from immutable typed rows rather than copied bytes
    def AddCount(self, Items: tuple[object, ...], Maximum: int) -> None:
        if type(Items) is not tuple or len(Items) > Maximum:
            raise ValueError("Invalid Fusion MetaStream sequence")
        self.AddWord(len(Items))
