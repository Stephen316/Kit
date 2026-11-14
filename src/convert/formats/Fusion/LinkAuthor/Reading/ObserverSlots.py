from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def IsObserver(
    Target: LocalRef | SegmentRef | CrossRef | None,
    Origin: int,
    Design: int,
    ObjectId: int,
) -> bool:
    if isinstance(Target, LocalRef):
        return Origin == Design and Target.ObjectId == ObjectId
    if isinstance(Target, SegmentRef):
        return Target.SegmentId == Design and Target.ObjectId == ObjectId
    return False


def NextSlot(Model: DocumentModel, Design: int, ObjectId: int) -> int:
    Taken = tuple(
        Subject.ObserverIndex
        for Segment in Model.Segments
        for Record in Segment.Records
        for Subject in Record.Frame.Subjects or ()
        if IsObserver(
            Subject.Target, Segment.Metadata.Header.SegmentId, Design, ObjectId
        )
    )
    return max(Taken, default=-1) + 1
