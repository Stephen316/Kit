from convert.Formats.Fusion.DrawingCodec.Dwg.Header.MakeCryptMask import MakeCryptMask

# data page type must remain consistent across callers so section boundaries and object references remain consistent
KDataPageType = 0x4163043B

# section map type must remain consistent across callers so section boundaries and object references remain consistent
KSectionMapType = 0x4163003B

# page map type must remain consistent across callers so section boundaries and object references remain consistent
KPageMapType = 0x41630E3B

# page mask must remain consistent across callers so section boundaries and object references remain consistent
KPageMask = 0x4164536B

# page base must remain consistent across callers so section boundaries and object references remain consistent
KPageBase = 0x100

# mask bytes must remain consistent across callers so section boundaries and object references remain consistent
KMaskBytes = MakeCryptMask(0x8000)
