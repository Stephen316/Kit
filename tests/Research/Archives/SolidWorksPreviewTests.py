from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from tests.Research.Archives.SolidWorksFreshBossTests import KFreshContext

from tests.Research.Archives.SolidWorksWriterStreamTests import LoadReport


# both native preview wrappers must preserve their authored pixel order and framing
def CheckPreviews() -> None:
    Report = LoadReport("VerifyPartPreviews.py", 8)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "58e800f573b900c94a1fb040778afcd5803485109579a6bae0a24824475040b3"
    )


# fresh preview members must preserve every previously generated package member
def CheckPrevsPkg() -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Program = RootPath / "re/solidworks/WriterResearch/VerifyPackPreviews.py"
    Result = RunProcess(
        [PythonExe, "-B", str(Program), "--fixture-context", "-"],
        cwd=RootPath,
        input=EncodeJson(KFreshContext),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Result.returncode == 0, Result.stderr
    Report = ParseJson(Result.stdout)
    assert Report["unchanged_members"] == 30
    assert Report["total_members"] == 32
    assert set(Report["images"]) == {"Preview", "PreviewPNG"}
