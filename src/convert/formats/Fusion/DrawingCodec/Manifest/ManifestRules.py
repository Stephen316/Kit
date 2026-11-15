# root format needs a stable location so drawing packages resolves inputs independently of the caller working directory
KRootFormat = "3-2-0-0"

# modern magic must remain consistent across callers so drawing members retain their sheet and model associations
KModernMagic = 1234

# modern version must remain consistent across callers so drawing members retain their sheet and model associations
KModernVersion = 20

# legacy version must remain consistent across callers so drawing members retain their sheet and model associations
KLegacyVersion = 10

# max manifest rows must remain consistent across callers so drawing members retain their sheet and model associations
KMaxManifestRows = 256

# max path text needs a stable location so drawing packages resolves inputs independently of the caller working directory
KMaxPathText = 4096

# drawing doc type must remain consistent across callers so drawing members retain their sheet and model associations
KDrawingDocType = "FusionDrawingDocType"

# drawing asset type must remain consistent across callers so drawing members retain their sheet and model associations
KDrawingAssetType = "FusionDrawingAssetType"

# drawing extension must remain consistent across callers so drawing members retain their sheet and model associations
KDrawingExtension = ".f2d"
