# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from re import split as SplitBytes
from typing import cast as CastValue

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.adapters.freecad.EditShape.Prism.PrismRaw import (
    CheckVertData,
    KLocationChain,
)
from convert.adapters.freecad.EditShape.Revolution.RevCarriers import (
    CheckCurveAxes,
    KRevCurve,
    KRevSurface,
    ReadRevSurface,
)
from convert.adapters.freecad.EditShape.Revolution.RevTrimRead import (
    ReadRevPcurves,
    ReadRevTrims,
)
from convert.adapters.freecad.EditShape.TrimBind import TrimBinding
from convert.adapters.freecad.EditShape.TrimGeometry import TrimCurve
from convert.geometry.Opencascade import (
    DecodeFailure,
    ExpectHeader,
    FoldMatrix,
    LocationProduct,
    LocationScale,
    ReadChainMut,
    ReadCount,
    ReadModelCurves,
    ReadReference,
    Reference,
    ShapeRecord,
    ShapeRecords,
    Tokens,
    ZeroTable,
)

# ordinary repeated edits preserve dormant parameter curves and their carrier locations
KMaxRevPlaces = 512

# repeated edit history is bounded independently of the number of active faces
KMaxRevTrims = 1024


# symbolic locations retain native sharing even when distinct datums have identical matrices
@MakeDataClass(frozen=True, slots=True)
class RevRaw:
    Chains: tuple[KLocationChain, ...]
    Datums: dict[int, tuple[float, ...]]
    Curves: tuple[KRevCurve, ...]
    Surfaces: tuple[KRevSurface, ...]
    Pcurves: tuple[TrimCurve, ...]
    Trims: dict[int, tuple[TrimBinding, ...]]
    Records: dict[int, ShapeRecord]
    RootRef: Reference

    # native datum products are stored innermost first so symbolic incidence survives composition
    def Place(self, Index: int, Parent: KLocationChain = ()) -> KLocationChain:
        return LocationProduct(Parent, self.Chains[Index])

    # the matrix for a located use follows the same chain as its topology
    def Matrix(self, ChainValue: KLocationChain, Index: int = 0) -> tuple[float, ...]:
        return FoldMatrix(self.Place(Index, ChainValue)[::-1], self.Datums)


# only proper rigid native placements can participate in an editable revolution
def ReadRevPlaces(
    Cursor: Tokens,
) -> tuple[tuple[KLocationChain, ...], dict[int, tuple[float, ...]]]:
    Count = ReadCount(Cursor, b"Locations", KMaxRevPlaces)
    Chains: list[KLocationChain] = []
    Seen: set[KLocationChain] = set()
    Datums: dict[int, tuple[float, ...]] = {}
    for Index in range(1, Count + 1):
        ChainValue = ReadChainMut(Cursor, Index, Chains, Datums)
        if (
            not ChainValue
            or ChainValue in Seen
            or len(ChainValue) > 16
            or any(abs(Power) > 16 for _, Power in ChainValue)
            or abs(LocationScale(FoldMatrix(ChainValue[::-1], Datums)) - 1.0)
            > KAngleTolerance
        ):
            raise DecodeFailure("unsupported Revolution placement")
        Chains.append(ChainValue)
        Seen.add(ChainValue)
    return ((), *Chains), Datums


# every stored pcurve and surface must have an explicit raw topology binding
def ReadTrimTable(
    ShapeData: bytes,
    Records: dict[int, ShapeRecord],
    Curves: int,
    Pcurves: int,
    Surfaces: int,
    Locations: int,
) -> dict[int, tuple[TrimBinding, ...]]:
    IdsValue = [Index for Index, Record in Records.items() if Record.KindValue == b"Ed"]
    Blocks = SplitBytes(rb"(?<!\S)Ed(?=\s)", ShapeData)[1:]
    if len(IdsValue) != len(Blocks):
        raise DecodeFailure("cannot locate Revolution edge representations")
    Table = {
        Index: ReadRevTrims(Block, Curves, Pcurves, Surfaces, Locations)
        for Index, Block in zip(IdsValue, Blocks, strict=True)
    }
    Bindings = tuple(TrimValue for Values in Table.values() for TrimValue in Values)
    UsedIds = sorted(Index for TrimValue in Bindings for Index in TrimValue.CurveIds)
    if UsedIds != list(range(1, Pcurves + 1)):
        raise DecodeFailure("unreachable or shared Revolution pcurve")
    return Table


# native saves use direct elementary geometry and one solid root without mesh fallbacks
def ReadRevRaw(ShapeData: bytes, EdgeLimit: int, ShapeLimit: int) -> RevRaw:
    Cursor = Tokens(ShapeData)
    ExpectHeader(Cursor)
    Chains, Datums = ReadRevPlaces(Cursor)
    Start = Cursor.LastEnd
    Pcurves = ReadRevPcurves(Cursor, KMaxRevTrims)
    CheckCurveAxes(Cursor, EdgeLimit)
    Cursor = Tokens(ShapeData[Start:])
    _, Curves = ReadModelCurves(Cursor, "revolution")
    ZeroTable(Cursor, b"Polygon3D")
    ZeroTable(Cursor, b"PolygonOnTriangulations")
    SurfCount = ReadCount(Cursor, b"Surfaces", KMaxRevTrims)
    Surfaces = tuple(ReadRevSurface(Cursor, Index) for Index in range(1, SurfCount + 1))
    ZeroTable(Cursor, b"Triangulations")
    Count = ReadCount(Cursor, b"TShapes", ShapeLimit)
    Records = ShapeRecords(
        Cursor, Count, len(Curves), len(Pcurves), SurfCount, len(Chains) - 1
    )
    RootRef = ReadReference(Cursor, Count, len(Chains) - 1)
    if RootRef is None or RootRef.Orientation != "+" or Cursor.PeekToken() is not None:
        raise DecodeFailure("unsupported Revolution root")
    CheckVertData(ShapeData, Records)
    Trims = ReadTrimTable(
        ShapeData, Records, len(Curves), len(Pcurves), SurfCount, len(Chains) - 1
    )
    return RevRaw(
        Chains,
        Datums,
        CastValue(tuple[KRevCurve, ...], Curves),
        Surfaces,
        Pcurves,
        Trims,
        Records,
        RootRef,
    )
