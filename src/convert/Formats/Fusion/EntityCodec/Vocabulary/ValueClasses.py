from convert.Formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType


# value classes needs an explicit validity boundary so entity identifiers retain their schema and reference meaning
def ValueClasses(Shape: WireType, Depth: int = 0) -> tuple[str, ...]:
    if Depth >= KMaxDepth:
        raise ValueError("Fusion native value schema exceeds the depth limit")
    Current = (Shape.ClassGuid,) if Shape.KindValue == "object" else ()
    Arguments = tuple(
        Identity
        for Argument in Shape.Arguments
        for Identity in ValueClasses(Argument, Depth + 1)
    )
    Members = tuple(
        Identity
        for Field in Shape.Members
        for Identity in ValueClasses(Field.ValueType, Depth + 1)
    )
    return Current + Arguments + Members
