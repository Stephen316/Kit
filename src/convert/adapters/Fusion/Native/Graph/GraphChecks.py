from math import isclose as IsClose

from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap


# invalid fields input must fail here so public document claims remain grounded in native records
def RequireFields(NodeValue: NativeNode, Values: dict[str, KEntityValue]) -> None:
    for NameValue, Expected in Values.items():
        if NodeValue.Fields.get(NameValue) != Expected:
            raise ValueError(
                f"Unsupported native Fusion {NodeValue.ClassName}.{NameValue}"
            )


# empty fields needs an explicit validity boundary so public document claims remain grounded in native records
def EmptyFields(NodeValue: NativeNode, Names: tuple[str, ...]) -> None:
    for NameValue in Names:
        Value = NodeValue.Fields[NameValue]
        if Value.Entries if isinstance(Value, ValueMap) else SeriesItems(Value):
            raise ValueError(f"Unsupported populated native Fusion {NameValue}")


# resolve field needs an explicit validity boundary so public document claims remain grounded in native records
def ResolveField(
    Graph: NativeGraph, NodeValue: NativeNode, FieldName: str, ClassName: str
) -> NativeNode:
    Target = Graph.Resolve(NodeValue.Fields[FieldName], NodeValue.SegmentId)
    if Target.ClassName != ClassName:
        raise ValueError(f"Native Fusion {FieldName} references an incompatible class")
    return Target


# linked nodes must resolve unambiguously so public document claims remain grounded in native records
def LinkedNodes(
    Graph: NativeGraph, NodeValue: NativeNode, FieldName: str
) -> tuple[NativeNode, ...]:
    return tuple(
        Graph.Resolve(Value, NodeValue.SegmentId)
        for Value in SeriesItems(NodeValue.Fields[FieldName])
    )


# same nodes needs an explicit validity boundary so public document claims remain grounded in native records
def SameNodes(Actual: tuple[NativeNode, ...], Expected: tuple[NativeNode, ...]) -> None:
    if sorted(NodeValue.Identity for NodeValue in Actual) != sorted(
        NodeValue.Identity for NodeValue in Expected
    ):
        raise ValueError(
            "Native Fusion ownership collection disagrees with its semantic graph"
        )


# same numbers needs an explicit validity boundary so public document claims remain grounded in native records
def SameNumbers(Actual: tuple[float, ...], Expected: tuple[float, ...]) -> None:
    if len(Actual) != len(Expected) or any(
        not IsClose(First, Second, rel_tol=1e-10, abs_tol=1e-9)
        for First, Second in zip(Actual, Expected, strict=True)
    ):
        raise ValueError("Native Fusion saved geometry or parameter values disagree")
