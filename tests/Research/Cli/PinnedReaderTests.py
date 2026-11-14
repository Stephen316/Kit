from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from tests.Research.Cli.ResearchClient import KResearchRoot, ResearchCli
from tests.Research.FusionClient import KArchiveAsset, KControlAsset


def CheckSwReceipts(TmpPath: FilePath) -> None:
    Direct = TmpPath / "Direct"
    Bridged = TmpPath / "Bridged"
    Arguments = ("--asset", "re/solidworks/examples/.SLDPRT/example.SLDPRT")
    Reference = RunProcess(
        (
            KPythonPath,
            str(KResearchRoot / "re/automation/SolidworksReader.py"),
            *Arguments,
            "--output",
            str(Direct),
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    Result = ResearchCli("solidworks", *Arguments, "--output", str(Bridged))
    assert Reference.returncode == Result.returncode == 0, (
        Reference.stderr,
        Result.stderr,
    )
    for FileName in ("document.json", "receipt.json"):
        assert (Direct / FileName).read_bytes() == (Bridged / FileName).read_bytes()
    assert (
        LoadJson((Bridged / "receipt.json").read_text())["portable_complete"] is False
    )
    Before = (Bridged / "receipt.json").read_bytes()
    Repeated = ResearchCli("solidworks", *Arguments, "--output", str(Bridged))
    assert Repeated.returncode == 1
    assert (Bridged / "receipt.json").read_bytes() == Before


def CheckFusReceipt(TmpPath: FilePath) -> None:
    Direct = TmpPath / "Direct"
    Bridged = TmpPath / "Bridged"
    Arguments = ("--asset", KControlAsset, "--asset", KArchiveAsset, "--allow-partial")
    Reference = RunProcess(
        (
            KPythonPath,
            str(KResearchRoot / "re/automation/FusionReader.py"),
            *Arguments,
            "--output",
            str(Direct),
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    Result = ResearchCli("fusion", *Arguments, "--output", str(Bridged))
    assert Reference.returncode == Result.returncode, (Reference.stderr, Result.stderr)
    assert Result.returncode in (0, 3)
    assert {
        Value.relative_to(Direct) for Value in Direct.rglob("*") if Value.is_file()
    } == {Value.relative_to(Bridged) for Value in Bridged.rglob("*") if Value.is_file()}
    for FilePath in Direct.rglob("*.json"):
        assert (
            FilePath.read_bytes()
            == (Bridged / FilePath.relative_to(Direct)).read_bytes()
        )
    Summary = LoadJson((Bridged / "summary.json").read_text())
    assert Summary["counts"]["assets"] == 2
    assert Summary["counts"]["decoded"] >= 1
    assert Summary["allow_partial"] is True and Summary["portable_complete"] is False
    Rejected = ResearchCli(
        "fusion", "--asset", KArchiveAsset, "--output", str(TmpPath / "Rejected")
    )
    assert Rejected.returncode == 3, Rejected.stderr
    assert (TmpPath / "Rejected" / "summary.json").is_file()
