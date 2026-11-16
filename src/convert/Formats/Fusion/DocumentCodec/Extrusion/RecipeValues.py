# the sketch tag contract needs a shared interpretation so model state retains its native feature and ownership relationships
def SketchTag(TagId: int, IsReversed: bool) -> dict[str, object]:
    return dict(
        version=3,
        tagId=TagId,
        secondaryTagId=0,
        direction=int(IsReversed),
        splitSequenceId=1,
        splitTotalNumber=1,
        objectOffset20=0,
    )


# the curve recipe contract needs a shared interpretation so model state retains its native feature and ownership relationships
def CurveRecipe(TagId: int, IsReversed: bool) -> dict[str, object]:
    return dict(
        version=0,
        sketchTags=[SketchTag(TagId, IsReversed)],
        objectOffset20Set=[],
        objectOffset38Set=[],
    )


# the circle loop contract needs a shared interpretation so model state retains its native feature and ownership relationships
def CircleLoop(TagId: int) -> dict[str, object]:
    return {"first": [SketchTag(TagId, False)], "second": True}
