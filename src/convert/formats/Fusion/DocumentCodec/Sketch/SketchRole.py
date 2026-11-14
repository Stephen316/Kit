from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def SketchRole(Author: AuthorState) -> str:
    return (
        "rectangle_sketch"
        if Author.SpecValue.ProfileKind in ("rectangle", "cuboid")
        else "circle_sketch"
    )
