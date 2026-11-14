def EmitMapAtom(Value: str | int | bool) -> bytes:
    if isinstance(Value, bool):
        return bytes((195 if Value else 194,))
    if isinstance(Value, str):
        Payload = Value.encode("utf-8")
        if not Payload or len(Payload) > 4096 or b"\0" in Payload:
            raise ValueError("Invalid Fusion mesh MessagePack text")
        if len(Payload) < 32:
            return bytes((160 + len(Payload),)) + Payload
        if len(Payload) < 256:
            return b"\xd9" + bytes((len(Payload),)) + Payload
        return b"\xda" + len(Payload).to_bytes(2, "big") + Payload
    if not 0 <= Value < 1 << 32:
        raise ValueError("Unsupported Fusion mesh MessagePack integer")
    if Value < 128:
        return bytes((Value,))
    for Width, TagCode in ((1, 204), (2, 205), (4, 206)):
        if Value < 1 << (Width * 8):
            return bytes((TagCode,)) + Value.to_bytes(Width, "big")
    raise ValueError("Unsupported Fusion mesh MessagePack atom")
