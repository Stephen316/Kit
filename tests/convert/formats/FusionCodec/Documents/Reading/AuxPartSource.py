from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart

# repo root needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KRepoRoot = FilePath(__file__).resolve().parents[6]

# the snapshot paths cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KSnapshotPaths = (
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
    "re/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d",
    "re/Fusion/LocalOracle/Features/extrude_07mm.f3d",
)


# shared native aux parts setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def NativeAuxParts(SourceIndex: int) -> tuple[ContainerPart, ...]:
    Prefix = "FusionAssetName[Active]/"
    with ZipFile(KRepoRoot / KSnapshotPaths[SourceIndex]) as Archive:
        return tuple(
            ContainerPart(NameValue.removeprefix(Prefix), Archive.read(NameValue))
            for NameValue in Archive.namelist()
            if NameValue.endswith((".smb", ".dsgcfg", ".dsgcfgrule"))
        )


# shared store aux part setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def StoreAuxPart(PathValue: FilePath, Value: ContainerPart) -> ContainerPart:
    with ZipFile(PathValue, "w") as Archive:
        Archive.writestr(Value.Name, Value.Payload)
    with ZipFile(PathValue) as Archive:
        return ContainerPart(Value.Name, Archive.read(Value.Name))
