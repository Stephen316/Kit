from math import pi as KHalfTurn
from math import sqrt as SquareRoot

from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    CylinderSurface,
    PlaneSurface,
    SphereSurface,
)
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
)
from interchange.geometry.models.VectorSpace import SpaceVector

# the point triple shape must stay shared so native document reconstruction uses one contract for compatible values
KPointTriple = tuple[float, float, float]

# the line specification shape must stay shared so native document reconstruction uses one contract for compatible values
KLineSpec = tuple[KPointTriple, KPointTriple]

# the ring specification shape must stay shared so native document reconstruction uses one contract for compatible values
KRingSpec = tuple[KPointTriple, KPointTriple, float]

# the face specification shape must stay shared so native document reconstruction uses one contract for compatible values
KFaceSpec = tuple[BrepSurface, tuple[tuple[KLineSpec | KRingSpec, ...], ...]]


# shared make vector setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def MakeVector(Values: KPointTriple) -> SpaceVector:
    return SpaceVector(x=Values[0], y=Values[1], z=Values[2])


# shared across setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def Across(Normal: KPointTriple) -> KPointTriple:
    return (0.0, 1.0, 0.0) if abs(Normal[0]) > 0.5 else (1.0, 0.0, 0.0)


# shared flat surface setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def FlatSurface(Origin: KPointTriple, Normal: KPointTriple) -> PlaneSurface:
    return PlaneSurface(
        id=f"plane{Origin}{Normal}",
        origin=MakeVector(Origin),
        normal=MakeVector(Normal),
        reference_direction=MakeVector(Across(Normal)),
    )


# shared tube surface setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def TubeSurface(
    Origin: KPointTriple, Along: KPointTriple, Radius: float
) -> CylinderSurface:
    return CylinderSurface(
        id=f"tube{Origin}{Along}",
        origin=MakeVector(Origin),
        axis=MakeVector(Along),
        reference_direction=MakeVector(Across(Along)),
        radius=Radius,
    )


# shared ball surface setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def BallSurface(Center: KPointTriple, Radius: float) -> SphereSurface:
    return SphereSurface(
        id="ball",
        center=MakeVector(Center),
        axis=MakeVector((0.0, 0.0, 1.0)),
        reference_direction=MakeVector((1.0, 0.0, 0.0)),
        radius=Radius,
    )


# the solid builder boundary needs grouped coverage so repository automation cannot silently change its observable contract
class SolidBuilder:

    # shared solid builder setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
    def __init__(self) -> None:
        super().__init__()
        self.Vertices: dict[KPointTriple, BrepVertex] = {}
        self.Edges: dict[object, BrepEdge] = {}
        self.Curves: list[BrepCurve] = []
        self.Coedges: list[BrepCoedge] = []


# shared vertex setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def VertexMut(Builder: SolidBuilder, Point: KPointTriple) -> str:
    if Point not in Builder.Vertices:
        Named = f"v{len(Builder.Vertices)}"
        Builder.Vertices[Point] = BrepVertex(id=Named, point=MakeVector(Point))
    return Builder.Vertices[Point].id


# shared line setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def LineMut(Builder: SolidBuilder, Start: KPointTriple, Finish: KPointTriple) -> str:
    Keyed = frozenset((Start, Finish))
    if Keyed not in Builder.Edges:
        Named = f"e{len(Builder.Edges)}"
        Length = SquareRoot(
            sum((Latter - Former) ** 2 for Former, Latter in zip(Start, Finish))
        )
        Toward = tuple(
            (Latter - Former) / Length for Former, Latter in zip(Start, Finish)
        )
        Builder.Curves.append(
            LineCurve(
                id="c" + Named,
                origin=MakeVector(Start),
                direction=MakeVector((Toward[0], Toward[1], Toward[2])),
            )
        )
        Builder.Edges[Keyed] = BrepEdge(
            id=Named,
            start_vertex_id=VertexMut(Builder, Start),
            end_vertex_id=VertexMut(Builder, Finish),
            curve_id="c" + Named,
            start_parameter=0.0,
            end_parameter=Length,
        )
    return Builder.Edges[Keyed].id


# shared ring setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def RingMut(
    Builder: SolidBuilder, Center: KPointTriple, Normal: KPointTriple, Radius: float
) -> str:
    Keyed = (Center, Radius)
    if Keyed not in Builder.Edges:
        Named = f"e{len(Builder.Edges)}"
        Reference = Across(Normal)
        Point = tuple(
            Centre + Radius * Facing for Centre, Facing in zip(Center, Reference)
        )
        Vertex = VertexMut(Builder, (Point[0], Point[1], Point[2]))
        Builder.Curves.append(
            CircleCurve(
                id="c" + Named,
                center=MakeVector(Center),
                axis=MakeVector(Normal),
                reference_direction=MakeVector(Reference),
                radius=Radius,
            )
        )
        Builder.Edges[Keyed] = BrepEdge(
            id=Named,
            start_vertex_id=Vertex,
            end_vertex_id=Vertex,
            curve_id="c" + Named,
            start_parameter=0.0,
            end_parameter=2 * KHalfTurn,
        )
    return Builder.Edges[Keyed].id


# shared loop setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def LoopMut(
    Builder: SolidBuilder, Specs: tuple[KLineSpec | KRingSpec, ...], Named: str
) -> BrepLoop:
    Coedges: list[str] = []
    for EdgeSpec in Specs:
        if len(EdgeSpec) == 3:
            EdgeKey = RingMut(Builder, EdgeSpec[0], EdgeSpec[1], EdgeSpec[2])
        else:
            EdgeKey = LineMut(Builder, EdgeSpec[0], EdgeSpec[1])
        Builder.Coedges.append(
            BrepCoedge(id=f"k{len(Builder.Coedges)}", edge_id=EdgeKey)
        )
        Coedges.append(Builder.Coedges[-1].id)
    return BrepLoop(id=Named, coedge_ids=tuple(Coedges))


# shared build solid setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def BuildSolid(Faces: tuple[KFaceSpec, ...]) -> BrepModel:
    Builder = SolidBuilder()
    Loops: list[BrepLoop] = []
    Shaped: list[BrepFace] = []
    for Index, (Surface, Specs) in enumerate(Faces):
        Owned = [
            LoopMut(Builder, EdgeSpec, f"l{Index}_{Count}")
            for Count, EdgeSpec in enumerate(Specs)
        ]
        Loops.extend(Owned)
        Shaped.append(
            BrepFace(
                id=f"f{Index}",
                surface_id=Surface.id,
                loop_ids=tuple(Entry.id for Entry in Owned),
            )
        )
    FaceUses = tuple(
        BrepFaceUse(id=f"u{Entry.id}", face_id=Entry.id) for Entry in Shaped
    )
    return BrepModel(
        curves=tuple(Builder.Curves),
        surfaces=tuple({Surface.id: Surface for Surface, _ in Faces}.values()),
        vertices=tuple(Builder.Vertices.values()),
        edges=tuple(Builder.Edges.values()),
        coedges=tuple(Builder.Coedges),
        loops=tuple(Loops),
        faces=tuple(Shaped),
        face_uses=FaceUses,
        shells=(
            BrepShell(
                id="shell",
                face_use_ids=tuple(Entry.id for Entry in FaceUses),
                closed=True,
            ),
        ),
        shell_uses=(BrepShellUse(id="usage", shell_id="shell"),),
        regions=(BrepRegion(id="region", shell_use_ids=("usage",)),),
        bodies=(BrepBody(id="body", region_ids=("region",)),),
    )


# shared corner setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def Corner(Lower: KPointTriple, Upper: KPointTriple, Choices: str) -> KPointTriple:
    return (
        Upper[0] if Choices[0] == "1" else Lower[0],
        Upper[1] if Choices[1] == "1" else Lower[1],
        Upper[2] if Choices[2] == "1" else Lower[2],
    )


# shared ring of setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def RingOf(
    Lower: KPointTriple, Upper: KPointTriple, *Choices: str
) -> tuple[KLineSpec, ...]:
    Points = [Corner(Lower, Upper, Choice) for Choice in Choices]
    return tuple(zip(Points, Points[1:] + Points[:1]))


# shared box faces setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def BoxFaces(Lower: KPointTriple, Upper: KPointTriple) -> list[KFaceSpec]:
    return [
        (
            FlatSurface(Upper, (0.0, 1.0, 0.0)),
            (RingOf(Lower, Upper, "110", "010", "011", "111"),),
        ),
        (
            FlatSurface(Upper, (1.0, 0.0, 0.0)),
            (RingOf(Lower, Upper, "100", "110", "111", "101"),),
        ),
        (
            FlatSurface(Lower, (0.0, -1.0, 0.0)),
            (RingOf(Lower, Upper, "000", "100", "101", "001"),),
        ),
        (
            FlatSurface(Lower, (-1.0, 0.0, 0.0)),
            (RingOf(Lower, Upper, "010", "000", "001", "011"),),
        ),
        (
            FlatSurface(Upper, (0.0, 0.0, 1.0)),
            (RingOf(Lower, Upper, "001", "101", "111", "011"),),
        ),
        (
            FlatSurface(Lower, (0.0, 0.0, -1.0)),
            (RingOf(Lower, Upper, "000", "010", "110", "100"),),
        ),
    ]


# shared box solid setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def BoxSolid(Lower: KPointTriple, Upper: KPointTriple) -> BrepModel:
    return BuildSolid(tuple(BoxFaces(Lower, Upper)))


# shared hole solid setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def HoleSolid(
    Lower: KPointTriple, Upper: KPointTriple, Middle: tuple[float, float], Radius: float
) -> BrepModel:
    Bottom = (Middle[0], Middle[1], Lower[2])
    Upside = (Middle[0], Middle[1], Upper[2])
    TopRing: KRingSpec = (Upside, (0.0, 0.0, 1.0), Radius)
    BottomRing: KRingSpec = (Bottom, (0.0, 0.0, -1.0), Radius)
    Faces = BoxFaces(Lower, Upper)
    Faces[4] = (Faces[4][0], (*Faces[4][1], (TopRing,)))
    Faces[5] = (Faces[5][0], (*Faces[5][1], (BottomRing,)))
    TubeFace = (
        TubeSurface(Bottom, (0.0, 0.0, 1.0), Radius),
        ((TopRing,), (BottomRing,)),
    )
    return BuildSolid((TubeFace, *Faces))
