from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# meta value needs an explicit validity boundary so supporting records retain their owning document relationships
def MetaValue(Record: EntityRecord, FieldName: str) -> KEntityValue:
    Matches = [
        Entry.Value
        for Entry in Record.Frame.Metadata or ()
        if Entry.FieldName == FieldName
    ]
    if len(Matches) != 1:
        raise ValueError("Form entity lacks its named body link")
    return Matches[0]
