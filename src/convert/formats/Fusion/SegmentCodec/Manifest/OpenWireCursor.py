from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ManifestCursor import (
    ManifestCursor,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KMaxManifestBytes,
)


# standalone payload readers use the same bound as the indexed archive reader
def OpenWireCursor(Payload: bytes) -> ManifestCursor:
    if type(Payload) is not bytes or not 0 < len(Payload) <= KMaxManifestBytes:
        raise ValueError("Invalid Fusion manifest payload size")
    return ManifestCursor(Payload)
