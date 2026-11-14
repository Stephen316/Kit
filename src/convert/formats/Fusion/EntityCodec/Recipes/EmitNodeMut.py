from convert.formats.Fusion.EntityCodec.Limits import KMaxDepth
from convert.formats.Fusion.EntityCodec.Recipes.EmitNodesMut import EmitNodesMut
from convert.formats.Fusion.EntityCodec.Recipes.EmitUvOrdersMut import EmitUvOrdersMut
from convert.formats.Fusion.EntityCodec.Recipes.Model.BaseRecipe import BaseRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.BodyRecipe import BodyRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe
from convert.formats.Fusion.EntityCodec.Recipes.RecipeKinds import KRecipeKinds
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


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
