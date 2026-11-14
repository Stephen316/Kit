from convert.formats.Fusion.MetaIndex import SegmentKind

KAssetPrefix = "FusionAssetName[Active]/"
KRootName = "Manifest.dat"
KPropertiesName = "Properties.dat"
KAssetName = KAssetPrefix + KRootName
KPreviewNames = ("Previews/big.png", "Previews/small.png")
KPartFolders = frozenset(
    (
        "Breps.BlobParts",
        "ProteinAssets.BlobParts",
        "Images.BlobParts",
        "OGS.BlobFolder",
        "DesignConfigurationTable.BlobParts",
        "ParaMeshGeometry.BlobParts",
        "TSplines.BlobParts",
    )
)
KCoreSegments = (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)
KMaxProperties = 1024
KMaxPreviewSize = 16 * 1024 * 1024
KMaxPreviewSide = 4096
KRedirectName = "RedirectionsStream.dat"
KComponentRefs = "ComponentReferenceData.json"
KComponentBody = b"{}"
KMaxDocProps = 64 * 1024
KMaxRedirects = 4 * 1024 * 1024
