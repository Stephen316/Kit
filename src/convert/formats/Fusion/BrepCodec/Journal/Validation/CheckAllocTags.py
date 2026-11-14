from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


def CheckAllocTags(Model: JournalModel) -> None:
    for Value in Model.Entities:
        Record = MakeEntityNode(Value)
        if Record.Name == "ATTRIB_CUSTOM-attrib":
            continue
        EntityTag = Record.Tokens[1][1]
        if (
            type(EntityTag) is not int
            or not -1 <= EntityTag < Model.Stream.NextEntityTag
        ):
            raise ValueError("Fusion entity tag exceeds its history allocator")
