from convert.Formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KLegacyVersion,
    KModernMagic,
    KModernVersion,
)


# the modern wire decision must stay consistent so drawing members retain their sheet and model associations
def IsModernWire(Magic: int, Version: int) -> bool:
    if Magic == KModernMagic and Version == KModernVersion:
        return True
    if Magic != KModernMagic and Version == KLegacyVersion:
        return False
    raise ValueError("Unsupported Fusion drawing manifest version")
