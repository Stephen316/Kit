from convert.Formats.Fusion.SegmentCodec.Metadata.MetaLimits import KMaxMetaText


# the meta text operation needs a consistent construction rule so native records retain their segment ownership and schema
def EncodeMetaText(Content: str, WideText: bool) -> tuple[bytes, int]:
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
    return DataValue, Count
