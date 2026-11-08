# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as ReplaceData

from convert.adapters.freecad.EditShape.Prism.PrismRaw import (
    PrismRaw,
    ReadPrismPlaces,
    ReadPrismTree,
)
from convert.adapters.freecad.EditShape.Prism.PrismTrim import ReadPrismBinds
from convert.adapters.freecad.EditShape.Scale.ScaleLines import ScaleLines
from convert.adapters.freecad.EditShape.Scale.ScalePatch import ReadScalePatch
from convert.adapters.freecad.EditShape.Scale.ScaleSpan import ReadScaleSpan
from convert.adapters.freecad.EditShape.Scale.ScaleTrims import CheckScaleTrims
from convert.geometry.Opencascade import ExpectHeader, ReadCount, Tokens, ZeroTable


# native nonuniform scaling needs its own bounded carrier grammar and trim proof
def ReadScaleSpline(ShapeData: bytes, Sides: int) -> PrismRaw:
    Cursor = Tokens(ShapeData)
    ExpectHeader(Cursor)
    Chains, Datums = ReadPrismPlaces(Cursor)
    TrimCount = ReadCount(Cursor, b"Curve2ds", 6 * Sides)
    Trims = tuple(ReadScaleSpan(Cursor, 2) for Index in range(TrimCount))
    CurveCount = ReadCount(Cursor, b"Curves", 3 * Sides)
    Curves = tuple(ReadScaleSpan(Cursor, 3) for Index in range(CurveCount))
    ZeroTable(Cursor, b"Polygon3D")
    ZeroTable(Cursor, b"PolygonOnTriangulations")
    SurfaceCount = ReadCount(Cursor, b"Surfaces", Sides + 2)
    Patches = tuple(
        ReadScalePatch(Cursor, Index) for Index in range(1, SurfaceCount + 1)
    )
    PlaceCount = len(Chains) - 1
    Records, RootRef = ReadPrismTree(
        Cursor, ShapeData, Sides, CurveCount, TrimCount, SurfaceCount, PlaceCount
    )
    Bindings = ReadPrismBinds(ShapeData, Records, TrimCount, SurfaceCount, PlaceCount)
    Lines, LineRecords = ScaleLines(Curves, Records)
    Planes = tuple(Value.Plane for Value in Patches)
    RawValue = PrismRaw(Chains, Datums, (), Bindings, Lines, Planes, Records, RootRef)
    CheckScaleTrims(RawValue, Curves, Trims, Patches)
    return ReplaceData(RawValue, Records=LineRecords)
