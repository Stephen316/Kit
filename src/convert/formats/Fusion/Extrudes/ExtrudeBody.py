from dataclasses import replace as Replace

from convert.formats.Fusion.Extrudes.SavedSolidSets import BuildSolidSets
from convert.formats.Fusion.Extrudes.SolidCreators import FindExtCreators
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.records.RecordDiagnostic import Diagnostic


# unsupported shapes remain editable without posing as a partially rebuilt final body set
def ProjectExtBody(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Members: tuple[NativeBody, ...],
) -> CadDocument:
    if not any(
        isinstance(StepValue.definition, (DistanceExtrude, PlaneExtrude))
        for StepValue in Document.feature_timeline
    ):
        return Document
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
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
