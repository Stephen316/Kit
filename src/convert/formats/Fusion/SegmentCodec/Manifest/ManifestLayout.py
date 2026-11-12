# the fixed root format labels distinguish this document layout from other containers
KRootFormat = ("3-2-0-0", "FusionDocType", ".f3d")

# the native header starts with a magic before the shared manifest version
KRootMagic = 1234

# both manifest payload types use the same observed numeric schema version
KWireVersion = 20

# the counted asset name appears in both manifests with the same native spelling
KAssetName = "FusionAssetName"

# the single root asset row ends with the native export marker
KExportLabel = "NA_EXPORT"

# the active manifest header declares this asset role after the two identity tokens
KAssetRole = "FusionAssetType"

# the active property block begins with a named native asset kind
KAssetKind = "Neutron3DAssetType"

# the observed extension name retains its literal wire spelling
KPhysicalKey = "physicalChangeGuid"

# both observed active suffix values share the same remaining segment grammar
KOpaqueWords = (5, 7)
