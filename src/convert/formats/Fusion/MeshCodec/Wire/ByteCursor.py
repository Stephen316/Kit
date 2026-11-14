class ByteCursor:
    def __init__(self, Payload: bytes) -> None:
        super().__init__()
        self.Payload = Payload
        self.Position = 0

    def TakeBytes(self, Length: int) -> bytes:
        Ending = self.Position + Length
        if Length < 0 or Ending > len(self.Payload):
            raise ValueError("Truncated Fusion mesh input")
        Result = self.Payload[self.Position : Ending]
        self.Position = Ending
        return Result

    def Integer(self, Length: int, Order: str = "little") -> int:
        if Order == "little":
            return int.from_bytes(self.TakeBytes(Length), "little")
        if Order == "big":
            return int.from_bytes(self.TakeBytes(Length), "big")
        raise ValueError("Invalid mesh integer byte order")

    def Remaining(self) -> int:
        return len(self.Payload) - self.Position
