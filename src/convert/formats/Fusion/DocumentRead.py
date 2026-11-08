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

from convert.formats.Fusion.Assembly.AssemblyRead import ReadAssemblyProjection
from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.Extrudes.ExtrudeProject import ProjectExtrudes
from convert.formats.Fusion.Extrudes.Plane.PlaneExtProject import ProjectPlaneExts
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.PlaneProjection import ProjectPlanes
from convert.formats.Fusion.Profiles.ProfileProjection import ProjectProfiles
from convert.formats.Fusion.Revolves.RevolveBody import ProjectRevBody
from convert.formats.Fusion.Revolves.RevolveProject import ProjectRevolves
from convert.formats.Fusion.Sketches.SketchProjection import ProjectSketches
from convert.formats.Fusion.SourceBytes import LoadFusionBytes
from convert.formats.Fusion.Topology.BodyProjection import ProjectBodyList
from convert.formats.Fusion.ZipHistory import ReadBulkHistory
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
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
    """Project a native Fusion history or a qualified local assembly."""
    DataValue, SourceName = LoadFusionBytes(SourceData)
    BulkData, Spans = ReadDesignZip(DataValue, InflateZstd)
    Parts, Params, Diagnostics = ReadBulkHistory(BulkData, Spans)
    Assembly, History, AssemblyIssues = (
        ReadAssemblyProjection(BulkData, Spans, Parts)
        if HistoryId is None
        else (None, None, ())
    )
    if History is None:
        History = SelectHistory(Parts, HistoryId)
    Planes, PlaneIssues = ProjectPlanes(BulkData, Spans, History)
    Frames, Sketches, Steps, SketchIssues = ProjectSketches(BulkData, Spans, History)
    Steps, Sketches, ProfileIssues = ProjectProfiles(BulkData, Spans, Steps, Sketches)
    Steps, Selections, RevolveIssues = ProjectRevolves(
        BulkData, Spans, Steps, Params, Planes, Frames, Sketches
    )
    Owners = {
        ParamId: StepValue.id
        for StepValue in History.Steps
        for ParamId in StepValue.parameter_ids
    }
    Parameters = tuple(
        Replace(ParamValue, owner_id=Owners.get(ParamValue.id, ""))
        for ParamValue in Params
    )
    Steps, ExtrudeIssues = ProjectExtrudes(
        BulkData, Spans, Steps, Parameters, Frames, Sketches
    )
    Steps, PlanePicks, PlaneExtIssues = ProjectPlaneExts(
        BulkData, Spans, History.OwnerId, Steps, Parameters, Planes + Frames, Sketches
    )
    Selections += PlanePicks
    ResolvedExts = {
        StepValue.id
        for StepValue in Steps
        if isinstance(StepValue.definition, PlaneExtrude)
    }
    ExtrudeIssues = tuple(
        Issue for Issue in ExtrudeIssues if Issue.entity_id not in ResolvedExts
    )
    if Assembly is None and not any(
        isinstance(StepValue.definition, (DistanceExtrude, PlaneExtrude))
        for StepValue in Steps
    ):
        Bodies, Model, BodyIssues = ProjectRevBody(
            BulkData, Spans, Steps, Sketches, Frames, Parameters
        )
    else:
        Bodies, Model, BodyIssues = (), None, ()
    Digest = ShaDigest(DataValue).hexdigest()
    Capabilities = {Capability.KNativePayloads, Capability.KProvenance}
    if Parameters:
        Capabilities.add(Capability.KParameters)
    if Planes or Frames:
        Capabilities.add(Capability.KSupportPlanes)
    if Selections:
        Capabilities.add(Capability.KSelections)
    if Model is not None:
        Capabilities.update((Capability.KBodyStructure, Capability.KBrep))
    if Assembly is not None:
        Capabilities.add(Capability.KAssemblies)
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
        selections=Selections,
        feature_timeline=Steps,
        bodies=Bodies,
        assembly=Assembly,
        brep=Model,
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
        + ProfileIssues
        + RevolveIssues
        + ExtrudeIssues
        + PlaneExtIssues
        + BodyIssues
        + AssemblyIssues
        + (
            Diagnostic(
                code="fusion.history.partial",
                message="Fusion history projection covers ordering, numeric parameters, supported plane frames, a subset of sketch geometry, and supported Extrude and Revolve definitions and solids. "
                "Additional feature definitions, bodies, and assemblies require further decoding.",
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
    Document = ProjectBodyList(Document, BulkData, Spans, History)
    Document.AssertValid()
    return Document
