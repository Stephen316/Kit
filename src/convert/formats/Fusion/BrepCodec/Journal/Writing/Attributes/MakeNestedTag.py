from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import (
    KNestedHead,
    NestedTag,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeNestedTag(Value: NestedTag) -> AsmRecord:
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            *MakeAttribHead(
                AttribLinks(-1, -1, Value.OwnerRef), "generic_tag_attrib_def"
            ),
            *KNestedHead,
            (4, Value.OperationId),
            (4, 0),
        ),
    )
