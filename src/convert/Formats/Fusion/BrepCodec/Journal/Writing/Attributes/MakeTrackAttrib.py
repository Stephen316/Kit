from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the track attribute operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeTrackAttrib(Value: TrackAttrib) -> AsmRecord:
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            *MakeAttribHead(Value.Links, "FPM_tracked_attrib_def"),
            (4, 1),
            (4, Value.TrackedId),
        ),
    )
