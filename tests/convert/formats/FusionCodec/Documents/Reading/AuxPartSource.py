from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart

KRepoRoot = FilePath(__file__).resolve().parents[6]
KSnapshotPaths = (
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
    "re/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d",
    "re/Fusion/LocalOracle/Features/extrude_07mm.f3d",
)


def NativeAuxParts(SourceIndex: int) -> tuple[ContainerPart, ...]:
    Prefix = "FusionAssetName[Active]/"
    with ZipFile(KRepoRoot / KSnapshotPaths[SourceIndex]) as Archive:
        return tuple(
            ContainerPart(NameValue.removeprefix(Prefix), Archive.read(NameValue))
            for NameValue in Archive.namelist()
            if NameValue.endswith((".smb", ".dsgcfg", ".dsgcfgrule"))
        )


def StoreAuxPart(PathValue: FilePath, Value: ContainerPart) -> ContainerPart:
    with ZipFile(PathValue, "w") as Archive:
        Archive.writestr(Value.Name, Value.Payload)
    with ZipFile(PathValue) as Archive:
        return ContainerPart(Value.Name, Archive.read(Value.Name))
