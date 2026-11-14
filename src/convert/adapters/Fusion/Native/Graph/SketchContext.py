from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


@MakeDataClass(frozen=True, slots=True)
class SketchContext:
    Component: NativeNode
    Fragment: NativeNode
    SketchFeature: NativeNode
    Sketch: NativeNode
    Plane: NativeNode
