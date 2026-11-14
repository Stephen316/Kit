from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile
from pytest import mark as MarkTests
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.GraphicsCodec.Model.Values.CircleArcValue import (
    CircleArcValue,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.RenderMesh import RenderMesh

KRepoRoot = FilePath(__file__).resolve().parents[6]


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@MarkTests.parametrize("ProfileName", ("circle", "extrusion", "frustum"))
def TestCircleScene(TmpPath: FilePath, ProfileName: str) -> None:
    Source = (
        KRepoRoot
        / "re/Fusion/LocalOracle/PublicAdapter"
        / ("vendor_" + ProfileName + "Edited.f3d")
    )
    Model = ReadDocument(Source.read_bytes())
    assert Model.Graphics is not None
    assert any(
        isinstance(Entry.Value, CircleArcValue) for Entry in Model.Graphics.Objects
    )
    HasMesh = any(
        isinstance(Entry.Value, RenderMesh) for Entry in Model.Graphics.Objects
    )
    assert HasMesh == (ProfileName == "circle")
    Target = TmpPath / "CircleGraphics.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    assert ReadDocument(Target.read_bytes()) == Model
    with ZipFile(Source) as Before, ZipFile(Target) as After:
        Members = tuple(
            Entry for Entry in Before.namelist() if "OGS.BlobFolder/" in Entry
        )
        assert Members
        for Entry in Members:
            assert After.read(Entry) == Before.read(Entry)
