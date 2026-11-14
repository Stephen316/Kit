from sys import version_info as PythonVersion
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Graphics.CorruptScene import (
    CorruptScene,
)
from tests.convert.formats.FusionCodec.Documents.Graphics.GraphicsSources import (
    KGraphicSources,
)


@MarkTests.parametrize(
    "Variant, ErrorText",
    (
        ("world-tail", "Trailing Fusion graphics world"),
        ("version", "Unsupported graphics serializer versions"),
    ),
)
@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestSceneReject(TmpPath: FilePath, Variant: str, ErrorText: str) -> None:
    Target = TmpPath / "CorruptGraphics.f3d"
    CorruptScene(KGraphicSources[0], Target, Variant)
    with RaisesError(ValueError, match=ErrorText):
        _ = ReadDocument(Target.read_bytes())


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestMeshTail(TmpPath: FilePath) -> None:
    Target = TmpPath / "TailGraphics.f3d"
    CorruptScene(KGraphicSources[0], Target, "mesh-tail")
    Model = ReadDocument(Target.read_bytes())
    assert Model.Graphics is not None
    assert [Entry.Payload for Entry in Model.Graphics.MeshSlack] == [b"\x00"]
    assert ReadDocument(EmitParsed(Model)) == Model
