from convert.formats.Fusion.AssetCodec.Zip.ZipNames import EncodeZipName
from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject
from convert.formats.Fusion.BundleCodec.Validation.CheckRefs import CheckRefs


def CheckObject(Value: BundleObject, ObjectIds: set[int]) -> None:
    _ = EncodeZipName(Value.MemberPath)
    if (
        "/" in Value.MemberPath
        or Value.DownloadAs != Value.MemberPath
        or not Value.MemberPath.endswith("." + Value.ContentType)
        or Value.Version < 1
        or Value.ObjectId < 1
    ):
        raise ValueError("Invalid Fusion bundle document identity")
    if not Value.VersionUrn.endswith(f"?version={Value.Version}"):
        raise ValueError("Fusion bundle version URN disagrees")
    if not Value.LineageUrn.startswith("urn:") or not Value.VersionUrn.startswith(
        "urn:"
    ):
        raise ValueError("Invalid Fusion bundle lineage or version URN")
    if not Value.StorageUrn.startswith("urn:adsk.objects:os.object:"):
        raise ValueError("Invalid Fusion bundle storage URN")
    if len({Group.KindValue for Group in Value.References}) != len(Value.References):
        raise ValueError("Duplicate Fusion bundle reference group")
    for Group in Value.References:
        CheckRefs(Group, ObjectIds)
