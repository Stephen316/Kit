from sys import version_info as PythonVersion
from pathlib import Path as FilePath
from zipfile import ZipFile

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Graphics.GraphicsSources import (
    KGraphicSources,
)


@MarkTests.parametrize("SourceIndex, ObjectCount", ((0, 39), (1, 41)))
@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestNativeScene(TmpPath: FilePath, SourceIndex: int, ObjectCount: int) -> None:
    Source = KGraphicSources[SourceIndex]
    Model = ReadDocument(Source.read_bytes())
    assert Model.Graphics is not None
    assert len(Model.Graphics.Objects) == ObjectCount
    Target = TmpPath / "Graphics.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened == Model
    with ZipFile(Source) as Before, ZipFile(Target) as After:
        Names = tuple(
            NameValue
            for NameValue in Before.namelist()
            if "OGS.BlobFolder/" in NameValue
        )
        assert len(Names) == 5
        for NameValue in Names:
            assert After.read(NameValue) == Before.read(NameValue)
