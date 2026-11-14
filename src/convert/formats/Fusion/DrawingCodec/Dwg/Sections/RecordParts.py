from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgRecord,
    KDwgValue,
)


def RecordParts(
    Record: DwgRecord, FieldNames: tuple[str, ...]
) -> tuple[KDwgValue, ...]:
    Present = tuple(Entry.FieldName for Entry in Record.RecordFields)
    if Present != FieldNames:
        raise ValueError(
            f"DWG section record fields {Present!r} are not {FieldNames!r}"
        )
    return tuple(Entry.FieldValue for Entry in Record.RecordFields)


def NamedValue(Record: DwgRecord, FieldName: str) -> KDwgValue:
    for Entry in Record.RecordFields:
        if Entry.FieldName == FieldName:
            return Entry.FieldValue
    raise ValueError(f"DWG section record lacks field {FieldName!r}")
