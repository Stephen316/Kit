from convert.formats.Fusion.DocumentCodec.Extrusion.MassCache import MassCache
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.CuboidCache import CuboidCache
from convert.formats.Fusion.DocumentCodec.Tapered.TaperCache import TaperCache


def BodyCache(Author: AuthorState) -> list[dict[str, object]]:
    if Author.SpecValue.ProfileKind == "cuboid":
        return CuboidCache(Author)
    if Author.SpecValue.ProfileKind == "frustum":
        return TaperCache(Author)
    return MassCache(Author)
