from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage
from tests.convert.formats.FusionCodec.Materials.ChangeAssets import ChangeAssets
from tests.convert.formats.FusionCodec.Materials.Package.NativePackage import (
    NativePackage,
)


def TestNativePack(TmpPath: FilePath) -> None:
    Model = ReadPackage(NativePackage())
    assert len(Model.Assets) == 6
    assert len(Model.Schemas) == 11
    Target = TmpPath / "Reemitted.protein"
    _ = Target.write_bytes(EmitPackage(Model))
    with ZipFile(Target) as Archive:
        assert len(Archive.namelist()) == 25
        assert {
            NameValue.rsplit("/", 1)[-1]
            for NameValue in Archive.namelist()
            if NameValue.endswith(".bin")
        } == {
            "AssetTableOfContents.bin",
            "DefinitionIteratorProperties.bin",
            "InstanceProperties.bin",
        }
    assert ReadPackage(Target.read_bytes()) == Model


def TestPackageEdit(TmpPath: FilePath) -> None:
    Original = ReadPackage(NativePackage())
    Changed = ReplaceValue(Original, Assets=ChangeAssets(Original.Assets))
    Target = TmpPath / "Changed.protein"
    _ = Target.write_bytes(EmitPackage(Changed))
    Reopened = ReadPackage(Target.read_bytes())
    Densities = [
        Field.Value
        for Asset in Reopened.Assets
        for Field in Asset.Properties
        if Field.FieldName in ("structural_Density", "thermal_Density")
    ]
    assert Densities == [UnitValue(69633, 6300.0)] * 2
    assert Reopened == Changed
