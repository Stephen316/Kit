from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.json.Adapter import JsonAdapter
from convert.adapters.solidworks.Core.Native import KRefSupportSource
from tests.Convert.Api.ApiTestPaths import KSamplePath
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# direct json writing must preserve an ordinary typed fusion source
def TestDirectJson(TmpPath: FilePath) -> None:
    NativePath = TmpPath / "Source.f3d"
    _ = WriteDocument(
        AdapterCase("rectangle"),
        NativePath,
        destination_format="f3d",
        allow_carrier=False,
    )
    Original = OpenDocument(NativePath)
    TargetPath = TmpPath / "Target.json"
    Result = JsonAdapter().write(Original, TargetPath, WriteOptions())
    assert Result.bytes_written == TargetPath.stat().st_size
    assert OpenDocument(TargetPath) == Original


# legacy json inspection needs an escape for complete serialization of retained evidence
def TestLegacyJson(TmpPath: FilePath) -> None:
    Original = OpenDocument(KSamplePath)
    assert Original.sketches
    assert any(
        Sketch.attributes.get("support_plane_source") != KRefSupportSource
        or Sketch.attributes.get("unframed_support_plane_native_id") is not None
        for Sketch in Original.sketches
    )
    TargetPath = TmpPath / "Target.json"
    _ = TargetPath.write_bytes(b"existing destination")
    with RaisesError(ValueError, match="unqualified SOLIDWORKS sketch support"):
        _ = JsonAdapter().write(Original, TargetPath, WriteOptions(overwrite=True))
    assert TargetPath.read_bytes() == b"existing destination"
