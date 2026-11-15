from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

# the profile order order must stay explicit so feature parameters remain connected to the resulting geometry
KProfileOrder = (2, 1, 0, 3)

# floor side must remain consistent across callers so feature parameters remain connected to the resulting geometry
KFloorSide = 0

# right side must remain consistent across callers so feature parameters remain connected to the resulting geometry
KRightSide = 1

# roof side must remain consistent across callers so feature parameters remain connected to the resulting geometry
KRoofSide = 2

# left side must remain consistent across callers so feature parameters remain connected to the resulting geometry
KLeftSide = 3

# first face tag must remain consistent across callers so feature parameters remain connected to the resulting geometry
KFirstFaceTag = 3


# the sweep tags contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
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


# the side label contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def SideLabel(
    TagMap: dict[tuple[int, int], int], SideIndex: int, Operation: int
) -> FaceLabel:
    Numbers = sorted(
        TagValue for (FaceSide, _), TagValue in TagMap.items() if FaceSide == SideIndex
    )
    Groups = tuple(FaceLabel(str(TagValue), (Operation,)) for TagValue in Numbers)
    return ReplaceValue(Groups[0], Merged=Groups[1:])


# the wall label contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def WallLabel(
    TagMap: dict[tuple[int, int], int], SideIndex: int, Place: int, Operation: int
) -> FaceLabel:
    return FaceLabel(str(TagMap[(SideIndex, Place)]), (Operation,))


# the face ids contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
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
