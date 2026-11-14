from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag, SketchTag
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


def CheckRoundTags(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Shape: CircleShape,
    OperationId: int,
    Actual: TopologyTags,
) -> None:
    Table = ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
    Pairs = SeriesItems(Table.Fields["ProgenitorTagVec"])
    Curves = tuple(
        PairValue
        for PairValue in Pairs
        if isinstance(PairValue, ValuePair)
        and Graph.Resolve(PairValue.First).ClassName == "SketchCurveProgenitor"
    )
    if len(Curves) != 1:
        raise ValueError("Native circular extrusion requires one side progenitor")
    Recipe = ResolveField(
        Graph, Graph.Resolve(Curves[0].First), "rRecipe", "SketchCurveRecipe"
    )
    Fields = ObjectFields(Recipe.Fields["profileEdgeTagData"])
    if Fields["version"] != 0:
        raise ValueError("Unsupported native circular progenitor recipe version")
    TagValues = SeriesItems(Fields["sketchTags"])
    Primary = CurveTag(Shape.CurveNode)
    if (
        len(TagValues) != 1
        or SketchTag(TagValues[0], 1) != Primary
        or SeriesItems(Fields["startAdjacentPrimaryTagIds"])
        or SeriesItems(Fields["endAdjacentPrimaryTagIds"])
    ):
        raise ValueError(
            "Native circle progenitor recipe disagrees with the full-circle profile"
        )
    Operations = (OperationId,)
    Expected = TopologyTags(
        FeatureTag(str(IntegerValue(Curves[0].Second)), Operations),
        FeatureTag("2", Operations),
        FeatureTag("1", Operations),
        FeatureTag("-1", Operations),
        FeatureTag("-" + str(Primary), Operations),
        SketchLink(Primary, 0, 0, 1, 1),
    )
    if Actual != Expected:
        raise ValueError(
            "Native circular history topology tags disagree with feature progenitors"
        )
