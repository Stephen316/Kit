from typing import cast as CastValue

from convert.Formats.Fusion.EntityCodec.Limits import KMaxDepth
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
from convert.Formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.Formats.Fusion.EntityCodec.Recipes.ReadUvOrdersMut import ReadUvOrdersMut
from convert.Formats.Fusion.EntityCodec.Recipes.RecipeKinds import KRecipeKinds
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the node operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadNodeMut(
    Cursor: MetaCursor, KindValue: str, Catalog: EntityCatalog, Depth: int
) -> KRecipePayload:
    if Depth >= KMaxDepth or KindValue not in KRecipeKinds.values():
        raise ValueError("Unsupported or excessively nested Fusion recipe payload")
    Catalog.Quota.TakeValue()
    Primary = int(ReadAtomMut(Cursor, WireType("i32")))
    if KindValue == "base_recipe_data":
        return BaseRecipe(Primary)
    if KindValue == "vertex_recipe_data":
        Faces = tuple(
            CastValue(
                FaceRecipe, ReadNodeMut(Cursor, "face_recipe_data", Catalog, Depth + 1)
            )
            for _ in range(ReadCountMut(Cursor, Catalog))
        )
        Edges = tuple(
            CastValue(
                EdgeRecipe, ReadNodeMut(Cursor, "edge_recipe_data", Catalog, Depth + 1)
            )
            for _ in range(ReadCountMut(Cursor, Catalog))
        )
        return VertexRecipe(Primary, Faces, Edges, ReadUvOrdersMut(Cursor, Catalog))
    LwdIndex = int(ReadAtomMut(Cursor, WireType("i32")))
    if KindValue == "body_recipe_data":
        return BodyRecipe(Primary, LwdIndex)
    if KindValue == "face_recipe_data":
        return FaceRecipe(Primary, LwdIndex)
    if KindValue == "bounded_face_recipe_data":
        Edges = tuple(
            CastValue(
                EdgeRecipe, ReadNodeMut(Cursor, "edge_recipe_data", Catalog, Depth + 1)
            )
            for _ in range(ReadCountMut(Cursor, Catalog))
        )
        return BoundFaceRecipe(Primary, LwdIndex, Edges)
    Faces = tuple(
        CastValue(
            FaceRecipe, ReadNodeMut(Cursor, "face_recipe_data", Catalog, Depth + 1)
        )
        for _ in range(ReadCountMut(Cursor, Catalog))
    )
    Vertices = tuple(
        CastValue(
            VertexRecipe[EdgeRecipe],
            ReadNodeMut(Cursor, "vertex_recipe_data", Catalog, Depth + 1),
        )
        for _ in range(ReadCountMut(Cursor, Catalog))
    )
    return EdgeRecipe(
        Primary, LwdIndex, Faces, Vertices, int(ReadAtomMut(Cursor, WireType("i32")))
    )
