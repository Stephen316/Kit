from convert.formats.Fusion.DrawingCodec.Dwg.Pack.EncodeLong import EncodeLong


def EncodeMatch(Length: int, Distance: int, Trailing: int) -> bytes:
    if 3 <= Length <= 14 and 0 <= Distance <= 0x3FF:
        LeadByte = (Length + 1) << 4 | (Distance & 3) << 2 | Trailing
        return bytes((LeadByte, Distance >> 2))
    if 3 <= Length and 0 <= Distance <= 0x3FFF:
        if Length <= 0x21:
            Opening = bytes((Length + 0x1E,))
        else:
            Opening = b"\x20" + EncodeLong(Length - 0x21)
        return Opening + bytes(((Distance & 0x3F) << 2 | Trailing, Distance >> 6))
    FarDistance = Distance - 0x3FFF
    if Length < 4 or not 0 < FarDistance <= 0x3FFF:
        raise ValueError("DWG compressed match is outside the encodable range")
    if Length <= 9:
        Opening = bytes((0x10 | Length - 2,))
    else:
        Opening = b"\x10" + EncodeLong(Length - 9)
    return Opening + bytes(((FarDistance & 0x3F) << 2 | Trailing, FarDistance >> 6))
