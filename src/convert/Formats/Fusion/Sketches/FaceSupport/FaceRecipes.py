from typing import TypeAlias

from convert.Formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipePayload import (
    KRecipePayload,
)
from convert.Formats.Fusion.EntityCodec.Recipes.ReadNodeMut import ReadNodeMut
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.RecipeRead import KRecipeGuid, ReadRecipe

# within recipe indices must resolve to ordered names before separate recipes can be compared
KEdgeNames: TypeAlias = tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]


# the target body recipe corroborates the scope of every named face operand
def ReadScopedNode(
    Cursor: MetaCursor, BodyName: str, KindValue: str, Count: int, SizeValue: int
) -> tuple[tuple[str, ...], KRecipePayload]:
    if (
        len(Cursor.DataValue) > 1024
        or not BodyName.isascii()
        or not BodyName.isdecimal()
    ):
        raise ValueError("Unsupported Fusion sketch support recipe scope")
    RecipeKind, Groups, Payload = ReadRecipe(Cursor)
    if RecipeKind != KindValue or len(Groups) != Count or len(Payload) != SizeValue:
        raise ValueError("Unsupported Fusion sketch support recipe framing")
    Names: list[str] = []
    for Group in Groups:
        if len(Group) != 1 or Group[0][1:] != (0, (int(BodyName),)):
            raise ValueError("Fusion face recipe operand belongs to another body scope")
        Names.append(Group[0][0])
    if len(set(Names)) != Count:
        raise ValueError("Fusion sketch support recipe names are ambiguous")
    NodeWire = MetaCursor(Payload)
    Catalog = EntityCatalog(KRecipeGuid, {}, {}, {}, {})
    NodeValue = ReadNodeMut(NodeWire, KindValue, Catalog, 0)
    if NodeWire.Offset != len(Payload):
        raise ValueError("Fusion sketch support recipe has trailing operands")
    return tuple(Names), NodeValue


# every face name must be a direct indexed operand in the current recipe table
def FaceName(Names: tuple[str, ...], FaceValue: FaceRecipe | BoundFaceRecipe) -> str:
    Index = FaceValue.PrimaryTagIndex
    if FaceValue.LwdTagIndex != -1 or not 0 <= Index < len(Names):
        raise ValueError("Unsupported Fusion sketch support face operand")
    return Names[Index]


# explicit adjacent faces and ordered vertices distinguish boundaries with similar geometry
def EdgeNames(Names: tuple[str, ...], EdgeValue: EdgeRecipe) -> KEdgeNames:
    if (
        (EdgeValue.PrimaryTagIndex, EdgeValue.LwdTagIndex, EdgeValue.ReferenceFaceIndex)
        != (-1, -1, -1)
        or len(EdgeValue.AdjacentFaces) != 2
        or len(EdgeValue.AdjacentVertices) != 2
    ):
        raise ValueError("Unsupported Fusion sketch support edge operand")
    Faces = tuple(FaceName(Names, Value) for Value in EdgeValue.AdjacentFaces)
    Vertices: list[tuple[str, ...]] = []
    for Vertex in EdgeValue.AdjacentVertices:
        if Vertex.PrimaryTagIndex != -1 or Vertex.AdjacentEdges or Vertex.UvOrders:
            raise ValueError("Unsupported Fusion sketch support vertex operand")
        VertexNames = tuple(FaceName(Names, Value) for Value in Vertex.AdjacentFaces)
        if (
            len(set(VertexNames)) != len(VertexNames)
            or len(VertexNames) != 3
            or not set(Faces) <= set(VertexNames)
        ):
            raise ValueError("Fusion sketch support edge and vertex operands disagree")
        Vertices.append(VertexNames)
    if len(set(Faces)) != 2 or set(Vertices[0]) == set(Vertices[1]):
        raise ValueError("Fusion sketch support edge operands are ambiguous")
    return Faces, tuple(Vertices)


# the selected face must bind a complete four side perimeter in its saved naming scope
def ReadFaceEdges(
    Cursor: MetaCursor, BodyName: str
) -> tuple[str, frozenset[KEdgeNames]]:
    Names, NodeValue = ReadScopedNode(
        Cursor, BodyName, "bounded_face_recipe_data", 5, 476
    )
    if not isinstance(NodeValue, BoundFaceRecipe) or len(NodeValue.Edges) != 4:
        raise ValueError("Fusion sketch support requires a bounded four edge face")
    Selected = FaceName(Names, NodeValue)
    Edges = frozenset(EdgeNames(Names, EdgeValue) for EdgeValue in NodeValue.Edges)
    if (
        len(Edges) != 4
        or any(Selected not in FacePair for FacePair, _ in Edges)
        or {NameValue for FacePair, _ in Edges for NameValue in FacePair} != set(Names)
    ):
        raise ValueError("Fusion face recipe does not exhaust its named boundary")
    return Selected, Edges
