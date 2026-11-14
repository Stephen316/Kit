from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCoverage import (
    CheckCoverage,
)
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckInventory import (
    CheckInventory,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckSheets import CheckSheets
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckSolid import CheckSolid
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckSnapTags import (
    CheckSnapTags,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def CheckCircular(
    Model: DocumentModel,
    Shape: CircleShape,
    History: HistoryModel | FrustumHistory | None,
    Solid: FrustumBody | None,
) -> None:
    for PartValue in Model.Snapshots:
        Snapshot = PartValue.Snapshot
        if isinstance(Snapshot, SnapshotModel) and isinstance(History, HistoryModel):
            if Snapshot.Model != History.Model or Snapshot.TagSet != History.TagSet:
                raise ValueError("Native circular snapshot disagrees with body history")
        elif isinstance(Snapshot, GeometryState):
            CheckRoundState(Snapshot, Shape, History, Solid)
        else:
            raise ValueError("Unsupported native circular snapshot profile")


def CheckRoundState(
    State: GeometryState,
    Shape: CircleShape,
    History: HistoryModel | FrustumHistory | None,
    Solid: FrustumBody | None,
) -> None:
    CheckInventory(State, Solid is not None)
    CheckCoverage(State)
    Sheets: list[FaceNode] = []
    SolidFaces: tuple[FaceNode, ...] = ()
    for Entity in State.Entities:
        if not isinstance(Entity, BodyNode):
            continue
        Faces = BodyFaces(State, Entity)
        if len(Faces) == 1:
            Sheets.extend(Faces)
        elif len(Faces) == 3 and Solid is not None and not SolidFaces:
            CheckSolid(State, Faces, Solid)
            SolidFaces = Faces
        else:
            raise ValueError("Native circular snapshot contains an unsupported body")
    if bool(SolidFaces) != (Solid is not None):
        raise ValueError("Native circular snapshot is missing its modeled solid")
    CheckSheets(State, tuple(Sheets), Shape)
    Sketch = SketchLink(CurveTag(Shape.CurveNode), 0, 0, 1, 1)
    CheckSnapTags(
        State, SolidFaces, Sketch, History.TagSet if History is not None else None
    )
