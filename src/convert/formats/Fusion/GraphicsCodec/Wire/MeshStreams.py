from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.formats.Fusion.GraphicsCodec.Wire.MeshState import MeshState
from convert.formats.Fusion.GraphicsCodec.Wire.TransferSpanMut import TransferSpanMut
from convert.formats.Fusion.GraphicsCodec.Wire.FinishStreams import FinishStreams


class MeshStreams(MeshState):
    def Transfer(
        self, Stream: int, Offset: int, Length: int, Payload: bytes | None
    ) -> bytes:
        return TransferSpanMut(self, Stream, Offset, Length, Payload)

    def Finalize(self) -> tuple[GraphicsStream, ...]:
        Streams, self.Tails = FinishStreams(self)
        return Streams

    def SlackValues(self) -> tuple[GraphicsStream, ...]:
        return tuple(
            GraphicsStream(Stream, Payload)
            for Stream, Payload in sorted(self.Tails.items())
        )
