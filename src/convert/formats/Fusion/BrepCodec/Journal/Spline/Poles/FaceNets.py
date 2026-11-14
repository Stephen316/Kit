from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleMesh import (
    KCornerKind,
    KCreaseKind,
    KDartKind,
    KEdgeKey,
    KFaceKey,
    PoleMesh,
    BuildMesh,
    EdgePoint,
    FaceMean,
    VertexKind,
    VertexPoint,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)

KSlot = tuple[int, int]
KNetRows = tuple[tuple[KPoleRow, ...], ...]
KCornerSteps = ((0, 0), (1, 0), (1, 1), (0, 1))
KOutward = ((0, -1), (1, 0), (0, 1), (-1, 0))
KRingSteps = 3


def GroupSize(MeshValue: PoleMesh, Vertex: int, FaceKey: KFaceKey) -> int:
    Found = {FaceKey}
    Pending = [FaceKey]
    while Pending:
        LoopValue = MeshValue.Faces[Pending.pop()]
        Corner = LoopValue.index(Vertex)
        for Other in (LoopValue[(Corner + 1) % 4], LoopValue[(Corner - 1) % 4]):
            if frozenset((Vertex, Other)) in MeshValue.Sharp:
                continue
            for HalfKey in ((Vertex, Other), (Other, Vertex)):
                Entry = MeshValue.Halves.get(HalfKey)
                if Entry is not None and Entry[0] not in Found:
                    Found.add(Entry[0])
                    Pending.append(Entry[0])
    return len(Found)


def IsCornerFit(MeshValue: PoleMesh, Vertex: int, FaceKey: KFaceKey) -> bool:
    KindValue = VertexKind(MeshValue, Vertex)
    if KindValue == KDartKind:
        return False
    if KindValue == 0:
        return len(MeshValue.Around[Vertex]) == 4
    Wanted = 1 if KindValue == KCornerKind else KCreaseKind
    return GroupSize(MeshValue, Vertex, FaceKey) == Wanted


def Reflect(
    GridRows: dict[KSlot, KPoleRow], NearSlot: KSlot, FarSlot: KSlot
) -> KPoleRow:
    return MixRows(((2.0, GridRows[NearSlot]), (-1.0, GridRows[FarSlot])))


def SideSlots(MeshValue: PoleMesh, LoopValue: tuple[int, ...]) -> dict[KSlot, KPoleRow]:
    GridRows = {
        KCornerSteps[Corner]: MeshValue.Values[LoopValue[Corner]] for Corner in range(4)
    }
    for SideIndex in range(4):
        Start, Final = LoopValue[SideIndex], LoopValue[(SideIndex + 1) % 4]
        First, Second = KCornerSteps[SideIndex], KCornerSteps[(SideIndex + 1) % 4]
        StepX, StepY = KOutward[SideIndex]
        OuterFirst = (First[0] + StepX, First[1] + StepY)
        OuterSecond = (Second[0] + StepX, Second[1] + StepY)
        if frozenset((Start, Final)) in MeshValue.Sharp:
            GridRows[OuterFirst] = Reflect(
                GridRows, First, (First[0] - StepX, First[1] - StepY)
            )
            GridRows[OuterSecond] = Reflect(
                GridRows, Second, (Second[0] - StepX, Second[1] - StepY)
            )
            continue
        OtherKey, OtherCorner = MeshValue.Halves[(Final, Start)]
        RingLoop = MeshValue.Faces[OtherKey]
        GridRows[OuterFirst] = MeshValue.Values[RingLoop[(OtherCorner + 2) % 4]]
        GridRows[OuterSecond] = MeshValue.Values[RingLoop[(OtherCorner + 3) % 4]]
    return GridRows


def Diagonal(
    MeshValue: PoleMesh, LoopValue: tuple[int, ...], Corner: int
) -> int | None:
    Vertex, Before = LoopValue[Corner], LoopValue[(Corner - 1) % 4]
    Entry = MeshValue.Halves.get((Vertex, Before))
    if Entry is None:
        return None
    RingLoop = MeshValue.Faces[Entry[0]]
    Entry = MeshValue.Halves.get((Vertex, RingLoop[(Entry[1] - 1) % 4]))
    if Entry is None:
        return None
    return MeshValue.Faces[Entry[0]][(Entry[1] + 2) % 4]


def CornerSlot(
    MeshValue: PoleMesh,
    LoopValue: tuple[int, ...],
    GridRows: dict[KSlot, KPoleRow],
    Corner: int,
) -> KPoleRow | None:
    Before, After = (Corner - 1) % 4, Corner
    Point = KCornerSteps[Corner]
    SpotSlot = (
        Point[0] + KOutward[Before][0] + KOutward[After][0],
        Point[1] + KOutward[Before][1] + KOutward[After][1],
    )
    for SideIndex in (After, Before):
        Start, Final = LoopValue[SideIndex], LoopValue[(SideIndex + 1) % 4]
        if frozenset((Start, Final)) in MeshValue.Sharp:
            StepX, StepY = KOutward[SideIndex]
            NearSlot = (SpotSlot[0] - StepX, SpotSlot[1] - StepY)
            return Reflect(
                GridRows, NearSlot, (SpotSlot[0] - 2 * StepX, SpotSlot[1] - 2 * StepY)
            )
    Across = Diagonal(MeshValue, LoopValue, Corner)
    return None if Across is None else MeshValue.Values[Across]


def FaceNet(MeshValue: PoleMesh, FaceKey: KFaceKey) -> KNetRows | None:
    LoopValue = MeshValue.Faces[FaceKey]
    if len(LoopValue) != 4:
        return None
    if not all(IsCornerFit(MeshValue, Vertex, FaceKey) for Vertex in LoopValue):
        return None
    GridRows = SideSlots(MeshValue, LoopValue)
    Spots: dict[KSlot, KPoleRow] = {}
    for Corner in range(4):
        Found = CornerSlot(MeshValue, LoopValue, GridRows, Corner)
        if Found is None:
            return None
        Point = KCornerSteps[Corner]
        Spots[(3 * Point[0] - 1, 3 * Point[1] - 1)] = Found
    GridRows.update(Spots)
    return tuple(
        tuple(GridRows[(Column - 1, RowIndex - 1)] for Column in range(4))
        for RowIndex in range(4)
    )


def EdgeOrder(Start: int, Final: int) -> tuple[int, int]:
    return (Start, Final) if Start < Final else (Final, Start)


def ChildFaces(
    MeshValue: PoleMesh,
    Ordered: list[KFaceKey],
    EdgeIds: dict[tuple[int, int], int],
    VertexIds: dict[int, int],
) -> dict[KFaceKey, tuple[int, ...]]:
    Faces: dict[KFaceKey, tuple[int, ...]] = {}
    for FacePlace, FaceKey in enumerate(Ordered):
        LoopValue = MeshValue.Faces[FaceKey]
        SideCount = len(LoopValue)
        for Corner, Vertex in enumerate(LoopValue):
            After, Before = (
                LoopValue[(Corner + 1) % SideCount],
                LoopValue[(Corner - 1) % SideCount],
            )
            Faces[FaceKey + (Corner,)] = (
                VertexIds[Vertex],
                EdgeIds[EdgeOrder(Vertex, After)],
                FacePlace,
                EdgeIds[EdgeOrder(Before, Vertex)],
            )
    return Faces


def ChildSharp(
    MeshValue: PoleMesh, EdgeIds: dict[tuple[int, int], int], VertexIds: dict[int, int]
) -> frozenset[KEdgeKey]:
    Found: set[KEdgeKey] = set()
    for (Start, Final), Middle in EdgeIds.items():
        if frozenset((Start, Final)) in MeshValue.Sharp:
            Found.add(frozenset((VertexIds[Start], Middle)))
            Found.add(frozenset((Middle, VertexIds[Final])))
    return frozenset(Found)


def SplitMesh(MeshValue: PoleMesh, KeepFaces: frozenset[KFaceKey]) -> PoleMesh:
    Ordered = sorted(KeepFaces)
    EdgeList = sorted(
        {
            EdgeOrder(Vertex, LoopValue[(Corner + 1) % len(LoopValue)])
            for LoopValue in (MeshValue.Faces[FaceKey] for FaceKey in Ordered)
            for Corner, Vertex in enumerate(LoopValue)
        }
    )
    VertexList = sorted(
        {Vertex for FaceKey in Ordered for Vertex in MeshValue.Faces[FaceKey]}
    )
    EdgeIds = {
        EdgePair: len(Ordered) + Place for Place, EdgePair in enumerate(EdgeList)
    }
    Offset = len(Ordered) + len(EdgeList)
    VertexIds = {Vertex: Offset + Place for Place, Vertex in enumerate(VertexList)}
    Values = {
        Place: FaceMean(MeshValue, FaceKey) for Place, FaceKey in enumerate(Ordered)
    }
    Values.update(
        {
            EdgeIds[EdgePair]: EdgePoint(MeshValue, EdgePair[0], EdgePair[1])
            for EdgePair in EdgeList
        }
    )
    Values.update(
        {VertexIds[Vertex]: VertexPoint(MeshValue, Vertex) for Vertex in VertexList}
    )
    Corners = frozenset(
        VertexIds[Vertex]
        for Vertex in VertexList
        if VertexKind(MeshValue, Vertex) == KCornerKind
    )
    return BuildMesh(
        ChildFaces(MeshValue, Ordered, EdgeIds, VertexIds),
        Values,
        ChildSharp(MeshValue, EdgeIds, VertexIds),
        Corners,
    )


def RingFaces(MeshValue: PoleMesh, Seeds: frozenset[KFaceKey]) -> frozenset[KFaceKey]:
    Found = set(Seeds)
    for _ in range(KRingSteps):
        Found |= {
            Other
            for FaceKey in tuple(Found)
            for Vertex in MeshValue.Faces[FaceKey]
            for Other in MeshValue.Touch[Vertex]
        }
    return frozenset(Found)


def MeshLevels(MeshValue: PoleMesh, Depth: int) -> dict[KFaceKey, KNetRows | None]:
    NetTable = {FaceKey: FaceNet(MeshValue, FaceKey) for FaceKey in MeshValue.Faces}
    Broken: frozenset[KFaceKey] = frozenset(
        FaceKey for FaceKey, NetRows in NetTable.items() if NetRows is None
    )
    Current = MeshValue
    for _ in range(Depth):
        if not Broken:
            break
        Child = SplitMesh(Current, RingFaces(Current, Broken))
        Fresh: dict[KFaceKey, KNetRows | None] = {
            FaceKey + (Corner,): FaceNet(Child, FaceKey + (Corner,))
            for FaceKey in Broken
            for Corner in range(len(Current.Faces[FaceKey]))
        }
        NetTable.update(Fresh)
        Broken = frozenset(
            FaceKey for FaceKey, NetRows in Fresh.items() if NetRows is None
        )
        Current = Child
    return NetTable
