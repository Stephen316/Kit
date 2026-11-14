def EncodeSmbString(TagValue: int, TextValue: str) -> bytes:
    Payload = TextValue.encode("utf-8")
    if len(Payload) > 255:
        raise ValueError("ASM short string exceeds its byte-count field")
    return bytes((TagValue, len(Payload))) + Payload
