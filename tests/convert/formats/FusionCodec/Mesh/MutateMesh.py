from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.MeshCodec.Envelope.EmitEnvelope import EmitEnvelope
from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh
from convert.formats.Fusion.MeshCodec.Registry.EmitRegistry import EmitRegistry
from convert.formats.Fusion.MeshCodec.Streams.EmitStream import EmitStream
from convert.formats.Fusion.MeshCodec.Streams.EmitTerminal import EmitTerminal
from convert.formats.Fusion.MeshCodec.Streams.MakePayloads import MakePayloads
from convert.formats.Fusion.MeshCodec.Streams.StreamSpecs import StreamSpecs


def MutateMesh(Model: ParaMesh, KindValue: str) -> bytes:
    Registry = Model.Registry
    Payloads = MakePayloads(Model)
    if KindValue == "override":
        Payloads[Registry.OverrideStream] = EmitTerminal(
            (*Model.Overrides[:-1], len(Model.Corners))
        )
    elif KindValue == "facegroup":
        Unknown = max(Group.GroupKey for Group in Registry.Groups) + 1
        Payloads[Registry.GroupStream] = EmitTerminal((Unknown, *Model.FaceGroups[1:]))
    elif KindValue == "edge":
        Payloads[Registry.EdgeStream] = EmitTerminal((0, len(Model.Positions)))
    elif KindValue == "registry":
        Registry = ReplaceValue(Registry, VertexStream=Registry.CornerStream)
    elif KindValue != "allocation":
        raise ValueError("Unknown malformed mesh case")
    Specs = StreamSpecs(Model.Registry)
    Streams = [
        EmitStream(Payloads[NameValue], Specs[NameValue])
        for NameValue in Registry.StreamOrder
    ]
    if KindValue == "allocation":
        Offset = 2 + int.from_bytes(Streams[0][:2], "little")
        Streams[0] = (
            Streams[0][:Offset]
            + (64 * 1024 * 1024 + 4).to_bytes(4, "little")
            + Streams[0][Offset + 4 :]
        )
    return EmitEnvelope(EmitRegistry(Registry), Registry.StreamOrder, tuple(Streams))
