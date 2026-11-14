from json import loads as LoadJson
from pathlib import Path as FilePath
from shutil import which as FindProgram
from subprocess import run as RunProcess

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess


def CheckCliCatalog(TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, "formats", "--json")
    assert Result.returncode == 0, Result.stderr
    Formats = {Value["format"]: Value for Value in LoadJson(Result.stdout)}
    assert Formats["solidworks.sldprt"]["read"] is True
    assert Formats["solidworks.sldprt"]["write"] is False
    assert Formats["fusion.f3d"]["write"] is True
    assert Formats["interchange.json"]["write"] is True
    Console = FindProgram("kit")
    assert Console is not None
    HelpResult = RunProcess(
        (Console, "--help"),
        cwd=TmpPath,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert HelpResult.returncode == 0, HelpResult.stderr
    assert "convert" in HelpResult.stdout and "decode" in HelpResult.stdout


def CheckCliConvert(TmpPath: FilePath) -> None:
    Target = TmpPath / "decoded.json"
    Result = CliProcess(TmpPath, "convert", str(KSamplePath), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    Report = LoadJson(Result.stdout)
    assert Report["source_format"] == "solidworks.sldprt"
    assert Report["destination_format"] == "interchange.json"
    assert Report["dropped"] == [] and Report["requirements"] == []
    assert Report["application_usable"] is True
    assert (
        CadDocument.from_json(Target.read_text()).Source.FormatId == "solidworks.sldprt"
    )
    Before = Target.read_bytes()
    Repeated = CliProcess(TmpPath, "convert", str(KSamplePath), str(Target))
    assert Repeated.returncode == 1 and Target.read_bytes() == Before
    Overwrite = CliProcess(
        TmpPath, "convert", str(KSamplePath), str(Target), "--overwrite"
    )
    assert Overwrite.returncode == 0, Overwrite.stderr
    assert "Writer evidence only" in Overwrite.stdout


def CheckCliRound(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.f3d"
    Original = EmitDocument(
        DocumentSpec(
            "CLI cylinder", "height", 17.0, ProfileKind="extrusion", RadiusMm=12.0
        )
    )
    _ = Source.write_bytes(Original)
    Neutral = TmpPath / "neutral.json"
    First = CliProcess(TmpPath, "convert", str(Source), str(Neutral), "--json")
    assert First.returncode == 0, First.stderr
    Restored = TmpPath / "restored.f3d"
    Second = CliProcess(
        TmpPath, "convert", str(Neutral), str(Restored), "--to", "f3d", "--json"
    )
    assert Second.returncode == 0, Second.stderr
    assert Restored.read_bytes() == Original
    assert Source.read_bytes() == Original


def CheckCliPolicy(TmpPath: FilePath) -> None:
    Target = TmpPath / "blocked.CATPart"
    _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(KSamplePath), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    assert Error["details"]["code"] == "output_not_application_usable"
    assert Target.read_bytes() == b"existing output"
    assert sorted(Value.name for Value in TmpPath.iterdir()) == ["blocked.CATPart"]
