from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.ProfileSide import ProfileSide
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleRoles import (
    KLineRoles,
    KSideIndices,
)


def ProfileSides(Author: AuthorState) -> tuple[ProfileSide, ...]:
    Policy = Author.Policy
    if Author.SpecValue.ProfileKind != "cuboid":
        return (
            ProfileSide(
                "curve_progenitor",
                "curve_recipe",
                Policy.CurveProgenitorTag,
                Policy.FirstSketchTag + 2,
            ),
        )
    FirstTag = Policy.FirstSketchTag + 5
    return tuple(
        ProfileSide(
            KLineRoles[EdgeIndex] + "_progenitor",
            KLineRoles[EdgeIndex] + "_recipe",
            Policy.CurveProgenitorTag + SideIndex,
            FirstTag + EdgeIndex,
            FirstTag + (EdgeIndex - 1) % 4,
            FirstTag + (EdgeIndex + 1) % 4,
        )
        for SideIndex, EdgeIndex in enumerate(KSideIndices)
    )
