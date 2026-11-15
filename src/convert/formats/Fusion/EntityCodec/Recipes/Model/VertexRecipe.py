from dataclasses import dataclass as MakeDataClass
from typing import Generic, TypeVar

from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry

# vertex edge must remain consistent across callers so entity identifiers retain their schema and reference meaning
KVertexEdge = TypeVar("KVertexEdge", covariant=True)


# vertex recipe needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class VertexRecipe(Generic[KVertexEdge]):
    PrimaryTagIndex: int
    AdjacentFaces: tuple[FaceRecipe, ...]
    AdjacentEdges: tuple[KVertexEdge, ...]
    UvOrders: tuple[UvOrderEntry, ...]
