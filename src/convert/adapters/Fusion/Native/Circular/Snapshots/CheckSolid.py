from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import FaceCoedges
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCarriers import (
    CheckPlane,
    CheckCone,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckRim import CheckRim
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def CheckSolid(
    State: GeometryState, Faces: tuple[FaceNode, ...], Model: FrustumBody
) -> None:
    ConeCount = 0
    CapLevels: set[bool] = set()
    for FaceValue in Faces:
        if FaceValue.DoubleSided or FaceValue.Contained is not None:
            raise ValueError("Native circular solid has a sheet face")
        Surface = State.Entities[FaceValue.Surface]
        Coedges = FaceCoedges(State, FaceValue)
        if isinstance(Surface, ConeNode):
            CheckCone(Surface, Model)
            ConeCount += 1
            if FaceValue.Reversed or len(Coedges) != 2:
                raise ValueError("Native circular side face requires two forward loops")
        elif isinstance(Surface, PlaneNode):
            IsTop = Surface.OriginCm[2] > Model.BasePoint[2] / 10
            Center = (
                Model.BasePoint[0] / 10,
                Model.BasePoint[1] / 10,
                (Model.BasePoint[2] + (Model.Height if IsTop else 0.0)) / 10,
            )
            CheckPlane(Surface, Center)
            CapLevels.add(IsTop)
            if len(Coedges) != 1 or FaceValue.Reversed == IsTop:
                raise ValueError(
                    "Native circular cap orientation disagrees with its solid"
                )
        else:
            raise ValueError("Native circular solid contains an unsupported surface")
        for Coedge in Coedges:
            if Coedge.Partner == -1 or Coedge.Reversed != isinstance(
                Surface, PlaneNode
            ):
                raise ValueError(
                    "Native circular solid coedge orientation disagrees with its carrier"
                )
            CheckSolidRim(State, SnapEntity(State, Coedge.EdgeRef, EdgeNode), Model)
    if len(Faces) != 3 or ConeCount != 1 or CapLevels != {False, True}:
        raise ValueError(
            "Native circular solid requires one side and two distinct caps"
        )


def CheckSolidRim(
    State: GeometryState, EdgeValue: EdgeNode, Model: FrustumBody
) -> None:
    Curve = SnapEntity(State, EdgeValue.CurveRef, EllipseNode)
    IsTop = Curve.OriginCm[2] > Model.BasePoint[2] / 10
    Center = (
        Model.BasePoint[0] / 10,
        Model.BasePoint[1] / 10,
        (Model.BasePoint[2] + (Model.Height if IsTop else 0.0)) / 10,
    )
    CheckRim(
        State,
        EdgeValue,
        Center,
        (Model.TopRadius if IsTop else Model.BottomRadius) / 10,
        IsTop,
    )
