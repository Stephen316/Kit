# the rectangle tag contract needs a shared interpretation so model state retains its native feature and ownership relationships
def RectangleTag(TagId: int, Direction: int) -> dict[str, object]:
    return dict(
        version=3,
        tagId=TagId,
        secondaryTagId=0,
        direction=Direction,
        splitSequenceId=1,
        splitTotalNumber=1,
        topologyRoleFlags=0,
    )
