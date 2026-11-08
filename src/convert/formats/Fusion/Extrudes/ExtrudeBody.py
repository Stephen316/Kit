# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.Extrudes.SavedSolidSets import BuildSolidSets
from convert.formats.Fusion.Extrudes.SolidCreators import FindExtCreators
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
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
    try:
        Creators = FindExtCreators(Document.feature_timeline)
        Solids = BuildSolidSets(Document, BulkData, Owners, Creators, Members)
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
    if not Solids:
        return Document
    ((Bodies, Model),) = Solids.values()
    return Replace(
        Document,
        bodies=Bodies,
        brep=Model,
        capabilities=Document.capabilities
        | {Capability.KBodyStructure, Capability.KBrep},
    )
