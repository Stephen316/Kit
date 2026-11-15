# root manifest needs a stable location so drawing packages resolves inputs independently of the caller working directory
KRootManifest = "Manifest.dat"

# properties name must remain consistent across callers so drawing members retain their sheet and model associations
KPropertiesName = "Properties.dat"

# reference name must remain consistent across callers so drawing members retain their sheet and model associations
KReferenceName = "ComponentReferenceData.json"

# redirect name must remain consistent across callers so drawing members retain their sheet and model associations
KRedirectName = "RedirectionsStream.dat"

# asset manifest must remain consistent across callers so drawing members retain their sheet and model associations
KAssetManifest = "Manifest.dat"

# sheet name must remain consistent across callers so drawing members retain their sheet and model associations
KSheetName = "DrawingManifest.json"

# settings folder must remain consistent across callers so drawing members retain their sheet and model associations
KSettingsFolder = "AutomationSettings/"

# the image folders order must stay explicit so drawing members retain their sheet and model associations
KImageFolders = ("Previews/", "SheetThumbnails/")

# database folder must remain consistent across callers so drawing members retain their sheet and model associations
KDatabaseFolder = "Dwg.BlobParts/"
