from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def LinkRootsMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "components_root", rootId="ComponentsRoot", rooted=[Reference("component")]
    )
    Author.Change(
        "instances_root",
        rootId="ComponentInstancesRoot",
        rooted=[Reference("root_instance")],
    )
    Author.Change("component_instances", rACTInstances=Author.ActReference("instances"))
    Author.Change(
        "settings",
        activeUnitSystem=Reference("unit_system"),
        threadSettings=Reference("thread_settings"),
        pmiSettings=Reference("pmi_settings"),
        namedViews=Reference("named_views"),
        rNamedLights=Reference("named_lights"),
    )
    Author.Change(
        "bodies",
        rBRepSerializer=Reference("brep_history"),
        surfaceGroups=Reference("surface_groups"),
    )
    Author.Change("brep_history", rBodies=Reference("bodies"))
    Author.Change("cache_bodies", rBRepSerializer=Reference("cache_serializer"))
    Author.Change(
        "cache_serializer",
        rBodies=Reference("cache_bodies"),
        topEntityPIDGenerator=Reference("passive_ids"),
    )
    Author.Change("sketches", sketchCustomGroups=Reference("sketch_groups"))
    Author.FindEntity("sketches").NamedPairs = [
        {"name": "crv_tag_id_idx", "metatype": "IntrinsicMetaTypeuint64", "value": 100}
    ]
    Author.Change("work_geometries", workGeometryCustomGroups=Reference("work_groups"))
    Author.Change("canvases", canvasGroups=Reference("canvas_groups"))
    HasLength = "length_parameter" in Author.Roles
    Author.Change(
        "parameters",
        highWaterMark=1 if HasLength else 0,
        rParameterSearchByNameHelper=Reference("parameter_names"),
    )
    Author.Change(
        "parameter_names",
        parameterMap=(
            [
                {
                    "key": Author.SpecValue.ParamName,
                    "value": Reference("length_parameter"),
                }
            ]
            if HasLength
            else []
        ),
    )
    Author.Change(
        "fragment",
        dcBodies=[],
        featureIndexMap=[],
        nextParamId=0,
        occurrences=[Reference("occurrence")],
        rAssociationManager=Reference("association"),
        rComputeManager=Reference("compute"),
        rCreationOrderFeatures=Reference("creation_order"),
        rDependencyManager=Reference("dependency"),
        rFeatureIdManager=Reference("feature_ids"),
        rNodes=Reference("nodes"),
        rXRefIdManager=Reference("xref"),
    )
    for RoleName in ("compute", "dependency", "association", "feature_ids", "xref"):
        Author.Change(RoleName, rOwnerFragment=Reference("fragment"))
    Author.Change(
        "dc_component",
        rFusionComponent=Reference("component"),
        rDynamicUpdateData=Reference("dynamic"),
    )
    Author.Change(
        "dynamic",
        rOwnerNode=Reference("dc_component"),
        timeStamp=Author.Policy.TimeStamp,
    )
    Author.Change("creation_order", rFragment=Reference("fragment"))
    PathValue = [
        Author.MakeGroup("OccurrencePathValue", {}),
        Author.MakeGroup(
            "BaseOccurrencePathValue",
            dict(
                componentInstances=[],
                creationState=3,
                passiveOccurrencePath=Author.MakeValue("ACTPassivePathValue"),
                sourceACTComponent=Author.ActReference("component"),
                sourceComponent=Reference("component"),
            ),
        ),
    ]
    Author.Change(
        "occurrence",
        contextPositionMap=[],
        dcAssyConstraintOccurrences=[],
        path=PathValue,
        stateIdx=-1,
        states=[],
    )
