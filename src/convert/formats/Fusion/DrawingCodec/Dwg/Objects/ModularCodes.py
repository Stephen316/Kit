from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields


def ReadModular(DataValue: bytes, Offset: int) -> tuple[int, int]:
    Value = 0
    Shift = 0
    Position = Offset
    while True:
        WordValue = ReadFields(DataValue, Position, "<H", "object size")[0]
        Position += 2
        Value |= (WordValue & 0x7FFF) << Shift
        Shift += 15
        if not WordValue & 0x8000:
            return Value, Position


def EncodeModular(Value: int) -> bytes:
    Output = bytearray()
    while Value >> 15:
        Output += (Value & 0x7FFF | 0x8000).to_bytes(2, "little")
        Value >>= 15
    return bytes(Output) + Value.to_bytes(2, "little")


def EncodeUnsigned(Value: int) -> bytes:
    Output = bytearray()
    while Value >> 7:
        Output.append(Value & 0x7F | 0x80)
        Value >>= 7
    return bytes(Output) + bytes((Value,))


def EncodeSigned(Value: int) -> bytes:
    Magnitude = abs(Value)
    Output = bytearray()
    while Magnitude >= 0x40:
        Output.append(Magnitude & 0x7F | 0x80)
        Magnitude >>= 7
    return bytes(Output) + bytes((Magnitude | (0x40 if Value < 0 else 0),))
