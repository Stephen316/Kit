from struct import pack as PackValue, unpack as UnpackValue, calcsize as CalcSize


class ByteStream:
    def __init__(self, Payload: bytes | None) -> None:
        super().__init__()
        self.IsReading = Payload is not None
        self.Payload = Payload or b""
        self.Position = 0
        self.Output = bytearray()

    def Transfer(self, Length: int, Value: bytes | None) -> bytes:
        if self.IsReading:
            Ending = self.Position + Length
            if Ending > len(self.Payload):
                raise ValueError("Truncated Fusion graphics stream")
            Result = self.Payload[self.Position : Ending]
            self.Position = Ending
            return Result
        if Value is None or len(Value) != Length:
            raise ValueError("Missing graphics field value")
        self.Output.extend(Value)
        return Value

    def Integer(self, Value: int | None, Format: str = "<I") -> int:
        if not self.IsReading and type(Value) is not int:
            raise ValueError("Expected an integer graphics field")
        Encoded = None if self.IsReading else PackValue(Format, Value)
        return int(UnpackValue(Format, self.Transfer(CalcSize(Format), Encoded))[0])
