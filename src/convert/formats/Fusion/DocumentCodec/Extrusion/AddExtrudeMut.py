from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Extrusion.ProfileSides import ProfileSides


def AddExtrudeMut(Author: AuthorState) -> None:
    Author.Allocate("dc_extrude", "DcExtrudeFeature", ParentRole="nodes", NamedPairs=[])
    Author.Allocate("profile_model", "ModelDataRef", ParentRole="nodes")
    Author.Allocate("profile_region", "SketchRegionRef", ParentRole="nodes")
    Author.Allocate("region_recipe", "SketchRegionRecipe")
    Author.Allocate("along_parameter", "Parameter", ParentRole="parameters")
    Author.Allocate(
        "along_binding",
        "DcDoubleParameter",
        ParentRole="nodes",
        Subjects=["dc_extrude"],
    )
    Author.Allocate("taper_parameter", "Parameter", ParentRole="parameters")
    Author.Allocate(
        "taper_binding",
        "DcDoubleParameter",
        ParentRole="nodes",
        Subjects=["dc_extrude"],
    )
    Author.Allocate("extrude_tool", "DcExtrudeToolBody", ParentRole="nodes")
    Author.Allocate("extrude_progenitors", "ProgenitorTable")
    for SideValue in ProfileSides(Author):
        Author.Allocate(
            SideValue.ProgenitorRole, "SketchCurveProgenitor", NamedPairs=[]
        )
        Author.Allocate(SideValue.RecipeRole, "SketchCurveRecipe")
    Author.Allocate("body_progenitor", "BodyProgenitor")
    Author.Allocate("body", "Body", ParentRole="bodies")
    Author.Allocate("bodies_root", "BodiesRoot", RootName="BodiesRoot")
    Author.Allocate("body_passive_ids", "PassiveIdGenerator")
    Author.Allocate("dc_body", "DcBody", ParentRole="fragment")
    for RoleName in ("dc_extrude", "profile_model", "profile_region", "extrude_tool"):
        Author.Allocate(RoleName + "_dynamic", "DynamicUpdateData")
        Author.Allocate(RoleName + "_status", "DcStatus", NamedPairs=[])
    for RoleName in ("along_binding", "taper_binding"):
        Author.Allocate(RoleName + "_dynamic", "DynamicUpdateData")
