from convert.formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.formats.Fusion.MeshCodec.Streams.ReadStream import ReadStream
from convert.formats.Fusion.MeshCodec.Streams.StreamSpecs import StreamSpecs


def ReadStreams(Value: MeshRegistry, Payloads: tuple[bytes, ...]) -> dict[str, bytes]:
    Specs = StreamSpecs(Value)
    Result: dict[str, bytes] = {}
    Total = 0
    for NameValue, Payload in zip(Value.StreamOrder, Payloads, strict=True):
        Decoded = ReadStream(Payload, Specs[NameValue])
        Total += len(Decoded)
        if Total > 64 * 1024 * 1024:
            raise ValueError("Fusion mesh total decoded allocation exceeds limit")
        Result[NameValue] = Decoded
    return Result
