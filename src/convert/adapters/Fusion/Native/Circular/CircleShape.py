from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Sketch import SketchEntity


@MakeDataClass(frozen=True, slots=True)
class CircleShape:
    CurveNode: NativeNode
    CenterNode: NativeNode
    Entities: tuple[SketchEntity, ...]
    Geometry: CircleGeometry
