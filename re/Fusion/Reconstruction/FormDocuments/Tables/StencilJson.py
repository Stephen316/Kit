"""Research copy of the retired per-layout Form tables. Nothing in src/ loads this folder."""
from typing import TypedDict

KKnotJson = list[tuple[float, int]]


class TableJson(TypedDict):
    Label: str
    LayoutKey: str
    GripCount: int
    Rows: list[list[tuple[int, float]]]
    Faces: list[tuple[int, KKnotJson, KKnotJson, list[int]]]
    Curves: list[tuple[list[float], list[int], list[int]]]
    Points: list[int]


class StencilsJson(TypedDict):
    Tables: list[TableJson]
