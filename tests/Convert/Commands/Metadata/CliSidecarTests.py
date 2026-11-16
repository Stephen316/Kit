from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Commands.Metadata.BuildSidecar import BuildSidecar


# metadata sidecars must not escape conversion policy or alter existing companion files
@TestMark.parametrize("RecordKind", ("Mesh", "Sketch", "Parameter"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
@TestMark.parametrize("Suffix", (".json", ".FCStd"))
def CheckSidecars(
    RecordKind: str,
    IsNested: bool,
    HasOutput: bool,
    Suffix: str,
    TmpPath: FilePath,
) -> None:
    Document = BuildSidecar(RecordKind, IsNested)
    Document.AssertValid()
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / ("blocked" + Suffix)
    Sidecar = TmpPath / "blocked"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
        Sidecar.mkdir()
        _ = (Sidecar / "child.FCStd").write_bytes(b"existing companion")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    assert Error["error"] == "ValueError" and "ExternalDocuments" in Error["message"]
    assert "kit decode or kit research" in Error["message"]
    assert Source.read_text(encoding="utf-8") == Original
    assert Target.exists() is HasOutput and Sidecar.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
        assert list(Sidecar.iterdir()) == [Sidecar / "child.FCStd"]
        assert (Sidecar / "child.FCStd").read_bytes() == b"existing companion"
    Decoded = CliProcess(TmpPath, "decode", str(Source))
    assert Decoded.returncode == 0, Decoded.stderr
