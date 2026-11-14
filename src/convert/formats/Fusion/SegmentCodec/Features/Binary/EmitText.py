from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText


def EmitText(Value: str, WideText: bool = False) -> bytes:
    if type(Value) is not str or len(Value) > KMaxFeatureText:
        raise ValueError("Invalid Fusion feature text")
    if not all(
        Letter.isprintable() or (WideText and Letter in "\r\n\t") for Letter in Value
    ):
        raise ValueError("Unsupported Fusion feature text character")
    try:
        Encoded = Value.encode("utf-16le" if WideText else "ascii")
    except UnicodeError as ErrorInfo:
        raise ValueError("Invalid Fusion feature text encoding") from ErrorInfo
    Length = len(Encoded) // (2 if WideText else 1)
    if Length > KMaxFeatureText:
        raise ValueError("Oversized Fusion feature text")
    return PackValue("<I", Length) + Encoded
