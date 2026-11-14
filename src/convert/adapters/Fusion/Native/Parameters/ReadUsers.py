from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContext import SketchContext
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ProjectParam
from interchange.records.RecordParameter import Parameter


def ReadUsers(Graph: NativeGraph, Context: SketchContext) -> tuple[Parameter, ...]:
    Table = ResolveField(Graph, Context.Component, "rParameterTable", "ParameterTable")
    Nodes = LinkedNodes(Graph, Table, "children")
    SameNodes(Nodes, Graph.ByClass("Parameter"))
    Catalog = {
        TextValue(NodeValue.Fields["userName"]): NodeValue for NodeValue in Nodes
    }
    if (
        len(Catalog) != len(Nodes)
        or "" in Catalog
        or Graph.ByClass("DcDoubleParameter")
    ):
        raise ValueError(
            "Native sketch-only parameters must be named independent user values"
        )
    return tuple(ProjectParam(NodeValue, Catalog, None) for NodeValue in Nodes)
