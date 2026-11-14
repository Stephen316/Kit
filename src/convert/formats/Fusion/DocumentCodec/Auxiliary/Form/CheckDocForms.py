from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.CheckFormBreps import (
    CheckFormBreps,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.CheckFormFrame import (
    CheckFormFrame,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.CheckFormNodes import (
    CheckFormNodes,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.CheckFormParts import (
    CheckFormParts,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.LeadGuid import LeadGuid
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import (
    KFrameGuid,
    KNodeGuid,
)


def CheckDocForms(Value: DocumentModel, CheckBodies: bool = True) -> None:
    Owners = {
        Record.ObjectId: Record
        for Segment in Value.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        if Record.IsPrimary
    }
    Joined = CheckFormParts(Owners, Value.Forms)
    for Record in Owners.values():
        if LeadGuid(Record) == KFrameGuid:
            CheckFormFrame(Record, Owners, Joined)
        if LeadGuid(Record) == KNodeGuid:
            CheckFormNodes(Record, Owners, Joined)
    if CheckBodies:
        CheckFormBreps(Value, tuple(Joined.values()))
