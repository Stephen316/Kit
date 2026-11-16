from convert.Formats.Fusion.DocumentCodec.Extrusion.MassCache import MassCache
from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.Rectangle.CuboidCache import CuboidCache
from convert.Formats.Fusion.DocumentCodec.Tapered.TaperCache import TaperCache


# the body cache contract needs a shared interpretation so model state retains its native feature and ownership relationships
def BodyCache(Author: AuthorState) -> list[dict[str, object]]:
    if Author.SpecValue.ProfileKind == "cuboid":
        return CuboidCache(Author)
    if Author.SpecValue.ProfileKind == "frustum":
        return TaperCache(Author)
    return MassCache(Author)
