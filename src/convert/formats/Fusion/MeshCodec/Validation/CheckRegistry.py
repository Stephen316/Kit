from convert.formats.Fusion.MeshCodec.Model.MeshRegistry import MeshRegistry
from convert.formats.Fusion.MeshCodec.Validation.CheckUuid import CheckUuid


def CheckRegistry(Value: MeshRegistry) -> None:
    Names = (
        Value.VertexStream,
        Value.CornerStream,
        Value.NormalStream,
        Value.OverrideStream,
        Value.EdgeStream,
        Value.GroupStream,
    )
    if (
        len(set(Names)) != 6
        or len(Value.StreamOrder) != 6
        or set(Names) != set(Value.StreamOrder)
    ):
        raise ValueError(
            "Fusion mesh stream references do not match unique declarations"
        )
    for NameValue in Names:
        if not NameValue or "\0" in NameValue or len(NameValue.encode("utf-8")) > 4096:
            raise ValueError("Invalid Fusion mesh stream name")
    for Identity in (Value.MeshId, Value.FusionId, Value.NormalId):
        CheckUuid(Identity)
    if type(Value.FaceGroupCount) is not int or Value.FaceGroupCount != 1:
        raise ValueError("Unsupported Fusion mesh face-group-associated count")
    KeyValues = tuple(Group.GroupKey for Group in Value.Groups)
    if len(set(KeyValues)) != len(KeyValues) or any(
        type(KeyValue) is not int or not 0 <= KeyValue < 1 << 32
        for KeyValue in KeyValues
    ):
        raise ValueError("Invalid Fusion mesh face-group keys")
    for Group in Value.Groups:
        CheckUuid(Group.GroupId)
