from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)


# the leaf operation needs a distinct decoding boundary so nested geometry retains unambiguous record boundaries
def ReadLeafMut(Cursor: FieldCursor, LeafKind: str) -> KGrammarValue:
    if LeafKind == "flag":
        return IsLogicalMut(Cursor)
    if LeafKind == "bound":
        return ReadBoundMut(Cursor)
    if LeafKind == "real":
        return ReadDoubleMut(Cursor)
    if LeafKind == "int":
        return ReadLongMut(Cursor)
    if LeafKind == "enum":
        return ReadLongMut(Cursor, 21)
    if LeafKind == "text":
        return ReadTextMut(Cursor)
    if LeafKind == "point":
        return ReadVectorMut(Cursor, 19)
    if LeafKind == "vector":
        return ReadVectorMut(Cursor, 20)
    raise ValueError("Unsupported Fusion grammar leaf kind: " + LeafKind)
