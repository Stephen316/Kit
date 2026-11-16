from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgRecord,
    KDwgValue,
)


# record parts needs an explicit validity boundary so section boundaries and object references remain consistent
def RecordParts(
    Record: DwgRecord, FieldNames: tuple[str, ...]
) -> tuple[KDwgValue, ...]:
    Present = tuple(Entry.FieldName for Entry in Record.RecordFields)
    if Present != FieldNames:
        raise ValueError(
            f"DWG section record fields {Present!r} are not {FieldNames!r}"
        )
    return tuple(Entry.FieldValue for Entry in Record.RecordFields)


# named value needs an explicit validity boundary so section boundaries and object references remain consistent
def NamedValue(Record: DwgRecord, FieldName: str) -> KDwgValue:
    for Entry in Record.RecordFields:
        if Entry.FieldName == FieldName:
            return Entry.FieldValue
    raise ValueError(f"DWG section record lacks field {FieldName!r}")
