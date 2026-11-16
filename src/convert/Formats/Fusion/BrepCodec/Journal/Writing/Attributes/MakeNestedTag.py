from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import (
    KNestedHead,
    NestedTag,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the nested tag operation needs a consistent construction rule so revision ownership survives native history reconstruction
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
