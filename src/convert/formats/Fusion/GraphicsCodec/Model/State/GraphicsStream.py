from dataclasses import dataclass as MakeDataClass


# graphics stream needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class GraphicsStream:
    StreamIndex: int
    Payload: bytes
