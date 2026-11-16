from collections.abc import Mapping
from struct import Struct

from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Partition.PartRecordBody import FindPartBodies
from convert.Geometry.Parasolid import TopologyRecord

# compact shell and region records carry reciprocal references and their common owner
KShellRecord = Struct(">HI8H")

# the solid region record carries the reference back to its owning shell
KRegionRecord = Struct(">HI6HB")


# the resolved region must point back to the same shell and body
def CheckRegion(DataValue: bytes, RegionId: int, Owner: int, ShellId: int) -> None:
    Matches = [
        Start
        for Start in FindPartBodies(DataValue, 19, KRegionRecord.size, HasMarker=True)
        for Index, NodeId, Attribute, BodyId, Sibling, Previous, Anchor, Extra, Sense in (
            KRegionRecord.unpack_from(DataValue, Start),
        )
        if (Index, BodyId, Anchor, Sense) == (RegionId, Owner, ShellId, ord("S"))
        and NodeId > 0
        and Previous > 1
        and (Attribute, Sibling, Extra) == (1, 1, 1)
    ]
    RequireArch(len(Matches), 1, "unique solid region owns its shell and body")


# every native face must resolve back to the same shell and predecessor
def ReadFaceChain(
    Faces: Mapping[int, TopologyRecord], ShellId: int, First: int
) -> frozenset[int]:
    Visited: set[int] = set()
    Previous, Index = 1, First
    while Index != 1:
        FaceValue = Faces.get(Index)
        if FaceValue is None or Index in Visited:
            raise ArchiveError("incomplete or cyclic native shell face chain")
        RequireArch(
            (FaceValue.references[1], FaceValue.references[3]),
            (Previous, ShellId),
            "reciprocal native shell and face references",
        )
        Visited.add(Index)
        Previous, Index = Index, FaceValue.references[0]
    return frozenset(Visited)


# one typed shell joins its native region record and complete face roster
def ReadShellOwner(
    DataValue: bytes, Faces: Mapping[int, TopologyRecord], ShellId: int
) -> tuple[int, int, frozenset[int]]:
    Matches = [
        (Owner, First, RegionId)
        for Start in FindPartBodies(DataValue, 13, KShellRecord.size, HasMarker=True)
        for Index, NodeId, Attribute, Owner, Sibling, First, LeftRef, Right, RegionId, Complement in (
            KShellRecord.unpack_from(DataValue, Start),
        )
        if Index == ShellId
        and NodeId > 0
        and First in Faces
        and (Attribute, Sibling, LeftRef, Right, Complement) == (1, 1, 1, 1, 1)
        and min(Owner, First, RegionId) > 1
    ]
    RequireArch(len(Matches), 1, "unique native shell record")
    Owner, First, RegionId = Matches[0]
    CheckRegion(DataValue, RegionId, Owner, ShellId)
    return Owner, RegionId, ReadFaceChain(Faces, ShellId, First)
