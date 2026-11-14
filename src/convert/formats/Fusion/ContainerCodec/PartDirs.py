from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix


def PartDirs(Values: tuple[ContainerPart, ...]) -> set[str]:
    return {
        KAssetPrefix + "/".join(Entry.Name.split("/")[:Index]) + "/"
        for Entry in Values
        for Index in range(1, len(Entry.Name.split("/")))
    }
