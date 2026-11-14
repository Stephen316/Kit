from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
    SameNodes,
    LinkedNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts


def CheckAssembly(Graph: NativeGraph, Context: KSketchContexts) -> None:
    Component = Graph.Resolve(Context.Component.Fields["rACTComponent"])
    Instance = Graph.OneClass("ComponentInstance")
    ActInstance = Graph.Resolve(Instance.Fields["rACTInstance"])
    SameNodes((Component,), Graph.ByClass("ACTComponent", Component.SegmentId))
    SameNodes((ActInstance,), Graph.ByClass("ACTInstance", Component.SegmentId))
    if (
        Graph.Resolve(Component.Fields["designComponent"], Component.SegmentId)
        != Context.Component
        or Graph.Resolve(ActInstance.Fields["designInstance"], Component.SegmentId)
        != Instance
    ):
        raise ValueError("Native assembly and Design ownership are not reciprocal")
    if (
        Graph.Resolve(ActInstance.Fields["targetComponent"], Component.SegmentId)
        != Component
    ):
        raise ValueError("Native assembly root targets another component")
    RequireFields(ActInstance, {"bSoftDeleted": False, "rParent": None})
    Instances = ResolveField(Graph, Component, "ACTInstances", "ACTInstances")
    EmptyFields(Instances, ("children", "softDeletedInstances"))
    DesignInstances = Graph.Resolve(Context.Component.Fields["rComponentBaseInstances"])
    if (
        Graph.Resolve(Instances.Fields["rDesignInstances"], Component.SegmentId)
        != DesignInstances
    ):
        raise ValueError("Native assembly instance container disagrees with Design")
    Fields = ObjectFields(ActInstance.Fields["ACTRef"])
    if Fields["crossAsset"] is not False or Fields["actRefdTable"] is not None:
        raise ValueError("Native external assembly references are not qualified")
    if Graph.Resolve(Fields["refdEntity"], Component.SegmentId) != Component:
        raise ValueError("Native assembly reference targets another component")
    Roots = Graph.OneClass("ACTComponentsRoot", Component.SegmentId)
    SameNodes((Component,), LinkedNodes(Graph, Roots, "rooted"))
