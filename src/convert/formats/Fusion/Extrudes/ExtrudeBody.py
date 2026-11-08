# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.Extrudes.BuildSolidStep import BuildSolidStep
from convert.formats.Fusion.Extrudes.ExtBodyLinks import LinkSolidBodies
from convert.formats.Fusion.Extrudes.SolidCreators import FindExtCreators
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.records.RecordDiagnostic import Diagnostic


# unsupported shapes remain editable without posing as a partially rebuilt final body set
def ProjectExtBody(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Members: tuple[NativeBody, ...],
) -> CadDocument:
    if not any(
        isinstance(StepValue.definition, DistanceExtrude)
        for StepValue in Document.feature_timeline
    ):
        return Document
    Owners = {Span.ObjectId: Span for Span in Spans if Span.IsPrimary}
    Sketches = {SketchValue.id: SketchValue for SketchValue in Document.sketches}
    Frames = {FrameValue.id: FrameValue for FrameValue in Document.support_planes}
    Params = {Param.id: Param for Param in Document.parameters}
    Bodies: list[DesignBody] = []
    Models: list[BrepModel] = []
    try:
        Creators = FindExtCreators(Document.feature_timeline)
        Links = LinkSolidBodies(BulkData, Owners, Creators, Members)
        for StepValue in Creators:
            SketchValue = Sketches.get(StepValue.sketch_id or "")
            FrameValue = (
                None
                if SketchValue is None
                else Frames.get(SketchValue.support_plane_id)
            )
            if SketchValue is None or FrameValue is None:
                raise ValueError("Missing Fusion solid profile sketch frame")
            Member, AnchorId = Links[StepValue.id]
            BodyValue, Model = BuildSolidStep(
                Owners, StepValue, SketchValue, FrameValue, Params, Member, AnchorId
            )
            Bodies.append(BodyValue)
            Models.append(Model)
    except ValueError as ErrorInfo:
        return Replace(
            Document,
            diagnostics=Document.diagnostics
            + (
                Diagnostic(
                    code="fusion.extrude.body_unsupported", message=str(ErrorInfo)
                ),
            ),
        )
    if not Models:
        return Document
    return Replace(
        Document,
        bodies=tuple(Bodies),
        brep=JoinRevModels(tuple(Models)),
        capabilities=Document.capabilities
        | {Capability.KBodyStructure, Capability.KBrep},
    )
