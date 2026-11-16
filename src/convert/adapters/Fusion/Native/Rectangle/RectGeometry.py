from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity


# rect geometry needs an explicit state contract so public document claims remain grounded in native records
@MakeDataClass(frozen=True, slots=True)
class RectGeometry:
    Entities: tuple[SketchEntity, ...]
    Lines: tuple[LineGeometry, ...]
    LineNodes: tuple[NativeNode, ...]
    Width: float
    Depth: float
    BasePoint: tuple[float, float, float]
