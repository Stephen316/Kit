from convert.Formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.CheckReference import CheckReference
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Values.ReadPairsMut import ReadPairsMut
from convert.Formats.Fusion.EntityCodec.Values.ReadSeriesMut import ReadSeriesMut
from convert.Formats.Fusion.EntityCodec.Values.ReadGeArrayMut import ReadGeArrayMut
from convert.Formats.Fusion.EntityCodec.Values.ReadShapeMut import ReadShapeMut
from convert.Formats.Fusion.EntityCodec.Wire.AtomKinds import KAtomKinds
from convert.Formats.Fusion.EntityCodec.Wire.FlagByte import ReadFlagMut
from convert.Formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.Formats.Fusion.EntityCodec.Wire.ReadRefMut import ReadRefMut
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText


# the value operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadValueMut(
    Cursor: MetaCursor, Shape: WireType, Catalog: EntityCatalog, Depth: int = 0
) -> KEntityValue:
    Catalog.Quota.TakeValue()
    if Depth >= KMaxDepth:
        raise ValueError("Fusion entity values exceed the nesting limit")
    if Shape.KindValue == "bool":
        return ReadFlagMut(Cursor)
    if Shape.KindValue in KAtomKinds:
        return ReadAtomMut(Cursor, Shape)
    if Shape.KindValue in ("ascii", "utf16"):
        IsWide = Shape.KindValue == "utf16"
        return Cursor.ReadText(IsWide, Maximum=KMaxFeatureText, AllowControls=IsWide)
    if Shape.KindValue == "ref":
        Target = ReadRefMut(Cursor)
        CheckReference(Target, Shape.ClassGuid, Catalog)
        return Target
    if Shape.KindValue in ("sequence", "set", "fixed"):
        return ReadSeriesMut(Cursor, Shape, Catalog, Depth, ReadValueMut)
    if Shape.KindValue == "ge-array":
        return ReadGeArrayMut(Cursor, Shape, Catalog, Depth, ReadValueMut)
    if Shape.KindValue in ("map", "pair"):
        return ReadPairsMut(Cursor, Shape, Catalog, Depth, ReadValueMut)
    if Shape.KindValue == "optional":
        return (
            None
            if not Cursor.ReadCount(1)
            else OptionalValue(
                ReadValueMut(Cursor, Shape.Arguments[0], Catalog, Depth + 1)
            )
        )
    return ReadShapeMut(Cursor, Shape, Catalog, Depth, ReadValueMut)
