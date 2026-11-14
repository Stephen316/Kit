from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode


def BodyFaces(State: GeometryState, BodyValue: BodyNode) -> tuple[FaceNode, ...]:
    LumpValue = SnapEntity(State, BodyValue.FirstLump, LumpNode)
    Shell = SnapEntity(State, LumpValue.FirstShell, ShellNode)
    if (
        BodyValue.TransformRef != -1
        or LumpValue.NextLump != -1
        or Shell.NextShell != -1
    ):
        raise ValueError(
            "Native circular snapshot requires one untransformed shell per body"
        )
    Faces: list[FaceNode] = []
    Identity = Shell.FirstFace
    while Identity != -1:
        FaceValue = SnapEntity(State, Identity, FaceNode)
        if FaceValue in Faces:
            raise ValueError("Native snapshot face chain is cyclic")
        Faces.append(FaceValue)
        Identity = FaceValue.NextFace
    return tuple(Faces)


def FaceCoedges(State: GeometryState, FaceValue: FaceNode) -> tuple[CoedgeNode, ...]:
    Coedges: list[CoedgeNode] = []
    SeenLoops: set[int] = set()
    Identity = FaceValue.FirstLoop
    while Identity != -1:
        if Identity in SeenLoops:
            raise ValueError("Native snapshot loop chain is cyclic")
        SeenLoops.add(Identity)
        LoopValue = SnapEntity(State, Identity, LoopNode)
        Coedge = SnapEntity(State, LoopValue.FirstCoedge, CoedgeNode)
        if (
            Coedge.NextCoedge != LoopValue.FirstCoedge
            or Coedge.PriorCoedge != LoopValue.FirstCoedge
        ):
            raise ValueError(
                "Native circular snapshot requires one full-circle coedge per loop"
            )
        Coedges.append(Coedge)
        Identity = LoopValue.NextLoop
    return tuple(Coedges)
