from typing import cast as CastValue

from convert.formats.Fusion.EntityCodec.Limits import KMaxDepth
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
from convert.formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.formats.Fusion.EntityCodec.Recipes.ReadUvOrdersMut import ReadUvOrdersMut
from convert.formats.Fusion.EntityCodec.Recipes.RecipeKinds import KRecipeKinds
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor


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
