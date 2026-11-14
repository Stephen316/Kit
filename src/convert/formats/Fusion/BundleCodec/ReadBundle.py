from collections.abc import Callable

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.BundleCodec.Json.ReadModel import ReadModel
from convert.formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.formats.Fusion.BundleCodec.Model.FusionBundle import FusionBundle
from convert.formats.Fusion.BundleCodec.Validation.CheckModel import CheckModel


def ReadBundle(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> FusionBundle:
    if len(DataValue) > 128 * 1024 * 1024:
        raise ValueError("Fusion bundle exceeds archive limit")
    with OpenFusionZip(DataValue, InflateZstd) as Archive:
        Model = ReadModel(
            Archive.ReadMember("Manifest.json", 4 * 1024 * 1024),
            Archive.ReadMember("DesignDescription.json", 4 * 1024 * 1024),
        )
        CheckModel(Model)
        Names = {Entry.MemberPath for Entry in Model.Graph.Objects}
        if set(Archive.Entries) != Names | {"Manifest.json", "DesignDescription.json"}:
            raise ValueError("Fusion bundle members disagree with design graph")
        Documents = tuple(
            BundleFile(
                Entry.MemberPath, Archive.ReadMember(Entry.MemberPath, 64 * 1024 * 1024)
            )
            for Entry in Model.Graph.Objects
        )
    return FusionBundle(Model, Documents)
