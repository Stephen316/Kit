from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.formats.Fusion.GraphicsCodec.Wire.MeshState import MeshState
from convert.formats.Fusion.GraphicsCodec.Wire.TransferSpanMut import TransferSpanMut
from convert.formats.Fusion.GraphicsCodec.Wire.FinishStreams import FinishStreams


# the mesh streams contract needs a dedicated boundary so display geometry retains its entity and scene relationships
class MeshStreams(MeshState):

    # the transfer contract needs a shared interpretation so display geometry retains its entity and scene relationships
    def Transfer(
        self, Stream: int, Offset: int, Length: int, Payload: bytes | None
    ) -> bytes:
        return TransferSpanMut(self, Stream, Offset, Length, Payload)

    # the finalize contract needs a shared interpretation so display geometry retains its entity and scene relationships
    def Finalize(self) -> tuple[GraphicsStream, ...]:
        Streams, self.Tails = FinishStreams(self)
        return Streams

    # the slack values contract needs a shared interpretation so display geometry retains its entity and scene relationships
    def SlackValues(self) -> tuple[GraphicsStream, ...]:
        return tuple(
            GraphicsStream(Stream, Payload)
            for Stream, Payload in sorted(self.Tails.items())
        )
