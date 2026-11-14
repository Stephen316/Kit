from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def MetaValue(Record: EntityRecord, FieldName: str) -> KEntityValue:
    Matches = [
        Entry.Value
        for Entry in Record.Frame.Metadata or ()
        if Entry.FieldName == FieldName
    ]
    if len(Matches) != 1:
        raise ValueError("Form entity lacks its named body link")
    return Matches[0]
