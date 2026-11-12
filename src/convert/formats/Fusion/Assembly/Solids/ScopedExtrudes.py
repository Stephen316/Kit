from dataclasses import replace as Replace

from convert.formats.Fusion.Assembly.Solids.AuthoringAxis import ResolveAuthAxis
from convert.formats.Fusion.Assembly.Solids.CreatorScopes import ReadAsmScopes
from convert.formats.Fusion.Extrudes.ExtrudeAttach import AttachDistExt
from convert.formats.Fusion.Extrudes.SolidCreators import FindExtCreators, IsSavedActive
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.document.models.DocumentModel import AssemblyData, CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep


# component scope and sketch ownership must agree before publishing any assembly geometry
def ReadScopedExts(
    Document: CadDocument,
    Assembly: AssemblyData,
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OwnerId: int,
    Edits: dict[str, int],
) -> tuple[CadDocument, tuple[FeatureStep, ...]]:
    Steps = {
        int(StepValue.provenance.native_id): StepValue
        for StepValue in Document.feature_timeline
        if StepValue.provenance is not None
    }
    SketchSteps = {
        StepValue.sketch_id: Identity
        for Identity, StepValue in Steps.items()
        if StepValue.sketch_id is not None
        and Owners[Identity].ClassGuid == KSketchFeature
    }
    FrameMap = {Plane.id: Plane for Plane in Document.support_planes}
    SketchFrames = {
        SketchValue.id: FrameMap.get(SketchValue.support_plane_id)
        for SketchValue in Document.sketches
    }
    ExtIds = {
        Identity
        for Identity, StepValue in Steps.items()
        if StepValue.kind == FeatureKind.KExtrusion
    }
    Scopes = ReadAsmScopes(
        BulkData, Owners, OwnerId, frozenset(ExtIds | set(SketchSteps.values()))
    )
    Params = {Param.id: Param for Param in Document.parameters}
    Resolved: dict[str, FeatureStep] = {}
    for Identity, StepValue in Steps.items():
        if Identity not in ExtIds or not IsSavedActive(StepValue):
            continue
        Scope = Scopes.get(Identity)
        SketchId = StepValue.sketch_id or ""
        Frame = SketchFrames.get(SketchId)
        SketchIdentity = SketchSteps.get(SketchId)
        if (
            Scope is None
            or Frame is None
            or SketchIdentity is None
            or Scopes.get(SketchIdentity) != Scope
            or Frame.attributes.get("fusion.component_object_id") != Scope.ComponentId
        ):
            raise ValueError(
                "Fusion assembly Extrude and sketch component scopes disagree"
            )
        if not isinstance(StepValue.definition, DistanceExtrude):
            Authoring = ResolveAuthAxis(
                BulkData,
                Owners,
                Assembly,
                Scope,
                StepValue,
                Steps,
                Edits,
                Frame.transform.z_axis,
            )
            Resolved[StepValue.id] = AttachDistExt(
                BulkData, Owners, StepValue, Frame, Params, Authoring
            )
    Timeline = tuple(
        Resolved.get(StepValue.id, StepValue) for StepValue in Document.feature_timeline
    )
    Creators = FindExtCreators(
        tuple(StepValue for StepValue in Timeline if StepValue.id not in Edits)
    )
    if any(
        not isinstance(StepValue.definition, DistanceExtrude) for StepValue in Creators
    ):
        raise ValueError("Unsupported Fusion assembly solid creator")
    return (
        Replace(
            Document,
            feature_timeline=Timeline,
            diagnostics=tuple(
                Issue
                for Issue in Document.diagnostics
                if Issue.code != "fusion.extrude.unsupported"
                or Issue.entity_id not in Resolved
            ),
        ),
        Creators,
    )
