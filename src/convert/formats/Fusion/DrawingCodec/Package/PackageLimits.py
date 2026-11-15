# package limit needs one explicit bound so drawing packages cannot accept inconsistent resource or layout limits
KPackageLimit = 128 * 1024 * 1024

# max entries must remain consistent across callers so drawing members retain their sheet and model associations
KMaxEntries = 4096

# max entry bytes must remain consistent across callers so drawing members retain their sheet and model associations
KMaxEntryBytes = 64 * 1024 * 1024

# utf flag must remain consistent across callers so drawing members retain their sheet and model associations
KUtfFlag = 0x0800

# descriptor flag must remain consistent across callers so drawing members retain their sheet and model associations
KDescriptorFlag = 0x0008

# the allowed flags variants need one shared contract so drawing packages cannot omit a supported value shape
KAllowedFlags = KUtfFlag | KDescriptorFlag

# the methods vocabulary must stay centralized so drawing packages agrees on supported native identities
KMethods = frozenset((0, 8, 93))

# deflate level must remain consistent across callers so drawing members retain their sheet and model associations
KDeflateLevel = 6

# zstd magic must remain consistent across callers so drawing members retain their sheet and model associations
KZstdMagic = b"\x28\xb5\x2f\xfd"
