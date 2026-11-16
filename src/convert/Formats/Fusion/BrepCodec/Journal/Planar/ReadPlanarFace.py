from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBoundary import ReadBoundary
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


# the planar face operation needs a distinct decoding boundary so topology changes retain their native revision relationships
def ReadPlanarFace(Table: LiveTable, FaceRef: int, ShellRef: int) -> FaceBoundary:
    FaceValue = RequireLive(Table, FaceRef, FaceNode)
    if StableRef(Table, FaceValue.OwnerShell) != ShellRef or FaceValue.DoubleSided:
        raise ValueError("Unsupported Fusion planar face ownership or sidedness")
    LoopValue = RequireLive(Table, FaceValue.FirstLoop, LoopNode)
    if LoopValue.NextLoop != -1 or StableRef(Table, LoopValue.OwnerFace) != FaceRef:
        raise ValueError("Fusion planar face requires one owned outer loop")
    Surface = RequireLive(Table, FaceValue.Surface, PlaneNode)
    BoundaryUses = ReadBoundary(
        Table, LoopValue.FirstCoedge, StableRef(Table, FaceValue.FirstLoop)
    )
    return FaceBoundary(FaceRef, Surface, FaceValue.Reversed, BoundaryUses)
