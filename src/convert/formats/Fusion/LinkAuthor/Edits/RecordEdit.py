from dataclasses import replace as Replace

from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def OwnedIds(Segment: ParsedSegment, ClassGuid: str) -> tuple[int, ...]:
    return tuple(
        Identity
        for Entry in Segment.Metadata.Classes
        if Entry.ClassGuid.upper() == ClassGuid.upper()
        for Identity in Entry.OwnerIds
    )


def SoleId(Segment: ParsedSegment, ClassGuid: str) -> int:
    Found = OwnedIds(Segment, ClassGuid)
    if len(Found) != 1:
        raise ValueError("Fusion link authoring needs exactly one record of a class")
    return Found[0]


def ReadValue(
    Records: tuple[EntityRecord, ...], ObjectId: int, FieldName: str
) -> KEntityValue:
    Found = tuple(
        Field.Value
        for Record in Records
        if Record.ObjectId == ObjectId
        for Group in Record.Groups
        for Field in Group.Fields
        if Field.FieldName == FieldName
    )
    if len(Found) != 1:
        raise ValueError("Fusion link authoring needs exactly one named field")
    return Found[0]


def ReadLocal(Records: tuple[EntityRecord, ...], ObjectId: int, FieldName: str) -> int:
    Value = ReadValue(Records, ObjectId, FieldName)
    if not isinstance(Value, LocalRef):
        raise ValueError("Fusion link authoring expected a local reference")
    return Value.ObjectId


def ReadText(Records: tuple[EntityRecord, ...], ObjectId: int, FieldName: str) -> str:
    Value = ReadValue(Records, ObjectId, FieldName)
    if type(Value) is not str:
        raise ValueError("Fusion link authoring expected a text field")
    return Value


def ReadNumber(Records: tuple[EntityRecord, ...], ObjectId: int, FieldName: str) -> int:
    Value = ReadValue(Records, ObjectId, FieldName)
    if type(Value) is not int:
        raise ValueError("Fusion link authoring expected an integer field")
    return Value


def WriteValue(
    Records: tuple[EntityRecord, ...],
    ObjectId: int,
    FieldName: str,
    Value: KEntityValue,
) -> tuple[EntityRecord, ...]:
    _ = ReadValue(Records, ObjectId, FieldName)
    return tuple(
        (
            Replace(
                Record,
                Groups=tuple(
                    Replace(
                        Group,
                        Fields=tuple(
                            (
                                NamedValue(FieldName, Value)
                                if Field.FieldName == FieldName
                                else Field
                            )
                            for Field in Group.Fields
                        ),
                    )
                    for Group in Record.Groups
                ),
            )
            if Record.ObjectId == ObjectId
            else Record
        )
        for Record in Records
    )


def AppendItems(
    Records: tuple[EntityRecord, ...],
    ObjectId: int,
    FieldName: str,
    Items: tuple[KEntityValue, ...],
) -> tuple[EntityRecord, ...]:
    Current = ReadValue(Records, ObjectId, FieldName)
    if not isinstance(Current, ValueSeries):
        raise ValueError("Fusion link authoring expected a sequence field")
    return WriteValue(Records, ObjectId, FieldName, ValueSeries(Current.Items + Items))


def MarkFrame(
    Records: tuple[EntityRecord, ...], ObjectId: int
) -> tuple[EntityRecord, ...]:
    return tuple(
        (
            Replace(Record, Frame=Replace(Record.Frame, Metadata=()))
            if Record.ObjectId == ObjectId and Record.IsPrimary
            else Record
        )
        for Record in Records
    )


def AddPairs(
    Records: tuple[EntityRecord, ...],
    ObjectId: int,
    FieldName: str,
    Pairs: tuple[ValuePair[KEntityValue], ...],
) -> tuple[EntityRecord, ...]:
    Current = ReadValue(Records, ObjectId, FieldName)
    if not isinstance(Current, ValueMap):
        raise ValueError("Fusion link authoring expected a map field")
    return WriteValue(Records, ObjectId, FieldName, ValueMap(Pairs + Current.Entries))
