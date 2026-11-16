from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the observer counts contract needs a shared interpretation so archive members retain their native ownership and reference relationships
def ObserverCounts(Records: tuple[EntityRecord, ...]) -> dict[int, int]:
    Counts: dict[int, int] = {}
    for Record in Records:
        for Subject in Record.Frame.Subjects or ():
            Target = Subject.Target
            if (
                isinstance(Target, LocalRef)
                or isinstance(Target, SegmentRef)
                and Target.SegmentId == 0
            ):
                Counts[Target.ObjectId] = max(
                    Counts.get(Target.ObjectId, 0), Subject.ObserverIndex + 1
                )
    return Counts
