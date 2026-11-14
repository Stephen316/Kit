from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

KProfileOrder = (2, 1, 0, 3)
KFloorSide = 0
KRightSide = 1
KRoofSide = 2
KLeftSide = 3
KFirstFaceTag = 3


def SweepTags(Count: int) -> dict[tuple[int, int], int]:
    TagMap: dict[tuple[int, int], int] = {}
    Rotated = (*range(1, Count), 0)
    for Segment in range(Count):
        for SideIndex in KProfileOrder:
            IsSpread = SideIndex in (KFloorSide, KRoofSide)
            if IsSpread and Segment:
                continue
            for Place in Rotated if IsSpread else (Segment,):
                TagMap[(SideIndex, Place)] = len(TagMap) + Count + KFirstFaceTag
    return TagMap


def SideLabel(
    TagMap: dict[tuple[int, int], int], SideIndex: int, Operation: int
) -> FaceLabel:
    Numbers = sorted(
        TagValue for (FaceSide, _), TagValue in TagMap.items() if FaceSide == SideIndex
    )
    Groups = tuple(FaceLabel(str(TagValue), (Operation,)) for TagValue in Numbers)
    return ReplaceValue(Groups[0], Merged=Groups[1:])


def WallLabel(
    TagMap: dict[tuple[int, int], int], SideIndex: int, Place: int, Operation: int
) -> FaceLabel:
    return FaceLabel(str(TagMap[(SideIndex, Place)]), (Operation,))


def FaceIds(TagMap: dict[tuple[int, int], int]) -> tuple[bytes, ...]:
    Firsts = {
        SideIndex: min(
            TagValue
            for (FaceSide, _), TagValue in TagMap.items()
            if FaceSide == SideIndex
        )
        for SideIndex in (KFloorSide, KRoofSide)
    }
    Labels = sorted(
        str(Firsts.get(SideIndex, TagValue))
        for (SideIndex, _), TagValue in TagMap.items()
    )
    return tuple(Label.encode("ascii") for Label in Labels)
