from convert.Formats.Fusion.MeshCodec.Envelope.EmitEnvelope import EmitEnvelope
from convert.Formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh
from convert.Formats.Fusion.MeshCodec.Registry.EmitRegistry import EmitRegistry
from convert.Formats.Fusion.MeshCodec.Streams.EmitStream import EmitStream
from convert.Formats.Fusion.MeshCodec.Streams.MakePayloads import MakePayloads
from convert.Formats.Fusion.MeshCodec.Streams.StreamSpecs import StreamSpecs
from convert.Formats.Fusion.MeshCodec.Validation.CheckMesh import CheckMesh


# the para mesh operation needs a consistent construction rule so vertex and index streams retain their intended connectivity
def EmitParaMesh(Value: ParaMesh) -> bytes:
    CheckMesh(Value)
    Payloads = MakePayloads(Value)
    Specs = StreamSpecs(Value.Registry)
    Streams = tuple(
        EmitStream(Payloads[NameValue], Specs[NameValue])
        for NameValue in Value.Registry.StreamOrder
    )
    return EmitEnvelope(
        EmitRegistry(Value.Registry), Value.Registry.StreamOrder, Streams
    )
