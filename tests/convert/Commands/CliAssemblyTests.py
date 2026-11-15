from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark

from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess


# assembly container inspection must retain format identity even when extension inference is unavailable
def CheckAsmLabel(TmpPath: FilePath) -> None:
    Source = (
        KSamplePath.parents[1]
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "Cylinder Head Assy 1.SLDASM"
    )
    Result = CliProcess(TmpPath, "decode", str(Source), "--layer", "container")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)["format"] == "solidworks.sldasm"
    Renamed = TmpPath / "assembly.data"
    _ = Renamed.write_bytes(Source.read_bytes())
    Explicit = CliProcess(
        TmpPath,
        "decode",
        str(Renamed),
        "--layer",
        "container",
        "--from",
        "solidworks.sldasm",
    )
    assert Explicit.returncode == 0, Explicit.stderr
    assert LoadJson(Explicit.stdout)["format"] == "solidworks.sldasm"


# missing companion files must prevent conversion without destroying the inspectable assembly source
@TestMark.parametrize("HasOutput", (False, True))
def CheckAsmSources(HasOutput: bool, TmpPath: FilePath) -> None:
    Fixture = (
        KSamplePath.parents[1]
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "ENSAMBLAJE DE SEGURO DE ARBOL DE LEVAS.SLDASM"
    )
    Source = TmpPath / "isolated.SLDASM"
    Original = Fixture.read_bytes()
    _ = Source.write_bytes(Original)
    Decoded = CliProcess(TmpPath, "decode", str(Source), "--partial")
    assert Decoded.returncode == 0, Decoded.stderr
    Assembly = CadDocument.from_json(
        DumpJson(LoadJson(Decoded.stdout)["document"])
    ).assembly
    assert Assembly is not None
    RootDef = next(
        Definition
        for Definition in Assembly.definitions
        if Definition.id == Assembly.root_definition_id
    )
    assert RootDef.attributes["source_resolved"] is True
    Unloaded = [
        Definition
        for Definition in Assembly.definitions
        if Definition.id != Assembly.root_definition_id
    ]
    assert Unloaded and not Assembly.documents
    assert all(
        Definition.attributes["source_resolved"] is False
        and Definition.document_id == ""
        for Definition in Unloaded
    )
    Target = TmpPath / "blocked.json"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    assert "error" in LoadJson(Result.stderr)
    assert Source.read_bytes() == Original and Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"


# deferred component discovery must remain distinguishable from resolved sources in sdk output
def CheckDeferred(TmpPath: FilePath) -> None:
    Fixture = (
        KSamplePath.parents[1]
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "ENSAMBLAJE DE SEGURO DE ARBOL DE LEVAS.SLDASM"
    )
    Source = TmpPath / "isolated.SLDASM"
    Original = Fixture.read_bytes()
    _ = Source.write_bytes(Original)
    Result = RunProcess(
        (
            KPythonPath,
            "-I",
            "-c",
            """from pathlib import Path as FilePath
from sys import argv as ArgValues
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.core.Adapter import SldprtAdapter
Document = SldprtAdapter().read(
    FilePath(ArgValues[1]),
    ReadOptions(strict=False, values={"resolve_components": False, "discover_companions": False}),
)
print(Document.to_json())
""",
            str(Source),
        ),
        cwd=TmpPath,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert Result.returncode == 0, Result.stderr
    Assembly = CadDocument.from_json(Result.stdout).assembly
    assert Assembly is not None
    assert len(Assembly.definitions) > 1 and not Assembly.documents
    assert all(
        "source_resolved" not in Definition.attributes
        for Definition in Assembly.definitions
    )
    assert all(
        (
            Definition.attributes.get("source_resolution") == "deferred"
            if Definition.id != Assembly.root_definition_id
            else "source_resolution" not in Definition.attributes
        )
        for Definition in Assembly.definitions
    )
    assert Source.read_bytes() == Original
