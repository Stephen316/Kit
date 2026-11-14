from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Materials.CheckMatLinks import (
    CheckMatLinks,
)
from tests.convert.formats.FusionCodec.Documents.Tapered.CheckTaperGraph import (
    CheckTaperGraph,
)
from tests.convert.formats.FusionCodec.Documents.Tapered.CheckTaperRefs import (
    CheckTaperRefs,
)


@MarkTests.parametrize("Degrees", (-5.0, 0.0, 7.0))
def TestTaperDoc(TmpPath: FilePath, Degrees: float) -> None:
    SpecValue = DocumentSpec(
        "Independent tapered extrusion",
        "frustumHeight",
        17.0,
        ProfileKind="frustum",
        RadiusMm=10.0,
        TaperDegrees=Degrees,
        Material=MaterialSpec("Independent frustum material", 2870.0),
    )
    Source = TmpPath / "Tapered.f3d"
    _ = Source.write_bytes(EmitDocument(SpecValue))
    Model = ReadDocument(Source.read_bytes())
    CheckTaperGraph(Model, Degrees)
    CheckTaperRefs(Model, Degrees)
    CheckMatLinks(Model)
    Target = TmpPath / "Reemitted.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened.Segments == Model.Segments
    assert Reopened.Bodies == Model.Bodies
    assert Reopened.Materials == Model.Materials
