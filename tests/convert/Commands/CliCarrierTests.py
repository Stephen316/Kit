from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath
from zipfile import ZipFile

from pytest import mark as TestMark

from tests.convert.Commands.BuildVariants import BuildVariants
from tests.convert.Commands.CliProcess import CliProcess


# parameter only inputs must fail qualification before configuration carrier output can be considered
@TestMark.parametrize("HasOutput", (False, True))
def CheckCliCarrier(HasOutput: bool, TmpPath: FilePath) -> None:
    Document = BuildVariants()
    Document.AssertValid()
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "blocked.FCStd"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    assert Error["error"] == "ValueError"
    assert "MissingFeatureHistory" in Error["message"]
    assert Source.read_text(encoding="utf-8") == Original
    assert Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
    assert sorted(Value.name for Value in TmpPath.iterdir()) == (
        ["blocked.FCStd", "source.json"] if HasOutput else ["source.json"]
    )


# the stricter cli policy must preserve existing sdk behavior for unsupported configuration transfer
def CheckSdkDefault(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.json"
    Original = BuildVariants().to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "sdk.FCStd"
    Result = RunProcess(
        (
            KPythonPath,
            "-I",
            "-c",
            """from json import dumps
from pathlib import Path
from sys import argv
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
Document = OpenDocument(Path(argv[1]))
Result = WriteDocument(Document, Path(argv[2]), AllowCarrier=False)
print(dumps({"usable": Result.IsAppUsable, "carriers": {Transfer.CapabilityData.value: Transfer.CarrierCause.value for Transfer in Result.Transfers if Transfer.CarrierCause is not None}}))
""",
            str(Source),
            str(Target),
        ),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert Result.returncode == 0, Result.stderr
    Evidence = LoadJson(Result.stdout)
    assert Evidence["usable"] is True
    assert Evidence["carriers"]["configurations"] == "target_unsupported"
    with ZipFile(Target) as Archive:
        assert Archive.read("Document.xml")
    assert Source.read_text(encoding="utf-8") == Original
