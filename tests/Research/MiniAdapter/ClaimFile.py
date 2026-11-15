import json as JsonCodec
import os as OsLayer
from pathlib import Path as FilePath


# exclusive claim publication prevents the fixture from overwriting an existing worker lease
def WriteClaim(ClaimPath: FilePath, ClaimInfo: dict[str, object], Token: str) -> None:
    Handle = OsLayer.open(
        ClaimPath, OsLayer.O_CREAT | OsLayer.O_EXCL | OsLayer.O_WRONLY, 0o600
    )
    with OsLayer.fdopen(Handle, "w", encoding="utf-8") as Output:
        _ = Output.write(JsonCodec.dumps(dict(ClaimInfo, lease_token=Token)))
