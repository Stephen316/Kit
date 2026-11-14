from dataclasses import fields as DataFields
from math import isclose as IsClose
from typing import cast as CastValue

from pytest import mark as MarkTests, raises as ExpectError

from convert.adapters.Fusion.Projection.NativeMaterial import NativeMaterial
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Materials.BuildMaterial import BuildMaterial
from convert.formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import (
    ThermalSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.ProjectMaterial import (
    ProjectMaterial,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage
from tests.convert.formats.FusionCodec.Documents.Materials.BadFamilies import KBadCases
from tests.convert.formats.FusionCodec.Documents.Materials.MaterialCases import (
    KClassTypes,
    KFamilyCases,
)


def AssetRoles(Package: MaterialPackage) -> tuple[str, str | None, str]:
    Roles = {Asset.AssetRole: Asset.SchemaName for Asset in Package.Assets}
    assert len(Roles) == len(Package.Assets)
    assert Roles["physicalmaterial"] == "PhysMatSchema"
    return (Roles["Structural"], Roles.get("Thermal"), Roles["materialappearance"])


def PhysicalId(Package: MaterialPackage) -> str:
    Found = tuple(
        Asset.InstanceId
        for Asset in Package.Assets
        if Asset.SchemaName == "PhysMatSchema"
    )
    assert len(Found) == 1
    return Found[0]


def SameGiven(
    Given: MechanicSpec | ThermalSpec | FinishSpec,
    Found: MechanicSpec | ThermalSpec | FinishSpec,
) -> None:
    assert type(Found) is type(Given)
    for Field in DataFields(Given):
        Expected: object = getattr(Given, Field.name)
        Actual: object = getattr(Found, Field.name)
        if Expected is None:
            continue
        if type(Expected) is float and type(Actual) is float:
            assert IsClose(Actual, Expected, rel_tol=1e-12)
        elif isinstance(Expected, tuple) and isinstance(Actual, tuple):
            SameSteps(
                CastValue(tuple[DirectionValue, ...], Expected),
                CastValue(tuple[DirectionValue, ...], Actual),
            )
        else:
            assert Actual == Expected


def SameSteps(
    Expected: tuple[DirectionValue, ...], Actual: tuple[DirectionValue, ...]
) -> None:
    Found = {(Entry.FieldKey, Entry.Direction): Entry.Value for Entry in Actual}
    for Entry in Expected:
        assert IsClose(
            Found[(Entry.FieldKey, Entry.Direction)], Entry.Value, rel_tol=1e-12
        )


def SameMaterial(Given: MaterialSpec, Found: MaterialSpec) -> None:
    assert Found.NameValue == Given.NameValue
    assert IsClose(Found.Density, Given.Density, rel_tol=1e-12)
    assert Found.Color == Given.Color
    SameGiven(Given.Mechanics, Found.Mechanics)
    if Given.Thermal is None:
        assert Found.Thermal is None
    else:
        assert Found.Thermal is not None
        SameGiven(Given.Thermal, Found.Thermal)
    SameGiven(Given.Finish, Found.Finish)
    if Given.TypeName is not None:
        assert Found.TypeName == Given.TypeName


@MarkTests.parametrize("CaseName", tuple(KFamilyCases))
def TestFamilies(CaseName: str) -> None:
    SpecValue, Expected = KFamilyCases[CaseName]
    Built = BuildMaterial(SpecValue)
    assert AssetRoles(Built.Package) == Expected
    assert ReadPackage(EmitPackage(Built.Package)) == Built.Package


@MarkTests.parametrize("CaseName", tuple(KBadCases))
def TestBadFamily(CaseName: str) -> None:
    SpecValue, Message = KBadCases[CaseName]
    with ExpectError(ValueError, match=Message):
        _ = BuildMaterial(SpecValue)


@MarkTests.parametrize("CaseName", tuple(KFamilyCases))
def TestFixPoint(CaseName: str) -> None:
    SpecValue, Expected = KFamilyCases[CaseName]
    Built = BuildMaterial(SpecValue)
    Projected = ProjectMaterial(Built.Package, PhysicalId(Built.Package))
    SameMaterial(SpecValue, Projected)
    assert Projected.ClassName == Expected[0][len("Structural") : -len("Schema")]
    assert Projected.TypeName == (SpecValue.TypeName or KClassTypes[CaseName])
    Again = BuildMaterial(Projected)
    assert AssetRoles(Again.Package) == Expected
    Reprojected = ProjectMaterial(Again.Package, PhysicalId(Again.Package))
    assert Reprojected.ClassName == Projected.ClassName
    SameMaterial(Projected, Reprojected)


@MarkTests.parametrize("CaseName", tuple(KFamilyCases))
def TestFamilyDoc(CaseName: str) -> None:
    SpecValue = KFamilyCases[CaseName][0]
    Document = DocumentSpec(
        "Material family",
        "bodyHeight",
        30.0,
        ProfileKind="cuboid",
        WidthMm=10.0,
        DepthMm=20.0,
        Material=SpecValue,
    )
    Model = ReadDocument(EmitDocument(Document))
    SameMaterial(SpecValue, NativeMaterial(Model))
    assert ReadDocument(EmitParsed(Model)).Materials == Model.Materials
    assert DecodeState(EncodeState(SpecValue)) == SpecValue


def TestOldState() -> None:
    SpecValue = MaterialSpec("Older material", 2870.0, ColorValue(0.2, 0.4, 0.6, 1.0))
    Encoded = CastValue(dict[str, object], EncodeState(SpecValue))
    Fields = dict(CastValue(dict[str, object], Encoded["fields"]))
    for FieldName in ("ClassName", "Mechanics", "Thermal", "Finish", "TypeName"):
        del Fields[FieldName]
    assert DecodeState({**Encoded, "fields": Fields}) == SpecValue
