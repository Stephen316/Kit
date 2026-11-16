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
    ReadScopeHistory,
    ScopeHistory,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Records.RecordParameter import Parameter

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
    ConfigMap, Walk = ReadOrdinaryMap(
        Archive.require(f"Contents/Config-{ConfigId}"), Generation, Scoped=True
    )
    History = ReadScopeHistory(ConfigMap, Archive.require(StreamName), Generation)
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
            {RowValue[0] for RowValue in Group} == Expected for Group in Walk["regions"]
        ),
        True,
        "the active partition and configuration name the same result atoms",
    )
    return AttachScopeDoc(Document, History, Proof, PartValue, StreamName, RetainBrep)


# the scope projection publishes geometry, history and selection only as one validated document
def AttachScopeDoc(
    Document: CadDocument,
    History: ScopeHistory,
    Proof: ScopeCutProof,
    PartValue: ScopePart,
    StreamName: str,
    RetainBrep: bool,
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

    CutValue = Proof.Operation
    CutId = f"sldprt:feature:{CutValue['native_feature_id']}"
    ProfileId = Proof.Profile.FeatureId
    PlaneId = f"sldprt:plane:{ProfileId}:face"
    RequireArch(PlaneId in Planes, False, "unused scoped face support identity")
    Frame = PlaceCutFrame(Proof.Support["face"]["plane"])
    Source = CutFaceSource(Proof.Support, StreamName)
    FirstBoss = ChangedSteps[f"sldprt:feature:{First.Owner.FeatureId}"]
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
    ChangedSketches[CutSketchId] = BuildScopeRect(
        Sketches[CutSketchId], Proof.Profile, Support, StreamName
    )
    CutProfile = Steps[f"sldprt:feature:{ProfileId}"]
    ChangedSteps[CutProfile.id] = Replace(
        CutProfile,
        input_feature_ids=(FirstBoss.id,),
        selection_ids=(FacePick.id,),
    )
    BodyPicks = ScopeBodyPicks(CutValue, StreamName)
    Affected = tuple(
        Value.id for Value in PartValue.Bodies if Value.final_feature_id == CutId
    )
    ChangedSteps[CutId] = ScopeCutStep(
        Steps[CutId],
        CutValue,
        ProfileId,
        (First.Owner, History.Second.Owner),
        BodyPicks,
        Affected,
        Frame.z_axis,
        StreamName,
    )
    RequireArch(
        set(ChangedSketches),
        set(Sketches),
        "typed owners cover all saved scoped sketches",
    )
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
        Document,
        parameters=tuple(
            ChangedParams.get(Value.id, Value) for Value in Document.parameters
        ),
        support_planes=(
            *(ChangedPlanes.get(Value.id, Value) for Value in Document.support_planes),
            Support,
        ),
        sketches=tuple(ChangedSketches[Value.id] for Value in Document.sketches),
        selections=(*Document.selections, FacePick, *BodyPicks),
        feature_timeline=tuple(
            ChangedSteps.get(Value.id, Value) for Value in Document.feature_timeline
        ),
        bodies=Bodies,
        brep=PartValue.ModelValue if RetainBrep else None,
        diagnostics=tuple(
            Value for Value in Document.diagnostics if Value.message != KScopeUnresolved
        ),
    )
    Scoped.assert_valid()
    return Scoped
