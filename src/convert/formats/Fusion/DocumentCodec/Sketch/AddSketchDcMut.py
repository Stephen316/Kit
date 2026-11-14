from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def AddSketchDcMut(Author: AuthorState) -> None:
    Author.Allocate("dc_sketch", "DcSketch", ParentRole="nodes")
    Author.Allocate("sketch_progenitors", "ProgenitorTable")
    Author.Allocate("sketch_plane", "EntityDataRef", ParentRole="nodes")
    Author.Allocate("plane_recipe", "EntityRecipe")
    Author.Allocate("sketch_matrix", "DRMatrix", ParentRole="nodes")
    Author.Allocate("plane_cache", "ETCachedPlane")
    Author.Allocate("matrix_cache", "ETCachedMatrix3d")
    Author.Allocate("plane_progenitor", "EntityProgenitor")
    Author.Allocate("plane_progenitor_recipe", "EntityRecipe")
    for RoleName in ("dc_sketch", "sketch_plane", "sketch_matrix"):
        Author.Allocate(RoleName + "_dynamic", "DynamicUpdateData")
        Author.Allocate(RoleName + "_status", "DcStatus", NamedPairs=[])
