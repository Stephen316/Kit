from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# extrude context needs an explicit state contract so public document claims remain grounded in native records
@MakeDataClass(frozen=True, slots=True)
class ExtrudeContext:
    Component: NativeNode
    Fragment: NativeNode
    SketchFeature: NativeNode
    Sketch: NativeNode
    Plane: NativeNode
    Extrude: NativeNode
    Along: NativeNode
    Taper: NativeNode
    BodyNode: NativeNode
    DcBody: NativeNode
