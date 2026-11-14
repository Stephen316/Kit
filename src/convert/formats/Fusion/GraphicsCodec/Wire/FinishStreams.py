from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.MeshState import MeshState


def FinishStreams(
    State: MeshState,
) -> tuple[tuple[GraphicsStream, ...], dict[int, bytes]]:
    Results: list[GraphicsStream] = []
    Tails: dict[int, bytes] = {} if State.IsReading else dict(State.Tails)
    if State.IsReading and set(State.Inputs) != set(State.Ranges):
        raise ValueError("Unreferenced graphics mesh streams")
    if not set(Tails) <= set(State.Ranges):
        raise ValueError("Graphics mesh slack names an unreferenced stream")
    for Stream, Ranges in sorted(State.Ranges.items()):
        Output = bytearray()
        for (Start, _), Payload in sorted(Ranges.items()):
            if Start != len(Output):
                raise ValueError("Unaccounted graphics mesh bytes")
            Output.extend(Payload)
        if State.IsReading and len(Output) < len(State.Inputs[Stream]):
            Tails[Stream] = State.Inputs[Stream][len(Output) :]
        elif not State.IsReading:
            Output.extend(Tails.get(Stream, b""))
        Results.append(GraphicsStream(Stream, bytes(Output)))
    return tuple(Results), Tails
