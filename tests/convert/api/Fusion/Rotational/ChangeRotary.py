from convert.formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel

from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.convert.api.Fusion.Native.ChangeNative import ChangeField


def ChangeRotary(Model: DocumentModel, RoleName: str) -> DocumentModel:
    if RoleName == "circle":
        Circle = BuildGraph(Model).OneClass("CircArc3D")
        return ChangeField(Model, Circle.ObjectId, "isFixed", True)
    if RoleName == "extrusion":
        Snapshot = Model.Snapshots[0]
        if not isinstance(Snapshot.Snapshot, SnapshotModel):
            raise ValueError("Cylinder corruption requires its qualified snapshot")
        Shape = ReplaceData(Snapshot.Snapshot.Model, Radius=19.0)
        Altered = ReplaceData(Snapshot.Snapshot, Model=Shape)
        return ReplaceData(Model, Snapshots=(ReplaceData(Snapshot, Snapshot=Altered),))
    BodyValue = Model.Bodies[0]
    if not isinstance(BodyValue.History, FrustumHistory):
        raise ValueError("Frustum corruption requires conical history")
    Identity = ReplaceData(BodyValue.History.Identity, SecondaryId=987)
    History = ReplaceData(BodyValue.History, Identity=Identity)
    return ReplaceData(Model, Bodies=(ReplaceData(BodyValue, History=History),))


def ChangeSnapTag(Model: DocumentModel) -> DocumentModel:
    PartValue = Model.Snapshots[0]
    Snapshot = PartValue.Snapshot
    if not isinstance(Snapshot, GeometryState):
        raise ValueError("Circular corruption requires generic snapshot geometry")
    Entities = tuple(
        (
            ReplaceData(
                Entity, SourceLink=ReplaceData(Entity.SourceLink, PrimaryId=987)
            )
            if isinstance(Entity, SketchAttrib)
            else Entity
        )
        for Entity in Snapshot.Entities
    )
    Changed = ReplaceData(PartValue, Snapshot=ReplaceData(Snapshot, Entities=Entities))
    return ReplaceData(Model, Snapshots=(Changed,))
