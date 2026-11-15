from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.json.Adapter import JsonAdapter
from tests.convert.api.ApiTestPaths import KSamplePath


def TestDirectJson(TmpPath: FilePath) -> None:
    Original = OpenDocument(KSamplePath)
    TargetPath = TmpPath / "Target.json"
    Result = JsonAdapter().write(Original, TargetPath, WriteOptions())
    assert Result.bytes_written == TargetPath.stat().st_size
    assert OpenDocument(TargetPath) == Original
