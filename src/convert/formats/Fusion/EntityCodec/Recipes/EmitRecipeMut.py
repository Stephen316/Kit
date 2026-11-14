from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Recipes.EmitNodeMut import EmitNodeMut
from convert.formats.Fusion.EntityCodec.Recipes.EmitTagsMut import EmitTagsMut
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.EntityCodec.Recipes.RecipeKinds import KRecipeKinds
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitRecipeMut(Value: KEntityValue, Catalog: EntityCatalog, Depth: int) -> bytes:
    if (
        not isinstance(Value, RecipeValue)
        or Value.Version != 3
        or type(Value.Payload) not in KRecipeKinds
    ):
        raise ValueError("Only typed Fusion ASM recipe version three is qualified")
    Output = FeatureSink()
    Output.AddBytes(EmitAtom(Value.Version, WireType("i32")))
    EmitTagsMut(Output, Value.Tags, Catalog)
    EmitTagsMut(Output, Value.LwdTags, Catalog)
    KindValue = KRecipeKinds[type(Value.Payload)].encode("ascii")
    Catalog.Quota.TakeMany(len(KindValue))
    Output.AddBytes(EmitAtom(len(KindValue), WireType("i32")))
    Output.AddBytes(KindValue)
    EmitNodeMut(Output, Value.Payload, Catalog, Depth + 1)
    return bytes(Output.Buffer)
