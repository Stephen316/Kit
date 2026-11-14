from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.CliProcess import CliProcess


@TestMark.parametrize("Layer", ("neutral", "container", "native"))
def CheckSourceLink(Layer: str, TmpPath: FilePath) -> None:
    Stored = TmpPath / "object"
    _ = Stored.write_bytes(EmitDocument(DocumentSpec("Linked source", "height", 17.0)))
    Source = TmpPath / "design.f3d"
    Source.symlink_to(Stored)
    Result = CliProcess(TmpPath, "decode", str(Source), "--layer", Layer)
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)
    assert Source.is_symlink()


def CheckTargetLink(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.f3d"
    _ = Source.write_bytes(EmitDocument(DocumentSpec("Linked target", "height", 17.0)))
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
