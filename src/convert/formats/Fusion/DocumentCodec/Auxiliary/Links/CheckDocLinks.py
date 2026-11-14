from convert.formats.Fusion.DocumentCodec.Auxiliary.Links.IsOlderUrn import IsOlderUrn
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KLinkedAsset,
    KLinkedUrl,
)


def CheckDocLinks(Value: DocumentModel) -> None:
    Targets: dict[str, tuple[str | None, str | None]] = {}
    for Entry in Value.Document.Links:
        Fields = dict(Entry.Properties)
        Targets[Entry.LinkId] = Fields.get(KLinkedAsset), Fields.get(KLinkedUrl)
    Assets = {Entry.LinkId: Entry.AssetId for Entry in Value.Asset.Links}
    if (
        len(Targets) != len(Value.Document.Links)
        or len(Assets) != len(Value.Asset.Links)
        or Targets.keys() != Assets.keys()
    ):
        raise ValueError("Fusion root and asset link tables disagree")
    if any(
        Targets[LinkId][0] not in (None, AssetId) for LinkId, AssetId in Assets.items()
    ):
        raise ValueError("Fusion link target asset identities disagree")
    for Segment in Value.Segments:
        for Context in Segment.Metadata.Contexts:
            VersionUrn = Targets.get(Context.LinkId, (None, None))[1]
            if Assets.get(Context.LinkId) != Context.AssetId or (
                VersionUrn not in (None, Context.VersionUrn)
                and not IsOlderUrn(VersionUrn, Context.VersionUrn)
            ):
                raise ValueError("Fusion version context disagrees with its link")
