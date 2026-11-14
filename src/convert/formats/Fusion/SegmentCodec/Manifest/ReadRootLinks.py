from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KLinkWords,
    KMaxLinkProps,
    KMaxLinks,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLink import ManifestLink
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ManifestCursor import (
    ManifestCursor,
)


def ReadRootLinks(Cursor: ManifestCursor) -> tuple[ManifestLink, ...]:
    FlagValue = Cursor.TakeBytes(1)
    if FlagValue == b"\0":
        return ()
    if FlagValue != b"\1":
        raise ValueError("Unsupported Fusion root manifest link flag")
    Count = Cursor.ReadCount(KMaxLinks)
    if Count == 0:
        raise ValueError("Unsupported empty Fusion root manifest link table")
    Links: list[ManifestLink] = []
    for _ in range(Count):
        LinkId = Cursor.ReadGuid()
        Paths = tuple(Cursor.ReadText(True) for _ in range(3))
        if tuple(Cursor.ReadWord() for _ in KLinkWords) != KLinkWords:
            raise ValueError("Unsupported Fusion root manifest link words")
        Properties = tuple(
            (Cursor.ReadText(True), Cursor.ReadText(True))
            for _ in range(Cursor.ReadCount(KMaxLinkProps))
        )
        Links.append(ManifestLink(LinkId, Paths[0], Paths[1], Paths[2], Properties))
    return tuple(Links)
