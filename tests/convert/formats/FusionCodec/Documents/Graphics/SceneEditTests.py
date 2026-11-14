from sys import version_info as PythonVersion
from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.TextValue import TextValue
from tests.convert.formats.FusionCodec.Documents.Graphics.GraphicsSources import (
    KGraphicSources,
)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestTextEdit(TmpPath: FilePath) -> None:
    Model = ReadDocument(KGraphicSources[0].read_bytes())
    assert Model.Graphics is not None
    Selected = next(
        Entry
        for Entry in Model.Graphics.Objects
        if isinstance(Entry.Value, TextValue) and Entry.Value.TextData is not None
    )
    assert isinstance(Selected.Value, TextValue)
    Changed = ReplaceValue(
        Selected, Value=ReplaceValue(Selected.Value, TextData="Kit axis")
    )
    Objects = tuple(
        Changed if Entry.Reference == Selected.Reference else Entry
        for Entry in Model.Graphics.Objects
    )
    Scene = ReplaceValue(Model.Graphics, Objects=Objects)
    Target = TmpPath / "EditedGraphics.f3d"
    _ = Target.write_bytes(EmitParsed(ReplaceValue(Model, Graphics=Scene)))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened.Graphics == Scene
    assert Reopened.Segments == Model.Segments
    assert Reopened.Bodies == Model.Bodies
