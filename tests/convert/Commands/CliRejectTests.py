from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess


# invalid command syntax must return usable cli diagnostics without a traceback
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


# incompatible inspection flags must fail before creating an output file
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


# source aliases must never allow conversion or decoding to overwrite the input
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


# invalid inputs and unsupported destinations must fail cleanly while explicit supported formats remain usable
def CheckBadFiles(TmpPath: FilePath) -> None:
    Source = TmpPath / "invalid.f3d"
    _ = Source.write_bytes(b"not a CAD file")
    for Layer in ("neutral", "container", "native"):
        Result = CliProcess(TmpPath, "decode", str(Source), "--layer", Layer)
        assert Result.returncode == 1 and Result.stdout == ""
        assert "Traceback" not in Result.stderr
    Missing = CliProcess(TmpPath, "decode", str(TmpPath / "missing.f3d"))
    assert Missing.returncode == 1 and "Traceback" not in Missing.stderr
    TypedSource = TmpPath / "typed.f3d"
    _ = TypedSource.write_bytes(
        EmitDocument(
            DocumentSpec(
                "CLI cuboid",
                "height",
                17.0,
                ProfileKind="cuboid",
                ConstrainRectangle=True,
            )
        )
    )
    Unknown = CliProcess(
        TmpPath, "convert", str(TypedSource), str(TmpPath / "out.unsupported")
    )
    assert Unknown.returncode == 1 and not (TmpPath / "out.unsupported").exists()
    assert "no writer supports the destination" in Unknown.stderr
    Target = TmpPath / "out.unsupported"
    _ = Target.write_bytes(b"existing output")
    Refused = CliProcess(
        TmpPath, "convert", str(TypedSource), str(Target), "--overwrite"
    )
    assert Refused.returncode == 1 and Target.read_bytes() == b"existing output"
    Explicit = CliProcess(
        TmpPath,
        "convert",
        str(TypedSource),
        str(Target),
        "--to",
        "interchange.json",
        "--overwrite",
    )
    assert Explicit.returncode == 1 and Target.read_bytes() == b"existing output"
    assert "does not support the destination" in Explicit.stderr
    Fusion = CliProcess(
        TmpPath,
        "convert",
        str(TypedSource),
        str(Target),
        "--to",
        "fusion.f3d",
        "--overwrite",
    )
    assert Fusion.returncode == 0, Fusion.stderr
    assert Target.read_bytes() == TypedSource.read_bytes()


# input bounds must reject oversized files and unsafe argument text before processing
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
