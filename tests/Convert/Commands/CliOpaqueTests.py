from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.BuildOpaque import BuildOpaque
from tests.Convert.Commands.CliProcess import CliProcess


# opaque neutral records must remain decodable while user conversion fails with actionable diagnostics
@TestMark.parametrize(
    "RecordKind", ("NativeFeature", "NativeGeometry", "UnqualifiedResearch")
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckOpaqueJson(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildOpaque(RecordKind, IsNested)
    Document.AssertValid()
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original)
    Target = TmpPath / "blocked.json"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    assert Error["error"] == "ValueError"
    assert (
        RecordKind in Error["message"]
        and "kit decode or kit research" in Error["message"]
    )
    assert Source.read_text() == Original
    assert Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
    Decoded = CliProcess(TmpPath, "decode", str(Source))
    assert Decoded.returncode == 0, Decoded.stderr
