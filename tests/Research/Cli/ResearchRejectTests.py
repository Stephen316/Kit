from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark

from tests.Research.Cli.ResearchClient import KResearchRoot, ResearchCli


@TestMark.parametrize(
    "FieldName,FieldValue",
    (
        ("sha256", "0" * 64),
        ("git_blob", "0" * 40),
        ("size_bytes", 1),
        ("prefix_hex", "00" * 16),
    ),
)
def CheckPinFailure(FieldName: str, FieldValue: str | int, TmpPath: FilePath) -> None:
    Manifest = LoadJson((KResearchRoot / "re/automation/Corpus.json").read_text())
    AssetPath = "re/solidworks/examples/.SLDPRT/example.SLDPRT"
    for Entry in Manifest["assets"]:
        if Entry["path"] == AssetPath:
            Entry[FieldName] = FieldValue
    ManifestPath = TmpPath / "Manifest.json"
    _ = ManifestPath.write_text(DumpJson(Manifest))
    TargetPath = TmpPath / "Rejected"
    Result = ResearchCli(
        "solidworks",
        "--asset",
        AssetPath,
        "--manifest",
        str(ManifestPath),
        "--output",
        str(TargetPath),
    )
    assert Result.returncode == 1 and not TargetPath.exists()


def CheckRootGuard(TmpPath: FilePath) -> None:
    Result = RunProcess(
        (
            KPythonPath,
            "-m",
            "convert",
            "research",
            "--root",
            str(TmpPath),
            "solidworks",
            "--help",
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == 1 and "requested PR94 research tool" in Result.stderr
    RootOverride = ResearchCli("solidworks", "--root", str(TmpPath))
    assert RootOverride.returncode == 1 and "--root once" in RootOverride.stderr
    Unknown = ResearchCli("unknown", "--help")
    assert Unknown.returncode == 2
    HelpResult = ResearchCli("controller", "--help")
    assert HelpResult.returncode == 0 and "submit-batch" in HelpResult.stdout


@TestMark.parametrize(
    "RootFlag", ("--r", "--ro", "--roo", "--root", "--roo=other", "--root=other")
)
def CheckRootPrefix(RootFlag: str, TmpPath: FilePath) -> None:
    Result = ResearchCli(
        "corpus",
        "check",
        RootFlag,
        str(TmpPath),
        "--manifest",
        str(TmpPath / "Manifest.json"),
    )
    assert Result.returncode == 1 and "--root once" in Result.stderr
