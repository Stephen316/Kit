from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess


@TestMark.parametrize(
    "Arguments",
    (
        ("convert",),
        ("decode",),
        ("formats", "--js"),
        ("convert", "a", "b", "--partial"),
        ("decode", "a", "--layer", "unknown"),
    ),
)
def CheckCliUsage(Arguments: tuple[str, ...], TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, *Arguments)
    assert Result.returncode == 2 and Result.stdout == ""
    assert "usage:" in Result.stderr and "Traceback" not in Result.stderr


@TestMark.parametrize(
    "Arguments",
    (
        ("--layer", "native"),
        ("--stream", "Header2"),
        ("--layer", "container", "--partial"),
        ("--layer", "container", "--configuration", "Default"),
    ),
)
def CheckCliLayers(Arguments: tuple[str, ...], TmpPath: FilePath) -> None:
    Target = TmpPath / "blocked.json"
    Result = CliProcess(
        TmpPath, "decode", str(KSamplePath), "-o", str(Target), *Arguments
    )
    assert Result.returncode == 1 and Result.stdout == ""
    assert not Target.exists() and "Traceback" not in Result.stderr


@TestMark.parametrize("Command", ("convert", "decode"))
@TestMark.parametrize("LinkKind", ("same", "hard", "symbolic"))
def CheckCliSource(Command: str, LinkKind: str, TmpPath: FilePath) -> None:
    Source = TmpPath / "source.SLDPRT"
    Original = KSamplePath.read_bytes()
    _ = Source.write_bytes(Original)
    Target = Source
    if LinkKind != "same":
        Target = TmpPath / "linked.json"
        if LinkKind == "hard":
            Target.hardlink_to(Source)
        else:
            Target.symlink_to(Source)
    Arguments = (str(Target),) if Command == "convert" else ("-o", str(Target))
    Result = CliProcess(TmpPath, Command, str(Source), *Arguments, "--overwrite")
    assert Result.returncode == 1 and Result.stdout == ""
    assert Source.read_bytes() == Original and Target.read_bytes() == Original


def CheckBadFiles(TmpPath: FilePath) -> None:
    Source = TmpPath / "invalid.f3d"
    _ = Source.write_bytes(b"not a CAD file")
    for Layer in ("neutral", "container", "native"):
        Result = CliProcess(TmpPath, "decode", str(Source), "--layer", Layer)
        assert Result.returncode == 1 and Result.stdout == ""
        assert "Traceback" not in Result.stderr
    Missing = CliProcess(TmpPath, "decode", str(TmpPath / "missing.f3d"))
    assert Missing.returncode == 1 and "Traceback" not in Missing.stderr
    Unknown = CliProcess(
        TmpPath, "convert", str(KSamplePath), str(TmpPath / "out.unsupported")
    )
    assert Unknown.returncode == 1 and not (TmpPath / "out.unsupported").exists()


def CheckCliBounds(TmpPath: FilePath) -> None:
    Source = TmpPath / "oversized.f3d"
    with Source.open("wb") as Output:
        _ = Output.truncate(256 * 1024 * 1024 + 1)
    Result = CliProcess(TmpPath, "decode", str(Source))
    assert Result.returncode == 1 and "256 MiB" in Result.stderr
    Argument = CliProcess(TmpPath, "decode", "x" * 4097)
    assert Argument.returncode == 1 and "4096" in Argument.stderr
    Control = CliProcess(TmpPath, "decode", "bad\x1bname")
    assert Control.returncode == 1 and "\x1b" not in Control.stderr
