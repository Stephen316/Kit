from pathlib import Path as FilePath
from typing import Literal

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Rectangle.CheckPrismGraph import (
    CheckPrismGraph,
)
from tests.convert.formats.FusionCodec.Documents.Rectangle.CheckRectGraph import (
    CheckRectGraph,
)
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectFields import RectFields


@MarkTests.parametrize("ProfileKind", ("rectangle", "cuboid"))
def TestRectArchive(
    TmpPath: FilePath, ProfileKind: Literal["rectangle", "cuboid"]
) -> None:
    SpecValue = DocumentSpec(
        "Independent rectangle",
        "boxHeight",
        31.0,
        ProfileKind=ProfileKind,
        WidthMm=17.0,
        DepthMm=23.0,
        SketchName="Box sketch",
        BodyName="Box body",
    )
    Source = TmpPath / "Rectangle.f3d"
    _ = Source.write_bytes(EmitDocument(SpecValue))
    Model = ReadDocument(Source.read_bytes())
    CheckRectGraph(Model)
    assert len(RectFields(Model, "DcExtrudeFeature")) == int(ProfileKind == "cuboid")
    if ProfileKind == "cuboid":
        CheckPrismGraph(Model)
    else:
        assert not Model.Bodies
    Target = TmpPath / "Reemitted.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened.Segments == Model.Segments
    assert Reopened.Bodies == Model.Bodies
