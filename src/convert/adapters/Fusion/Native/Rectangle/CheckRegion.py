from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, SeriesItems
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag, SketchTag
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


def CheckRegion(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    CurveNodes: tuple[NativeNode, ...],
    AssetId: str,
) -> None:
    Profiles = LinkedNodes(Graph, Context.Extrude, "profileDataRefs")
    SameNodes(Profiles, Graph.ByClass("ModelDataRef"))
    if len(Profiles) != 1:
        raise ValueError("Native extrusion requires one profile reference")
    Regions = LinkedNodes(Graph, Profiles[0], "dataRefs")
    SameNodes(Regions, Graph.ByClass("SketchRegionRef"))
    if len(Regions) != 1:
        raise ValueError("Native extrusion requires one sketch region")
    Region = Regions[0]
    Scope = ObjectFields(Region.Fields["rScope"])
    if Scope != {
        "assetId": AssetId,
        "scopeEntityIdentifier": str(Context.Sketch.ObjectId),
        "scopeIdType": 1,
        "segmentId": Context.Sketch.SegmentId,
    }:
        raise ValueError("Native extrusion profile scope disagrees with its sketch")
    Recipe = ResolveField(Graph, Region, "rRecipe", "SketchRegionRecipe")
    if Graph.Resolve(Recipe.Fields["rSketchRegionRef"]) != Region:
        raise ValueError("Native sketch region recipe link is not reciprocal")
    Recipes = SeriesItems(Recipe.Fields["skRegionRecipe"])
    if len(Recipes) != 1:
        raise ValueError("Native extrusion requires one sketch region recipe")
    Fields = ObjectFields(Recipes[0])
    Loops = SeriesItems(Fields["faceRecipe"])
    if (
        SeriesItems(Fields["originalFaceRecipes"])
        or len(Loops) != 1
        or not isinstance(Loops[0], ValuePair)
        or Loops[0].Second is not True
    ):
        raise ValueError("Native extrusion requires one positive profile loop")
    TagValues = tuple(SketchTag(Value, 0) for Value in SeriesItems(Loops[0].First))
    if sorted(TagValues) != sorted(CurveTag(NodeValue) for NodeValue in CurveNodes):
        raise ValueError("Native region recipe does not consume the sketch profile")
