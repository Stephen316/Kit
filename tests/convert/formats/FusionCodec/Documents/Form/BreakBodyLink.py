from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def BreakRecord(Record: EntityRecord) -> EntityRecord:
    Entries = tuple(
        (
            ReplaceValue(Entry, Value=LocalRef(Record.ObjectId))
            if Entry.FieldName == "FORMFEAT_DM_SUBD_REF"
            else Entry
        )
        for Entry in Record.Frame.Metadata or ()
    )
    if Entries == (Record.Frame.Metadata or ()):
        return Record
    return ReplaceValue(Record, Frame=ReplaceValue(Record.Frame, Metadata=Entries))


def BreakSegment(Segment: ParsedSegment) -> ParsedSegment:
    Records = tuple(BreakRecord(Record) for Record in Segment.Records)
    return ReplaceValue(Segment, Records=Records)


def BreakBodyLink(Model: DocumentModel) -> DocumentModel:
    Segments = tuple(BreakSegment(Segment) for Segment in Model.Segments)
    if Segments == Model.Segments:
        raise ValueError("The Form document has no converted body link")
    return ReplaceValue(Model, Segments=Segments)
