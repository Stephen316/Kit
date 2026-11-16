from collections.abc import Callable
from dataclasses import replace as Replace
from hashlib import sha256 as ShaDigest
from pathlib import Path as FilePath

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.Assembly.AssemblyRead import ReadAsmProject
from convert.Formats.Fusion.BodyInputs.BodyInputProject import ProjectPicks
from convert.Formats.Fusion.ConstructionPlane.ProjectConstruction import (
    ProjectDatums,
)
from convert.Formats.Fusion.Extrudes.ExtrudeProject import ProjectExtrudes
from convert.Formats.Fusion.Extrudes.Plane.PlaneExtProject import ProjectPlaneExt
from convert.Formats.Fusion.FormulaDeps.FormulaLink import LinkFormulaDeps
from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.PlaneProjection import ProjectPlanes
from convert.Formats.Fusion.Profiles.ProfileProjection import ProjectProfiles
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.RevolveBody import ProjectRevBody
from convert.Formats.Fusion.Revolves.RevolveProject import ProjectRevolves
from convert.Formats.Fusion.Scales.ScaleProject import ProjectScale
from convert.Formats.Fusion.Sketches.SketchRules import AttachRules
from convert.Formats.Fusion.Sketches.SketchProjection import ProjectSketches
from convert.Formats.Fusion.SourceBytes import LoadFusionBytes
from convert.Formats.Fusion.Topology.BodyProjection import ProjectBodyList
from convert.Formats.Fusion.ZipHistory import ReadBulkHistory
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Payloads.PayloadRoles import PayloadRole
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordSource import CadSource


# callers must choose a native history when the archive has more than one owner
def SelectHistory(Parts: tuple[HistoryPart, ...], HistoryId: int | None) -> HistoryPart:
    Matches = (
        Parts
        if HistoryId is None
        else tuple(PartValue for PartValue in Parts if PartValue.HistoryId == HistoryId)
    )
    if len(Matches) != 1:
        Available = tuple(PartValue.HistoryId for PartValue in Parts)
        raise ValueError(
            f"Select exactly one Fusion history. Available IDs: {Available}"
        )
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
    with OpenFusionZip(DataValue, InflateZstd) as Archive:
        BulkData, Spans = Archive.ReadDesign()
        return ProjectFusDoc(
            DataValue, SourceName, BulkData, Spans, HistoryId, Archive.ReadBody
        )


# the projection shares one archive context with inspection and every geometry consumer
def ProjectFusDoc(
    DataValue: bytes,
    SourceName: str,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    HistoryId: int | None,
    LoadBlob: Callable[[str], bytes],
) -> CadDocument:
    Parts, Params, Diagnostics = ReadBulkHistory(BulkData, Spans)
    Assembly, History, AssemblyIssues = (
        ReadAsmProject(BulkData, Spans, Parts)
        if HistoryId is None
        else (None, None, ())
    )
    if History is None:
        History = SelectHistory(Parts, HistoryId)
    Planes, PlaneIssues = ProjectPlanes(BulkData, Spans, History)
    Frames, Sketches, Steps, SketchIssues = ProjectSketches(BulkData, Spans, History)
    Steps, Sketches, ProfileIssues = ProjectProfiles(BulkData, Spans, Steps, Sketches)
    Owners = {
        ParamId: StepValue.id
        for StepValue in History.Steps
        for ParamId in StepValue.parameter_ids
    }
    Parameters = LinkFormulaDeps(
        BulkData,
        Spans,
        History,
        tuple(
            Replace(ParamValue, owner_id=Owners.get(ParamValue.id, ""))
            for ParamValue in Params
        ),
    )
    Steps = ProjectDatums(BulkData, Spans, History, Planes, Steps, Parameters)
    Sketches, SketchRuleIssues = AttachRules(BulkData, Spans, Sketches, Parameters)
    Steps, ExtrudeIssues = ProjectExtrudes(
        BulkData, Spans, Steps, Parameters, Frames, Sketches
    )
    Steps, PlanePicks, PlaneExtIssues = ProjectPlaneExt(
        BulkData, Spans, History.OwnerId, Steps, Parameters, Planes + Frames, Sketches
    )
    Steps, Selections, RevolveIssues = ProjectRevolves(
        BulkData,
        Spans,
        Steps,
        Parameters,
        Planes,
        Frames,
        Sketches,
        LoadBlob,
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
    Capabilities = GetFusionCaps(
        bool(Parameters),
        bool(Planes or Frames),
        bool(Selections),
        Model is not None,
        Assembly is not None,
    )
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
        + SketchRuleIssues
        + ProfileIssues
        + RevolveIssues
        + ExtrudeIssues
        + PlaneExtIssues
        + BodyIssues
        + AssemblyIssues
        + (
            Diagnostic(
                code="fusion.history.partial",
                message="Fusion history projection covers ordering, numeric parameters, supported plane frames, a subset of sketch geometry and constraints, and supported Extrude and Revolve definitions and solids. "
                + "Additional feature definitions, bodies, and assemblies require further decoding.",
            ),
        ),
        capabilities=Capabilities,
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
    return FinishFusionDoc(Document, BulkData, Spans, History, LoadBlob)


# later body and feature associations must resolve before document validation
def FinishFusionDoc(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    LoadBlob: Callable[[str], bytes],
) -> CadDocument:
    Document = ProjectBodyList(Document, BulkData, Spans, History)
    Document = ProjectPicks(Document, BulkData, Spans, History)
    Document = ProjectScale(Document, BulkData, Spans, History, LoadBlob)
    Document.AssertValid()
    return Document


# capabilities reflect the evidence retained in the completed neutral document
def GetFusionCaps(
    Parameters: bool,
    HasPlanes: bool,
    Selections: bool,
    HasModel: bool,
    HasAssembly: bool,
) -> frozenset[Capability]:
    Capabilities = {Capability.KNativePayloads, Capability.KProvenance}
    if Parameters:
        Capabilities.add(Capability.KParameters)
    if HasPlanes:
        Capabilities.add(Capability.KSupportPlanes)
    if Selections:
        Capabilities.add(Capability.KSelections)
    if HasModel:
        Capabilities.update((Capability.KBodyStructure, Capability.KBrep))
    if HasAssembly:
        Capabilities.add(Capability.KAssemblies)
    return frozenset(Capabilities)
