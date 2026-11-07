# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from dataclasses import replace as Replace
from hashlib import sha256 as ShaDigest
from pathlib import Path as FilePath

from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.PlaneProjection import ProjectPlanes
from convert.formats.Fusion.Sketches.SketchProjection import ProjectSketches
from convert.formats.Fusion.SourceBytes import LoadFusionBytes
from convert.formats.Fusion.ZipHistory import ReadBulkHistory
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordSource import CadSource


# callers must choose a native history when the archive has more than one owner
def SelectHistory(Parts: tuple[HistoryPart, ...], HistoryId: int | None) -> HistoryPart:
    Matches = (
        Parts
        if HistoryId is None
        else tuple(PartValue for PartValue in Parts if PartValue.HistoryId == HistoryId)
    )
    if len(Matches) != 1:
        Available = tuple(PartValue.HistoryId for PartValue in Parts)
        raise ValueError(f"Select exactly one Fusion history from {Available}")
    return Matches[0]


# source archives stay available for inspection and reversible interchange
def ReadFusionDoc(
    SourceData: str | FilePath | bytes,
    *,
    HistoryId: int | None = None,
    InflateZstd: Callable[[bytes, int], bytes] | None = None,
) -> CadDocument:
    """Project one native Fusion history into a partial, validated document."""
    DataValue, SourceName = LoadFusionBytes(SourceData)
    BulkData, Spans = ReadDesignZip(DataValue, InflateZstd)
    Parts, Params, Diagnostics = ReadBulkHistory(BulkData, Spans)
    History = SelectHistory(Parts, HistoryId)
    Planes, PlaneIssues = ProjectPlanes(BulkData, Spans, History)
    Frames, Sketches, Steps, SketchIssues = ProjectSketches(BulkData, Spans, History)
    Owners = {
        ParamId: StepValue.id
        for StepValue in History.Steps
        for ParamId in StepValue.parameter_ids
    }
    Parameters = tuple(
        Replace(ParamValue, owner_id=Owners.get(ParamValue.id, ""))
        for ParamValue in Params
    )
    Digest = ShaDigest(DataValue).hexdigest()
    Capabilities = {Capability.KNativePayloads, Capability.KProvenance}
    if Parameters:
        Capabilities.add(Capability.KParameters)
    if Planes or Frames:
        Capabilities.add(Capability.KSupportPlanes)
    Document = CadDocument(
        source=CadSource(format_id="fusion.f3d", path=SourceName, sha256=Digest),
        configurations=(
            Configuration(
                id="fusion-projection", name="History projection", active=True
            ),
        ),
        parameters=Parameters,
        support_planes=Planes + Frames,
        sketches=Sketches,
        selections=(),
        feature_timeline=Steps,
        bodies=(),
        brep_payloads=(
            BrepPayload(
                id="fusion-source-archive",
                format_id="fusion.f3d",
                kind="native_document",
                schema="f3d",
                sha256=Digest,
                data=DataValue,
                role=PayloadRole.KDocument,
                file_extension=".f3d",
            ),
        ),
        diagnostics=Diagnostics
        + PlaneIssues
        + SketchIssues
        + (
            Diagnostic(
                code="fusion.history.partial",
                message="Fusion history projection covers ordering, numeric parameters, supported plane frames, and a subset of sketch geometry. "
                "Editable feature definitions, geometry, and assemblies require further decoding.",
            ),
        ),
        capabilities=frozenset(Capabilities),
        metadata=FreezeMapping(
            {
                "fusion.history_id": History.HistoryId,
                "fusion.history_owner_id": History.OwnerId,
                "fusion.history_entries": History.EntryIds,
                "fusion.history_groups": tuple(
                    FreezeMapping(
                        {
                            "id": Group.ObjectId,
                            "name": Group.GroupName,
                            "collapsed": Group.IsCollapsed,
                            "members": Group.MemberIds,
                        }
                    )
                    for Group in History.Groups
                ),
            }
        ),
    )
    Document.AssertValid()
    return Document
