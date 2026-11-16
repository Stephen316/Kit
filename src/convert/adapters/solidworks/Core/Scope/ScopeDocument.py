from dataclasses import replace as Replace

from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError, ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Cut.FaceChart import PlaceCutFrame
from convert.adapters.solidworks.Core.Cut.FaceSelection import (
    CutFaceSource,
    MakeCutFacePick,
)
from convert.adapters.solidworks.Core.Partition.ScopePartProjection import (
    ProjectScope,
    ScopePart,
)
from convert.adapters.solidworks.Core.Scope.ScopeFeatures import (
    ScopeBodyPicks,
    ScopeBossStep,
    ScopeCutStep,
)
from convert.adapters.solidworks.Core.Scope.ScopeSketch import (
    BuildScopeRect,
    ScopeDatum,
)
from convert.adapters.solidworks.Resolved.RectanglePart import RectanglePart
from convert.adapters.solidworks.Resolved.Scope.CutProfile import (
    ReadScopeCut,
    ScopeCutProof,
)
from convert.adapters.solidworks.Resolved.Scope.History import (
    ReadBossHistory,
    ScopeHistory,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Records.RecordParameter import Parameter

# the fallback notice remains until all scoped source joins succeed
KScopeUnresolved = "Recognized two-body scope records. Neutral body history and feature scope remain unresolved."


# a full source walk is required before replacing the fallback model with both native bodies
def ReadScopeDoc(
    Document: CadDocument,
    Archive: SldprtArchive,
    ConfigId: int,
    Payloads: tuple[BrepPayload, ...],
    *,
    RetainBrep: bool,
) -> CadDocument:
    Generation = ContainerMo(Archive.streams)
    if Generation != KConfigGen:
        raise ArchiveError("unsupported scoped part generation")
    StreamName = f"Contents/Config-{ConfigId}-ResolvedFeatures"
    ConfigMap, ConfigWalk = ReadOrdinaryMap(
        Archive.require(f"Contents/Config-{ConfigId}"), Generation, Scoped=True
    )
    History = ReadBossHistory(ConfigMap, Archive.require(StreamName), Generation)
    Owners = (History.First.Owner, History.Second.Owner)
    Proof = ReadScopeCut(
        History.Cursor, Generation, History.First.Choices["caps"][1], Owners
    )
    PartValue = ProjectScope(Payloads, ConfigId, Proof.Operation, Owners)
    Expected = {
        BodyValue.attributes["native_recent_atom_id"] for BodyValue in PartValue.Bodies
    }
    RequireArch(
        all(
            {RowValue[0] for RowValue in Group} == Expected
            for Group in ConfigWalk["regions"]
        ),
        True,
        "the active partition and configuration name the same result atoms",
    )
    return AttachScopeDoc(Document, History, Proof, PartValue, StreamName, RetainBrep)


# both independently created bosses retain the typed profiles and their native parameters
def AttachBosses(
    Document: CadDocument,
    History: ScopeHistory,
    StreamName: str,
) -> CadDocument:
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    Params = {Value.id: Value for Value in Document.parameters}
    Sketches = {Value.id: Value for Value in Document.sketches}
    Planes = {Value.id: Value for Value in Document.support_planes}
    ChangedSteps = {}
    ChangedParams: dict[str, Parameter] = {}
    ChangedSketches = {}
    ChangedPlanes = {}
    First = History.First
    Anchor = RectanglePart(
        First.Profile.Sketch,
        First.Profile.Datum,
        First.Profile.Reference,
        First.Profile.Directions,
        History.Origin,
        None,
    )
    for BossValue, OriginAnchor in ((First, Anchor), (History.Second, None)):
        Profile = BossValue.Profile
        PlaneId = f"sldprt:plane:{Profile.Datum.FeatureId}"
        Datum = ScopeDatum(Planes[PlaneId], Profile, StreamName)
        ChangedPlanes[Datum.id] = Datum
        BossSketchId = f"sldprt:sketch:{Profile.Sketch.FeatureId}"
        ChangedSketches[BossSketchId] = BuildScopeRect(
            Sketches[BossSketchId], Profile.Sketch, Datum, StreamName, OriginAnchor
        )
        ProfileStep = Steps[f"sldprt:feature:{Profile.Sketch.FeatureId}"]
        ChangedSteps[ProfileStep.id] = Replace(
            ProfileStep,
            input_feature_ids=(f"sldprt:feature:{Profile.Datum.FeatureId}",),
        )
        BossStep, Dimensions = ScopeBossStep(
            Steps[f"sldprt:feature:{BossValue.Owner.FeatureId}"],
            BossValue,
            Params,
            StreamName,
        )
        ChangedSteps[BossStep.id] = BossStep
        ChangedParams.update((Value.id, Value) for Value in Dimensions)
    return Replace(
        Document,
        parameters=tuple(
            ChangedParams.get(Value.id, Value) for Value in Document.parameters
        ),
        support_planes=tuple(
            ChangedPlanes.get(Value.id, Value) for Value in Document.support_planes
        ),
        sketches=tuple(
            ChangedSketches.get(Value.id, Value) for Value in Document.sketches
        ),
        feature_timeline=tuple(
            ChangedSteps.get(Value.id, Value) for Value in Document.feature_timeline
        ),
    )


# the same earlier boss cap owns the cut frame and its historical selection
def AttachScopeCut(
    Document: CadDocument,
    History: ScopeHistory,
    Proof: ScopeCutProof,
    PartValue: ScopePart,
    StreamName: str,
) -> CadDocument:
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    Sketches = {Value.id: Value for Value in Document.sketches}
    First = History.First
    CutValue = Proof.Operation
    CutId = f"sldprt:feature:{CutValue['native_feature_id']}"
    ProfileId = Proof.Profile.FeatureId
    PlaneId = f"sldprt:plane:{ProfileId}:face"
    RequireArch(
        PlaneId in {Value.id for Value in Document.support_planes},
        False,
        "unused scoped face support identity",
    )
    Frame = PlaceCutFrame(Proof.Support["face"]["plane"])
    Source = CutFaceSource(Proof.Support, StreamName)
    FirstBoss = Steps[f"sldprt:feature:{First.Owner.FeatureId}"]
    FacePick = MakeCutFacePick(
        FirstBoss, First.Owner.FeatureId, ProfileId, Proof.Support, Frame.origin, Source
    )
    Support = SupportPlane(
        PlaneId,
        f"{Proof.Profile.NameValue} face support",
        Frame,
        support_selection_id=FacePick.id,
        provenance=Source,
    )
    CutSketchId = f"sldprt:sketch:{ProfileId}"
    CutSketch = BuildScopeRect(
        Sketches[CutSketchId], Proof.Profile, Support, StreamName
    )
    ProfileStep = Replace(
        Steps[f"sldprt:feature:{ProfileId}"],
        input_feature_ids=(FirstBoss.id,),
        selection_ids=(FacePick.id,),
    )
    BodyPicks = ScopeBodyPicks(CutValue, StreamName)
    Affected = tuple(
        Value.id for Value in PartValue.Bodies if Value.final_feature_id == CutId
    )
    CutStep = ScopeCutStep(
        Steps[CutId],
        CutValue,
        ProfileId,
        (First.Owner, History.Second.Owner),
        BodyPicks,
        Affected,
        Frame.z_axis,
        StreamName,
    )
    ChangedSteps = {ProfileStep.id: ProfileStep, CutStep.id: CutStep}
    return Replace(
        Document,
        support_planes=(*Document.support_planes, Support),
        sketches=tuple(
            CutSketch if Value.id == CutSketchId else Value
            for Value in Document.sketches
        ),
        selections=(*Document.selections, FacePick, *BodyPicks),
        feature_timeline=tuple(
            ChangedSteps.get(Value.id, Value) for Value in Document.feature_timeline
        ),
    )


# scoped history and geometry are published together only after document validation
def AttachScopeDoc(
    Document: CadDocument,
    History: ScopeHistory,
    Proof: ScopeCutProof,
    PartValue: ScopePart,
    StreamName: str,
    RetainBrep: bool,
) -> CadDocument:
    RequireArch(
        {Value.id for Value in Document.sketches},
        {
            f"sldprt:sketch:{Profile.FeatureId}"
            for Profile in (
                History.First.Profile.Sketch,
                History.Second.Profile.Sketch,
                Proof.Profile,
            )
        },
        "typed owners cover all saved scoped sketches",
    )
    Bosses = AttachBosses(Document, History, StreamName)
    HistoryDoc = AttachScopeCut(Bosses, History, Proof, PartValue, StreamName)
    Bodies = (
        PartValue.Bodies
        if RetainBrep
        else tuple(
            Replace(
                Value,
                attributes=FreezeMapping(
                    {
                        NameValue: ItemValue
                        for NameValue, ItemValue in Value.attributes.items()
                        if NameValue != "parasolid_active_payload_id"
                    }
                ),
            )
            for Value in PartValue.Bodies
        )
    )
    Scoped = Replace(
        HistoryDoc,
        bodies=Bodies,
        brep=PartValue.ModelValue if RetainBrep else None,
        diagnostics=tuple(
            Value
            for Value in HistoryDoc.diagnostics
            if Value.message != KScopeUnresolved
        ),
    )
    Scoped.assert_valid()
    return Scoped
