from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import KActivePrefix

# the active asset stores both configuration json members under the same directory
KConfigPrefix = KActivePrefix + "DesignConfigurationTable.BlobParts/"

# configuration serializers name their own sidecar in a counted logical filename
KConfigClasses = {
    "49B2AA69-7655-4C36-A14E-9582CCF1283C": ("DesignConfigurationTable", ".dsgcfg"),
    "3185B924-6C84-4804-BE77-9105B09209DA": ("DesignConfigurationRule", ".dsgcfgrule"),
}
