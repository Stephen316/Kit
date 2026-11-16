from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Commands.Metadata.BuildCaptured import BuildCaptured
from tests.Convert.Commands.WrapDocument import WrapDocument


# captured text objects must not bypass conversion guards through a qualified source contract
@TestMark.parametrize("Suffix", (".json", ".FCStd"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckCaptured(
    Suffix: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildCaptured()
    if IsNested:
        Document = WrapDocument(Document)
    Document.AssertValid()
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / ("blocked" + Suffix)
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    assert Error["error"] == "ValueError" and "CapturedObjects" in Error["message"]
    assert "kit decode or kit research" in Error["message"]
    assert Source.read_text(encoding="utf-8") == Original
    assert Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
    assert sorted(Value.name for Value in TmpPath.iterdir()) == (
        [Target.name, Source.name] if HasOutput else [Source.name]
    )
    Decoded = CliProcess(TmpPath, "decode", str(Source))
    assert Decoded.returncode == 0, Decoded.stderr
