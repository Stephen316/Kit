KMaxPackage = 16 * 1024 * 1024
KMaxXmlBytes = 1024 * 1024
KMaxSchemas = 64
KMaxSchemaNodes = 20000
KMaxEntries = 4096
KMaxFolderDepth = 8
KFolderSets = (("AssetData", "Schemas"), ("AssetData", "Resources", "Schemas"))
KMaxXmlDepth = 8
KVersionTable = (
    b"AssetTableOfContents:3.1,\n"
    b"DefinitionIteratorProperties:3.2,\n"
    b"InstanceProperties:3.2,\n"
    b"AssetLibVersion:1.0\n"
)
KStreamNames = (
    "AssetTableOfContents.bin",
    "DefinitionIteratorProperties.bin",
    "InstanceProperties.bin",
    "StreamVersionTable",
)
KContentTypes = (
    ("xml", "application/xml"),
    ("", "application/octet-stream"),
    ("bin", "application/octet-stream"),
)
KTypeNamespace = "http://schemas.openxmlformats.org/package/2006/content-types"
KPackageFormat = "http://schema.autodesk.com/design-package/2009"
