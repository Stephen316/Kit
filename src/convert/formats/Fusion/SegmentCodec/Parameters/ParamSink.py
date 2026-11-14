from math import isfinite as IsFinite
from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


class ParamSink(MetaSink):
    __slots__ = ()

    def AddParamText(self, Content: str, AllowControls: bool = False) -> None:
        if type(Content) is not str or not all(
            Letter.isprintable() or (AllowControls and Letter in "\r\n\t")
            for Letter in Content
        ):
            raise ValueError("Invalid Fusion parameter text")
        if len(Content) > 1024:
            raise ValueError("Oversized Fusion parameter text")
        Encoded = Content.encode("utf-16le")
        if len(Encoded) > 2048:
            raise ValueError("Oversized Fusion parameter text")
        self.AddWord(len(Encoded) // 2)
        self.AddBytes(Encoded)

    def AddNumber(self, Number: float) -> None:
        if type(Number) not in (float, int) or not IsFinite(Number):
            raise ValueError("Invalid Fusion parameter number")
        self.AddBytes(PackValue("<d", Number))
