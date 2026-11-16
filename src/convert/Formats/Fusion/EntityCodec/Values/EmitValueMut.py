from struct import pack as PackValue

from convert.Formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.CheckReference import CheckReference
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Values.EmitPairsMut import EmitPairsMut
from convert.Formats.Fusion.EntityCodec.Values.EmitSeriesMut import EmitSeriesMut
from convert.Formats.Fusion.EntityCodec.Values.EmitGeArrayMut import EmitGeArrayMut
from convert.Formats.Fusion.EntityCodec.Values.EmitShapeMut import EmitShapeMut
from convert.Formats.Fusion.EntityCodec.Wire.AtomKinds import KAtomKinds
from convert.Formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.Formats.Fusion.EntityCodec.Wire.FlagByte import EmitFlag
from convert.Formats.Fusion.EntityCodec.Wire.EmitReference import EmitReference
from convert.Formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText


# the value operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitValueMut(
    Value: KEntityValue, Shape: WireType, Catalog: EntityCatalog, Depth: int = 0
) -> bytes:
    Catalog.Quota.TakeValue()
    if Depth >= KMaxDepth:
        raise ValueError("Fusion entity values exceed the nesting limit")
    if Shape.KindValue == "bool":
        return EmitFlag(Value)
    if Shape.KindValue in KAtomKinds:
        return EmitAtom(Value, Shape)
    if Shape.KindValue in ("ascii", "utf16") and isinstance(Value, str):
        return EmitText(Value, Shape.KindValue == "utf16")
    if Shape.KindValue == "ref":
        CheckReference(Value, Shape.ClassGuid, Catalog)
        return EmitReference(Value)
    if Shape.KindValue in ("sequence", "set", "fixed"):
        return EmitSeriesMut(Value, Shape, Catalog, Depth, EmitValueMut)
    if Shape.KindValue == "ge-array":
        return EmitGeArrayMut(Value, Shape, Catalog, Depth, EmitValueMut)
    if Shape.KindValue in ("map", "pair"):
        return EmitPairsMut(Value, Shape, Catalog, Depth, EmitValueMut)
    if Shape.KindValue == "optional":
        if Value is None:
            return PackValue("<I", 0)
        if isinstance(Value, OptionalValue):
            return PackValue("<I", 1) + EmitValueMut(
                Value.Value, Shape.Arguments[0], Catalog, Depth + 1
            )
    return EmitShapeMut(Value, Shape, Catalog, Depth, EmitValueMut)
