from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the count operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitCountMut(
    Output: FeatureSink, Items: tuple[object, ...], Catalog: EntityCatalog
) -> None:
    if type(Items) is not tuple or len(Items) > KMaxCount:
        raise ValueError("Fusion recipe count exceeds the supported range")
    Catalog.Quota.TakeMany(len(Items))
    Output.AddBytes(EmitAtom(len(Items), WireType("i32")))
