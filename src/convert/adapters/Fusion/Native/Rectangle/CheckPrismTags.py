from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.adapters.Fusion.Native.Rectangle.CheckSideRecipe import CheckSideRecipe
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


def CheckPrismTags(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Shape: RectGeometry,
    History: PrismHistory,
) -> None:
    Table = ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
    Labels: dict[int, str] = {}
    for PairValue in SeriesItems(Table.Fields["ProgenitorTagVec"]):
        if not isinstance(PairValue, ValuePair):
            raise ValueError("Malformed native progenitor table entry")
        Progenitor = Graph.Resolve(PairValue.First)
        if Progenitor.ClassName == "SketchCurveProgenitor":
            Recipe = ResolveField(Graph, Progenitor, "rRecipe", "SketchCurveRecipe")
            TagId = CheckSideRecipe(Recipe.Fields["profileEdgeTagData"], Shape)
            if TagId in Labels:
                raise ValueError("Duplicate native curve progenitor tag")
            Labels[TagId] = str(IntegerValue(PairValue.Second))
    Sides = SideTags(Shape)
    ExpectedFaces = (
        "1",
        "2",
        Labels[Sides[0]],
        Labels[Sides[2]],
        Labels[Sides[3]],
        Labels[Sides[1]],
    )
    Operations = (History.Identity.OperationId,)
    if History.TagSet.Faces != tuple(
        FeatureTag(Label, Operations) for Label in ExpectedFaces
    ):
        raise ValueError("Native history face tags disagree with sketch progenitors")
    if History.TagSet.Sketches != tuple(
        SketchLink(TagId, 0, 0, 1, 1) for TagId in Sides
    ):
        raise ValueError("Native history sketch tags disagree with profile edges")


def SideTags(Shape: RectGeometry) -> tuple[int, ...]:
    Result: dict[int, int] = {}
    for LineNode, Geometry in zip(Shape.LineNodes, Shape.Lines, strict=True):
        DeltaX, DeltaY = (
            Geometry.end.x - Geometry.start.x,
            Geometry.end.y - Geometry.start.y,
        )
        SideValue = (0 if DeltaX > 0 else 2) if DeltaX else (1 if DeltaY > 0 else 3)
        if SideValue in Result:
            raise ValueError("Native rectangle profile winding is inconsistent")
        Result[SideValue] = CurveTag(LineNode)
    if len(Result) != 4:
        raise ValueError("Native rectangle requires four distinct side roles")
    return tuple(Result[Index] for Index in range(4))
