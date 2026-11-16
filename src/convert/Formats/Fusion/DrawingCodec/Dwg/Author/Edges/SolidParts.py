from dataclasses import dataclass as MakeDataClass

# the point pair shape must stay shared so drawing edge authoring uses one contract for compatible values
KPointPair = tuple[float, float]

# the point triple shape must stay shared so drawing edge authoring uses one contract for compatible values
KPointTriple = tuple[float, float, float]


# line path needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class LinePath:
    Start: KPointTriple
    Finish: KPointTriple


# round path needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class RoundPath:
    Center: KPointTriple
    Normal: KPointTriple
    XAxis: KPointTriple
    YAxis: KPointTriple
    Radius: float
    Opening: float
    Sweep: float


# the edge path variants need one shared contract so drawing edge authoring cannot omit a supported value shape
KEdgePath = LinePath | RoundPath


# solid edge needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class SolidEdge:
    EdgeId: int
    Curve: KEdgePath


# flat line needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class FlatLine:
    Start: KPointPair
    Finish: KPointPair


# flat arc needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class FlatArc:
    Center: KPointPair
    Radius: float
    Opening: float
    Sweep: float


# flat face needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class FlatFace:
    Origin: KPointTriple
    Normal: KPointTriple
    XAxis: KPointTriple
    YAxis: KPointTriple
    Bounds: tuple[FlatLine | FlatArc, ...]


# ring bound needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class RingBound:
    Height: float
    Opening: float
    Sweep: float


# seam bound needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class SeamBound:
    Angle: float
    Lowest: float
    Highest: float


# round face needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class RoundFace:
    FaceIndex: int
    Origin: KPointTriple
    Along: KPointTriple
    XAxis: KPointTriple
    YAxis: KPointTriple
    Radius: float
    Slope: float
    Rings: tuple[RingBound, ...]
    Seams: tuple[SeamBound, ...]


# solid shape needs an explicit state contract so projected boundaries retain their intended visibility and geometry
@MakeDataClass(frozen=True, slots=True)
class SolidShape:
    Edges: tuple[SolidEdge, ...]
    Flats: tuple[FlatFace, ...]
    Rounds: tuple[RoundFace, ...]
