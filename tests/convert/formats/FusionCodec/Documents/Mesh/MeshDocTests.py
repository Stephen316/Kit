from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Mesh.ReadMeshCases import ReadMeshCases
from tests.convert.formats.FusionCodec.Mesh.ReadMeshFile import KRootPath


@MarkTests.parametrize(
    "FileName", tuple(sorted({CaseValue["Archive"] for CaseValue in ReadMeshCases()}))
)
@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native mesh archive requires ZIP Zstandard"
)
def TestMeshDocs(TmpPath: FilePath, FileName: str) -> None:
    Source = KRootPath / FileName
    Model = ReadDocument(Source.read_bytes())
    Expected = tuple(
        CaseValue for CaseValue in ReadMeshCases() if CaseValue["Archive"] == FileName
    )
    assert len(Model.Meshes) == len(Expected)
    assert {Value.Name for Value in Model.Meshes} == {
        Value["Member"].removeprefix("FusionAssetName[Active]/") for Value in Expected
    }
    Target = TmpPath / "Meshes.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    assert ReadDocument(Target.read_bytes()) == Model
    with ZipFile(Source) as Before, ZipFile(Target) as After:
        for NameValue in Before.namelist():
            if (
                NameValue.endswith(("MetaStream.dat", "BulkStream.dat"))
                or "/OGS/" in NameValue
            ):
                assert After.read(NameValue) == Before.read(NameValue)
