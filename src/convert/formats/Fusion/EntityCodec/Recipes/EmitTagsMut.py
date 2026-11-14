from convert.formats.Fusion.EntityCodec.Recipes.EmitCountMut import EmitCountMut
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitTagsMut(
    Output: FeatureSink,
    Groups: tuple[tuple[RecipeTag, ...], ...],
    Catalog: EntityCatalog,
) -> None:
    EmitCountMut(Output, Groups, Catalog)
    for TagRows in Groups:
        EmitCountMut(Output, TagRows, Catalog)
        for Entry in TagRows:
            EmitCountMut(Output, Entry.PrimaryId, Catalog)
            for Number in Entry.PrimaryId:
                Output.AddBytes(EmitAtom(Number, WireType("u8")))
            Output.AddBytes(EmitAtom(Entry.SecondaryId, WireType("i32")))
            EmitCountMut(Output, Entry.OperationIds, Catalog)
            for Number in Entry.OperationIds:
                Output.AddBytes(EmitAtom(Number, WireType("i32")))
            Output.AddBytes(EmitAtom(Entry.ApproachId, WireType("i32")))
