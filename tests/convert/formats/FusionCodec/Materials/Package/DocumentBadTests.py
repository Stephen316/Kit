from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from pytest import raises as ExpectError

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage


def TestMissingPack(TmpPath: FilePath) -> None:
    Source = EmitDocument(DocumentSpec("Missing material", "height", 17.0))
    Container = ReadContainer(Source)
    Parts = tuple(
        PartValue
        for PartValue in Container.Parts
        if not PartValue.Name.endswith(".protein")
    )
    Target = TmpPath / "MissingMaterial.f3d"
    _ = Target.write_bytes(EmitContainer(ReplaceValue(Container, Parts=Parts)))
    with ExpectError(ValueError, match="manager package is missing"):
        _ = ReadDocument(Target.read_bytes())


def TestWrongRole(TmpPath: FilePath) -> None:
    Source = EmitDocument(DocumentSpec("Wrong material role", "height", 17.0))
    Container = ReadContainer(Source)
    Material = next(
        PartValue
        for PartValue in Container.Parts
        if PartValue.Name.endswith(".protein")
    )
    Package = ReadPackage(Material.Payload)
    Assets = tuple(
        (
            ReplaceValue(Asset, AssetRole="Structural")
            if Asset.AssetRole == "physicalmaterial"
            else Asset
        )
        for Asset in Package.Assets
    )
    Changed = ReplaceValue(
        Material, Payload=EmitPackage(ReplaceValue(Package, Assets=Assets))
    )
    Parts = tuple(
        Changed if PartValue.Name == Material.Name else PartValue
        for PartValue in Container.Parts
    )
    Target = TmpPath / "WrongRole.f3d"
    _ = Target.write_bytes(EmitContainer(ReplaceValue(Container, Parts=Parts)))
    with ExpectError(ValueError, match="missing or incompatible asset"):
        _ = ReadDocument(Target.read_bytes())
