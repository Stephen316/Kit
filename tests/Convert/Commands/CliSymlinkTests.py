from json import loads as LoadJson
from pathlib import Path as FilePath
from sys import version_info as KPythonVersion

from pytest import mark as TestMark

from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Commands.CliProcess import CliProcess


# source symlinks must remain usable for inspection without changing the link itself
@TestMark.parametrize("Layer", ("neutral", "container", "native"))
def CheckSourceLink(Layer: str, TmpPath: FilePath) -> None:
    Stored = TmpPath / "object"
    _ = Stored.write_bytes(EmitDocument(DocumentSpec("Linked source", "height", 17.0)))
    Source = TmpPath / "design.f3d"
    Source.symlink_to(Stored)
    Result = CliProcess(TmpPath, "decode", str(Source), "--layer", Layer)
    if Layer == "native" and KPythonVersion < (3, 14):
        assert Result.returncode == 1 and "Python 3.14" in Result.stderr
        assert Source.is_symlink()
        return
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)
    assert Source.is_symlink()


# explicit destination symlinks must preserve their identity when publishing converted or decoded content
def CheckTargetLink(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.f3d"
    _ = Source.write_bytes(
        EmitDocument(
            DocumentSpec(
                "Linked target",
                "height",
                17.0,
                ProfileKind="cuboid",
                ConstrainRectangle=True,
            )
        )
    )
    Stored = TmpPath / "object"
    _ = Stored.write_text("existing output")
    Target = TmpPath / "destination.json"
    Target.symlink_to(Stored)
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--overwrite")
    assert Result.returncode == 0, Result.stderr
    assert CadDocument.from_json(Stored.read_text()).Source.FormatId == "fusion.f3d"
    assert Target.is_symlink()
    Decoded = CliProcess(
        TmpPath, "decode", str(Source), "-o", str(Target), "--overwrite"
    )
    assert Decoded.returncode == 0, Decoded.stderr
    assert LoadJson(Stored.read_text())["kind"] == "kit.decode"
    assert Target.is_symlink()
