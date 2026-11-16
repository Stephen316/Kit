import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# the research writer and reader must agree on the full stream in real native files
def CheckDefinition() -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Program = RootPath / "re/solidworks/WriterResearch/VerifyDefinition.py"
    Process = Subprocess.run(
        [System.executable, str(Program)],
        cwd=RootPath,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr
    Report = JsonCodec.loads(Process.stdout)
    assert Report["capture_revision"] == "466dcb172dfa3803463e07ccde963ba01671d200"
    assert len(Report["captures"]) == 25
    assert Report["preamble_view_forms"] == Report["line_font_orders"] == 2
