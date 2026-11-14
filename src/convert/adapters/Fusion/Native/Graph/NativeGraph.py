from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


@MakeDataClass(frozen=True, slots=True)
class NativeGraph:
    Nodes: dict[tuple[int, int], NativeNode]
    Bases: dict[str, tuple[str, ...]]

    def Resolve(self, Value: KEntityValue, SegmentId: int = 0) -> NativeNode:
        if not isinstance(Value, (LocalRef, SegmentRef)):
            raise ValueError("Native Fusion semantic link requires an entity reference")
        TargetSegment = Value.SegmentId if isinstance(Value, SegmentRef) else SegmentId
        Target = self.Nodes.get((TargetSegment, Value.ObjectId))
        if Target is None:
            raise ValueError("Native Fusion semantic reference has no target")
        return Target

    def ResolveId(self, Value: KEntityValue, SegmentId: int = 0) -> NativeNode:
        if type(Value) is not int or (SegmentId, Value) not in self.Nodes:
            raise ValueError("Native Fusion numeric identity has no target")
        return self.Nodes[(SegmentId, Value)]

    def ByClass(self, ClassName: str, SegmentId: int = 0) -> tuple[NativeNode, ...]:
        return tuple(
            Value
            for Value in self.Nodes.values()
            if Value.SegmentId == SegmentId and Value.ClassName == ClassName
        )

    def OneClass(self, ClassName: str, SegmentId: int = 0) -> NativeNode:
        Values = self.ByClass(ClassName, SegmentId)
        if len(Values) != 1:
            raise ValueError(f"Native Fusion profile requires one {ClassName}")
        return Values[0]

    def HasBase(self, NodeValue: NativeNode, ClassName: str) -> bool:
        return ClassName in (NodeValue.ClassName, *self.Bases[NodeValue.ClassName])
