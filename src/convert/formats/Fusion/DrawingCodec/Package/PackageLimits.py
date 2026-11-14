KPackageLimit = 128 * 1024 * 1024

KMaxEntries = 4096

KMaxEntryBytes = 64 * 1024 * 1024

KUtfFlag = 0x0800

KDescriptorFlag = 0x0008

KAllowedFlags = KUtfFlag | KDescriptorFlag

KMethods = frozenset((0, 8, 93))

KDeflateLevel = 6

KZstdMagic = b"\x28\xb5\x2f\xfd"
