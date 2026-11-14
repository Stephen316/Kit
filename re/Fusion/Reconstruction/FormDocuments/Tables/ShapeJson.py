"""Research copy of the retired per-layout Form tables. Nothing in src/ loads this folder."""
from typing import TypedDict

KCurveJson = tuple[
    bool, int, int, list[float], list[int], int, list[list[float]], list[float]
]
KWindowJson = tuple[int, float, float, float, float]
KUseJson = tuple[int, bool, KCurveJson, float]
KCellJson = tuple[int, list[int], list[int]]
KEdgeJson = tuple[int, int, int, str, str, list[KWindowJson], list[float] | None]
KFaceJson = tuple[int, str, bool, bool | None, list[KUseJson]]


class ShapeJson(TypedDict):
    Label: str
    LayoutKey: str
    Points: list[int]
    Edges: list[KEdgeJson]
    Faces: list[KFaceJson]
    Regions: list[list[KCellJson]]


class ShapesJson(TypedDict):
    Shapes: list[ShapeJson]
