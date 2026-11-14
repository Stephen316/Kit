from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import FaceCoedges
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCarriers import CheckPlane
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckRim import CheckRim
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode


def CheckSheets(
    State: GeometryState, Faces: tuple[FaceNode, ...], Shape: CircleShape
) -> None:
    Center = (Shape.Geometry.center.x / 10, Shape.Geometry.center.y / 10, 0.0)
    if len(Faces) not in (1, 2) or sorted(
        FaceValue.DoubleSided for FaceValue in Faces
    ) != ([False] if len(Faces) == 1 else [False, True]):
        raise ValueError("Native circular snapshot has unaccounted sheet bodies")
    for FaceValue in Faces:
        if FaceValue.Reversed or FaceValue.Contained != (
            False if FaceValue.DoubleSided else None
        ):
            raise ValueError(
                "Native circle snapshot sheet has unsupported face orientation"
            )
        CheckPlane(SnapEntity(State, FaceValue.Surface, PlaneNode), Center)
        Coedges = FaceCoedges(State, FaceValue)
        if len(Coedges) != 1 or Coedges[0].Partner != -1 or Coedges[0].Reversed:
            raise ValueError(
                "Native circle snapshot requires an open planar circular loop"
            )
        CheckRim(
            State,
            SnapEntity(State, Coedges[0].EdgeRef, EdgeNode),
            Center,
            Shape.Geometry.radius / 10,
            False,
        )
