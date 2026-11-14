from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def MakeTimeAttrib(Value: TimeAttrib) -> AsmRecord:
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            *MakeAttribHead(Value.Links, "Timestamp_attrib_def"),
            (4, 1),
            (6, Value.UnixMicros),
        ),
    )
