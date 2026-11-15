from collections.abc import Callable
from typing import TypeAlias

from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink

# the recipe writer shape must stay shared so entity reconstruction uses one contract for compatible values
KRecipeWriter: TypeAlias = Callable[
    [FeatureSink, KRecipePayload, EntityCatalog, int], None
]
