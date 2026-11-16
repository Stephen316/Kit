from convert.Formats.Fusion.EntityCodec.Frame.NamedKinds import KNamedKinds
from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Schema.NamedType import NamedType
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText


# named types needs an explicit validity boundary so entity identifiers retain their schema and reference meaning
def NamedTypes(Entries: tuple[NamedType, ...]) -> dict[str, WireType]:
    if len(Entries) > KMaxCount or len({Entry.TypeName for Entry in Entries}) != len(
        Entries
    ):
        raise ValueError("Duplicate or oversized Fusion named metatype declarations")
    Result = dict(KNamedKinds)
    for Entry in Entries:
        if not Entry.TypeName or not EmitText(Entry.TypeName):
            raise ValueError("Fusion named metatype requires an identifier")
        if (
            Entry.TypeName in KNamedKinds
            and Entry.ValueType != KNamedKinds[Entry.TypeName]
        ):
            raise ValueError("Fusion named intrinsic metatype cannot be redefined")
        Result[Entry.TypeName] = Entry.ValueType
    return Result
