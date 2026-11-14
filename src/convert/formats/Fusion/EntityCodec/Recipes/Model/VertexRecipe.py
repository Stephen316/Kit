from dataclasses import dataclass as MakeDataClass
from typing import Generic, TypeVar

from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry

KVertexEdge = TypeVar("KVertexEdge", covariant=True)


@MakeDataClass(frozen=True, slots=True)
class VertexRecipe(Generic[KVertexEdge]):
    PrimaryTagIndex: int
    AdjacentFaces: tuple[FaceRecipe, ...]
    AdjacentEdges: tuple[KVertexEdge, ...]
    UvOrders: tuple[UvOrderEntry, ...]
