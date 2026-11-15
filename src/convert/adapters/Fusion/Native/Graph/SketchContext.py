from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# sketch context needs an explicit state contract so public document claims remain grounded in native records
@MakeDataClass(frozen=True, slots=True)
class SketchContext:
    Component: NativeNode
    Fragment: NativeNode
    SketchFeature: NativeNode
    Sketch: NativeNode
    Plane: NativeNode
