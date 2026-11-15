from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.PlaceGrips import (
    PoleIndex,
    SpokePoles,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.PlaceVertices import (
    KSpokeSteps,
    PlaceVertices,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.SpokeIndices import (
    SpokeIndices,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    KEndCount,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleLines import (
    KKnotList,
    ClampKnot,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KIndexedRow,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

# the grid place shape must stay shared so spline pole reconstruction uses one contract for compatible values
KGridPlace = tuple[int, int]

# the pole grid shape must stay shared so spline pole reconstruction uses one contract for compatible values
KPoleGrid = list[list[KIndexedRow]]

# the side grip shape must stay shared so spline pole reconstruction uses one contract for compatible values
KSideGrip = tuple[KGridPlace, int]


# the compound decision must stay consistent so neighboring patches retain consistent subdivision boundaries
def IsCompound(Surface: TsplineSurface) -> bool:
    return len(Surface.Grips) > len(Surface.Topology.Vertices)


# the grid places contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def GridPlaces(Surface: TsplineSurface) -> tuple[KGridPlace, ...]:
    return PlaceVertices(Surface.Topology, SpokeIndices(Surface.Topology))


# the rim place decision must stay consistent so neighboring patches retain consistent subdivision boundaries
def IsRimPlace(Place: KGridPlace, Limits: KGridPlace) -> bool:
    return Place[0] in (0, Limits[0]) or Place[1] in (0, Limits[1])


# base grid needs an explicit validity boundary so neighboring patches retain consistent subdivision boundaries
def BaseGrid(
    Surface: TsplineSurface, Places: tuple[KGridPlace, ...], Limits: KGridPlace
) -> dict[KGridPlace, int]:
    Mapping = Surface.Mapping
    if Mapping is None:
        raise ValueError("Fusion Form grid poles need compound grips")
    Centers = [
        (PoleIndex(Place[0], Limits[0]), PoleIndex(Place[1], Limits[1]))
        for Place in Places
    ]
    Found = {
        Centers[Owner.VertexIndex]: GripIndex
        for GripIndex, Owner in enumerate(Mapping.Owners)
        if Owner.IsPrimary
    }
    for Compound in Mapping.Compounds:
        if IsRimPlace(Places[Compound.VertexIndex], Limits):
            Targets = SpokePoles(Compound, Centers[Compound.VertexIndex])
            Found.update(zip(Targets, Compound.GripIndices))
    if len(Found) != (Limits[0] + 3) * (Limits[1] + 3):
        raise ValueError("Fusion Form grid poles need one rim grip per pole")
    return Found


# side grips needs an explicit validity boundary so neighboring patches retain consistent subdivision boundaries
def SideGrips(
    Surface: TsplineSurface, Places: tuple[KGridPlace, ...], Limits: KGridPlace
) -> dict[int, list[KSideGrip]]:
    Found: dict[int, list[KSideGrip]] = {}
    Mapping = Surface.Mapping
    if Mapping is None:
        return Found
    for Compound in Mapping.Compounds:
        if IsRimPlace(Places[Compound.VertexIndex], Limits):
            continue
        Steps = [
            KSpokeSteps[Spoke]
            for Spoke, Length in enumerate(Compound.SpokeLengths)
            if Length
        ]
        if len(Steps) != len(Compound.GripIndices):
            raise ValueError("Fusion Form grid poles need one grip per crease spoke")
        Found[Compound.VertexIndex] = list(zip(Steps, Compound.GripIndices))
    return Found


# the crease lines contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def CreaseLines(
    Graph: CageGraph, Places: tuple[KGridPlace, ...], Limits: KGridPlace
) -> tuple[frozenset[int], frozenset[int]]:
    LinesU: set[int] = set()
    LinesV: set[int] = set()
    for LinkIndex, LinkValue in enumerate(Graph.Links):
        if not Graph.Creased[LinkIndex] or Graph.Open[LinkIndex]:
            continue
        Start, Final = Places[LinkValue.VertexIndex], Places[Graph.Heads[LinkIndex]]
        if Start[0] == Final[0] and 0 < Start[0] < Limits[0]:
            LinesU.add(Start[0])
        if Start[1] == Final[1] and 0 < Start[1] < Limits[1]:
            LinesV.add(Start[1])
    return frozenset(LinesU), frozenset(LinesV)


# the uniform knots contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def UniformKnots(Limit: int) -> KKnotList:
    Inner = tuple(Fraction(Value) for Value in range(1, Limit))
    return (
        (Fraction(0),) * (KEndCount + 1) + Inner + (Fraction(Limit),) * (KEndCount + 1)
    )


# the split line contract needs a stable decomposition so neighboring patches retain consistent subdivision boundaries
def SplitLine(
    Knots: KKnotList, Poles: list[KIndexedRow], Lines: frozenset[int]
) -> tuple[KKnotList, list[KIndexedRow]]:
    Current = (Knots, Poles)
    for Value in sorted(Lines):
        Current = ClampKnot(Current, Fraction(Value))
    return Current


# the transposed contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def Transposed(GridRows: KPoleGrid) -> KPoleGrid:
    return [list(Column) for Column in zip(*GridRows)]


# the split grid contract needs a stable decomposition so neighboring patches retain consistent subdivision boundaries
def SplitGrid(
    BaseGrips: dict[KGridPlace, int],
    Limits: KGridPlace,
    Lines: tuple[frozenset[int], frozenset[int]],
) -> tuple[KKnotList, KKnotList, KPoleGrid]:
    Width, Height = Limits[0] + 3, Limits[1] + 3
    Start: KPoleGrid = [
        [(None, {BaseGrips[(Column, RowIndex)]: 1.0}) for Column in range(Width)]
        for RowIndex in range(Height)
    ]
    KnotsU = UniformKnots(Limits[0])
    KnotsV = UniformKnots(Limits[1])
    RowLines = [SplitLine(KnotsU, RowValue, Lines[0]) for RowValue in Start]
    Columns = [
        SplitLine(KnotsV, Column, Lines[1])
        for Column in Transposed([Entry[1] for Entry in RowLines])
    ]
    return RowLines[0][0], Columns[0][0], Transposed([Entry[1] for Entry in Columns])
