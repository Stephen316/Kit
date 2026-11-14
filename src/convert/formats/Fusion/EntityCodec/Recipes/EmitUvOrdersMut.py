from convert.formats.Fusion.EntityCodec.Recipes.EmitCountMut import EmitCountMut
from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitUvOrdersMut(
    Output: FeatureSink, Entries: tuple[UvOrderEntry, ...], Catalog: EntityCatalog
) -> None:
    if len({Entry.KeyValue for Entry in Entries}) != len(Entries):
        raise ValueError("Duplicate Fusion recipe UV-order key")
    EmitCountMut(Output, Entries, Catalog)
    for Entry in Entries:
        Order = Entry.Value
        Values = (
            Entry.KeyValue,
            Order.FaceVertexCount,
            Order.UOrder,
            Order.ULowerOrder,
            Order.UUpperOrder,
            Order.VOrder,
            Order.VLowerOrder,
            Order.VUpperOrder,
        )
        for Number in Values:
            Output.AddBytes(EmitAtom(Number, WireType("i32")))
