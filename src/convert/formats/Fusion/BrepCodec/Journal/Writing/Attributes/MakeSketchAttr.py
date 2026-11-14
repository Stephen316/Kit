from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeSourceLink import (
    MakeSourceLink,
)


def MakeSketchAttr(Value: SketchAttrib) -> AsmRecord:
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            *MakeAttribHead(Value.Links, "sketch_attrib_def"),
            *MakeSourceLink(Value.SourceLink),
        ),
    )
