from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.TSplineCodec.Model.CageLink import CageLink
from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


@MakeDataClass(frozen=True, slots=True)
class CageGraph:
    Links: tuple[CageLink, ...]
    Heads: tuple[int, ...]
    Fans: tuple[tuple[int, ...], ...]
    Loops: tuple[tuple[int, ...], ...]
    Open: tuple[bool, ...]
    Creased: tuple[bool, ...]
    Sharp: tuple[bool, ...]
    Inside: tuple[bool, ...]
    Regular: tuple[bool, ...]


def VertexFan(Topology: CageTopology, VertexIndex: int) -> tuple[int, ...]:
    Links = Topology.Links
    FirstLink = Topology.Vertices[VertexIndex].OriginLink
    FanLinks = [FirstLink]
    NextLink = Links[Links[FirstLink].Previous].Opposite
    while NextLink != FirstLink:
        if len(FanLinks) > len(Links):
            raise ValueError("Fusion Form capped layout found an open vertex fan")
        FanLinks.append(NextLink)
        NextLink = Links[Links[NextLink].Previous].Opposite
    return tuple(FanLinks)


def FaceLoop(Topology: CageTopology, FaceIndex: int) -> tuple[int, ...]:
    FaceValue = Topology.Faces[FaceIndex]
    if FaceValue.IsHidden:
        raise ValueError("Fusion Form capped layout does not take hidden faces")
    LoopLinks = [FaceValue.OriginLink]
    while len(LoopLinks) <= 4:
        LoopLinks.append(Topology.Links[LoopLinks[-1]].NextLink)
    if LoopLinks[4] != LoopLinks[0] or len(set(LoopLinks[:4])) != 4:
        raise ValueError("Fusion Form capped layout needs quad cage faces")
    return tuple(LoopLinks[:4])


def ReadGraph(Surface: TsplineSurface) -> CageGraph:
    Topology = Surface.Topology
    Links = Topology.Links
    Creases = Surface.Creases
    CreaseEdges = frozenset(Creases.EdgeIndices if Creases else ())
    FanTable = tuple(
        VertexFan(Topology, Index) for Index in range(len(Topology.Vertices))
    )
    OpenLinks = tuple(
        LinkValue.FaceIndex < 0 or Links[LinkValue.Opposite].FaceIndex < 0
        for LinkValue in Links
    )
    CreasedLinks = tuple(LinkValue.EdgeIndex in CreaseEdges for LinkValue in Links)
    InsideVerts = tuple(
        not any(OpenLinks[Entry] for Entry in FanLinks) for FanLinks in FanTable
    )
    return CageGraph(
        Links,
        tuple(Links[LinkValue.NextLink].VertexIndex for LinkValue in Links),
        FanTable,
        tuple(FaceLoop(Topology, Index) for Index in range(len(Topology.Faces))),
        OpenLinks,
        CreasedLinks,
        tuple(First or Second for First, Second in zip(OpenLinks, CreasedLinks)),
        InsideVerts,
        tuple(
            Inner and len(FanLinks) == 4
            for Inner, FanLinks in zip(InsideVerts, FanTable)
        ),
    )


def StraightLink(Graph: CageGraph, LinkIndex: int) -> int | None:
    HeadVertex = Graph.Heads[LinkIndex]
    if not Graph.Regular[HeadVertex]:
        return None
    FanLinks = Graph.Fans[HeadVertex]
    Inbound = FanLinks.index(Graph.Links[LinkIndex].Opposite)
    return FanLinks[(Inbound + 2) % 4]
