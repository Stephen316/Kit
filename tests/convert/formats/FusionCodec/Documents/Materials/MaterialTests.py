from pathlib import Path as FilePath
from typing import Literal

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from tests.convert.formats.FusionCodec.Documents.Materials.CheckMatLinks import (
    CheckMatLinks,
)


@MarkTests.parametrize("ProfileKind", ("extrusion", "cuboid"))
@MarkTests.parametrize("Density", (1000.0, 2870.0))
def TestBodyMat(
    TmpPath: FilePath, ProfileKind: Literal["extrusion", "cuboid"], Density: float
) -> None:
    Material = MaterialSpec(
        "Independent material", Density, ColorValue(0.2, 0.4, 0.6, 1.0)
    )
    SpecValue = DocumentSpec(
        "Material document",
        "bodyHeight",
        31.0,
        ProfileKind=ProfileKind,
        WidthMm=17.0,
        DepthMm=23.0,
        Material=Material,
    )
    Source = TmpPath / "Material.f3d"
    _ = Source.write_bytes(EmitDocument(SpecValue))
    Model = ReadDocument(Source.read_bytes())
    CheckMatLinks(Model)
    Assets = Model.Materials[0].Package.Assets
    assert sorted(Asset.SchemaName for Asset in Assets) == [
        "PhysMatSchema",
        "PrismOpaqueSchema",
        "StructuralBasicSchema",
    ]
    for Asset in Assets:
        Fields = {Field.FieldName: Field.Value for Field in Asset.Properties}
        for FieldName in ("structural_Density", "thermal_Density"):
            if FieldName in Fields:
                assert Fields[FieldName] == UnitValue(69633, Density)
        if "opaque_albedo" in Fields:
            assert Fields["opaque_albedo"] == Material.Color
        if Asset.AssetRole == "physicalmaterial":
            Names = {Field.FieldName: Field.Value for Field in Asset.Definitions}
            assert Names["UIName"] == Material.NameValue
    Target = TmpPath / "Reemitted.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened.Materials == Model.Materials
    assert Reopened.Segments == Model.Segments
    assert Reopened.Bodies == Model.Bodies
