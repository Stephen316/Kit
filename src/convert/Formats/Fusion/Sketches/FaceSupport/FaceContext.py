from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.SelectionRef import ReadSelectUuid
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipes import (
    EdgeNames,
    KEdgeNames,
    ReadScopedNode,
)
from convert.Formats.Fusion.Topology.BodyPickContext import KBodyContext
from convert.Formats.Fusion.Topology.RecipeRead import KRecipeGuid

# the boundary context connects a local geometry witness to its named edge recipe
KFaceContext = "50AEE8B4-9456-4DD7-847D-6F6C909BBB9D"

# this naming record carries a recipe rather than a direct geometric object identity
KFaceEdgeLeaf = "4B31DA1B-FCD6-4527-BC3E-BE1FBAF867FE"


# the same typed naming link preserves source and projected recipe ownership
def ReadEdgeLeaf(BulkData: bytes, Owners: dict[int, RecordSpan], LeafId: int) -> int:
    LeafWire = SelectCursor(BulkData, Owners, LeafId, KFaceEdgeLeaf)
    if len(LeafWire.DataValue) != 18 or LeafWire.TakeBytes(6) != b"\0\1" + bytes(4):
        raise ValueError("Unsupported Fusion sketch support naming leaf")
    RecipeId = ReadNativeRef(LeafWire)
    if LeafWire.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion sketch support naming leaf trailer")
    return RecipeId


# both explicit context links must name the same edge recipe in the descriptor namespace
def ReadContextEdge(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ContextId: int,
    Namespace: str,
    EntityGuid: str,
    BodyName: str,
) -> tuple[int, KEdgeNames]:
    Cursor = SelectCursor(BulkData, Owners, ContextId, KFaceContext)
    if (
        len(Cursor.DataValue) != 75
        or Cursor.TakeBytes(2) != bytes(2)
        or not all(map(IsFinite, Unpack("<6d", Cursor.TakeBytes(48))))
        or Cursor.TakeBytes(1) != bytes(1)
    ):
        raise ValueError("Unsupported Fusion sketch support edge context")
    OwnerId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(2) != b"\0\1":
        raise ValueError("Unsupported Fusion sketch support context naming marker")
    LeafId = ReadNativeRef(Cursor)
    Owner = SelectCursor(BulkData, Owners, OwnerId, KBodyContext)
    if len(Owner.DataValue) != 181 or Owner.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion sketch support body context")
    _ = Owner.ReadLong()
    if (
        ReadSelectUuid(Owner) != Namespace
        or ReadSelectUuid(Owner) != EntityGuid
        or Owner.ReadLong() != 2
        or ReadNativeRef(Owner) != LeafId
    ):
        raise ValueError("Fusion sketch support context name or owner disagrees")
    RecipeId = ReadEdgeLeaf(BulkData, Owners, LeafId)
    Recipe = SelectCursor(BulkData, Owners, RecipeId, KRecipeGuid)
    Names, NodeValue = ReadScopedNode(Recipe, BodyName, "edge_recipe_data", 4, 116)
    if not isinstance(NodeValue, EdgeRecipe):
        raise ValueError("Fusion sketch support context lacks an edge recipe")
    return RecipeId, EdgeNames(Names, NodeValue)
