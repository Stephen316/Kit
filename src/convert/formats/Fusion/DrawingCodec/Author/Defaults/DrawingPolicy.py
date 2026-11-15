from convert.formats.Fusion.AssetCodec.Zip.ZipHeaders import KZipEpoch

# asset name must remain consistent across callers so sheet objects retain their intended document relationships
KAssetName = "Documentation"

# type name must remain consistent across callers so sheet objects retain their intended document relationships
KTypeName = "Fusion Drawing Document"

# type text must remain consistent across callers so sheet objects retain their intended document relationships
KTypeText = "Drawing Document"

# root modules needs a stable location so drawing authoring resolves inputs independently of the caller working directory
KRootModules = (("Application", 2),)

# the asset modules order must stay explicit so sheet objects retain their intended document relationships
KAssetModules = (("Application", 4), ("Server", 36))

# asset kind must remain consistent across callers so sheet objects retain their intended document relationships
KAssetKind = "Neutron3DAssetType"

# the link words order must stay explicit so sheet objects retain their intended document relationships
KLinkWords = (3, 4, 1, 0)

# link word must remain consistent across callers so sheet objects retain their intended document relationships
KLinkWord = 1

# allocation must remain consistent across callers so sheet objects retain their intended document relationships
KAllocation = 3

# change word must remain consistent across callers so sheet objects retain their intended document relationships
KChangeWord = 5

# first save must remain consistent across callers so sheet objects retain their intended document relationships
KFirstSave = "NA_OFFLINESAVE"

# link kind must remain consistent across callers so sheet objects retain their intended document relationships
KLinkKind = "OriginalDesign"

# file urn must remain consistent across callers so sheet objects retain their intended document relationships
KFileUrn = "urn:adsk.wipprod:fs.file:vf."

# lineage urn must remain consistent across callers so sheet objects retain their intended document relationships
KLineageUrn = "urn:adsk.wipprod:dm.lineage:"

# storage urn must remain consistent across callers so sheet objects retain their intended document relationships
KStorageUrn = "urn:adsk.objects:os.object:wip.dm.prod/"

# zero guid must remain consistent across callers so sheet objects retain their intended document relationships
KZeroGuid = "00000000-0000-0000-0000-000000000000"

# title block id must remain consistent across callers so sheet objects retain their intended document relationships
KTitleBlockId = "1"

# units must remain consistent across callers so sheet objects retain their intended document relationships
KUnits = "mm"

# the cycle color order must stay explicit so sheet objects retain their intended document relationships
KCycleColor = (0.8, 0.8, 0.8)

# the first stamp order must stay explicit so sheet objects retain their intended document relationships
KFirstStamp = (0, KZipEpoch)

# the design props order must stay explicit so sheet objects retain their intended document relationships
KDesignProps = (("Application", 2), ("Server", 7))

# the act props order must stay explicit so sheet objects retain their intended document relationships
KActProps = (("Application", 1), ("Server", 1))

# meta magic must remain consistent across callers so sheet objects retain their intended document relationships
KMetaMagic = 1234

# meta version must remain consistent across callers so sheet objects retain their intended document relationships
KMetaVersion = 8

# zstd method must remain consistent across callers so sheet objects retain their intended document relationships
KZstdMethod = 93

# stored method must remain consistent across callers so sheet objects retain their intended document relationships
KStoredMethod = 0

# deflate method must remain consistent across callers so sheet objects retain their intended document relationships
KDeflateMethod = 8

# dir extract must remain consistent across callers so sheet objects retain their intended document relationships
KDirExtract = 10

# file extract must remain consistent across callers so sheet objects retain their intended document relationships
KFileExtract = 20

# bundle creator must remain consistent across callers so sheet objects retain their intended document relationships
KBundleCreator = 20

# base columns must remain consistent across callers so sheet objects retain their intended document relationships
KBaseColumns = 7

# dimension strategy must remain consistent across callers so sheet objects retain their intended document relationships
KDimensionStrategy = "OverallDimension"

# the large thumb order must stay explicit so sheet objects retain their intended document relationships
KLargeThumb = (187, 133)

# the thumb small order must stay explicit so sheet objects retain their intended document relationships
KThumbSmall = (38, 28)

# preview side must remain consistent across callers so sheet objects retain their intended document relationships
KPreviewSide = 256

# the stream names order must stay explicit so sheet objects retain their intended document relationships
KStreamNames = ("BulkStream.dat", "MetaStream.dat")

# drawing type must remain consistent across callers so sheet objects retain their intended document relationships
KDrawingType = "f2d"

# design type must remain consistent across callers so sheet objects retain their intended document relationships
KDesignType = "f3d"

# service name must remain consistent across callers so sheet objects retain their intended document relationships
KServiceName = "wipdm"

# the folder order order must stay explicit so sheet objects retain their intended document relationships
KFolderOrder = (
    "SheetThumbnails/",
    "ProteinAssets.BlobParts/",
    "Previews/",
    "GenericModels/",
    "FusionDrawingDesignSegmentType1/",
    "FusionDrawingACTSegmentType1/",
    "Dwg.BlobParts/",
    "Breps.BlobParts/",
    "AutomationSettings/",
)
