from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from tests.convert.formats.FusionCodec.TSpline.TsmCase import TsmCase


def ReadTsmFile(CaseValue: TsmCase) -> bytes:
    RootPath = FilePath(__file__).resolve().parents[5]
    SourcePath = (RootPath / CaseValue["Source"]).resolve()
    _ = SourcePath.relative_to(RootPath)
    Payload = SourcePath.read_bytes()
    assert HashBytes(Payload).hexdigest() == CaseValue["SourceHash"]
    return Payload
