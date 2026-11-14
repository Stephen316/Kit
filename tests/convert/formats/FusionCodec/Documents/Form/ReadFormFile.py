from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath


def ReadFormFile(Relative: str, Digest: str) -> bytes:
    RootPath = FilePath(__file__).resolve().parents[6]
    SourcePath = (RootPath / Relative).resolve()
    _ = SourcePath.relative_to(RootPath)
    Payload = SourcePath.read_bytes()
    assert HashBytes(Payload).hexdigest() == Digest
    return Payload
