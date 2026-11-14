from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric


def AddCollectMut(Author: AuthorState) -> None:
    Names = {
        "overrides": "Overrides",
        "component_instances": "ComponentInstances",
        "bodies": "Bodies",
        "sketches": "Sketches",
        "work_geometries": "WorkGeometries",
        "joint_origins": "JointOrigins",
        "constraints": "AssyConstraints",
        "constraint_occurrences": "AssyConstraintOccurrences",
        "contacts": "ContactSets",
        "motion_studies": "MotionStudies",
        "parameters": "ParameterTable",
        "surface_groups": "SurfaceGroups",
        "selection_groups": "SelectionGroups",
        "work_groups": "WorkGeometryCustomGroups",
        "sketch_groups": "SketchCustomGroups",
        "cache_bodies": "Bodies",
        "features": "Features",
        "origin": "OriginWorkGeometry",
        "relationships": "Relationships",
        "subd": "SubDSurfaceNodes",
        "canvases": "Canvases",
        "feature_groups": "DcGroupFeatures",
        "decals": "DecalPatches",
        "annotations": "PMIAnnotations",
        "meshes": "MeshBodies",
        "canvas_groups": "CanvasGroups",
        "deformers": "LatticeRigDeformers",
        "eip_contexts": "EIPContexts",
        "history_free_manager": "HistoryFreeUpdateManager",
        "arrangements": "Arrangements",
    }
    for RoleName, NameValue in Names.items():
        Author.Allocate(RoleName, NameValue, ParentRole="component")
    Author.Allocate("brep_history", "BRepHistorySerializer")
    Author.Allocate("cache_serializer", "BRepSerializer")
    Author.Allocate("passive_ids", "PassiveIdGenerator")
    HasLength = Author.SpecValue.ProfileKind != "form"
    Author.Allocate(
        "parameter_names",
        "ParameterSearchByNameHelper",
        Subjects=["parameters", "length_parameter"] if HasLength else ["parameters"],
    )
    Author.Allocate("local_context", "EIPContext", ParentRole="eip_contexts")
    if not HasLength:
        return
    Author.Allocate(
        "length_parameter",
        "ParameterMetaType".removesuffix("MetaType"),
        ParentRole="parameters",
        Fields=MakeNumeric(
            Author.SpecValue.ParamName,
            Author.SpecValue.LengthMm,
            Author.SpecValue.ParamComment,
            Author.Policy.ParamBirthday,
        ),
    )
