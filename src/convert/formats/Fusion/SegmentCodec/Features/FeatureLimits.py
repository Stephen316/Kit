# max feature bytes must remain consistent across callers so native records retain their segment ownership and schema
KMaxFeatureBytes = 16 * 1024 * 1024

# max feature text must remain consistent across callers so native records retain their segment ownership and schema
KMaxFeatureText = 65536

# max feature references must remain consistent across callers so native records retain their segment ownership and schema
KMaxFeatureRefs = 100000

# max lineage must remain consistent across callers so native records retain their segment ownership and schema
KMaxLineage = 16
