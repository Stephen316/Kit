from base64 import b64decode as DecodeText
from functools import cache as CacheValue
from hashlib import sha256 as HashValue
from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import importorskip as ImportSkip
from pytest import skip as SkipTest

KSourcePath = FilePath(__file__).with_name("DrawingSources.xz")

KHistoricName = "20181122T163107_Boxes Drawing-V1.f3z"

KHistoricHash = "4e67c7a5487c3c1d3f3c193571206e87a0fb67da7990bd23f6638759aefe734b"

KInstallRoot = "Library/Application Support/Autodesk/webdeploy/production"


class FrameReplay:
    def __init__(self) -> None:
        super().__init__()
        self.Frames: dict[bytes, bytes] = {}

    def Inflate(self, Packed: bytes, Expected: int) -> bytes:
        Codec = ImportSkip("compression.zstd")
        Result = Codec.decompress(Packed)
        assert isinstance(Result, bytes) and len(Result) == Expected
        self.Frames[Result] = Packed
        return Result

    def Compress(self, Payload: bytes) -> bytes:
        return self.Frames[Payload]


@CacheValue
def DrawingSources() -> dict[str, bytes]:
    Encoded = CastValue(dict[str, str], LoadJson(Decompress(KSourcePath.read_bytes())))
    return {Label: DecodeText(TextValue) for Label, TextValue in Encoded.items()}


def HistoricBundle() -> bytes:  # lgtm[py/mixed-returns]
    Install = FilePath.home() / KInstallRoot
    Matches = sorted(
        Install.glob("*/Autodesk Fusion.app/Contents/Resources/CloudWorkFlowsData/*")
    )
    for Candidate in Matches:
        if Candidate.name == KHistoricName:
            DataValue = Candidate.read_bytes()
            if HashValue(DataValue).hexdigest() == KHistoricHash:
                return DataValue
    SkipTest("installed historical Fusion drawing example is unavailable")
