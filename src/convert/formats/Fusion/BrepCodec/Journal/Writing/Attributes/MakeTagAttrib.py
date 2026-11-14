from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeTagGroups import (
    MakeTagGroups,
)


def MakeTagAttrib(Value: TagAttrib) -> AsmRecord:
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            *MakeAttribHead(Value.Links, "generic_tag_attrib_def", Value.Attribute),
            *MakeTagGroups(Value.Groups),
        ),
    )
