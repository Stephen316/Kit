from io import BytesIO
from json import loads as LoadJson
from pathlib import Path as FilePath
from sys import version_info as KPythonVersion
from zipfile import ZipFile

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from tests.convert.Commands.CliProcess import CliProcess


# older runtimes must retain archive inventory while refusing unsupported extraction without publication
def CheckFusRuntime(TmpPath: FilePath) -> None:
    Source = TmpPath / "runtime.f3d"
    _ = Source.write_bytes(EmitDocument(DocumentSpec("CLI runtime", "height", 19.0)))
    if KPythonVersion >= (3, 14):
        with ZipFile(BytesIO(Source.read_bytes())) as Original:
            with ZipFile(Source, "w", compression=93) as Compressed:
                for Member in Original.infolist():
                    Compressed.writestr(
                        Member.filename,
                        Original.read(Member),
                        compress_type=0 if Member.is_dir() else 93,
                    )
    Inventory = CliProcess(TmpPath, "decode", str(Source), "--layer", "container")
    assert Inventory.returncode == 0, Inventory.stderr
    if KPythonVersion >= (3, 14):
        assert all(
            Value["compression_method"] == 93
            for Value in LoadJson(Inventory.stdout)["members"]
            if not Value["directory"]
        )
    StreamName = next(
        Value["name"]
        for Value in LoadJson(Inventory.stdout)["members"]
        if not Value["directory"]
    )
    for Arguments in (
        ("--layer", "container", "--stream", StreamName),
        ("--layer", "native"),
    ):
        Target = TmpPath / "runtime.json"
        Result = CliProcess(
            TmpPath, "decode", str(Source), *Arguments, "-o", str(Target)
        )
        if KPythonVersion < (3, 14):
            assert Result.returncode == 1 and "Python 3.14" in Result.stderr
            assert not Target.exists() and Result.stdout == ""
            continue
        assert Result.returncode == 0, Result.stderr
        assert LoadJson(Target.read_text())
        Target.unlink()
