from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import KMaxPackage
from convert.formats.Fusion.MaterialCodec.Package.Reading.ReadPackageBody import (
    ReadPackageBody,
)
from convert.formats.Fusion.MaterialCodec.Package.Reading.ReadPackageRoot import (
    ReadPackageRoot,
)
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckPackage import (
    CheckPackage,
)


def ReadPackage(Payload: bytes) -> MaterialPackage:
    if type(Payload) is not bytes or not 0 < len(Payload) <= KMaxPackage:
        raise ValueError("Invalid material package size")
    with OpenFusionZip(Payload) as Archive:
        Prefix, HasResources = ReadPackageRoot(Archive)
        Result = ReadPackageBody(Archive, Prefix, HasResources)
        CheckPackage(Result)
        if (
            Prefix != Result.AssetCore.Identifier + "/"
            or frozenset(Archive.Entries) != Archive.ReadNames
        ):
            raise ValueError(
                "Material package contains unmatched identities or unsupported members"
            )
    return Result
