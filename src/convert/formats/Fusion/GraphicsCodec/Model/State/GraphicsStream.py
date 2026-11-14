from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class GraphicsStream:
    StreamIndex: int
    Payload: bytes
