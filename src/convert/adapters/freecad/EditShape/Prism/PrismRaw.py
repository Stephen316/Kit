# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from re import findall as FindAll

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.adapters.freecad.EditShape.Prism.PrismTrim import (
    ReadPrismBinds,
    ReadPrismCurves,
)
from convert.adapters.freecad.EditShape.TrimBind import TrimBinding
from convert.adapters.freecad.EditShape.TrimGeometry import TrimCurve
from convert.geometry.Opencascade import (
    AssertReachable,
    DecodeFailure,
    EdgeData,
    ExpectHeader,
    FaceData,
    FoldMatrix,
    LocationProduct,
    LocationScale,
    ReadChainMut,
    ReadCount,
    ReadModelCurves,
    ReadModelSurfs,
    ReadReference,
    Reference,
    ShapeRecord,
    ShapeRecords,
    Tokens,
    ZeroTable,
)
from interchange.brep.curves.BrepCurves import BrepCurve
from interchange.brep.surfaces.BrepSurfaces import BrepSurface

# symbolic native datums distinguish real sharing from coincident independent topology
KLocationChain = tuple[tuple[int, int], ...]

# only the bounded solid shell face wire edge vertex hierarchy can describe a prism
KPrismKinds = {b"So": b"Sh", b"Sh": b"Fa", b"Fa": b"Wi", b"Wi": b"Ed", b"Ed": b"Ve"}


# native placements and carriers are retained separately from shared topology records
@MakeDataClass(frozen=True, slots=True)
class PrismRaw:
    Chains: list[KLocationChain]
    Datums: dict[int, tuple[float, ...]]
    Pcurves: tuple[TrimCurve, ...]
    Bindings: dict[int, tuple[TrimBinding, ...]]
    Curves: tuple[BrepCurve, ...]
    Surfaces: tuple[BrepSurface, ...]
    Records: dict[int, ShapeRecord]
    RootRef: Reference

    # reverse ordered datums preserve shared topology through native placement composition
    def Place(self, RefValue: Reference, Parent: KLocationChain = ()) -> KLocationChain:
        return LocationProduct(Parent, self.Chains[RefValue.KLocation])

    # datums are stored innermost first and geometry uses the world transform
    def Matrix(self, ChainValue: KLocationChain, Index: int = 0) -> tuple[float, ...]:
        return FoldMatrix(
            LocationProduct(ChainValue, self.Chains[Index])[::-1], self.Datums
        )


# vertex representations discarded by the general parser are outside this planar grammar
def CheckVertData(ShapeData: bytes, Records: dict[int, ShapeRecord]) -> None:
    Count = sum(Value.KindValue == b"Ve" for Value in Records.values())
    Pattern = rb"(?<!\S)Ve\s+(?:\S+\s+){4}0\s+0(?=\s)"
    if len(FindAll(Pattern, ShapeData)) != Count:
        raise DecodeFailure("unsupported prism vertex representations")


# coherent range flags prevent accepting a saved edge with an unqualified parameter state
def CheckEdgeFlags(ShapeData: bytes, Records: dict[int, ShapeRecord]) -> None:
    Count = sum(Value.KindValue == b"Ed" for Value in Records.values())
    Pattern = rb"(?<!\S)Ed\s+\S+\s+1\s+1\s+0(?=\s)"
    if len(FindAll(Pattern, ShapeData)) != Count:
        raise DecodeFailure("unsupported prism edge parameter flags")


# the root shell and each boundary record must have its qualified child type
def CheckPrismTree(
    Records: dict[int, ShapeRecord], RootRef: Reference, Sides: int
) -> None:
    if Records[RootRef.RecordA].KindValue != b"So" or RootRef.Orientation != "+":
        raise DecodeFailure("prism requires a single forward solid")
    for Record in Records.values():
        KindValue = Record.KindValue
        Count = len(Record.Children)
        if (
            (KindValue in {b"So", b"Fa"} and Count != 1)
            or (KindValue == b"Sh" and Count != Sides + 2)
            or (KindValue == b"Wi" and not 3 <= Count <= max(Sides, 4))
            or (KindValue == b"Ed" and Count != 2)
            or (KindValue == b"Ve" and Count != 0)
            or (KindValue in {b"Wi", b"Sh"} and Record.FlagBits[4] != "1")
            or (KindValue != b"Ve" and KindValue not in KPrismKinds)
            or any(
                Child.Orientation not in {"+", "-"}
                or Records[Child.RecordA].KindValue != KPrismKinds[KindValue]
                for Child in Record.Children
            )
        ):
            raise DecodeFailure("unsupported prism topology")
    AssertReachable(
        RootRef.RecordA,
        {
            Index: tuple(Child.RecordA for Child in Value.Children)
            for Index, Value in Records.items()
        },
        {Index: Value.KindValue for Index, Value in Records.items()},
    )


# retaining rigid datum chains lets one cap record represent two separate cap instances
def ReadPrismPlaces(
    Cursor: Tokens,
) -> tuple[list[KLocationChain], dict[int, tuple[float, ...]]]:
    Count = ReadCount(Cursor, b"Locations", 16)
    Chains: list[KLocationChain] = []
    Datums: dict[int, tuple[float, ...]] = {}
    for Index in range(1, Count + 1):
        Location = ReadChainMut(Cursor, Index, Chains, Datums)
        if (
            not Location
            or Location in Chains
            or abs(LocationScale(FoldMatrix(Location[::-1], Datums)) - 1.0)
            > KAngleTolerance
        ):
            raise DecodeFailure("unsupported prism location")
        Chains.append(Location)
    return [(), *Chains], Datums


# both carrier encodings need the same finite closed incidence grammar
def ReadPrismTree(
    Cursor: Tokens,
    ShapeData: bytes,
    Sides: int,
    CurveCount: int,
    TrimCount: int,
    SurfaceCount: int,
    PlaceCount: int,
) -> tuple[dict[int, ShapeRecord], Reference]:
    ZeroTable(Cursor, b"Triangulations")
    Count = ReadCount(Cursor, b"TShapes", 7 * Sides + 6)
    Records = ShapeRecords(
        Cursor, Count, CurveCount, TrimCount, SurfaceCount, PlaceCount
    )
    RootRef = ReadReference(Cursor, Count, PlaceCount)
    if RootRef is None or Cursor.PeekToken() is not None:
        raise DecodeFailure("unsupported prism root")
    CheckPrismTree(Records, RootRef, Sides)
    CheckVertData(ShapeData, Records)
    CheckEdgeFlags(ShapeData, Records)
    return Records, RootRef


# shared root placement cancels out when comparing a seed edge and trim
def CheckRootTrims(Records: dict[int, ShapeRecord], RootRef: Reference) -> None:
    if RootRef.KLocation != 1 or any(
        any(Child.KLocation for Child in Record.Children)
        or (
            isinstance(Geometry := Record.GeometryA, (EdgeData, FaceData))
            and Geometry.KLocation
        )
        for Record in Records.values()
    ):
        raise DecodeFailure("explicit prism trims require a shared root location")


# native saves use implicit planar trims while kit seeds store exact planar line trims
def ReadPrismRaw(ShapeData: bytes, Sides: int, AllowRootTrim: bool = False) -> PrismRaw:
    Cursor = Tokens(ShapeData)
    ExpectHeader(Cursor)
    Chains, Datums = ReadPrismPlaces(Cursor)
    ModelStart = Cursor.LastEnd
    Pcurves = ReadPrismCurves(Cursor, 6 * Sides)
    if Pcurves and Datums and (not AllowRootTrim or len(Chains) != 2):
        raise DecodeFailure("located explicit prism pcurves are unsupported")
    Cursor = Tokens(ShapeData[ModelStart:])
    Ignored, Curves = ReadModelCurves(Cursor, "freecad:edit-prism")
    ZeroTable(Cursor, b"Polygon3D")
    ZeroTable(Cursor, b"PolygonOnTriangulations")
    Surfaces = ReadModelSurfs(Cursor, "freecad:edit-prism")
    Records, RootRef = ReadPrismTree(
        Cursor,
        ShapeData,
        Sides,
        len(Curves),
        len(Pcurves),
        len(Surfaces),
        len(Chains) - 1,
    )
    if Pcurves and Datums:
        CheckRootTrims(Records, RootRef)
    Bindings = (
        ReadPrismBinds(ShapeData, Records, len(Pcurves), len(Surfaces))
        if Pcurves
        else {}
    )
    return PrismRaw(
        Chains, Datums, Pcurves, Bindings, Curves, Surfaces, Records, RootRef
    )
