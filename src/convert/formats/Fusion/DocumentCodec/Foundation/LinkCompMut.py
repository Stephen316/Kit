from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakeColor


def LinkCompMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    BodyFields: dict[str, object] = dict(
        isAsBuiltPositions=True,
        m_opacity=1.0,
        mappedProperties=[],
        operationSeedId=300,
        rClientContainers=[
            {"key": "arrangementsContainer", "value": Reference("arrangements")}
        ],
        rFeatRuleData=None,
        rLibaryItems=None,
        rSheetmetalData=None,
        rXRefManager=None,
        subType=0,
    )
    LinkRoles = dict(
        m_rCanvases="canvases",
        m_rDecalPatches="decals",
        m_rDeformers="deformers",
        m_rFeatures="features",
        m_rHFUM="history_free_manager",
        m_rOriginWorkGeometry="origin",
        m_rRelationships="relationships",
        m_rVSubDSurfaces="subd",
        rAnnotations="annotations",
        rCacheBodies="cache_bodies",
        rCanvasGroups="canvas_groups",
        rDesignFragment="fragment",
        rEIPContexts="eip_contexts",
        rGroupFeatures="feature_groups",
        rMeshBodies="meshes",
        m_SketchCustomGroups="sketch_groups",
        m_WorkGeometryCustomGroups="work_groups",
        rAssyConstraintOccs="constraint_occurrences",
        rAssyConstraints="constraints",
        rBodies="bodies",
        rContactSets="contacts",
        rJointOrigins="joint_origins",
        rMotionStudies="motion_studies",
        rParameterTable="parameters",
        rSelectionGroups="selection_groups",
        rSketches="sketches",
        rSurfaceGroups="surface_groups",
        rWorkGeometries="work_geometries",
        overrides="overrides",
        rComponentBaseInstances="component_instances",
    )
    BodyFields.update(
        {NameValue: Reference(RoleName) for (NameValue, RoleName) in LinkRoles.items()}
    )
    BodyFields.update(
        massProperties=Author.MakeValue("MassPropertiesValue"),
        rPersistedCustomGraphics=None,
        createdPreACT=False,
        creationIndex=0,
        cyclingColor=MakeColor(0.8, 0.8, 0.8),
        defaultPhysicalMaterial=Author.MakeValue("PhysicalMaterialValue"),
        isVisible=True,
        persistentId=Author.ComponentId,
        rACTComponent=Author.ActReference("component"),
        rOwningDeriveFeature=None,
        revisionGuid=Author.RevisionId,
        userName=Author.SpecValue.Title,
    )
    Author.Change("component", **BodyFields)
    Author.Change(
        "root_instance",
        bGroundToParent=False,
        bRigidSubAssembly=False,
        creationIndex=0,
        initialTransform={"identity": True},
        lastSavedTargetRevisionGuid=Author.RevisionId,
        persistentId=Author.InstanceId,
        rACTInstance=Author.ActReference("root_instance"),
        rOwningDeriveFeature=None,
        rTargetComponent=Reference("component"),
        transform={"identity": True},
        userName="",
        xAssetLinkName="",
    )
