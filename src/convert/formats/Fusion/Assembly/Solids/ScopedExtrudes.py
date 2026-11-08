# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
        int(Step.provenance.native_id): Step
        for Step in Document.feature_timeline
        if Step.provenance is not None
    }
    SketchSteps = {
        Step.sketch_id: Identity
        for Identity, Step in Steps.items()
        if Step.sketch_id is not None and Owners[Identity].ClassGuid == KSketchFeature
    }
    FrameMap = {Plane.id: Plane for Plane in Document.support_planes}
    SketchFrames = {
        SketchValue.id: FrameMap.get(SketchValue.support_plane_id)
        for SketchValue in Document.sketches
    }
    ExtIds = {
        Identity
        for Identity, Step in Steps.items()
        if Step.kind == FeatureKind.KExtrusion
    }
    Scopes = ReadAsmScopes(
        BulkData, Owners, OwnerId, frozenset(ExtIds | set(SketchSteps.values()))
    )
    Params = {Param.id: Param for Param in Document.parameters}
    Resolved: dict[str, FeatureStep] = {}
    for Identity, Step in Steps.items():
        if Identity not in ExtIds or not IsSavedActive(Step):
            continue
        Scope = Scopes.get(Identity)
        SketchId = Step.sketch_id or ""
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
        if not isinstance(Step.definition, DistanceExtrude):
            Authoring = ResolveAuthAxis(
                BulkData,
                Owners,
                Assembly,
                Scope,
                Step,
                Steps,
                Edits,
                Frame.transform.z_axis,
            )
            Resolved[Step.id] = AttachDistExt(
                BulkData, Owners, Step, Frame, Params, Authoring
            )
    Timeline = tuple(Resolved.get(Step.id, Step) for Step in Document.feature_timeline)
    Creators = FindExtCreators(tuple(Step for Step in Timeline if Step.id not in Edits))
    if any(not isinstance(Step.definition, DistanceExtrude) for Step in Creators):
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
