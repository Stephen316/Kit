from convert.formats.Fusion.GeometryCodec.EncodeSmbString import EncodeSmbString


def EncodeSmbName(NameValue: str) -> bytes:
    Parts = NameValue.split("-")
    return b"".join(
        EncodeSmbString(13 if Index == len(Parts) - 1 else 14, Value)
        for Index, Value in enumerate(Parts)
    )
