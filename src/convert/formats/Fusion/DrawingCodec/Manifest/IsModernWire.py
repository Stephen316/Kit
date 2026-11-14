from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KLegacyVersion,
    KModernMagic,
    KModernVersion,
)


def IsModernWire(Magic: int, Version: int) -> bool:
    if Magic == KModernMagic and Version == KModernVersion:
        return True
    if Magic != KModernMagic and Version == KLegacyVersion:
        return False
    raise ValueError("Unsupported Fusion drawing manifest version")
