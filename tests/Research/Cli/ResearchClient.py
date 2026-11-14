from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath

KResearchRoot = FilePath(__file__).resolve().parents[3]


def ResearchCli(ToolName: str, *Arguments: str) -> CompletedProcess[str]:
    return RunProcess(
        (
            KPythonPath,
            "-m",
            "convert",
            "research",
            "--root",
            str(KResearchRoot),
            ToolName,
            *Arguments,
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
