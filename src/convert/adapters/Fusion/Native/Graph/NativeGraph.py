from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# native graph needs an explicit state contract so public document claims remain grounded in native records
@MakeDataClass(frozen=True, slots=True)
class NativeGraph:
    Nodes: dict[tuple[int, int], NativeNode]
    Bases: dict[str, tuple[str, ...]]

    # resolve needs an explicit validity boundary so public document claims remain grounded in native records
    def Resolve(self, Value: KEntityValue, SegmentId: int = 0) -> NativeNode:
        if not isinstance(Value, (LocalRef, SegmentRef)):
            raise ValueError("Native Fusion semantic link requires an entity reference")
        TargetSegment = Value.SegmentId if isinstance(Value, SegmentRef) else SegmentId
        Target = self.Nodes.get((TargetSegment, Value.ObjectId))
        if Target is None:
            raise ValueError("Native Fusion semantic reference has no target")
        return Target

    # resolve id needs an explicit validity boundary so public document claims remain grounded in native records
    def ResolveId(self, Value: KEntityValue, SegmentId: int = 0) -> NativeNode:
        if type(Value) is not int or (SegmentId, Value) not in self.Nodes:
            raise ValueError("Native Fusion numeric identity has no target")
        return self.Nodes[(SegmentId, Value)]

    # the by class contract needs a shared interpretation so public document claims remain grounded in native records
    def ByClass(self, ClassName: str, SegmentId: int = 0) -> tuple[NativeNode, ...]:
        return tuple(
            Value
            for Value in self.Nodes.values()
            if Value.SegmentId == SegmentId and Value.ClassName == ClassName
        )

    # one class needs an explicit validity boundary so public document claims remain grounded in native records
    def OneClass(self, ClassName: str, SegmentId: int = 0) -> NativeNode:
        Values = self.ByClass(ClassName, SegmentId)
        if len(Values) != 1:
            raise ValueError(f"Native Fusion profile requires one {ClassName}")
        return Values[0]

    # the base decision must stay consistent so public document claims remain grounded in native records
    def HasBase(self, NodeValue: NativeNode, ClassName: str) -> bool:
        return ClassName in (NodeValue.ClassName, *self.Bases[NodeValue.ClassName])
