from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Api.ApiTestPaths import KSamplePath
from tests.Convert.Commands.CliProcess import CliProcess


# actual unqualified native features must refuse conversion without replacing user files
@TestMark.parametrize("HasOutput", (False, True))
def CheckNativeFile(HasOutput: bool, TmpPath: FilePath) -> None:
    Source = TmpPath / "source.SLDPRT"
    Original = KSamplePath.read_bytes()
    _ = Source.write_bytes(Original)
    Target = TmpPath / "blocked.json"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    assert "NativeFeature" in LoadJson(Result.stderr)["message"]
    assert Source.read_bytes() == Original
    assert Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
