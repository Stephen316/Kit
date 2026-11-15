from typing import TypeAlias

from convert.formats.Fusion.EntityCodec.Recipes.Model.BaseRecipe import BaseRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.BodyRecipe import BodyRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe

# the recipe payload variants need one shared contract so entity reconstruction cannot omit a supported value shape
KRecipePayload: TypeAlias = (  # lgtm[py/unused-global-variable]
    BaseRecipe
    | BodyRecipe
    | FaceRecipe
    | BoundFaceRecipe
    | EdgeRecipe
    | VertexRecipe[EdgeRecipe]
)
