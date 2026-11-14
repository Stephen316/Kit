from convert.formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry


def StreamSpecs(Value: MeshRegistry) -> dict[str, dict[str, int | bool]]:
    return {
        Value.VertexStream: {"D": 3, "T": 3},
        Value.CornerStream: {"T": 1, "d": 1},
        Value.NormalStream: {"D": 3, "T": 3, "U": True},
        Value.OverrideStream: {"T": 1, "d": 1},
        Value.EdgeStream: {"T": 1, "d": 1},
        Value.GroupStream: {"T": 1, "d": 1},
    }
