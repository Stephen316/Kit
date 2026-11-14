from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.LinkAuthor.Edits.RecordEdit import (
    ReadNumber,
    ReadText,
    ReadValue,
    SoleId,
)
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Reading.DocSegment import SegmentOf
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KActComponent,
    KActInstances,
    KActRoot,
    KActTable,
    KBrowserRoot,
    KComponentInstances,
    KConstraintOccs,
    KConstraints,
    KContextClass,
    KCreationOrder,
    KDcNodes,
    KDcOccurrence,
    KDesignFragment,
    KFeatureIds,
    KFusionComponent,
    KInstanceEntry,
    KInstancesRoot,
    KOverrides,
)
from convert.formats.Fusion.MetaIndex import SegmentKind


def IsLinkFree(Model: DocumentModel) -> bool:
    return not (
        Model.Document.Links
        or Model.Asset.Links
        or any(Segment.Metadata.Contexts for Segment in Model.Segments)
    )


def ReadRoot(Model: DocumentModel) -> RootFacts:
    Design = SegmentOf(Model, SegmentKind.KDesign)
    Tracking = SegmentOf(Model, SegmentKind.KAct)
    Browser = SegmentOf(Model, SegmentKind.KBrowser)
    Component = SoleId(Design, KFusionComponent)
    Instances = SoleId(Design, KComponentInstances)
    ActRoot = SoleId(Tracking, KActRoot)
    if (
        not IsLinkFree(Model)
        or ReadValue(Design.Records, Instances, "children") != ValueSeries(())
        or ReadValue(Design.Records, Component, "rXRefManager") is not None
    ):
        raise ValueError("Fusion assembly authoring needs an unlinked empty base")
    return RootFacts(
        Component,
        Instances,
        SoleId(Design, KOverrides),
        SoleId(Design, KConstraints),
        SoleId(Design, KConstraintOccs),
        SoleId(Design, KDesignFragment),
        SoleId(Design, KDcNodes),
        SoleId(Design, KFeatureIds),
        SoleId(Design, KCreationOrder),
        SoleId(Design, KInstancesRoot),
        SoleId(Design, KContextClass),
        SoleId(Design, KDcOccurrence),
        Model.Asset.AssetId,
        ReadText(Design.Records, Component, "persistentId"),
        SoleId(Tracking, KActComponent),
        SoleId(Tracking, KActTable),
        SoleId(Tracking, KActInstances),
        ActRoot,
        SoleId(Browser, KBrowserRoot),
        SoleId(Browser, KInstanceEntry),
        Design.Metadata.Header.SegmentId,
        Tracking.Metadata.Header.SegmentId,
        ReadNumber(Design.Records, Component, "operationSeedId"),
        ReadNumber(Tracking.Records, ActRoot, "nextInstanceId"),
    )
