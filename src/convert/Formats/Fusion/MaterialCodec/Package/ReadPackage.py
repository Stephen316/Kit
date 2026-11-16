from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.Formats.Fusion.MaterialCodec.Package.PackageLimits import KMaxPackage
from convert.Formats.Fusion.MaterialCodec.Package.Reading.ReadPackageBody import (
    ReadPackageBody,
)
from convert.Formats.Fusion.MaterialCodec.Package.Reading.ReadPackageRoot import (
    ReadPackageRoot,
)
from convert.Formats.Fusion.MaterialCodec.Package.Validation.CheckPackage import (
    CheckPackage,
)


# the package operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
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
