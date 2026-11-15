from json import loads as LoadJson
from pathlib import Path as FilePath

from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.CliProcess import CliProcess


# qualification refusals must preserve source and destination while keeping developer decoding available
def CheckJsonBlock(
    Document: CadDocument, RecordName: str, HasOutput: bool, WorkPath: FilePath
) -> None:
    Document.AssertValid()
    Source = WorkPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = WorkPath / "blocked.json"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        WorkPath,
        "convert",
        str(Source),
        str(Target),
        "--from",
        "INTERCHANGE.JSON",
        "--overwrite",
        "--json",
    )
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    assert Error["error"] == "ValueError" and RecordName in Error["message"]
    assert "kit decode or kit research" in Error["message"]
    assert Source.read_text(encoding="utf-8") == Original
    assert Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
    Decoded = CliProcess(WorkPath, "decode", str(Source))
    assert Decoded.returncode == 0, Decoded.stderr
