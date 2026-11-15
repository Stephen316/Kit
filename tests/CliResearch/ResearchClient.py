from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform

from tests.CliResearch.ResearchRoot import ResearchRoot


# compatibility checks must exercise the installed bridge against the explicitly pinned research checkout
def ResearchCli(
    WorkPath: FilePath, ToolName: str, *Arguments: str
) -> CompletedProcess[str]:
    return RunProcess(
        (
            str(
                FilePath(KPythonPath).with_name(
                    "kit.exe" if KPlatform == "win32" else "kit"
                )
            ),
            "research",
            "--root",
            str(ResearchRoot()),
            ToolName,
            *Arguments,
        ),
        cwd=WorkPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
