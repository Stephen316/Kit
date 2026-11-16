from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix


# the part dirs contract needs a shared interpretation so archive members retain their native ownership and reference relationships
def PartDirs(Values: tuple[ContainerPart, ...]) -> set[str]:
    return {
        KAssetPrefix + "/".join(Entry.Name.split("/")[:Index]) + "/"
        for Entry in Values
        for Index in range(1, len(Entry.Name.split("/")))
    }
