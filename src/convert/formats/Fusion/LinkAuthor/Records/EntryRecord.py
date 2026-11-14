from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KComponentEntry,
    KComponentInstances,
    KEntityEntry,
    KFeatures,
    KFusionComponent,
    KGroupEntry,
    KInstanceEntry,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    FrameRecord,
    MakeGroup,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def EntryRecord(
    RootInfo: RootFacts, Facts: TargetFacts, Linkage: LinkKeys, KeySet: PlaceKeys
) -> EntityRecord:
    Targets = (
        CrossRef(Facts.Component, Linkage.DesignToken, KFusionComponent),
        CrossRef(Facts.Instances, Linkage.DesignToken, KComponentInstances),
        CrossRef(Facts.Features, Linkage.DesignToken, KFeatures),
    )
    Instance = SegmentRef(KeySet.Instance, RootInfo.DesignSegment)
    Subjects = (
        SubjectValue(Instance, 0),
        *(
            SubjectValue(Target, SlotIndex)
            for Target, SlotIndex in zip(Targets, Facts.Slots)
        ),
    )
    return FrameRecord(
        KeySet.EntryId,
        EntityFrame("", Subjects, None),
        MakeGroup(KInstanceEntry, ("ComponentsFolderEntry", None)),
        MakeGroup(
            KComponentEntry,
            ("ACTInstance", SegmentRef(KeySet.ActInstance, RootInfo.ActSegment)),
        ),
        MakeGroup(
            KGroupEntry,
            ("AlwaysAddChild", True),
            ("ComponentInstance", ValueSeries(Targets)),
        ),
        MakeGroup(
            KEntityEntry,
            ("MissingLinkReason", 2),
            ("bHasRefdEntry", True),
            ("children", ValueSeries(())),
            ("entity", Instance),
            ("flags", 1),
            ("hiddenChildren", ValueSeries(())),
            ("parents", ValueSeries((LocalRef(RootInfo.RootEntry),))),
            ("root", LocalRef(RootInfo.BrowserRoot)),
            ("strEntityId", ""),
            ("virtualParents", ValueSeries(())),
        ),
    )
