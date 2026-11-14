from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Policy.CheckClasses import CheckClasses
from convert.adapters.Fusion.Native.Policy.CheckAssembly import CheckAssembly
from convert.adapters.Fusion.Native.Policy.CheckContainers import CheckContainers
from convert.adapters.Fusion.Native.Policy.CheckExtrusion import CheckExtrusion
from convert.adapters.Fusion.Native.Policy.CheckFeature import CheckFeature
from convert.adapters.Fusion.Native.Policy.CheckPlacement import CheckPlacement
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory


def CheckBase(Graph: NativeGraph, Context: KSketchContexts) -> None:
    CheckClasses(Graph)
    CheckAssembly(Graph, Context)
    CheckContainers(Graph, Context)
    CheckPlacement(Graph, Context)
    CheckFeature(Graph, Context.SketchFeature)
    Overrides = ObjectFields(Context.Component.Fields["massProperties"])
    if any(Value != -1.0 for Value in Overrides.values()):
        raise ValueError("Native component mass-property overrides are not qualified")


def CheckGraph(Graph: NativeGraph, Context: ExtrudeContext) -> None:
    CheckBase(Graph, Context)
    CheckFeature(Graph, Context.Extrude)
    CheckExtrusion(Graph, Context)
    Overrides = ObjectFields(Context.BodyNode.Fields["massProperties"])
    if any(Value != -1.0 for Value in Overrides.values()):
        raise ValueError("Native body mass-property overrides are not qualified")
    EmptyFields(Context.BodyNode, ("faceVisualMaterialByAttrTagID",))
    RequireFields(Context.DcBody, {"isEliminated": False})


def CheckShape(
    Context: ExtrudeContext, Shape: RectGeometry, History: PrismHistory
) -> None:
    Height = NumberValue(Context.Along.Fields["value"]) * 10
    Model = History.Model
    SameNumbers(
        (Model.Width, Model.Depth, Model.Height, *Model.BasePoint),
        (Shape.Width, Shape.Depth, Height, *Shape.BasePoint),
    )
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
    Volume = Shape.Width * Shape.Depth * Height / 1000
    AreaValue = (
        2 * (Shape.Width * Shape.Depth + (Shape.Width + Shape.Depth) * Height) / 100
    )
    SameNumbers(
        (NumberValue(Cache["volume"]), NumberValue(Cache["area"])), (Volume, AreaValue)
    )
    SameNumbers(
        PointCoords(Cache["cog"]),
        (
            (Shape.BasePoint[0] + Shape.Width / 2) / 10,
            (Shape.BasePoint[1] + Shape.Depth / 2) / 10,
            (Shape.BasePoint[2] + Height / 2) / 10,
        ),
    )
