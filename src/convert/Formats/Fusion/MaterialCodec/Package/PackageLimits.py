# max package must remain consistent across callers so typed appearance properties retain their native identifiers
KMaxPackage = 16 * 1024 * 1024

# max xml bytes must remain consistent across callers so typed appearance properties retain their native identifiers
KMaxXmlBytes = 1024 * 1024

# max schemas must remain consistent across callers so typed appearance properties retain their native identifiers
KMaxSchemas = 64

# max schema nodes must remain consistent across callers so typed appearance properties retain their native identifiers
KMaxSchemaNodes = 20000

# max entries must remain consistent across callers so typed appearance properties retain their native identifiers
KMaxEntries = 4096

# max folder depth needs one explicit bound so material reconstruction cannot accept inconsistent resource or layout limits
KMaxFolderDepth = 8

# the folder sets order must stay explicit so typed appearance properties retain their native identifiers
KFolderSets = (("AssetData", "Schemas"), ("AssetData", "Resources", "Schemas"))

# max xml depth needs one explicit bound so material reconstruction cannot accept inconsistent resource or layout limits
KMaxXmlDepth = 8

# version table must remain consistent across callers so typed appearance properties retain their native identifiers
KVersionTable = (
    b"AssetTableOfContents:3.1,\n"
    b"DefinitionIteratorProperties:3.2,\n"
    b"InstanceProperties:3.2,\n"
    b"AssetLibVersion:1.0\n"
)

# the stream names order must stay explicit so typed appearance properties retain their native identifiers
KStreamNames = (
    "AssetTableOfContents.bin",
    "DefinitionIteratorProperties.bin",
    "InstanceProperties.bin",
    "StreamVersionTable",
)

# the content types order must stay explicit so typed appearance properties retain their native identifiers
KContentTypes = (
    ("xml", "application/xml"),
    ("", "application/octet-stream"),
    ("bin", "application/octet-stream"),
)

# type namespace must remain consistent across callers so typed appearance properties retain their native identifiers
KTypeNamespace = "http://schemas.openxmlformats.org/package/2006/content-types"

# package format must remain consistent across callers so typed appearance properties retain their native identifiers
KPackageFormat = "http://schema.autodesk.com/design-package/2009"
