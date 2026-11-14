from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices


def CheckFaces(Topology: CageTopology) -> None:
    Visited: set[int] = set()
    for Index, FaceValue in enumerate(Topology.Faces):
        CheckIndices((FaceValue.OriginLink,), len(Topology.Links), "face root")
        if type(FaceValue.IsHidden) is not bool:
            raise ValueError("Invalid TSM face visibility")
        Current = FaceValue.OriginLink
        RingSet: set[int] = set()
        while Current not in RingSet:
            RingSet.add(Current)
            if Topology.Links[Current].FaceIndex != Index:
                raise ValueError("TSM face root ownership differs")
            Current = Topology.Links[Current].NextLink
        if Current != FaceValue.OriginLink or len(RingSet) != 4:
            raise ValueError("Unsupported TSM face valence or ring")
        Visited.update(RingSet)
    Expected = {
        Index
        for Index, LinkValue in enumerate(Topology.Links)
        if LinkValue.FaceIndex >= 0
    }
    if Visited != Expected:
        raise ValueError("TSM faces do not cover their links")
