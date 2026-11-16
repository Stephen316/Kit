from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Native import (
    KStreamOrderSupportSource,
    KUnresolvedSupportSource,
)
from convert.adapters.solidworks.Core.Cut.CutOwners import FindCutOwner
from convert.adapters.solidworks.Core.Cut.CutPerimeter import KCutLoopSource
from convert.adapters.solidworks.Core.Cut.FaceChart import PlaceCutFrame
from convert.adapters.solidworks.Core.Cut.FaceSelection import (
    CutFaceSource,
    MakeCutFacePick,
)
from convert.adapters.solidworks.Resolved.Support.SupportPlane import (
    SupportPlane as SavedSupport,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector

# the typed historical face remains distinct from a qualified editable export plane
KFaceSupportSource = "typed-archive-face"


# a face attachment requires the four typed local lines to form the owned directed loop
def CheckCutLoop(SketchValue: Sketch) -> None:
    RequireArch(
        SketchValue.attributes.get("native_geometry_source"),
        KCutLoopSource,
        "typed cut perimeter available",
    )
    RequireArch(len(SketchValue.closed_profile_entity_ids), 1, "one cut perimeter loop")
    (LoopValue,) = SketchValue.closed_profile_entity_ids
    RequireArch(
        (len(LoopValue), len(set(LoopValue))),
        (4, 4),
        "four unique loop member identities",
    )
    Entities = {Value.id: Value for Value in SketchValue.entities}
    Lines: list[LineGeometry] = []
    for Identity in LoopValue:
        Member = Entities[Identity]
        Geometry = Member.geometry
        if not isinstance(Geometry, LineGeometry) or Member.construction:
            raise ValueError("Cut loop contains an unsupported perimeter member")
        Lines.append(Geometry)
    RequireArch(
        all(
            Value.end == NextValue.start
            for Value, NextValue in zip(Lines, Lines[1:] + Lines[:1], strict=True)
        ),
        True,
        "closed directed cut perimeter",
    )


# only the earlier active join identified by the cap can own a new sketch face support
def FindCutBoss(
    Document: CadDocument, ProfileStep: FeatureStep, BossId: int
) -> FeatureStep:
    Identity = f"sldprt:feature:{BossId}"
    Matches = [Value for Value in Document.feature_timeline if Value.id == Identity]
    RequireArch(len(Matches), 1, "unique earlier solidworks boss")
    (BossStep,) = Matches
    RequireArch(
        (
            BossStep.kind,
            BossStep.operation,
            BossStep.suppressed,
            BossStep.order < ProfileStep.order,
        ),
        (FeatureKind.KExtrusion, BooleanOp.KJoin, False, True),
        "active earlier boss owns cut support",
    )
    return BossStep


# the face replaces only the existing provisional principal attachment and its dependency
def CheckCutPlane(
    Document: CadDocument,
    SketchValue: Sketch,
    ProfileStep: FeatureStep,
    BossStep: FeatureStep,
) -> None:
    RequireArch(
        SketchValue.attributes.get("support_plane_source")
        in (KStreamOrderSupportSource, KUnresolvedSupportSource),
        True,
        "replaceable provisional cut support",
    )
    Matches = [
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    ]
    RequireArch(len(Matches), 1, "unique provisional neutral cut plane")
    (Fallback,) = Matches
    RequireArch(Fallback.support_selection_id, None, "unbound provisional cut plane")
    NativeId = SketchValue.attributes.get("support_plane_native_id")
    RequireArch(
        Fallback.id, f"sldprt:plane:{NativeId}", "same provisional plane identity"
    )
    RequireArch(
        all(
            Value in (f"sldprt:feature:{NativeId}", BossStep.id)
            for Value in ProfileStep.input_feature_ids
        ),
        True,
        "only the provisional support or proved boss may precede the cut profile",
    )


# only the cut that completed the saved target walk can use this cap normal
def BindCutAxis(
    StepValue: FeatureStep, CutId: int, SketchId: str, Normal: SpaceVector
) -> FeatureStep:
    Definition = StepValue.definition
    if (
        StepValue.id == f"sldprt:feature:{CutId}"
        and StepValue.sketch_id == SketchId
        and StepValue.operation == BooleanOp.KCutOperation
        and StepValue.kind == FeatureKind.KExtrusion
        and not StepValue.suppressed
        and isinstance(Definition, ExtrudeFeature)
        and Definition.reversed
        and Definition.direction is None
    ):
        return Replace(StepValue, definition=Replace(Definition, direction=Normal))
    return StepValue


# neutral history and the new frame must point to the same persistent historical selection
def AttachCutFrame(
    Document: CadDocument,
    SketchValue: Sketch,
    ProfileStep: FeatureStep,
    BossStep: FeatureStep,
    PlaneValue: SupportPlane,
    FacePick: Selection,
    CutId: int | None,
) -> CadDocument:
    Bound = Replace(
        SketchValue,
        support_plane_id=PlaneValue.id,
        attributes=FreezeMapping(
            {
                **SketchValue.attributes,
                "support_plane_source": KFaceSupportSource,
                "support_plane_native_id": None,
                "unframed_support_plane_native_id": None,
            }
        ),
    )
    Profile = Replace(
        ProfileStep,
        input_feature_ids=(BossStep.id,),
        selection_ids=(*ProfileStep.selection_ids, FacePick.id),
    )
    return Replace(
        Document,
        support_planes=(*Document.support_planes, PlaneValue),
        selections=(*Document.selections, FacePick),
        sketches=tuple(
            Bound if Value is SketchValue else Value for Value in Document.sketches
        ),
        feature_timeline=tuple(
            (
                Profile
                if Value is ProfileStep
                else (
                    BindCutAxis(
                        Value, CutId, SketchValue.id, PlaneValue.transform.z_axis
                    )
                    if CutId is not None
                    else Value
                )
            )
            for Value in Document.feature_timeline
        ),
    )


# projection leaves the entire previous document intact when any owner or frame proof fails
def ProjectCutFace(
    Document: CadDocument,
    Support: SavedSupport,
    ProfileId: int,
    BossId: int,
    CutId: int,
    StreamName: str,
) -> CadDocument:
    try:
        SketchValue, ProfileStep = FindCutOwner(Document, ProfileId)
        CheckCutLoop(SketchValue)
        BossStep = FindCutBoss(Document, ProfileStep, BossId)
        CheckCutPlane(Document, SketchValue, ProfileStep, BossStep)
        Frame = PlaceCutFrame(Support["face"]["plane"])
        Source = CutFaceSource(Support, StreamName)
        FacePick = MakeCutFacePick(
            BossStep, BossId, ProfileId, Support, Frame.origin, Source
        )
        PlaneId = f"sldprt:plane:{ProfileId}:face"
        RequireArch(
            any(Value.id == PlaneId for Value in Document.support_planes),
            False,
            "unused cut support plane identity",
        )
        RequireArch(
            any(Value.id == FacePick.id for Value in Document.selections),
            False,
            "unused face selection identity",
        )
    except (KeyError, ValueError):
        return Document
    PlaneValue = SupportPlane(
        id=PlaneId,
        name=f"{SketchValue.name} face support",
        transform=Frame,
        support_selection_id=FacePick.id,
        provenance=Source,
    )
    return AttachCutFrame(
        Document, SketchValue, ProfileStep, BossStep, PlaneValue, FacePick, CutId
    )
