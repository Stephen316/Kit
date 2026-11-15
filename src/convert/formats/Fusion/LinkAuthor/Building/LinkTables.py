from convert.formats.Fusion.ContainerCodec.Model.AssetLink import AssetLink
from convert.formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.formats.Fusion.LinkAuthor.Model.LinkTarget import LinkTarget
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KLinkedAsset,
    KLinkedUrl,
    KUnchangedGuid,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLink import ManifestLink
from convert.formats.Fusion.SegmentCodec.Metadata.MetaContext import MetaContext

# version mark must remain consistent across callers so cross document references retain their intended ownership
KVersionMark = "?version="

# change key must remain consistent across callers so cross document references retain their intended ownership
KChangeKey = "physicalChangeGuid"


# urn version needs an explicit validity boundary so cross document references retain their intended ownership
def UrnVersion(VersionUrn: str) -> int:
    Prefix, Marker, Suffix = VersionUrn.rpartition(KVersionMark)
    if not Prefix or not Marker or not Suffix.isdigit() or not Suffix.isascii():
        raise ValueError("Fusion link version URN lacks a version number")
    return int(Suffix)


# the change guid contract needs a shared interpretation so cross document references retain their intended ownership
def ChangeGuid(Target: LinkTarget) -> str:
    return dict(Target.Target.Asset.Properties).get(KChangeKey, KUnchangedGuid)


# the x reference name contract needs a shared interpretation so cross document references retain their intended ownership
def XRefName(Target: LinkTarget, KeySet: LinkKeys) -> str:
    Version = UrnVersion(Target.VersionUrn)
    return f"_XRef_/_{Target.DisplayName}.{KeySet.CacheGuid}_LV{Version}.f3d"


# the manifest links contract needs a shared interpretation so cross document references retain their intended ownership
def ManifestLinks(
    Request: AssemblySpec, Scheme: AssemblyPlan
) -> tuple[ManifestLink, ...]:
    return tuple(
        ManifestLink(
            KeySet.LinkId,
            Request.SourcePath,
            f"_{Target.DisplayName}.{KeySet.CacheGuid}.f3d",
            XRefName(Target, KeySet),
            (
                ("LineageId", Target.LineageUrn),
                ("LineageUrn", Target.LineageUrn),
                ("toDocDisplayName", Target.DisplayName),
                (KLinkedUrl, Target.VersionUrn),
                (KLinkedAsset, Target.Target.Asset.AssetId),
            ),
        )
        for Target, KeySet in zip(Request.Targets, Scheme.Links, strict=True)
    )


# the asset links contract needs a shared interpretation so cross document references retain their intended ownership
def AssetLinks(Request: AssemblySpec, Scheme: AssemblyPlan) -> tuple[AssetLink, ...]:
    return tuple(
        AssetLink(
            KeySet.LinkId,
            Target.Target.Asset.AssetId,
            Target.Target.Asset.SnapshotId,
            1,
            ChangeGuid(Target),
        )
        for Target, KeySet in zip(Request.Targets, Scheme.Links, strict=True)
    )


# link contexts must resolve unambiguously so cross document references retain their intended ownership
def LinkContexts(
    Request: AssemblySpec,
    Scheme: AssemblyPlan,
    Facts: tuple[TargetFacts, ...],
    KindValue: SegmentKind,
) -> tuple[MetaContext, ...]:
    IsAct = KindValue is SegmentKind.KAct
    Contexts = (
        MetaContext(
            KeySet.ActToken if IsAct else KeySet.DesignToken,
            KeySet.LinkId,
            Target.Target.Document.DocumentId,
            Target.VersionUrn,
            Target.Target.Asset.AssetId,
            Detail.ActSegment if IsAct else Detail.DesignSegment,
        )
        for Target, KeySet, Detail in zip(
            Request.Targets, Scheme.Links, Facts, strict=True
        )
    )

    # ordering by context token must stay deterministic so document link authoring resolves equivalent inputs consistently
    return tuple(sorted(Contexts, key=lambda Context: Context.Token))
