from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.Scales.ConstructionCenter import KWorkPointStep
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from convert.formats.Fusion.Topology.BodyAnchor import KAnchorGuid
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from convert.formats.Fusion.Topology.ResultBody import IndexBodyLinks
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureStep import FeatureStep


# a supported final scale cannot silently consume bodies modified by other active steps
def CheckScaleSteps(
    Document: CadDocument, Feature: FeatureStep, Sources: frozenset[str]
) -> None:
    for StepValue in Document.feature_timeline:
        Origin = StepValue.provenance
        if (
            StepValue.id == Feature.id
            or StepValue.id in Sources
            or (
                Origin is not None
                and Origin.spans
                and Origin.spans[0].record_kind
                in (KSketchFeature, KPlaneFeature, KWorkPointStep)
            )
        ):
            continue
        if IsSavedActive(StepValue):
            raise ValueError(
                "Fusion Scale history contains another active modeling feature"
            )


# native bodies must exhaust the final inventory without assigning new result anchors
def ReadScalePicks(
    Document: CadDocument,
    BulkData: bytes,
    Context: InputContext,
    Feature: FeatureStep,
    FeatureId: int,
    Members: tuple[NativeBody, ...],
) -> tuple[tuple[FeatureStep, NativeBody, int], ...]:
    ByPick = {Value.id: Value for Value in Document.selections}
    Picks = tuple(ByPick[Identity] for Identity in Feature.selection_ids)
    NativeIds = frozenset(
        SourceId
        for PickValue in Picks
        if type(SourceId := PickValue.query.get("native_source_id")) is int
    )
    if not Picks or len(NativeIds) != len(Picks):
        raise ValueError("Fusion Scale historical source identities are ambiguous")
    Links = IndexBodyLinks(BulkData, Context.Owners, NativeIds)
    ByBody = {Member.ObjectId: Member for Member in Members}
    if set(ByBody) != {BodyId for BodyId, _ in Links.values()} or len(ByBody) != len(
        Picks
    ):
        raise ValueError("Fusion Scale picks do not cover the saved body inventory")
    for SpanValue in Context.Owners.values():
        if (
            SpanValue.ClassGuid == KAnchorGuid
            and ReadNativeRef(
                MetaCursor(BulkData[SpanValue.EndOffset - 11 : SpanValue.EndOffset])
            )
            == FeatureId
        ):
            raise ValueError("Fusion Scale has a separate result anchor")
    CheckScaleSteps(
        Document,
        Feature,
        frozenset(Context.Steps[Identity].id for Identity in NativeIds),
    )
    Result: list[tuple[FeatureStep, NativeBody, int]] = []
    for PickValue in Picks:
        SourceId = PickValue.query.get("native_source_id")
        if (
            type(SourceId) is not int
            or PickValue.query.get("kind") != "historical_body"
        ):
            raise ValueError("Fusion Scale input has no historical source")
        BodyId, AnchorId = Links[SourceId]
        if (
            PickValue.query.get("native_body_id") != BodyId
            or PickValue.query.get("native_anchor_id") != AnchorId
        ):
            raise ValueError("Fusion Scale input and source anchor disagree")
        Result.append((Context.Steps[SourceId], ByBody[BodyId], AnchorId))
    return tuple(Result)
