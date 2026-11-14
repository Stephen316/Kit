from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.FaceNets import SplitMesh
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleMesh import (
    KDartKind,
    PoleMesh,
    BuildMesh,
    VertexKind,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)

KLimitSteps = 200


def SmoothMask(MeshValue: PoleMesh, Vertex: int) -> KPoleRow:
    FaceKeys = MeshValue.Touch[Vertex]
    Valence = len(FaceKeys)
    Scale = 1.0 / (Valence * (Valence + 5))
    Parts: list[tuple[float, KPoleRow]] = [(Valence * Valence * Scale, {Vertex: 1.0})]
    Parts += [(4.0 * Scale, {Other: 1.0}) for Other in MeshValue.Around[Vertex]]
    for FaceKey in FaceKeys:
        LoopValue = MeshValue.Faces[FaceKey]
        Across = LoopValue[(LoopValue.index(Vertex) + 2) % len(LoopValue)]
        Parts.append((Scale, {Across: 1.0}))
    return MixRows(Parts)


def MeshRow(MeshValue: PoleMesh, Weights: KPoleRow) -> KPoleRow:
    return MixRows(
        (Weight, MeshValue.Values[Member]) for Member, Weight in Weights.items()
    )


def SmoothLimit(MeshValue: PoleMesh, Vertex: int) -> KPoleRow:
    return MeshRow(MeshValue, SmoothMask(MeshValue, Vertex))


def RingMatrix(MeshValue: PoleMesh, Vertex: int) -> dict[int, KPoleRow]:
    FaceKeys = MeshValue.Touch[Vertex]
    Faces = {FaceKey: MeshValue.Faces[FaceKey] for FaceKey in FaceKeys}
    Members = {Member for LoopValue in Faces.values() for Member in LoopValue}
    Local = BuildMesh(
        Faces,
        {Member: {Member: 1.0} for Member in Members},
        frozenset(EdgeKey for EdgeKey in MeshValue.Sharp if EdgeKey <= Members),
        MeshValue.Corners & frozenset(Members),
    )
    Child = SplitMesh(Local, frozenset(FaceKeys))
    Matrix: dict[int, KPoleRow] = {}
    for FaceKey, LoopValue in Faces.items():
        Corner = LoopValue.index(Vertex)
        ChildLoop = Child.Faces[FaceKey + (Corner,)]
        for Place, Member in (
            (0, Vertex),
            (1, LoopValue[(Corner + 1) % 4]),
            (2, LoopValue[(Corner + 2) % 4]),
            (3, LoopValue[(Corner - 1) % 4]),
        ):
            Matrix[Member] = Child.Values[ChildLoop[Place]]
    return Matrix


def RingStep(Matrix: dict[int, KPoleRow], Weights: KPoleRow) -> KPoleRow:
    return MixRows((Weight, Matrix[Member]) for Member, Weight in Weights.items())


def RingLimit(MeshValue: PoleMesh, Vertex: int) -> KPoleRow:
    Matrix = RingMatrix(MeshValue, Vertex)
    Weights: KPoleRow = {Vertex: 1.0}
    for _ in range(KLimitSteps):
        Fresh = RingStep(Matrix, Weights)
        if Fresh == Weights:
            break
        Weights = Fresh
    return MeshRow(MeshValue, Weights)


def LevelLimit(MeshValue: PoleMesh, Vertex: int, Level: int) -> KPoleRow:
    Matrix = RingMatrix(MeshValue, Vertex)
    Weights = SmoothMask(MeshValue, Vertex)
    for _ in range(Level + 1):
        Weights = RingStep(Matrix, Weights)
    return MeshRow(MeshValue, Weights)


def LimitRow(MeshValue: PoleMesh, Vertex: int, Level: int) -> KPoleRow:
    FaceKeys = MeshValue.Touch[Vertex]
    IsClosed = len(MeshValue.Around[Vertex]) == len(FaceKeys)
    KindValue = VertexKind(MeshValue, Vertex)
    if KindValue == 0 and IsClosed:
        return SmoothLimit(MeshValue, Vertex)
    if KindValue == KDartKind and IsClosed:
        return LevelLimit(MeshValue, Vertex, Level)
    return RingLimit(MeshValue, Vertex)
