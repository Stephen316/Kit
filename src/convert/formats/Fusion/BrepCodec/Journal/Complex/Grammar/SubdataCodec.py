from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
    LoftSubdata,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def SubdataSize(SubdataKind: int, RowCount: int, ColumnCount: int) -> int:
    if SubdataKind != 213 or not 1 <= RowCount <= 64 or not 0 <= ColumnCount <= 64:
        raise ValueError("Unsupported Fusion loft section subdata form")
    return RowCount * (ColumnCount + 2) * 2


def ReadSubdataMut(Cursor: FieldCursor) -> LoftSubdata:
    SubdataKind = ReadCountMut(Cursor, 1024)
    RowCount = ReadCountMut(Cursor, 64)
    ColumnCount = ReadCountMut(Cursor, 64)
    ValueCount = SubdataSize(SubdataKind, RowCount, ColumnCount)
    return LoftSubdata(
        SubdataKind,
        RowCount,
        ColumnCount,
        tuple(ReadDoubleMut(Cursor) for _ in range(ValueCount)),
    )


def MakeSubdata(Value: KGrammarValue) -> tuple[KAsmToken, ...]:
    if not isinstance(Value, LoftSubdata) or len(Value.Values) != SubdataSize(
        Value.SubdataKind, Value.RowCount, Value.ColumnCount
    ):
        raise ValueError("Invalid Fusion loft section subdata")
    if any(
        type(Number) is not float or not IsFinite(Number) for Number in Value.Values
    ):
        raise ValueError("Fusion loft section subdata must be finite doubles")
    return (
        (4, Value.SubdataKind),
        (4, Value.RowCount),
        (4, Value.ColumnCount),
        *((6, Number) for Number in Value.Values),
    )
