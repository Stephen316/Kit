def DecodeName(NameBytes: bytes) -> str:
    Trimmed = NameBytes.split(b"\x00", 1)[0]
    if any(ByteValue < 0x20 or ByteValue > 0x7E for ByteValue in Trimmed):
        raise ValueError("DWG section name is not printable ASCII")
    return Trimmed.decode("ascii")
