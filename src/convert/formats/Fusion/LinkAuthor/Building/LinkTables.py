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

KVersionMark = "?version="

KChangeKey = "physicalChangeGuid"


def UrnVersion(VersionUrn: str) -> int:
    Prefix, Marker, Suffix = VersionUrn.rpartition(KVersionMark)
    if not Prefix or not Marker or not Suffix.isdigit() or not Suffix.isascii():
        raise ValueError("Fusion link version URN lacks a version number")
    return int(Suffix)


def ChangeGuid(Target: LinkTarget) -> str:
    return dict(Target.Target.Asset.Properties).get(KChangeKey, KUnchangedGuid)


def XRefName(Target: LinkTarget, KeySet: LinkKeys) -> str:
    Version = UrnVersion(Target.VersionUrn)
    return f"_XRef_/_{Target.DisplayName}.{KeySet.CacheGuid}_LV{Version}.f3d"


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
    return tuple(sorted(Contexts, key=lambda Context: Context.Token))
