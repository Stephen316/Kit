from dataclasses import replace as Replace

from convert.Formats.Fusion.Extrudes.Plane.PlanePickSupport import CheckPickLinks
from convert.Formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.Sketches.FaceSupport.FaceContext import ReadContextEdge
from convert.Formats.Fusion.Sketches.FaceSupport.FaceDescriptor import ReadFaceDesc
from convert.Formats.Fusion.Sketches.FaceSupport.FaceOwner import ReadFaceOwner
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipes import ReadFaceEdges
from convert.Formats.Fusion.Topology.BodyAnchor import ReadBodyAnchor
from convert.Formats.Fusion.Topology.BodyRecipe import ReadBodyRecipe
from convert.Formats.Fusion.Topology.RecipeRead import KRecipeGuid
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Selection import Selection


# separately selected cut and sketch operands must agree on the historical body and creator
def MakeFacePick(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchId: int, Target: Selection
) -> FaceRecipePick:
    BodyId = Target.query.get("native_body_id")
    SourceId = Target.query.get("native_source_id")
    BodyRecipe = Target.attributes.get("fusion.recipe_object_id")
    if (
        type(BodyId) is not int
        or type(SourceId) is not int
        or type(BodyRecipe) is not int
    ):
        raise ValueError("Fusion sketch support lacks a typed historical Cut target")
    FeatureId, ProxyId, DescriptorId = ReadFaceOwner(BulkData, Owners, SketchId, BodyId)
    FaceValue = ReadFaceDesc(BulkData, Owners, DescriptorId, FeatureId)
    if FaceValue.AnchorId != Target.query.get("native_anchor_id") or ReadBodyAnchor(
        BulkData, Owners, FaceValue.AnchorId
    ) != (BodyId, SourceId):
        raise ValueError("Fusion sketch support and Cut target anchors disagree")
    CheckPickLinks(BulkData, Owners, FaceValue.SupportId, DescriptorId, (SourceId,))
    BodyName = ReadBodyRecipe(BulkData, Owners, BodyRecipe)
    Recipe = SelectCursor(BulkData, Owners, FaceValue.RecipeId, KRecipeGuid)
    FaceName, Perimeter = ReadFaceEdges(Recipe, BodyName)
    Contexts = tuple(
        ReadContextEdge(
            BulkData,
            Owners,
            ContextId,
            FaceValue.Namespace,
            FaceValue.EntityGuid,
            BodyName,
        )
        for ContextId in FaceValue.ContextIds
    )
    if (
        len({Identity for Identity, _ in Contexts}) != 4
        or frozenset(EdgeValue for _, EdgeValue in Contexts) != Perimeter
    ):
        raise ValueError(
            "Fusion sketch support contexts do not match the face boundary"
        )
    RecipeIds = tuple(Identity for Identity, _ in Contexts)
    Origin = RecordOrigin(Owners[DescriptorId])
    Records = (
        SketchId,
        FeatureId,
        ProxyId,
        FaceValue.SupportId,
        FaceValue.RecipeId,
        FaceValue.AnchorId,
        *FaceValue.ContextIds,
        *RecipeIds,
    )
    SelectionValue = Selection(
        id=f"fusion-historical-face-{SketchId}-{DescriptorId}",
        name=f"Historical face recipe {FaceName}",
        path=(),
        query=FreezeMapping(
            {
                **Target.query,
                "kind": "historical_face_recipe",
                "role": "sketch_support",
                "native_face_name": FaceName,
            }
        ),
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + tuple(
                SpanValue
                for Identity in Records
                for SpanValue in RecordOrigin(Owners[Identity]).spans
            ),
        ),
        attributes=FreezeMapping(
            {
                "fusion.proxy_object_id": ProxyId,
                "fusion.descriptor_object_id": DescriptorId,
                "fusion.support_object_id": FaceValue.SupportId,
                "fusion.recipe_object_id": FaceValue.RecipeId,
                "fusion.context_object_ids": FaceValue.ContextIds,
                "fusion.edge_recipe_object_ids": RecipeIds,
            }
        ),
    )
    ContextEdges = tuple(
        (ContextId, RecipeId, EdgeValue)
        for ContextId, (RecipeId, EdgeValue) in zip(
            FaceValue.ContextIds, Contexts, strict=True
        )
    )
    return FaceRecipePick(SelectionValue, BodyName, FaceName, Perimeter, ContextEdges)
