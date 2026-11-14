from pathlib import Path as FilePath

from pytest import approx as ApproxValue

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Materials.MaterialFields import (
    MaterialFields,
)
from tests.convert.formats.FusionCodec.Documents.NamedGroups import NamedGroups
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectValues import ReadPoint


def TestTaperCache(TmpPath: FilePath) -> None:
    Source = TmpPath / "CachedTaper.f3d"
    _ = Source.write_bytes(
        EmitDocument(
            DocumentSpec(
                "Cached taper",
                "frustumHeight",
                17.0,
                ProfileKind="frustum",
                RadiusMm=10.0,
                TaperDegrees=7.0,
            )
        )
    )
    Model = ReadDocument(Source.read_bytes())
    Cached = MaterialFields(NamedGroups(Model, "Body")[0]["cache"])
    assert Cached["volume"] == ApproxValue(6.533057919954656)
    assert Cached["area"] == ApproxValue(19.61636501856793)
    assert ReadPoint(Cached["cog"]) == ApproxValue((0.0, 0.0, 0.9033932075833666))
    assert ReadPoint(Cached["moi"]) == ApproxValue(
        (8.911809723623081, 8.91181045979142, 4.043132092296158), rel=1e-6
    )
    assert ReadPoint(Cached["moiOffDiag"]) == (0.0, 0.0, 0.0)
