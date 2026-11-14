from math import cos as Cosine, sin as SineValue, tau as KFullTurn

from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KLattice = tuple[int, int, int]
KCoords = tuple[float, float, float]
KQuad = tuple[int, int, int, int]
KCageParts = tuple[list[KCoords], list[KQuad]]
KCornerSteps = ((0, 0), (1, 0), (1, 1), (0, 1))


def MakeSurface(Parts: KCageParts) -> TsplineSurface:
    Grips = tuple(ControlGrip(Coords[0], Coords[1], Coords[2]) for Coords in Parts[0])
    return MakeClosedCage(Grips, tuple(Parts[1]), SurfaceHeader(VersionCount=1))


def NormalPart(Corners: list[KLattice], AxisIndex: int) -> int:
    Origin, Along, Across = Corners[0], Corners[1], Corners[3]
    First, Second = (AxisIndex + 1) % 3, (AxisIndex + 2) % 3
    return (Along[First] - Origin[First]) * (Across[Second] - Origin[Second]) - (
        Along[Second] - Origin[Second]
    ) * (Across[First] - Origin[First])


def PlaneKey(AxisIndex: int, Plane: int, Spans: KQuad) -> KLattice:
    Values = [0, 0, 0]
    Values[AxisIndex] = Plane
    Values[Spans[0]] = Spans[2]
    Values[Spans[1]] = Spans[3]
    return (Values[0], Values[1], Values[2])


def PlaneQuad(AxisIndex: int, Plane: int, Spans: KQuad, Facing: int) -> list[KLattice]:
    Corners = [
        PlaneKey(
            AxisIndex, Plane, (Spans[0], Spans[1], Spans[2] + StepU, Spans[3] + StepV)
        )
        for StepU, StepV in KCornerSteps
    ]
    return Corners if NormalPart(Corners, AxisIndex) * Facing > 0 else Corners[::-1]


def LatticeParts(Faces: list[list[KLattice]]) -> KCageParts:
    Lookup: dict[KLattice, int] = {}
    Quads: list[KQuad] = []
    for Corners in Faces:
        Indices = [Lookup.setdefault(Corner, len(Lookup)) for Corner in Corners]
        Quads.append((Indices[0], Indices[1], Indices[2], Indices[3]))
    Coords = [(float(Entry[0]), float(Entry[1]), float(Entry[2])) for Entry in Lookup]
    return Coords, Quads


def BoxParts(Counts: KLattice) -> KCageParts:
    Faces: list[list[KLattice]] = []
    for AxisIndex in range(3):
        Others = [Entry for Entry in range(3) if Entry != AxisIndex]
        for Plane in (0, Counts[AxisIndex]):
            for First in range(Counts[Others[0]]):
                for Second in range(Counts[Others[1]]):
                    Spans = (Others[0], Others[1], First, Second)
                    Facing = 1 if Plane else -1
                    Faces.append(PlaneQuad(AxisIndex, Plane, Spans, Facing))
    return LatticeParts(Faces)


def CubeParts(Cubes: list[KLattice]) -> KCageParts:
    Filled = set(Cubes)
    Faces: list[list[KLattice]] = []
    for CubeKey in sorted(Filled):
        for AxisIndex in range(3):
            for Facing in (-1, 1):
                Moved = [CubeKey[0], CubeKey[1], CubeKey[2]]
                Moved[AxisIndex] += Facing
                if (Moved[0], Moved[1], Moved[2]) in Filled:
                    continue
                Spare = [Entry for Entry in range(3) if Entry != AxisIndex]
                Plane = CubeKey[AxisIndex] + (1 if Facing > 0 else 0)
                Spans = (Spare[0], Spare[1], CubeKey[Spare[0]], CubeKey[Spare[1]])
                Faces.append(PlaneQuad(AxisIndex, Plane, Spans, Facing))
    return LatticeParts(Faces)


def MeanPoint(Coords: list[KCoords], Indices: tuple[int, ...]) -> KCoords:
    Count = len(Indices)
    return (
        sum(Coords[Index][0] for Index in Indices) / Count,
        sum(Coords[Index][1] for Index in Indices) / Count,
        sum(Coords[Index][2] for Index in Indices) / Count,
    )


def SplitFaces(Start: list[KCoords], Faces: list[tuple[int, ...]]) -> KCageParts:
    Coords = list(Start)
    Middles: dict[tuple[int, int], int] = {}
    Quads: list[KQuad] = []
    for FaceLoop in Faces:
        Center = len(Coords)
        Coords.append(MeanPoint(Coords, FaceLoop))
        for Place, Corner in enumerate(FaceLoop):
            Found: list[int] = []
            for EndPair in (
                (Corner, FaceLoop[(Place + 1) % len(FaceLoop)]),
                (FaceLoop[Place - 1], Corner),
            ):
                EdgeKey = (min(EndPair), max(EndPair))
                if EdgeKey not in Middles:
                    Middles[EdgeKey] = len(Coords)
                    Coords.append(MeanPoint(Coords, EdgeKey))
                Found.append(Middles[EdgeKey])
            Quads.append((Corner, Found[0], Center, Found[1]))
    return Coords, Quads


def PrismParts(Sides: int) -> KCageParts:
    Angles = [KFullTurn * Index / Sides for Index in range(Sides)]
    Coords = [
        (Cosine(Angle), SineValue(Angle), Level)
        for Level in (0.0, 1.0)
        for Angle in Angles
    ]
    Faces: list[tuple[int, ...]] = [
        tuple(range(Sides, 2 * Sides)),
        tuple(reversed(range(Sides))),
    ]
    Faces += [
        (Index, (Index + 1) % Sides, Sides + (Index + 1) % Sides, Sides + Index)
        for Index in range(Sides)
    ]
    return SplitFaces(Coords, Faces)


def TorusSpot(Major: int, Minor: int, Counts: tuple[int, int]) -> int:
    return (Major % Counts[0]) * Counts[1] + Minor % Counts[1]


def TorusPoint(Major: int, Minor: int, Counts: tuple[int, int]) -> KCoords:
    Around = KFullTurn * Major / Counts[0]
    Within = KFullTurn * Minor / Counts[1]
    Radius = 1.6 + 0.6 * Cosine(Within)
    return (
        Radius * Cosine(Around),
        Radius * SineValue(Around),
        0.6 * SineValue(Within),
    )


def TorusParts(Counts: tuple[int, int]) -> KCageParts:
    Coords: list[KCoords] = []
    Quads: list[KQuad] = []
    for Major in range(Counts[0]):
        for Minor in range(Counts[1]):
            Coords.append(TorusPoint(Major, Minor, Counts))
            Quads.append(
                (
                    TorusSpot(Major, Minor, Counts),
                    TorusSpot(Major + 1, Minor, Counts),
                    TorusSpot(Major + 1, Minor + 1, Counts),
                    TorusSpot(Major, Minor + 1, Counts),
                )
            )
    return Coords, Quads


def BoundCount(Coords: KCoords, Upper: float) -> int:
    return sum(1 for Value in Coords if Value in (0.0, Upper))


def BoxCreases(Parts: KCageParts, Surface: TsplineSurface, Upper: float) -> CreaseData:
    Links = Surface.Topology.Links
    Coords = Parts[0]
    Edges = {
        LinkValue.EdgeIndex
        for LinkValue in Links
        if BoundCount(Coords[LinkValue.VertexIndex], Upper) >= 2
        and BoundCount(Coords[Links[LinkValue.NextLink].VertexIndex], Upper) >= 2
    }
    return CreaseData(tuple(sorted(Edges)), ())


def RingCreases(Surface: TsplineSurface, Rings: list[set[int]]) -> CreaseData:
    Links = Surface.Topology.Links
    Edges = {
        LinkValue.EdgeIndex
        for LinkValue in Links
        for RingValue in Rings
        if LinkValue.VertexIndex in RingValue
        and Links[LinkValue.NextLink].VertexIndex in RingValue
    }
    return CreaseData(tuple(sorted(Edges)), ())
