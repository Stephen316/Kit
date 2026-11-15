from importlib.metadata import version as GetVersion
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import mark as TestMark


# installed module commands must preserve explicit version output and argparse placement rules
@TestMark.parametrize("ModuleName", ("convert", "KitCli"))
@TestMark.parametrize(
    "Arguments,ExpectedCode",
    ((("--version",), 0), (("--version", "formats"), 0), (("formats", "--version"), 2)),
)
def CheckVersion(
    ModuleName: str,
    Arguments: tuple[str, ...],
    ExpectedCode: int,
    TmpPath: FilePath,
) -> None:
    Result = RunProcess(
        (KPythonPath, "-I", "-m", ModuleName, *Arguments),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == ExpectedCode, Result.stderr
    if ExpectedCode == 0:
        assert Result.stdout.strip() == GetVersion("unicad-kit")
        assert Result.stderr == ""
        return
    assert Result.stdout == ""
    assert "unrecognized arguments: --version" in Result.stderr


# hosted parsers must discover the installed version independently from their host process arguments
def CheckHostVer(TmpPath: FilePath) -> None:
    Result = RunProcess(
        (
            KPythonPath,
            "-I",
            "-c",
            """from sys import argv
argv[:] = ["host", "formats"]
from convert.Commands.BuildParser import BuildParser
BuildParser().parse_args(["--version"])
""",
        ),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == 0, Result.stderr
    assert Result.stdout.strip() == GetVersion("unicad-kit")
    assert Result.stderr == ""
