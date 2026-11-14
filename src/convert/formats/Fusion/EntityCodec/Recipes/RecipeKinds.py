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

KRecipeKinds: dict[type[KRecipePayload], str] = {
    BaseRecipe: "base_recipe_data",
    BodyRecipe: "body_recipe_data",
    FaceRecipe: "face_recipe_data",
    BoundFaceRecipe: "bounded_face_recipe_data",
    EdgeRecipe: "edge_recipe_data",
    VertexRecipe: "vertex_recipe_data",
}
