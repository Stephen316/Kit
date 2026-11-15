# terminator must remain consistent across callers so section boundaries and object references remain consistent
KTerminator = b"\x00\x00"


# the wide operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def DecodeWide(DataValue: bytes) -> str:
    if not DataValue:
        return ""
    if len(DataValue) % 2 or not DataValue.endswith(KTerminator):
        raise ValueError("DWG wide text field is not terminated UTF-16 text")
    return DataValue[: -len(KTerminator)].decode("utf-16-le")


# the wide operation needs a consistent construction rule so section boundaries and object references remain consistent
def EncodeWide(TextValue: str, ByteCount: int) -> bytes:
    if ByteCount == 0 and not TextValue:
        return b""
    return TextValue.encode("utf-16-le") + KTerminator
