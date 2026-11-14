from pathlib import Path as FilePath
from typing import Literal

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Dimensions.CheckConstr import (
    CheckConstr,
)
from tests.convert.formats.FusionCodec.Documents.Dimensions.CheckDimensions import (
    CheckDimensions,
)
from tests.convert.formats.FusionCodec.Documents.Dimensions.CheckDimSlots import (
    CheckDimSlots,
)
from tests.convert.formats.FusionCodec.Documents.Dimensions.CheckDimGraph import (
    CheckDimGraph,
)
from tests.convert.formats.FusionCodec.Documents.Rectangle.CheckRectGraph import (
    CheckRectGraph,
)


@MarkTests.parametrize("ProfileKind", ("rectangle", "cuboid"))
@MarkTests.parametrize("Constrained", (False, True))
def TestDimArchive(
    TmpPath: FilePath, ProfileKind: Literal["rectangle", "cuboid"], Constrained: bool
) -> None:
    Specification = DocumentSpec(
        "Independent dimensioned rectangle",
        "boxHeight",
        31.0,
        ProfileKind=ProfileKind,
        WidthMm=17.0,
        DepthMm=23.0,
        ConstrainRectangle=Constrained,
        WidthParamName="boxWidth",
        DepthParamName="boxDepth",
    )
    Source = TmpPath / "Dimensioned.f3d"
    _ = Source.write_bytes(EmitDocument(Specification))
    Model = ReadDocument(Source.read_bytes())
    if Constrained:
        CheckConstr(Model)
        CheckDimensions(Model)
        CheckDimSlots(Model)
        CheckDimGraph(Model)
    else:
        CheckRectGraph(Model)
    assert len(Model.Bodies) == int(ProfileKind == "cuboid")
    Target = TmpPath / "Reemitted.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened.Segments == Model.Segments
    assert Reopened.Bodies == Model.Bodies
    assert Reopened.Materials == Model.Materials
