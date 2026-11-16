from convert.Formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.Formats.Fusion.EntityCodec.Recipes.EmitNodesMut import EmitNodesMut
from convert.Formats.Fusion.EntityCodec.Recipes.EmitUvOrdersMut import EmitUvOrdersMut
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BaseRecipe import BaseRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BodyRecipe import BodyRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.Formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.RecipeKinds import KRecipeKinds
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the node operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitNodeMut(
    Output: FeatureSink, Value: KRecipePayload, Catalog: EntityCatalog, Depth: int
) -> None:
    if Depth >= KMaxDepth or type(Value) not in KRecipeKinds:
        raise ValueError("Unsupported or excessively nested Fusion recipe payload")
    Catalog.Quota.TakeValue()
    Output.AddBytes(EmitAtom(Value.PrimaryTagIndex, WireType("i32")))
    if isinstance(Value, BaseRecipe):
        return
    if isinstance(Value, VertexRecipe):
        EmitNodesMut(
            Output, Value.AdjacentFaces, FaceRecipe, Catalog, Depth, EmitNodeMut
        )
        EmitNodesMut(
            Output, Value.AdjacentEdges, EdgeRecipe, Catalog, Depth, EmitNodeMut
        )
        EmitUvOrdersMut(Output, Value.UvOrders, Catalog)
        return
    Output.AddBytes(EmitAtom(Value.LwdTagIndex, WireType("i32")))
    if isinstance(Value, (BodyRecipe, FaceRecipe)):
        return
    if isinstance(Value, BoundFaceRecipe):
        EmitNodesMut(Output, Value.Edges, EdgeRecipe, Catalog, Depth, EmitNodeMut)
        return
    EmitNodesMut(Output, Value.AdjacentFaces, FaceRecipe, Catalog, Depth, EmitNodeMut)
    EmitNodesMut(
        Output, Value.AdjacentVertices, VertexRecipe, Catalog, Depth, EmitNodeMut
    )
    Output.AddBytes(EmitAtom(Value.ReferenceFaceIndex, WireType("i32")))
