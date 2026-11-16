import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from typing import cast as CastValue


# each research record verifier runs with its own pinned archive evidence
def LoadReport(ProgramName: str) -> dict[str, object]:
    RootPath = FilePath(__file__).resolve().parents[3]
    Program = RootPath / "re/solidworks/WriterResearch" / ProgramName
    Process = Subprocess.run(
        [System.executable, str(Program)],
        cwd=RootPath,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr
    Report: dict[str, object] = JsonCodec.loads(Process.stdout)
    assert Report["capture_revision"] == "466dcb172dfa3803463e07ccde963ba01671d200"
    Captures = Report["captures"]
    assert isinstance(Captures, dict)
    assert len(CastValue(dict[str, str], Captures)) == 25
    return Report


# the research writer and reader must agree on the full stream in real native files
def CheckDefinition() -> None:
    Report = LoadReport("VerifyDefinition.py")
    assert Report["preamble_view_forms"] == Report["line_font_orders"] == 2


# all observed default visual objects must reconstruct the same measured color body
def CheckDspbr() -> None:
    Report = LoadReport("VerifyCmgrColor.py")
    Captures = Report["captures"]
    assert isinstance(Captures, dict)
    assert set(CastValue(dict[str, str], Captures).values()) == {
        "3b77a4c24f8a5953b871c3b9fa7b0df54008ddf61bacb11baffc7c78fba937a9"
    }
