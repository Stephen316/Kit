from math import isfinite as IsFinite
from struct import pack as PackValue

from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


# the parameter sink contract needs a dedicated boundary so native records retain their segment ownership and schema
class ParamSink(MetaSink):
    __slots__ = ()

    # the parameter text operation needs a consistent construction rule so native records retain their segment ownership and schema
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

    # the number operation needs a consistent construction rule so native records retain their segment ownership and schema
    def AddNumber(self, Number: float) -> None:
        if type(Number) not in (float, int) or not IsFinite(Number):
            raise ValueError("Invalid Fusion parameter number")
        self.AddBytes(PackValue("<d", Number))
