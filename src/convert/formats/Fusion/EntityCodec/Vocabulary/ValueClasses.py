from convert.formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


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
