# the bit writer contract needs a dedicated boundary so compact fields retain unambiguous bit positions
class BitWriter:

    # bit writer needs explicit initial state so compact fields retain unambiguous bit positions
    def __init__(self) -> None:
        super().__init__()
        self.BitValue = 0
        self.BitCount = 0

    # the bits operation needs a consistent construction rule so compact fields retain unambiguous bit positions
    def PutBits(self, Value: int, Count: int) -> None:
        if Count < 0 or not 0 <= Value < 1 << Count:
            raise ValueError("DWG bit field does not fit its width")
        self.BitValue = self.BitValue << Count | Value
        self.BitCount += Count

    # the to bytes contract needs a shared interpretation so compact fields retain unambiguous bit positions
    def ToBytes(self) -> bytes:
        Padding = -self.BitCount & 7
        ByteCount = (self.BitCount + Padding) // 8
        return (self.BitValue << Padding).to_bytes(ByteCount, "big")
