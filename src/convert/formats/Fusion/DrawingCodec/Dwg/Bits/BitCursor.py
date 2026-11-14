class BitCursor:

    def __init__(self, DataValue: bytes, Position: int, Limit: int) -> None:
        super().__init__()
        if not 0 <= Position <= Limit <= len(DataValue) * 8:
            raise ValueError("DWG bit stream bounds lie outside the section data")
        self.DataValue = DataValue
        self.Position = Position
        self.Limit = Limit

    def TakeBits(self, Count: int) -> int:
        Finish = self.Position + Count
        if Count < 0 or Finish > self.Limit:
            raise ValueError("DWG bit stream is truncated")
        Window = self.DataValue[self.Position >> 3 : (Finish + 7) >> 3]
        Value = int.from_bytes(Window, "big") >> (-Finish & 7)
        self.Position = Finish
        return Value & ((1 << Count) - 1)
