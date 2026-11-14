from typing import cast as CastValue
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    DraftRecord,
    DraftSlot,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef


def ReadDraftRecord(Value: object) -> DraftRecord:
    Pairs: list[tuple[str, KDraftValue]] = []
    for Entry in ReadSeries(Value):
        FieldName, FieldValue = ReadSeries(Entry)
        Pairs.append((ReadString(FieldName), ReadDraftJson(FieldValue)))
    return DraftRecord(tuple(Pairs))


def ReadTagged(Fields: dict[str, object]) -> KDraftValue:
    if "Hex" in Fields:
        return bytes.fromhex(ReadString(Fields["Hex"]))
    if "Key" in Fields:
        return DraftLink(ReadInteger(Fields["Code"]), ReadString(Fields["Key"]))
    if "Handle" in Fields:
        return DwgHandleRef(ReadInteger(Fields["Code"]), ReadInteger(Fields["Handle"]))
    if "Slot" in Fields:
        return DraftSlot(ReadString(Fields["Slot"]), ReadInteger(Fields["Form"]))
    if "Fields" in Fields:
        return ReadDraftRecord(Fields["Fields"])
    raise ValueError(f"Authored DWG standard value has unknown tags {sorted(Fields)}")


def ReadDraftJson(Value: object) -> KDraftValue:
    if isinstance(Value, bool):
        raise ValueError("Authored DWG standard values never hold booleans")
    if isinstance(Value, (int, float, str)):
        return Value
    if isinstance(Value, list):
        Elements = CastValue(list[object], Value)
        return tuple(ReadDraftJson(Element) for Element in Elements)
    return ReadTagged(ReadObject(Value))
