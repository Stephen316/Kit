from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the time attribute operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeTimeAttrib(Value: TimeAttrib) -> AsmRecord:
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            *MakeAttribHead(Value.Links, "Timestamp_attrib_def"),
            (4, 1),
            (6, Value.UnixMicros),
        ),
    )
