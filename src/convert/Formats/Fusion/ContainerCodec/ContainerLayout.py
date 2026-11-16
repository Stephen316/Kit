from convert.Formats.Fusion.MetaIndex import SegmentKind

# asset prefix must remain consistent across callers so archive members retain their native ownership and reference relationships
KAssetPrefix = "FusionAssetName[Active]/"

# root name needs a stable location so container reconstruction resolves inputs independently of the caller working directory
KRootName = "Manifest.dat"

# properties name must remain consistent across callers so archive members retain their native ownership and reference relationships
KPropertiesName = "Properties.dat"

# asset name must remain consistent across callers so archive members retain their native ownership and reference relationships
KAssetName = KAssetPrefix + KRootName

# the preview names order must stay explicit so archive members retain their native ownership and reference relationships
KPreviewNames = ("Previews/big.png", "Previews/small.png")

# the part folders vocabulary must stay centralized so container reconstruction agrees on supported native identities
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

# the core segments order must stay explicit so archive members retain their native ownership and reference relationships
KCoreSegments = (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)

# max properties must remain consistent across callers so archive members retain their native ownership and reference relationships
KMaxProperties = 1024

# max preview size needs one explicit bound so container reconstruction cannot accept inconsistent resource or layout limits
KMaxPreviewSize = 16 * 1024 * 1024

# max preview side must remain consistent across callers so archive members retain their native ownership and reference relationships
KMaxPreviewSide = 4096

# redirect name must remain consistent across callers so archive members retain their native ownership and reference relationships
KRedirectName = "RedirectionsStream.dat"

# component references must remain consistent across callers so archive members retain their native ownership and reference relationships
KComponentRefs = "ComponentReferenceData.json"

# component body must remain consistent across callers so archive members retain their native ownership and reference relationships
KComponentBody = b"{}"

# max doc props must remain consistent across callers so archive members retain their native ownership and reference relationships
KMaxDocProps = 64 * 1024

# max redirects must remain consistent across callers so archive members retain their native ownership and reference relationships
KMaxRedirects = 4 * 1024 * 1024
