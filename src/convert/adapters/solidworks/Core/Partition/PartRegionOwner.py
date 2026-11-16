from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Partition.PartAtomOwner import ReadOwnerAtoms
from convert.adapters.solidworks.Core.Partition.PartShellOwner import ReadShellOwner
from convert.Geometry.Parasolid import NativeId, ScanPartRecords
from interchange.brep.Topology.BrepModel import BrepModel


# decoded face IDs identify the raw shell independently of region order and geometry
def ReadRegionAtoms(
    DataValue: bytes, Regions: tuple[BrepModel, BrepModel]
) -> dict[str, tuple[int, int, int]]:
    Tables = ScanPartRecords(DataValue)
    if Tables is None:
        raise ArchiveError("cannot resolve native partition face records")
    Faces = Tables.bridges
    ShellIds = {Value.references[3] for Value in Faces.values()}
    RequireArch(len(ShellIds), len(Regions), "two native partition shells")
    ShellValues = [ReadShellOwner(DataValue, Faces, ShellId) for ShellId in ShellIds]
    Owners = frozenset(Owner for Owner, _, _ in ShellValues)
    RequireArch(len(Owners), len(Regions), "unique owners for the native shells")
    RequireArch(
        len({RegionId for _, RegionId, _ in ShellValues}),
        len(Regions),
        "unique native regions for the shells",
    )
    Roster = [FaceId for _, _, FaceIds in ShellValues for FaceId in FaceIds]
    RequireArch(
        (len(Roster), set(Roster)),
        (len(Faces), set(Faces)),
        "complete disjoint native face roster",
    )
    AtomByOwner = ReadOwnerAtoms(DataValue, Owners)
    RegionByFaces = {
        frozenset(Value.id for Value in Region.faces): Region.regions[0].id
        for Region in Regions
    }
    Identity: dict[str, tuple[int, int, int]] = {}
    for Owner, RegionId, FaceIds in ShellValues:
        Match = RegionByFaces.get(
            frozenset(NativeId("face", FaceId) for FaceId in FaceIds)
        )
        if Match is not None:
            Identity[Match] = (Owner, RegionId, AtomByOwner[Owner])
    RequireArch(
        len(Identity), len(Regions), "native face rosters identify both decoded regions"
    )
    return Identity
