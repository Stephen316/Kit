from io import BytesIO as ByteStream
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue
from zipfile import ZipFile

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.GraphicsCodec.Model.Values.FieldValue import FieldValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.GraphicAttr import GraphicAttr
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)
from tests.convert.formats.FusionCodec.Documents.Graphics.FindValues import (
    FindValues,
)

KOpacityCases: tuple[tuple[str, str, int], ...] = (
    (
        "re/Fusion/LocalOracle/Features/vendor_23mm.f3d",
        "8e657ca5aa1591cdd18d4948995ecb384e2ea2bc571972bd46de5894fee71658",
        1,
    ),
    (
        "re/Fusion/LocalOracle/RolledHistory/vendor_ControlEdited.f3d",
        "1a485e2f44de6f6c08934d09007c322f075bbd0376d974aa9b30c3b95c20189a",
        3,
    ),
)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@MarkTests.parametrize(
    "CaseValue", KOpacityCases, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestOpacity(CaseValue: tuple[str, str, int]) -> None:
    Payload = ReadFormFile(CaseValue[0], CaseValue[1])
    Model = ReadDocument(Payload)
    Found = CastValue(
        list[GraphicAttr[SceneSet]], FindValues(Model.Graphics, GraphicAttr)
    )
    Opacity = [
        AttrValue for AttrValue in Found if AttrValue.ClassName == "OpacityAttribute"
    ]
    assert len(Opacity) == CaseValue[2]
    for AttrValue in Opacity:
        assert AttrValue.Fields == (
            FieldValue("Absolute", False),
            FieldValue("Opacity", 1.0),
        )
    Archive = EmitParsed(Model)
    assert ReadDocument(Archive) == Model
    with ZipFile(ByteStream(Payload)) as Before, ZipFile(ByteStream(Archive)) as After:
        Names = [
            NameValue
            for NameValue in Before.namelist()
            if "OGS.BlobFolder/" in NameValue
        ]
        assert len(Names) == 5
        for NameValue in Names:
            assert After.read(NameValue) == Before.read(NameValue)
