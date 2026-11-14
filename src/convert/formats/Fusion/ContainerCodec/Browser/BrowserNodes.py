from convert.formats.Fusion.ContainerCodec.Browser.BrowserNode import BrowserNode

KBrowserNodes = (
    BrowserNode(
        "component", "FusionComponentInstanceBrowserEntry", "root_instance", None
    ),
    BrowserNode("settings", "DocumentSettingsBrowserEntry", "settings", "component"),
    BrowserNode("named_views", "NamedViewsBrowserEntry", "named_views", "component"),
    BrowserNode("named_lights", "NamedLightsBrowserEntry", "named_lights", "component"),
    BrowserNode(
        "selection_groups",
        "SelectionGroupsBrowserEntry",
        "selection_groups",
        "component",
    ),
    BrowserNode("contacts", "ContactSetsBrowserEntry", "contacts", "component"),
    BrowserNode("origin", "OriginWorkGeometryBrowserEntry", "origin", "component"),
    BrowserNode(
        "motion_studies", "MotionStudiesBrowserEntry", "motion_studies", "component"
    ),
    BrowserNode(
        "joint_origins", "JointOriginsBrowserEntry", "joint_origins", "component"
    ),
    BrowserNode(
        "relationships",
        "RelationshipsBrowserEntry",
        "constraints",
        "component",
        "Ns::Comp::RelationshipsBrowserEntry",
    ),
    BrowserNode(
        "joints",
        "JointsBrowserEntry",
        "constraints",
        "relationships",
        "JointsBrowserEntry",
    ),
    BrowserNode(
        "rigid_groups",
        "RigidGroupsBrowserEntry",
        "constraints",
        "relationships",
        "Ns::Comp::RigidGroupsBrowserEntry",
    ),
    BrowserNode(
        "tangent",
        "TangentRelationshipsBrowserEntry",
        "constraints",
        "relationships",
        "TangentRelationshipsBrowserEntry",
    ),
    BrowserNode(
        "constraints",
        "ConstraintsBrowserEntry",
        "constraints",
        "relationships",
        "Ns::Comp::ConstraintsBrowserEntry",
    ),
    BrowserNode("bodies", "FusionBodiesBrowserEntry", "bodies", "component"),
    BrowserNode(
        "cache_bodies", "FusionBodiesBrowserEntry", "cache_bodies", "component"
    ),
    BrowserNode("canvases", "CanvasesBrowserEntry", "canvases", "component"),
    BrowserNode("annotations", "AnnotationsBrowserEntry", "annotations", "component"),
    BrowserNode("decals", "DecalPatchesBrowserEntry", "decals", "component"),
    BrowserNode("sketches", "FusionSketchesBrowserEntry", "sketches", "component"),
    BrowserNode(
        "construction", "FusionConstructionBrowserEntry", "work_geometries", "component"
    ),
    BrowserNode("eip_contexts", "EIPContextsBrowserEntry", "eip_contexts", "component"),
    BrowserNode(
        "surface_groups", "SurfaceGroupsBrowserEntry", "surface_groups", "component"
    ),
    BrowserNode(
        "work_groups",
        "WorkGeometryCustomGroupsBrowserEntry",
        "work_groups",
        "component",
    ),
    BrowserNode(
        "sketch_groups", "SketchCustomGroupsBrowserEntry", "sketch_groups", "component"
    ),
    BrowserNode("subd", "SubDSurfaceNodesBrowserEntry", "subd", "component"),
    BrowserNode(
        "arrangements", "ArrangementsBrowserEntry", "arrangements", "component"
    ),
    BrowserNode("units", "UnitsBrowserEntry", "units", "settings"),
    BrowserNode(
        "structure_type",
        "DocumentStructureTypeBrowserEntry",
        None,
        "settings",
        "Na::DocumentStructureTypeBrowserEntry",
    ),
    BrowserNode("pmi_settings", "PMISettingsBrowserEntry", "pmi_settings", "settings"),
    BrowserNode(
        "thread_settings", "ChangeThreadTypeBrowserEntry", "thread_settings", "settings"
    ),
)
