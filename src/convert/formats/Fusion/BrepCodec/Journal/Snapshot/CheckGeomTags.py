from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


def CheckGeomTags(Model: GeometryState) -> None:
    for Value in Model.Entities:
        Record = MakeEntityNode(Value)
        if Record.Name == "ATTRIB_CUSTOM-attrib":
            continue
        EntityTag = Record.Tokens[1][1]
        if not isinstance(EntityTag, int):
            raise ValueError("Invalid Fusion geometry entity tag")
        CheckInteger(EntityTag, "geometry entity tag", Lower=-1, Upper=(1 << 31) - 1)
