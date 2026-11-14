from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def DimGraphEdges(Author: AuthorState) -> tuple[tuple[str, str, int], ...]:
    Edges = (
        ("dc_component", "dc_sketch", 4096),
        ("sketch_plane", "sketch_matrix", 1),
        ("sketch_matrix", "dc_sketch", 1),
        ("width_binding", "dc_sketch", 1),
        ("depth_binding", "dc_sketch", 1),
    )
    if Author.SpecValue.ProfileKind != "cuboid":
        return Edges
    return Edges + (
        ("dc_component", "dc_extrude", 4096),
        ("dc_sketch", "profile_region", 4),
        ("profile_region", "profile_model", 1),
        ("profile_model", "extrude_tool", 1),
        ("along_binding", "extrude_tool", 1),
        ("taper_binding", "extrude_tool", 1),
        ("extrude_tool", "dc_extrude", 1),
    )
