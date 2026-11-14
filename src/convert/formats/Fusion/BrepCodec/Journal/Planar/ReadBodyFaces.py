from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarFace import (
    ReadPlanarFace,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


def ReadBodyFaces(Table: LiveTable, BodyRef: int) -> tuple[FaceBoundary, ...]:
    BodyValue = RequireLive(Table, BodyRef, BodyNode)
    LumpValue = RequireLive(Table, BodyValue.FirstLump, LumpNode)
    if LumpValue.NextLump != -1 or StableRef(Table, LumpValue.OwnerBody) != BodyRef:
        raise ValueError("Fusion planar body requires one owned lump")
    ShellValue = RequireLive(Table, LumpValue.FirstShell, ShellNode)
    if ShellValue.NextShell != -1 or StableRef(
        Table, ShellValue.OwnerLump
    ) != StableRef(Table, BodyValue.FirstLump):
        raise ValueError("Fusion planar body requires one owned shell")
    Current = ShellValue.FirstFace
    Results: list[FaceBoundary] = []
    SeenRefs: set[int] = set()
    while Current != -1:
        Current = StableRef(Table, Current)
        if Current in SeenRefs:
            raise ValueError("Cyclic Fusion planar face ownership")
        SeenRefs.add(Current)
        Results.append(
            ReadPlanarFace(Table, Current, StableRef(Table, LumpValue.FirstShell))
        )
        Current = RequireLive(Table, Current, FaceNode).NextFace
    if len(Results) < 4:
        raise ValueError("Fusion closed planar body requires at least four faces")
    return tuple(Results)
