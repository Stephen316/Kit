"""Research copy of the retired per-layout Form tables. Nothing in src/ loads this folder."""
from functools import cache as CacheValue
from pathlib import Path
from json import loads as LoadJson
from lzma import decompress as Decompress
from types import MappingProxyType as ReadOnlyMap
from typing import Mapping as KMapping
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormUse,
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from ReadStencils import (
    ReadStencils,
)
from ShapeJson import (
    KCellJson,
    KCurveJson,
    KEdgeJson,
    KFaceJson,
    ShapeJson,
    ShapesJson,
)
from StencilShape import (
    ShapeEdge,
    ShapeFace,
    StencilShape,
)


def ReadTrace(Entry: KCurveJson) -> BsCurve:
    Rational, Degree, Closure, Knots, Counts, Dimension, Poles, Weights = Entry
    return BsCurve(
        bool(Rational),
        int(Degree),
        int(Closure),
        tuple(float(Value) for Value in Knots),
        tuple(int(Count) for Count in Counts),
        int(Dimension),
        tuple(tuple(float(Value) for Value in PoleValue) for PoleValue in Poles),
        tuple(float(Value) for Value in Weights),
    )


def ReadEdge(Entry: KEdgeJson) -> ShapeEdge:
    Start, Final, CurveIndex, Convexity, Label, Windows, Bounds = Entry
    return ShapeEdge(
        int(Start),
        int(Final),
        int(CurveIndex),
        str(Convexity),
        str(Label),
        tuple(
            FormWindow(
                int(FaceIndex), float(ULower), float(UHigh), float(VLower), float(VHigh)
            )
            for FaceIndex, ULower, UHigh, VLower, VHigh in Windows
        ),
        None if Bounds is None else (float(Bounds[0]), float(Bounds[1])),
    )


def ReadFace(Entry: KFaceJson) -> ShapeFace:
    FaceIndex, Label, DoubleSided, Contained, UseEntries = Entry
    return ShapeFace(
        int(FaceIndex),
        tuple(
            FormUse(int(EdgeIndex), bool(Reversed), ReadTrace(Trace), float(FitValue))
            for EdgeIndex, Reversed, Trace, FitValue in UseEntries
        ),
        str(Label),
        bool(DoubleSided),
        None if Contained is None else bool(Contained),
    )


def ReadCell(Entry: KCellJson) -> PatchCell:
    FaceIndex, Window, Offset = Entry
    if len(Window) != 4 or len(Offset) != 3:
        raise ValueError("Fusion Form shape table has a malformed patch cell")
    return PatchCell(
        int(FaceIndex),
        (int(Window[0]), int(Window[1]), int(Window[2]), int(Window[3])),
        (int(Offset[0]), int(Offset[1]), int(Offset[2])),
    )


def CheckShape(Shape: StencilShape) -> None:
    Table = ReadStencils().get(Shape.LayoutKey)
    if Table is None:
        raise ValueError("Fusion Form shape table names a missing stencil")
    Faces = {FaceValue.FaceIndex for FaceValue in Table.Faces}
    IsValid = all(Index < len(Table.Points) for Index in Shape.Points)
    IsValid &= all(
        EdgeValue.CurveIndex < len(Table.Curves)
        and max(EdgeValue.StartVertex, EdgeValue.EndVertex) < len(Shape.Points)
        for EdgeValue in Shape.Edges
    )
    IsValid &= all(
        FaceValue.FaceIndex in Faces
        and all(UseValue.EdgeIndex < len(Shape.Edges) for UseValue in FaceValue.Uses)
        for FaceValue in Shape.Faces
    )
    if not IsValid or min(Shape.Points + (0,)) < 0:
        raise ValueError("Fusion Form shape table names a missing part")


def ReadShape(Entry: ShapeJson) -> StencilShape:
    Shape = StencilShape(
        str(Entry["Label"]),
        str(Entry["LayoutKey"]),
        tuple(int(Index) for Index in Entry["Points"]),
        tuple(ReadEdge(EdgeEntry) for EdgeEntry in Entry["Edges"]),
        tuple(ReadFace(FaceEntry) for FaceEntry in Entry["Faces"]),
        tuple(
            tuple(ReadCell(CellEntry) for CellEntry in Cells)
            for Cells in Entry["Regions"]
        ),
    )
    CheckShape(Shape)
    return Shape


@CacheValue
def ReadShapes() -> KMapping[str, StencilShape]:
    Source = Path(__file__).with_name("FormShapes.xz")
    Value = CastValue(ShapesJson, LoadJson(Decompress(Source.read_bytes())))
    Shapes = [ReadShape(Entry) for Entry in Value["Shapes"]]
    Keyed = {Shape.LayoutKey: Shape for Shape in Shapes}
    if len(Keyed) != len(Shapes):
        raise ValueError("Fusion Form shape tables repeat a cage layout")
    return ReadOnlyMap(Keyed)
