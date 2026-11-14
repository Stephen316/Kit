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


def CurveRecipe(TagId: int, IsReversed: bool) -> dict[str, object]:
    return dict(
        version=0,
        sketchTags=[SketchTag(TagId, IsReversed)],
        objectOffset20Set=[],
        objectOffset38Set=[],
    )


def CircleLoop(TagId: int) -> dict[str, object]:
    return {"first": [SketchTag(TagId, False)], "second": True}
