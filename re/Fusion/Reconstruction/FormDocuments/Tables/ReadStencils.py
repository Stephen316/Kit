"""Research copy of the retired per-layout Form tables. Nothing in src/ loads this folder."""
from dataclasses import dataclass as MakeDataClass
from functools import cache as CacheValue
from pathlib import Path
from json import loads as LoadJson
from lzma import decompress as Decompress
from types import MappingProxyType as ReadOnlyMap
from typing import Mapping as KMapping
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilCurve import (
    StencilCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilFace import (
    StencilFace,
)
from StencilJson import (
    KKnotJson,
    StencilsJson,
    TableJson,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilTable import (
    StencilTable,
)


def ReadKnots(Entries: KKnotJson) -> tuple[SplineKnot, ...]:
    return tuple(SplineKnot(float(Value), int(Count)) for Value, Count in Entries)


def ReadTable(Entry: TableJson) -> StencilTable:
    RowValues = tuple(
        tuple((int(GripIndex), float(Value)) for GripIndex, Value in RowValue)
        for RowValue in Entry["Rows"]
    )
    Faces = tuple(
        StencilFace(int(FaceIndex), ReadKnots(KnotsU), ReadKnots(KnotsV), tuple(Poles))
        for FaceIndex, KnotsU, KnotsV, Poles in Entry["Faces"]
    )
    Curves = tuple(
        StencilCurve(
            tuple(float(Value) for Value in Knots), tuple(Counts), tuple(Poles)
        )
        for Knots, Counts, Poles in Entry["Curves"]
    )
    Table = StencilTable(
        int(Entry["GripCount"]),
        RowValues,
        Faces,
        Curves,
        tuple(Entry["Points"]),
    )
    UsedRows = {Index for FaceValue in Faces for Index in FaceValue.Poles}
    UsedRows |= {Index for CurveValue in Curves for Index in CurveValue.Poles}
    if not UsedRows.union(Table.Points) <= set(range(len(RowValues))):
        raise ValueError("Fusion Form stencil table names a missing row")
    return Table


@MakeDataClass(frozen=True)
class LabelledTable:
    Label: str
    Table: StencilTable

    def __getattr__(self, Name: str) -> object:
        return getattr(self.Table, Name)


@CacheValue
def ReadStencils() -> KMapping[str, LabelledTable]:
    Source = Path(__file__).with_name("FormStencils.xz")
    Value = CastValue(StencilsJson, LoadJson(Decompress(Source.read_bytes())))
    Keyed = {
        str(Entry["LayoutKey"]): LabelledTable(str(Entry["Label"]), ReadTable(Entry))
        for Entry in Value["Tables"]
    }
    if len(Keyed) != len(Value["Tables"]):
        raise ValueError("Fusion Form stencil tables repeat a cage layout")
    return ReadOnlyMap(Keyed)
