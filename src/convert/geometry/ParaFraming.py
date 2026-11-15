# wrapper magic must remain consistent across callers so native geometry retains a consistent interchange interpretation
KWrapperMagic = bytes.fromhex("231dd571da8148a2a85898b21b89ef99")

# max decoded bytes must remain consistent across callers so native geometry retains a consistent interchange interpretation
KMaxDecodedBytes = 1 << 31
