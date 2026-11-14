from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchEntity


@MakeDataClass(frozen=True, slots=True)
class RectGeometry:
    Entities: tuple[SketchEntity, ...]
    Lines: tuple[LineGeometry, ...]
    LineNodes: tuple[NativeNode, ...]
    Width: float
    Depth: float
    BasePoint: tuple[float, float, float]
