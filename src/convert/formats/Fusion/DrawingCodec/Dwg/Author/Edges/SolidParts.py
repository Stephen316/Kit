from dataclasses import dataclass as MakeDataClass

KPointPair = tuple[float, float]
KPointTriple = tuple[float, float, float]


@MakeDataClass(frozen=True, slots=True)
class LinePath:
    Start: KPointTriple
    Finish: KPointTriple


@MakeDataClass(frozen=True, slots=True)
class RoundPath:
    Center: KPointTriple
    Normal: KPointTriple
    XAxis: KPointTriple
    YAxis: KPointTriple
    Radius: float
    Opening: float
    Sweep: float


KEdgePath = LinePath | RoundPath


@MakeDataClass(frozen=True, slots=True)
class SolidEdge:
    EdgeId: int
    Curve: KEdgePath


@MakeDataClass(frozen=True, slots=True)
class FlatLine:
    Start: KPointPair
    Finish: KPointPair


@MakeDataClass(frozen=True, slots=True)
class FlatArc:
    Center: KPointPair
    Radius: float
    Opening: float
    Sweep: float


@MakeDataClass(frozen=True, slots=True)
class FlatFace:
    Origin: KPointTriple
    Normal: KPointTriple
    XAxis: KPointTriple
    YAxis: KPointTriple
    Bounds: tuple[FlatLine | FlatArc, ...]


@MakeDataClass(frozen=True, slots=True)
class RingBound:
    Height: float
    Opening: float
    Sweep: float


@MakeDataClass(frozen=True, slots=True)
class SeamBound:
    Angle: float
    Lowest: float
    Highest: float


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


@MakeDataClass(frozen=True, slots=True)
class SolidShape:
    Edges: tuple[SolidEdge, ...]
    Flats: tuple[FlatFace, ...]
    Rounds: tuple[RoundFace, ...]
