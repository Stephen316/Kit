from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.MeshState import MeshState


def TransferSpanMut(
    State: MeshState, Stream: int, Offset: int, Length: int, Payload: bytes | None
) -> bytes:
    if not 0 <= Stream < 1000 or Offset < 0 or Length < 0 or Offset + Length > 67108864:
        raise ValueError("Invalid graphics buffer range")
    if State.IsReading:
        Source = State.Inputs.get(Stream)
        if Source is None or Offset + Length > len(Source):
            raise ValueError("Missing graphics buffer bytes")
        Payload = Source[Offset : Offset + Length]
    if Payload is None or len(Payload) != Length:
        raise ValueError("Incorrect graphics buffer length")
    Ranges = State.Ranges.setdefault(Stream, {})
    KeyValue = (Offset, Offset + Length)
    for (Start, Ending), Current in Ranges.items():
        if max(Start, Offset) < min(Ending, Offset + Length) and (
            KeyValue != (Start, Ending) or Current != Payload
        ):
            raise ValueError("Conflicting graphics buffer ranges")
    Ranges[KeyValue] = Payload
    return Payload
