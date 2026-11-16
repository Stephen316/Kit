from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


# the sketch role contract needs a shared interpretation so model state retains its native feature and ownership relationships
def SketchRole(Author: AuthorState) -> str:
    return (
        "rectangle_sketch"
        if Author.SpecValue.ProfileKind in ("rectangle", "cuboid")
        else "circle_sketch"
    )
