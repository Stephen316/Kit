from collections.abc import Callable
from typing import TypeAlias

from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink

# the recipe writer shape must stay shared so entity reconstruction uses one contract for compatible values
KRecipeWriter: TypeAlias = Callable[
    [FeatureSink, KRecipePayload, EntityCatalog, int], None
]
