from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase

KFileClass = "3B30D852-778A-4752-9EBD-A154875C911C"

KFileField = "persistedFileName"


def CheckDatabase(
    Segments: tuple[ParsedSegment | LegacySegment, ...],
    Database: DrawingDatabase | None,
) -> None:
    Parsed = tuple(Entry for Entry in Segments if isinstance(Entry, ParsedSegment))
    if Database is None or not Parsed:
        return
    Names = tuple(
        Field.Value
        for Segment in Parsed
        for Record in Segment.Records
        for Group in Record.Groups
        if Group.ClassGuid.upper() == KFileClass
        for Field in Group.Fields
        if Field.FieldName == KFileField
    )
    if Names != (Database.FileName,):
        raise ValueError("Fusion drawing database name disagrees with its segment")
