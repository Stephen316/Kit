from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel

from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# shared change rotary setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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


# shared change snapshot tag setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
