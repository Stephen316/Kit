from convert.formats.Fusion.DocumentCodec.Form.FormLabels import FormLabels
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState

KFrameKinds = (
    ("facet", "ControlFrameFacet"),
    ("edge", "ControlFrameEdge"),
    ("vertex", "ControlFrameVertex"),
    ("grip", "ControlFrameGrip"),
)


def FrameCounts(SpecValue: FormSpec) -> tuple[int, int, int, int]:
    Topology = SpecValue.Surface.Topology
    return (
        len(Topology.Faces),
        len(Topology.Edges),
        len(Topology.Vertices),
        len(SpecValue.Surface.Grips),
    )


def AddFrameMut(Author: AuthorState, SpecValue: FormSpec) -> None:
    Author.Allocate("form_frame", "ControlFrameMesh")
    Author.Allocate("form_surface", "TsSurface")
    Author.Allocate("form_tessellation", "SurfaceTessellation")
    Author.Allocate("form_serializer", "TSplineSerializer")
    Author.Allocate(
        "form_node",
        "SubDSurfaceNode",
        ParentRole="subd",
        NamedPairs=[
            {
                "name": "BASEFEAT_PM_BODIES_REF",
                "metatype": "Vector",
                "element": "PassiveRefMetaType",
                "roles": ["body"],
            }
        ],
    )
    Author.Allocate("form_node_tags", "ProgenitorTable")
    for (KindName, ClassName), Count in zip(KFrameKinds, FrameCounts(SpecValue)):
        for Index in range(Count):
            Author.Allocate(f"form_{KindName}_{Index}", ClassName)


def AddFormMut(Author: AuthorState, SpecValue: FormSpec) -> None:
    Author.Allocate(
        "form_feature", "DcTSplineFeature", ParentRole="nodes", NamedPairs=[]
    )
    Author.Allocate("form_feature_dynamic", "DynamicUpdateData")
    Author.Allocate("form_feature_status", "DcStatus", NamedPairs=[])
    Author.Allocate("form_feature_tags", "ProgenitorTable")
    Author.Allocate("form_data", "DirectModelingData", ParentRole="nodes")
    Author.Allocate("form_data_dynamic", "DynamicUpdateData")
    Author.Allocate("form_tool", "DcTSplineToolBody", ParentRole="nodes")
    Author.Allocate("form_tool_dynamic", "DynamicUpdateData")
    Author.Allocate("form_tool_status", "DcStatus", NamedPairs=[])
    AddFrameMut(Author, SpecValue)
    for LabelValue in FormLabels(SpecValue.Body):
        Author.Allocate("form_label_" + LabelValue.Label, "TSplineEntityProgenitor")
    Author.Allocate("form_tool_cache", "ETCachedTopology")
    Author.Allocate("form_tool_progenitor", "EntityProgenitor")
    Author.Allocate("form_tool_recipe", "EntityRecipe")
    Author.Allocate("body_progenitor", "BodyProgenitor")
    Author.Allocate(
        "body",
        "Body",
        ParentRole="bodies",
        NamedPairs=[
            {
                "name": "FORMFEAT_DM_SUBD_REF",
                "metatype": "PassiveRefMetaType",
                "role": "form_node",
            }
        ],
    )
    Author.Allocate("bodies_root", "BodiesRoot", RootName="BodiesRoot")
    Author.Allocate("body_passive_ids", "PassiveIdGenerator")
    Author.Allocate("dc_body", "DcBody", ParentRole="fragment")
