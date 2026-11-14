from convert.formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths
from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel
from convert.formats.Fusion.BundleCodec.Validation.CheckGraph import CheckGraph
from convert.formats.Fusion.BundleCodec.Validation.CheckObject import CheckObject


def CheckModel(Value: BundleModel) -> None:
    Objects = Value.Graph.Objects
    Owners = {Entry.ObjectId: Entry for Entry in Objects}
    if not 0 < len(Objects) <= 4094 or len(Owners) != len(Objects):
        raise ValueError("Invalid Fusion bundle document count or duplicate identity")
    if len(Value.Graph.RootIds) != 1 or Value.Graph.RootIds[0] not in Owners:
        raise ValueError("Fusion bundle requires one indexed root")
    RootValue = Owners[Value.Graph.RootIds[0]]
    if Value.RootPath != RootValue.MemberPath or Value.CurrentVersion != str(
        RootValue.Version
    ):
        raise ValueError("Fusion bundle root or version disagrees")
    if len({Entry.VersionUrn for Entry in Objects}) != len(Objects):
        raise ValueError("Duplicate Fusion bundle version identity")
    CheckZipPaths(tuple(Entry.MemberPath for Entry in Objects))
    for Entry in Objects:
        CheckObject(Entry, set(Owners))
    CheckGraph(Value.Graph)
