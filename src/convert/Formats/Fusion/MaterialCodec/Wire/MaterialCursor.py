from convert.Formats.Fusion.MaterialCodec.Limits import KMaxStream


# the material cursor contract needs a dedicated boundary so typed appearance properties retain their native identifiers
class MaterialCursor:

    # material cursor needs explicit initial state so typed appearance properties retain their native identifiers
    def __init__(self, Payload: bytes) -> None:
        super().__init__()
        if type(Payload) is not bytes or len(Payload) > KMaxStream:
            raise ValueError("Fusion material stream exceeds the size limit")
        self.Payload = Payload
        self.Offset = 0

    # the bytes operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def TakeBytes(self, Count: int) -> bytes:
        if Count < 0 or self.Offset + Count > len(self.Payload):
            raise ValueError("Truncated Fusion material stream")
        Result = self.Payload[self.Offset : self.Offset + Count]
        self.Offset += Count
        return Result

    # invalid end input must fail here so typed appearance properties retain their native identifiers
    def RequireEnd(self) -> None:
        if self.Offset != len(self.Payload):
            raise ValueError("Unexpected Fusion material trailing bytes")
