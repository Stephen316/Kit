from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.json.Adapter import JsonAdapter
from convert.adapters.solidworks.core.Native import KRefSupportSource
from tests.convert.api.ApiTestPaths import KSamplePath


def TestDirectJson(TmpPath: FilePath) -> None:
    Original = OpenDocument(KSamplePath)
    assert Original.sketches
    assert all(
        Sketch.attributes.get("support_plane_source") == KRefSupportSource
        and Sketch.attributes.get("unframed_support_plane_native_id") is None
        for Sketch in Original.sketches
    )
    TargetPath = TmpPath / "Target.json"
    Result = JsonAdapter().write(Original, TargetPath, WriteOptions())
    assert Result.bytes_written == TargetPath.stat().st_size
    assert OpenDocument(TargetPath) == Original
