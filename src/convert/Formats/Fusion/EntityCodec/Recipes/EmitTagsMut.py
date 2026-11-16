from convert.Formats.Fusion.EntityCodec.Recipes.EmitCountMut import EmitCountMut
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the tags operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
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
